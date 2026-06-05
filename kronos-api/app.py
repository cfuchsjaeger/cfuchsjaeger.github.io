#!/usr/bin/env python3
"""Kronos forecast API.

A thin FastAPI wrapper around the Kronos foundation model that powers the
static portal at /kronos/. Loads the model once at startup, then serves
JSON forecasts on demand.

  GET /health
  GET /predict?ticker=NVDA&period=1y&interval=1d&pred_len=30

Response schema matches kronos/data/<TICKER>.json so the frontend renders
live and cached forecasts identically.

Run locally:
  pip install -r requirements.txt
  git clone --depth 1 https://github.com/shiyu-coder/Kronos _kronos
  KRONOS_REPO=$(pwd)/_kronos uvicorn app:app --host 0.0.0.0 --port 7860
"""

from __future__ import annotations

import os
import sys
from functools import lru_cache
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

# --- Kronos model import (repo cloned to $KRONOS_REPO) -----------------------
KRONOS_REPO = Path(os.environ.get("KRONOS_REPO", Path(__file__).resolve().parent / "_kronos"))
sys.path.insert(0, str(KRONOS_REPO))

import yfinance as yf  # noqa: E402

from model import Kronos, KronosTokenizer, KronosPredictor  # noqa: E402

TOKENIZER_ID = "NeoQuasar/Kronos-Tokenizer-base"
MODEL_ID = "NeoQuasar/Kronos-small"

# Allowed yfinance values — guard the inputs.
PERIODS = {"1mo", "3mo", "6mo", "1y", "2y", "5y", "max"}
INTERVALS = {"1d", "1h", "4h", "1wk", "1mo"}

app = FastAPI(title="Kronos Forecast API", version="1.0")

# CORS: allow the static site (and local dev) to call this API from the browser.
# Tighten allow_origins to your Pages origin in production if you prefer.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@lru_cache(maxsize=1)
def get_predictor() -> KronosPredictor:
    """Load tokenizer + model once and reuse across requests."""
    tokenizer = KronosTokenizer.from_pretrained(TOKENIZER_ID)
    model = Kronos.from_pretrained(MODEL_ID)
    return KronosPredictor(model, tokenizer, device="cpu", max_context=512)


def build_future_timestamps(last_ts: pd.Timestamp, interval: str, pred_len: int) -> pd.DatetimeIndex:
    if interval in ("1d",):
        delta = pd.Timedelta(days=1)
    elif interval in ("1wk",):
        delta = pd.Timedelta(weeks=1)
    elif interval in ("1mo",):
        delta = pd.DateOffset(months=1)
    elif interval.endswith("h"):
        delta = pd.Timedelta(hours=int(interval.rstrip("h")))
    elif interval.endswith("m"):
        delta = pd.Timedelta(minutes=int(interval.rstrip("m")))
    else:
        delta = pd.Timedelta(days=1)
    return pd.DatetimeIndex([last_ts + delta * (i + 1) for i in range(pred_len)])


def band_label(pct: float) -> str:
    return "NARROW" if pct < 5 else ("MODERATE" if pct < 10 else "WIDE")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "model": MODEL_ID}


@app.get("/predict")
def predict(
    ticker: str = Query(..., min_length=1, max_length=15),
    period: str = "1y",
    interval: str = "1d",
    pred_len: int = Query(30, ge=1, le=120),
    history_points: int = Query(65, ge=10, le=400),
) -> dict:
    ticker = ticker.upper().strip()
    if period not in PERIODS:
        raise HTTPException(400, f"period must be one of {sorted(PERIODS)}")
    if interval not in INTERVALS:
        raise HTTPException(400, f"interval must be one of {sorted(INTERVALS)}")

    data = yf.Ticker(ticker).history(period=period, interval=interval, auto_adjust=False)
    if data.empty:
        raise HTTPException(
            404,
            f"No data for {ticker} (period={period}, interval={interval}). "
            f"Check the symbol on Yahoo Finance. Crypto needs a -USD suffix (e.g. BTC-USD).",
        )

    hist = data[["Open", "High", "Low", "Close", "Volume"]].copy()
    hist.columns = ["open", "high", "low", "close", "volume"]
    hist.index.name = "timestamps"

    predictor = get_predictor()
    last_ts = hist.index[-1]
    forecast = predictor.predict(
        df=hist,
        x_timestamp=pd.Series(hist.index),
        y_timestamp=pd.Series(build_future_timestamps(last_ts, interval, pred_len)),
        pred_len=pred_len,
        T=1.0,
        top_p=0.9,
        sample_count=1,
    )

    last_close = round(float(hist["close"].iloc[-1]), 2)
    closes = [round(float(c), 2) for c in forecast["close"]]
    pred_close = closes[-1]
    pct = round((pred_close - last_close) / last_close * 100.0, 2)
    rng_lo, rng_hi = min(closes), max(closes)
    band_pct = round((rng_hi - rng_lo) / last_close * 100.0, 2)
    direction = "UP" if pct > 0.25 else ("DOWN" if pct < -0.25 else "FLAT")

    fdates = [t.strftime("%Y-%m-%d") for t in forecast.index]
    is_intraday = interval.endswith("h") or interval.endswith("m")
    fmt = "%Y-%m-%d %H:%M" if is_intraday else "%Y-%m-%d"

    hist_tail = hist.tail(history_points)
    history_out = [
        {"date": idx.strftime(fmt), "close": round(float(row["close"]), 2)}
        for idx, row in hist_tail.iterrows()
    ]
    forecast_out = [
        {
            "date": d,
            "open": round(float(r["open"]), 2),
            "high": round(float(r["high"]), 2),
            "low": round(float(r["low"]), 2),
            "close": round(float(r["close"]), 2),
        }
        for d, (_, r) in zip(fdates, forecast.iterrows())
    ]

    return {
        "ticker": ticker,
        "company": ticker,
        "as_of": last_ts.strftime(fmt),
        "period": period,
        "interval": interval,
        "pred_len": pred_len,
        "last_close": last_close,
        "last_date": last_ts.strftime(fmt),
        "predicted_close": pred_close,
        "pct_change": pct,
        "direction": direction,
        "band": band_label(band_pct),
        "band_pct": band_pct,
        "range_low": rng_lo,
        "range_high": rng_hi,
        "history": history_out,
        "forecast": forecast_out,
    }
