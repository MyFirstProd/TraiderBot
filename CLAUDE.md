# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TraiderBot is a production-grade paper trading bot for Bybit with ML-powered signal generation, risk management, and Telegram integration. The system runs continuously via Docker Compose with auto-retraining ML models every 10 minutes.

## Development Commands

### Local Development
```bash
# Install dependencies
python -m pip install -e ".[dev]"

# Run API server (with hot reload)
uvicorn app.main:app --reload

# Run trading worker (processes market data every 10 seconds)
python -m app.workers.main

# Run Telegram bot
python -m app.workers.telegram_bot

# Run tests
pytest

# Lint and format
ruff check .
black .
mypy app
```

### Docker Development
```bash
# Start all services
docker-compose up --build

# Restart specific service
docker-compose restart app
docker-compose restart worker

# View logs
docker-compose logs -f worker
docker-compose logs app --tail 50

# Run database migrations
docker-compose exec app alembic upgrade head
```

### Testing & Quality
```bash
# Run specific test
pytest tests/test_runtime_flow.py -v

# Security audit
bandit -r app
pip-audit
```

## Architecture

### Core Flow (Every 10 Seconds)
1. **Worker** (`app/workers/main.py`) triggers `TradingRuntimeService.cycle()`
2. **Market Data** fetched from Bybit via `app/integrations/bybit/client.py`
3. **Context Events** collected:
   - News via RSS feeds (`app/integrations/news/rss.py`)
   - Whale transactions via blockchain.com API (`app/integrations/whales/providers.py`)
4. **Strategy** (`app/strategies/scalping.py`) computes base score from indicators (EMA, RSI, volatility, spread)
5. **ML Model** (`app/ml/service.py`) provides probabilistic gate — entry requires BOTH rule-based signal AND model confirmation
6. **Risk Manager** (`app/risk/manager.py`) enforces:
   - Daily loss limits
   - Max concurrent positions
   - Spread thresholds
   - Circuit breaker on consecutive losses
7. **Paper Execution** (`app/execution/paper.py`) simulates position lifecycle
8. **Persistence** — all signals, trades, positions, risk events saved to PostgreSQL

### Auto-Retraining
- ML model retrains every 60 cycles (10 minutes) on accumulated market data
- Training uses real per-candle news and whale scores
- Model: HistGradientBoostingClassifier with cross-validation
- Artifacts saved to `artifacts/gbdt_model.joblib`

### Key Services
- **TradingRuntimeService** (`app/services/trading_runtime.py`) — orchestrates entire trading loop
- **MLModelService** (`app/ml/service.py`) — trains and scores GBDT model
- **ConfigService** (`app/services/config_service.py`) — manages strategy configs per symbol
- **NewsService** / **WhaleService** — collect external context events

### API Structure
- `/health` — health check
- `/api/v1/market/*` — market snapshots, signals, trades
- `/api/v1/admin/*` — manual model training, config management
- `/api/v1/telegram/*` — Mini App dashboard, bot webhooks

### Database Models
All in `app/models/`:
- `MarketSnapshot` — OHLCV + volatility + orderbook imbalance
- `Signal` — strategy output with rationale
- `Trade` / `Position` — paper trading state
- `NewsEvent` / `WhaleEvent` — external context
- `RiskEvent` — risk manager decisions
- `LlmInference` — LLM analysis cache (when enabled)

## Important Implementation Details

### F-String Escaping in HTML
When modifying `app/api/routes/telegram.py` mini_app function:
- HTML is embedded as Python f-string
- JavaScript template literals use `${{variable}}` (double braces to escape)
- Python variables use `{variable}` (single braces)
- Test syntax before committing — f-string errors crash the app

### Cloudflare Tunnel for HTTPS
- Mini App requires HTTPS for Telegram Web App API
- Cloudflare Tunnel runs via `cloudflared.exe` in project root
- URL format: `https://xxx.trycloudflare.com`
- Set in `.env`: `TELEGRAM_MINI_APP_URL=https://xxx.trycloudflare.com/api/v1/telegram/miniapp`
- Restart `telegram-bot` service after URL change

### Environment Variables
Critical vars in `.env`:
- `TELEGRAM_BOT_TOKEN` — required for bot to start
- `TELEGRAM_MINI_APP_URL` — must be HTTPS for Mini App to work
- `LLM_ENABLED=true` — enables news analysis (requires LiteLLM)
- `BYBIT_TESTNET=true` — uses testnet API (default for paper trading)
- `PAPER_TRADING=true` — never set to false without explicit confirmation

### Git Workflow
- Main branch: `main`
- CI/CD via GitHub Actions (`.github/workflows/ci-cd.yml`)
- Auto-deploy on push to main (requires GitHub Secrets: DEPLOY_HOST, DEPLOY_USER, DEPLOY_SSH_KEY, DEPLOY_URL)
- Always test locally before pushing

## Common Pitfalls

1. **Worker not processing** — Check `RUNTIME_LOOP_SECONDS` in settings, verify PostgreSQL/Redis are healthy
2. **Mini App not opening** — Ensure `TELEGRAM_MINI_APP_URL` starts with `https://`
3. **Model not training** — Check logs for `auto_retrain_starting`, verify sufficient data in `market_snapshots` table
4. **Telegram bot not responding** — Verify `TELEGRAM_BOT_TOKEN` is set, check `telegram-bot` service logs
5. **Docker build fails** — Clear build cache: `docker-compose build --no-cache`

## Testing Strategy

- Unit tests for indicators, strategies, risk logic
- Integration tests for API endpoints with test database
- Mock external APIs (Bybit, news feeds) in tests
- Run full test suite before committing: `pytest -v`

## Security Notes

- Never commit `.env` file
- API keys stored as secrets in GitHub Actions
- Admin endpoints protected by `X-API-Key` header
- Telegram initData validated via HMAC signature
- SQL injection prevented via SQLAlchemy ORM
- XSS in Mini App mitigated by using textContent where possible
