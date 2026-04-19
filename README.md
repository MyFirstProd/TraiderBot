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
- **Auto ML retraining** every 10 minutes on live market data
- **Real whale tracking** via blockchain.com API
- **Telegram Mini App** dashboard with real-time updates

## CI/CD Pipeline

GitHub Actions автоматически:
1. **Тестирует** код при каждом push/PR
2. **Собирает** Docker образы и пушит в GitHub Container Registry
3. **Деплоит** на production сервер при push в main/master

### Настройка деплоя

Добавь GitHub Secrets в репозитории:
- `DEPLOY_HOST` — IP или домен сервера
- `DEPLOY_USER` — SSH пользователь
- `DEPLOY_SSH_KEY` — приватный SSH ключ
- `DEPLOY_URL` — URL для health check (например, https://your-domain.com)

На сервере:
```bash
# Клонируй репозиторий
git clone https://github.com/your-username/TraiderBot.git /opt/traiderbot
cd /opt/traiderbot

# Создай .env файл
cp .env.example .env
nano .env  # Заполни переменные

# Запусти
docker-compose up -d
```

После настройки каждый push в main автоматически обновит production!
