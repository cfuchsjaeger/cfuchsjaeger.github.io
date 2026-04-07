# WatchDeal Vienna

A watch deal finder app that scrapes willhaben.at and Chrono24, scores deals using a multi-factor algorithm, analyzes top deals with Claude AI, and sends Telegram alerts for good finds. Includes an AI-powered listing generator for willhaben.at.

## Features

- **Automated Scraping**: Playwright-based scrapers for willhaben.at and Chrono24
- **Deal Scoring**: Multi-factor scoring (price vs market, condition, completeness, source reliability)
- **AI Analysis**: Claude Haiku analyzes deals and gives buy/watch/skip recommendations
- **Telegram Alerts**: Instant notifications for good deals via Telegram bot
- **AI Listing Generator**: Generate professional German watch listings with Claude
- **Price History**: Track price changes over time
- **Search Configs**: Configurable scraping targets (brand, model, price range)

## Quick Start

### Prerequisites

- Docker and Docker Compose

### Setup

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and fill in your API keys:
   - `ANTHROPIC_API_KEY`: Get from [console.anthropic.com](https://console.anthropic.com)
   - `TELEGRAM_BOT_TOKEN`: Create via [@BotFather](https://t.me/BotFather)
   - `TELEGRAM_CHAT_ID`: Your Telegram chat/channel ID

3. Start the application:
   ```bash
   docker-compose up -d
   ```

4. Open the app at [http://localhost:3000](http://localhost:3000)

The backend API is available at [http://localhost:8000](http://localhost:8000) with Swagger docs at [http://localhost:8000/docs](http://localhost:8000/docs).

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection URL | `postgresql://watchdeal:watchdeal@db:5432/watchdeal` |
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude AI | required |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | optional |
| `TELEGRAM_CHAT_ID` | Telegram chat ID for alerts | optional |
| `SCRAPE_INTERVAL_WILLHABEN` | Minutes between willhaben scrapes | `5` |
| `SCRAPE_INTERVAL_CHRONO24` | Minutes between Chrono24 scrapes | `15` |
| `MIN_DEAL_SCORE` | Minimum score to create a deal (0-1) | `0.6` |

## Development

### Backend (Python FastAPI)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
uvicorn app.main:app --reload
```

### Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
```

### Database Migrations

```bash
cd backend
alembic upgrade head
```

## Architecture

```
watchdeal-vienna/
├── backend/
│   ├── app/
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── scrapers/      # Playwright scrapers
│   │   ├── services/      # Business logic
│   │   ├── routers/       # FastAPI routes
│   │   ├── main.py        # App entrypoint
│   │   ├── config.py      # Settings
│   │   ├── database.py    # DB setup
│   │   └── scheduler.py   # APScheduler jobs
│   └── alembic/           # DB migrations
├── frontend/
│   └── src/
│       ├── api/           # API client
│       ├── components/    # Shared components
│       ├── pages/         # Page components
│       └── types/         # TypeScript types
└── docker-compose.yml
```
