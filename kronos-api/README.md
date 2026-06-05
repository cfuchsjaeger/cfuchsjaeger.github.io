# Kronos Forecast API

A small FastAPI service that wraps the [Kronos](https://github.com/shiyu-coder/Kronos)
foundation model and serves JSON forecasts to the static portal at `/kronos/`.

It loads `NeoQuasar/Kronos-small` once at startup, then answers:

| Endpoint | Description |
|---|---|
| `GET /health` | Liveness check. |
| `GET /predict?ticker=NVDA&period=1y&interval=1d&pred_len=30` | Run a forecast. |

The `/predict` response matches the shape of `kronos/data/<TICKER>.json`, so the
frontend renders live and cached forecasts identically.

> **Not financial advice.** Research tool only.

---

## Run locally

```bash
cd kronos-api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
git clone --depth 1 https://github.com/shiyu-coder/Kronos _kronos
KRONOS_REPO=$(pwd)/_kronos uvicorn app:app --host 0.0.0.0 --port 7860
# → http://localhost:7860/predict?ticker=AAPL
```

First call downloads the model weights from HuggingFace (~500MB); after that it's fast.

---

## Deploy

The model needs real RAM and a persistent process — **not** a short-lived
serverless function. Pick a host that runs a long-lived container.

### Option A — HuggingFace Spaces (free, recommended)

1. Create a new **Space** → SDK: **Docker**.
2. Upload the contents of this `kronos-api/` folder (`app.py`, `requirements.txt`,
   `Dockerfile`) to the Space repo.
3. The Space builds the image (the `Dockerfile` clones Kronos and pre-caches
   weights) and starts on port `7860`.
4. Your API base URL is `https://<your-username>-<space-name>.hf.space`.

### Option B — Render / Railway / Fly.io

- Point the service at this folder; they auto-detect the `Dockerfile`.
- Ensure at least **2 GB RAM**. Expose `$PORT` (the image already honors it).

### Option C — Any VM / Docker host

```bash
docker build -t kronos-api ./kronos-api
docker run -p 7860:7860 kronos-api
```

---

## Wire it into the portal

Open `https://cfuchsjaeger.github.io/kronos/`, click **⚙ API settings**, paste your
API base URL (e.g. the HF Space URL), and save. The search box and portfolio/
watchlist refresh will then run **live forecasts for any ticker**.

Until a URL is set, the portal falls back to the bundled `data/*.json` snapshots
(NVDA, NOW, BE).

## Notes & limits

- `period` ∈ {1mo, 3mo, 6mo, 1y, 2y, 5y, max}; `interval` ∈ {1d, 1h, 4h, 1wk, 1mo}
  (intraday limited to the last ~60 days by Yahoo). `pred_len` ∈ [1, 120].
- CORS is open (`*`) for convenience — restrict `allow_origins` in `app.py` to
  your Pages origin if you want to lock it down.
- Forecasts are stochastic (`sample_count=1`); re-running a ticker gives a
  slightly different path. That's expected — read the confidence band, not the
  single line.
