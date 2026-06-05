---
title: Kronos Forecast API
emoji: 📈
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# Kronos Forecast API

A FastAPI wrapper around the [Kronos](https://github.com/shiyu-coder/Kronos) foundation model.
Serves live technical-analysis forecasts to the static portal at `cfuchsjaeger.github.io/kronos/`.

**Endpoints:**

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Liveness check |
| GET | `/predict?ticker=NVDA&period=1y&interval=1d&pred_len=30` | Run a forecast |

`period` ∈ {1mo, 3mo, 6mo, 1y, 2y, 5y, max} · `interval` ∈ {1d, 1h, 4h, 1wk, 1mo} · `pred_len` ∈ [1, 120]

---

## Deploy to HuggingFace Spaces

1. Create a new Space → **SDK: Docker**
2. Upload `app.py`, `requirements.txt`, `Dockerfile`, and this `README.md` to the Space repo
3. HF builds the image (~10–15 min first time, model weights pre-cached)
4. Space URL is `https://<username>-<space-name>.hf.space`
5. Paste that URL into the portal ⚙ settings at `cfuchsjaeger.github.io/kronos/`

## Run locally

```bash
git clone --depth 1 https://github.com/shiyu-coder/Kronos _kronos
pip install -r requirements.txt
KRONOS_REPO=$(pwd)/_kronos uvicorn app:app --host 0.0.0.0 --port 7860
```

> Research tool only. Not financial advice.
