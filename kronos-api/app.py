#!/usr/bin/env python3
"""Kronos forecast API — with indicators, analyst data, and Claude narrative.

  GET /health
  GET /predict?ticker=&period=&interval=&pred_len=&history_points=

Set ANTHROPIC_API_KEY env var to enable narrative generation.
"""

from __future__ import annotations

import logging
import os
import sys
import time
import random
import json
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("kronos")

KRONOS_REPO = Path(os.environ.get("KRONOS_REPO", Path(__file__).resolve().parent / "_kronos"))
sys.path.insert(0, str(KRONOS_REPO))

import yfinance as yf
from model import Kronos, KronosTokenizer, KronosPredictor

TOKENIZER_ID = "NeoQuasar/Kronos-Tokenizer-base"
MODEL_ID     = "NeoQuasar/Kronos-small"
PERIODS      = {"1mo", "3mo", "6mo", "1y", "2y", "5y", "max"}
INTERVALS    = {"1d", "1h", "4h", "1wk", "1mo"}

app = FastAPI(title="Kronos Forecast API", version="2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])


@lru_cache(maxsize=1)
def get_predictor() -> KronosPredictor:
    tokenizer = KronosTokenizer.from_pretrained(TOKENIZER_ID)
    model = Kronos.from_pretrained(MODEL_ID)
    return KronosPredictor(model, tokenizer, device="cpu", max_context=512)


def fetch_with_retry(ticker: str, period: str, interval: str, max_attempts: int = 5) -> pd.DataFrame:
    last_exc: Exception | None = None
    for attempt in range(max_attempts):
        try:
            return yf.Ticker(ticker).history(period=period, interval=interval, auto_adjust=False)
        except Exception as e:
            msg = str(e).lower()
            if "rate limit" in msg or "429" in msg or "too many" in msg:
                if attempt == max_attempts - 1:
                    last_exc = e
                    break
                time.sleep((2 ** attempt) + random.uniform(0, 1))
                last_exc = e
            else:
                raise
    raise HTTPException(429, f"Yahoo Finance rate-limiting. Wait and retry. ({last_exc})")


def fetch_info(ticker: str) -> dict:
    try:
        info = yf.Ticker(ticker).info or {}
        log.info("[%s] fetch_info keys: %s", ticker, list(info.keys())[:15])
        return info
    except Exception as e:
        log.warning("[%s] fetch_info failed: %s", ticker, e)
        return {}


def calc_rsi(closes: pd.Series, period: int = 14) -> float:
    delta = closes.diff().dropna()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean().iloc[-1]
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean().iloc[-1]
    if avg_loss == 0:
        return 100.0
    return round(100 - 100 / (1 + avg_gain / avg_loss), 1)


def calc_macd(closes: pd.Series) -> dict:
    ema12 = closes.ewm(span=12, adjust=False).mean()
    ema26 = closes.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal = macd_line.ewm(span=9, adjust=False).mean()
    hist = macd_line - signal
    is_bull = bool(hist.iloc[-1] > 0)
    return {"bull": is_bull, "histogram": round(float(hist.iloc[-1]), 4)}


def build_indicators(hist: pd.DataFrame, info: dict, kronos_pct: float, kronos_band: str) -> dict:
    closes = hist["close"]
    score = 0.0
    pills = []

    ma50  = closes.rolling(50).mean().iloc[-1]  if len(closes) >= 50  else None
    ma200 = closes.rolling(200).mean().iloc[-1] if len(closes) >= 200 else None
    last  = closes.iloc[-1]
    if ma50 is not None and ma200 is not None:
        above50  = last > ma50
        above200 = last > ma200
        golden    = ma50 > ma200
        side = "bull" if (above50 and above200 and golden) else ("bear" if (not above50 and not above200) else "neutral")
        score += 1 if side == "bull" else (-1 if side == "bear" else 0)
        val = "Above 50/200" if (above50 and above200) else ("Below 50/200" if (not above50 and not above200) else "Mixed")
        pills.append({"name": "Long-term Trend", "value": val,
                      "sub": f"50d ${ma50:.0f}  200d ${ma200:.0f}", "side": side})
    elif ma50 is not None:
        side = "bull" if last > ma50 else "bear"
        score += 1 if side == "bull" else -1
        pills.append({"name": "Long-term Trend", "value": "Above 50d" if side == "bull" else "Below 50d",
                      "sub": f"50d ${ma50:.0f}  (200d N/A)", "side": side})
    else:
        pills.append({"name": "Long-term Trend", "value": "N/A", "sub": "Not enough data", "side": "neutral"})

    if len(closes) >= 35:
        m = calc_macd(closes)
        side = "bull" if m["bull"] else "bear"
        score += 1 if side == "bull" else -1
        pills.append({"name": "MACD", "value": "Bullish" if m["bull"] else "Bearish",
                      "sub": f"Histogram {m['histogram']:+.4f}", "side": side})
    else:
        pills.append({"name": "MACD", "value": "N/A", "sub": "Not enough data", "side": "neutral"})

    if len(closes) >= 16:
        rsi = calc_rsi(closes)
        if rsi >= 70:
            side, label = "bear", "Overbought"
        elif rsi <= 30:
            side, label = "bull", "Oversold"
        else:
            side, label = "neutral", "Neutral"
        score += 1 if side == "bull" else (-1 if side == "bear" else 0)
        pills.append({"name": "RSI (14)", "value": label, "sub": f"RSI = {rsi}", "side": side})
    else:
        pills.append({"name": "RSI (14)", "value": "N/A", "sub": "Not enough data", "side": "neutral"})

    pe = info.get("trailingPE") or info.get("forwardPE")
    pe_type = "trailing" if info.get("trailingPE") else "forward"
    if pe and pe > 0:
        if pe < 15:
            side, label = "bull", "Cheap"
        elif pe > 40:
            side, label = "bear", "Expensive"
        else:
            side, label = "neutral", "Fair"
        score += 1 if side == "bull" else (-1 if side == "bear" else 0)
        pills.append({"name": "Valuation", "value": label,
                      "sub": f"{pe_type} P/E {pe:.1f}x", "side": side})
    else:
        pills.append({"name": "Valuation", "value": "N/A", "sub": "P/E unavailable", "side": "neutral"})

    rev_growth = info.get("revenueGrowth")
    if rev_growth is not None:
        if rev_growth >= 0.15:
            side, label = "bull", "Strong growth"
        elif rev_growth < 0:
            side, label = "bear", "Declining"
        else:
            side, label = "neutral", "Moderate"
        score += 1 if side == "bull" else (-1 if side == "bear" else 0)
        pills.append({"name": "Fundamentals", "value": label,
                      "sub": f"Rev growth {rev_growth*100:.1f}%", "side": side})
    else:
        pills.append({"name": "Fundamentals", "value": "N/A", "sub": "Revenue data N/A", "side": "neutral"})

    if kronos_band == "NARROW":
        side = "bull" if kronos_pct > 0.25 else ("bear" if kronos_pct < -0.25 else "neutral")
        score += 1 if side == "bull" else (-1 if side == "bear" else 0)
        label = "Bullish" if side == "bull" else ("Bearish" if side == "bear" else "Flat")
    elif kronos_band == "MODERATE":
        side = "neutral"
        label = "Uncertain"
    else:
        side = "bear" if kronos_pct < -5 else "neutral"
        score += -1 if side == "bear" else 0
        label = "High uncertainty"
    pills.append({"name": "Kronos 30d", "value": label,
                  "sub": f"{kronos_pct:+.1f}%  band {kronos_band}", "side": side})

    call = "BUY" if score >= 2.5 else ("SELL" if score <= -2.5 else "HOLD")
    return {"pills": pills, "call": call, "score": round(score, 1)}


def fetch_analyst(info: dict, last_close: float) -> dict:
    rec = info.get("recommendationKey", "")
    target = info.get("targetMeanPrice")
    upside = round((target - last_close) / last_close * 100, 1) if target and last_close else None
    num_analysts = info.get("numberOfAnalystOpinions")
    result = {
        "consensus": rec.replace("_", " ").title() if rec else "N/A",
        "target": round(float(target), 2) if target else None,
        "upside": upside,
        "num_analysts": num_analysts,
    }
    log.info("[analyst] recommendationKey=%r targetMeanPrice=%r result=%s", rec, target, result)
    return result


def generate_narrative(ticker: str, company: str, indicators: dict, analyst: dict,
                       last_close: float, pred_close: float, pct: float) -> dict | None:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        log.warning("[narrative] ANTHROPIC_API_KEY not set — skipping narrative")
        return None
    log.info("[narrative] calling Claude for %s (key present, len=%d)", ticker, len(api_key))
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        pill_lines = "\n".join(
            f"  - {p['name']}: {p['value']} ({p['sub']}) [{p['side']}]"
            for p in indicators["pills"]
        )
        prompt = (
            f"You are a senior equity analyst writing a concise stock tearsheet note.\n"
            f"Ticker: {ticker} | Company: {company}\n"
            f"Current price: ${last_close} | Kronos 30d forecast: ${pred_close} ({pct:+.1f}%)\n"
            f"Mechanical call: {indicators['call']} (score {indicators['score']})\n"
            f"Indicators:\n{pill_lines}\n"
            f"Analyst consensus: {analyst['consensus']} | Target: "
            f"{'$'+str(analyst['target']) if analyst['target'] else 'N/A'} "
            f"(upside {analyst['upside']}%)\n\n"
            f"Respond with ONLY valid JSON (no markdown) matching this exact schema:\n"
            '{"headline":"<10-word bold thesis>","subhead":"<20-word supporting context>",'
            '"bear_bullets":["<risk 1>","<risk 2>","<risk 3>"],'
            '"bull_bullets":["<catalyst 1>","<catalyst 2>","<catalyst 3>"],'
            '"action":"<1-2 sentence tactical suggestion>"}'
        )
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        text = msg.content[0].text.strip()
        log.info("[narrative] Claude response: %s", text[:120])
        return json.loads(text)
    except Exception as e:
        log.error("[narrative] failed: %s", e, exc_info=True)
        return None


def build_future_timestamps(last_ts: pd.Timestamp, interval: str, pred_len: int) -> pd.DatetimeIndex:
    if interval == "1d":
        delta = pd.Timedelta(days=1)
    elif interval == "1wk":
        delta = pd.Timedelta(weeks=1)
    elif interval == "1mo":
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

    data = fetch_with_retry(ticker, period, interval)
    if data.empty:
        raise HTTPException(404, f"No data for {ticker}. Check symbol on Yahoo Finance.")

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
    blabel = band_label(band_pct)

    is_intraday = interval.endswith("h") or interval.endswith("m")
    fmt = "%Y-%m-%d %H:%M" if is_intraday else "%Y-%m-%d"
    fdates = [t.strftime("%Y-%m-%d") for t in forecast.index]

    hist_tail = hist.tail(history_points)
    history_out = [
        {"date": idx.strftime(fmt), "close": round(float(row["close"]), 2)}
        for idx, row in hist_tail.iterrows()
    ]
    forecast_out = [
        {"date": d, "open": round(float(r["open"]), 2), "high": round(float(r["high"]), 2),
         "low": round(float(r["low"]), 2), "close": round(float(r["close"]), 2)}
        for d, (_, r) in zip(fdates, forecast.iterrows())
    ]

    info = fetch_info(ticker)
    company = info.get("shortName") or info.get("longName") or ticker
    exchange_map = {"NMS": "NASDAQ", "NYQ": "NYSE", "NGM": "NASDAQ", "PCX": "NYSE Arca",
                   "BTS": "BATS", "ASE": "AMEX"}
    exchange = exchange_map.get(info.get("exchange", ""), info.get("exchange", ""))

    indicators = build_indicators(hist, info, pct, blabel)
    analyst = fetch_analyst(info, last_close)
    narrative = generate_narrative(ticker, company, indicators, analyst, last_close, pred_close, pct)

    return {
        "ticker": ticker,
        "company": company,
        "exchange": exchange,
        "as_of": last_ts.strftime(fmt),
        "period": period,
        "interval": interval,
        "pred_len": pred_len,
        "last_close": last_close,
        "last_date": last_ts.strftime(fmt),
        "predicted_close": pred_close,
        "pct_change": pct,
        "direction": direction,
        "band": blabel,
        "band_pct": band_pct,
        "range_low": rng_lo,
        "range_high": rng_hi,
        "history": history_out,
        "forecast": forecast_out,
        "indicators": indicators,
        "analyst": analyst,
        "narrative": narrative,
    }
