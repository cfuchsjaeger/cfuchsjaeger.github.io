# Kronos Forecast API — container image.
# Works on HuggingFace Spaces (Docker SDK), Render, Railway, Fly.io, or any
# Docker host. Listens on $PORT (defaults to 7860, the HF Spaces convention).
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/tmp/hf \
    KRONOS_REPO=/app/_kronos \
    PORT=7860

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# Python deps first (better layer caching)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Kronos model code (the `model` module imported by app.py)
RUN git clone --depth 1 https://github.com/shiyu-coder/Kronos /app/_kronos

COPY app.py .

EXPOSE 7860

# Pre-cache the model weights at build time so the first request isn't slow.
RUN python -c "import os,sys; sys.path.insert(0,'/app/_kronos'); \
from model import Kronos, KronosTokenizer; \
KronosTokenizer.from_pretrained('NeoQuasar/Kronos-Tokenizer-base'); \
Kronos.from_pretrained('NeoQuasar/Kronos-small')" || true

CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT}"]
