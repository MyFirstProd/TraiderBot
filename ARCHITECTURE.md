# Architecture

## Layers

- `app/api`: FastAPI routes for health, market state, admin controls and Telegram-facing endpoints.
- `app/services`: orchestration layer for trading runtime, configs, news, whales, market data and LLM analysis.
- `app/ml`: baseline offline GBDT training and online model scoring.
- `app/integrations`: thin adapters for Bybit, RSS news, whale feeds, LiteLLM and Telegram Bot.
- `app/strategies`: deterministic strategy logic with indicators and scoring.
- `app/risk` and `app/execution`: risk gating and paper position lifecycle.
- `app/models`, `app/repositories`, `app/db`: persistence and database access.

## Decision flow

1. Worker requests latest market state from Bybit adapter.
2. News and whale collectors fetch context events.
3. Strategy computes base score from EMA/RSI/volatility/spread.
4. News and whale scores adjust, but do not replace, the deterministic signal.
5. GBDT baseline provides a separate probabilistic gate; entry requires both rules and model confirmation.
6. Risk manager enforces daily loss, max exposure, spread and circuit breaker limits.
7. Paper execution opens or closes simulated positions.
8. Signals, trades, positions, risk events and audit logs are persisted.
9. API and Telegram consumers read the current state from the database/runtime.

## LLM contour

- LiteLLM is used only for structured event assessment and explanation generation.
- Output is constrained to JSON and validated by Pydantic.
- When LLM is disabled or returns invalid output, runtime falls back to deterministic behavior.
