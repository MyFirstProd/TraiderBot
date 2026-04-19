# Security Review

## Fixed in this pass

- Removed hardcoded runtime secrets from application logic and moved them to environment-based settings.
- Added admin route protection through `X-API-Key`.
- Added Telegram Mini App `initData` signature validation and TTL checks.
- Added safe defaults: paper trading only, trading disabled, no live order path.
- Added request IDs, basic security headers and rate limiting middleware.
- Added non-root container execution.
- Added Bandit and `pip-audit` commands to the quality toolchain.
- Avoided raw SQL and shell interpolation in app code.
- Changed default bind host to `127.0.0.1`; container exposure is controlled explicitly by Docker/uvicorn command.
- Confirmed `pip-audit` reported no known third-party vulnerabilities in the installed environment.

## Residual risks

- In-memory rate limiting is single-instance only; Redis-backed limiter should replace it in clustered deployments.
- Bybit market data adapter currently falls back to synthetic data on transport failure; production should distinguish degraded mode more explicitly.
- Telegram bot command transport is scaffolded; webhook hardening and signature/IP validation should be completed before public exposure.
- LiteLLM output is validated, but prompt and provider policy controls should be tightened for production tenants.

## Recommendations

- Add vault-backed secret delivery.
- Add Prometheus metrics and alerting for risk breaches and degraded external integrations.
- Replace synthetic whale provider with authenticated upstream adapters.
- Add stricter RBAC and per-user audit scopes.
