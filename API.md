# API

## Public

- `GET /health`
- `GET /info`
- `GET /api/v1/market/signals`
- `GET /api/v1/market/positions`
- `GET /api/v1/market/trades`
- `GET /api/v1/market/news`
- `GET /api/v1/market/whales`
- `GET /api/v1/market/risk`

## Admin

Requires `X-API-Key`.

- `GET /api/v1/admin/config`
- `GET /api/v1/admin/strategies`
- `PUT /api/v1/admin/strategies/{symbol}`
- `POST /api/v1/admin/strategy/enable`
- `POST /api/v1/admin/strategy/disable`

## Telegram

- `POST /api/v1/telegram/miniapp/validate`
- `GET /api/v1/telegram/commands`
- `POST /api/v1/telegram/simulate/{command}`
