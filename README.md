# TraiderBot

Production-grade MVP skeleton for paper trading on Bybit with FastAPI, PostgreSQL, Redis, Telegram Bot, Telegram Mini App backend hooks, news/whale ingestion and LiteLLM-based explainability.

## Quick start

1. Copy `.env.example` to `.env`.
2. Run `docker compose up --build`.
3. Open `http://localhost:8000/health`.
4. API docs are available at `http://localhost:8000/docs`.
5. Telegram bot long polling starts in the `telegram-bot` service when `TELEGRAM_BOT_TOKEN` is set.

## Local development

- `python -m pip install -e ".[dev]"`
- `uvicorn app.main:app --reload`
- `python -m app.workers.main`
- `python -m app.workers.telegram_bot`
- `pytest`

## Core capabilities

- Paper trading runtime for `BTCUSDT`, `ETHUSDT`, `TONUSDT`
- RSI, SMA, EMA, WMA indicators
- Rule-based scalping strategy with explainability
- Risk manager with daily loss, exposure and circuit breaker controls
- PostgreSQL persistence for signals, trades, positions, news, whales and audit logs
- Telegram Bot command scaffold and Mini App initData validation
- LiteLLM structured output adapter with safe fallback
