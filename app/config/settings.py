from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    APP_NAME: str = "TraiderBot"
    APP_VERSION: str = "0.1.0"
    APP_ENV: Literal["local", "test", "staging", "prod"] = "local"
    DEBUG: bool = False
    API_PREFIX: str = "/api/v1"
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    ALLOWED_ORIGINS: list[str] = Field(default_factory=lambda: ["http://localhost:3000", "http://localhost:5173"])
    REQUESTS_PER_MINUTE: int = 120

    SECRET_KEY: SecretStr = SecretStr("change-me-change-me")
    ADMIN_API_KEY: SecretStr = SecretStr("change-me-admin-key")
    TELEGRAM_INITDATA_TTL_SECONDS: int = 3600

    DATABASE_URL: str = "postgresql+asyncpg://traderbot:traderbot@postgres:5432/traderbot"
    REDIS_URL: str = "redis://redis:6379/0"

    BYBIT_API_KEY: SecretStr = SecretStr("")
    BYBIT_API_SECRET: SecretStr = SecretStr("")
    BYBIT_TESTNET: bool = True
    BYBIT_DEMO: bool = False
    BYBIT_CATEGORY: Literal["linear", "spot"] = "linear"
    BYBIT_TIMEOUT_SECONDS: float = 10.0

    TELEGRAM_BOT_TOKEN: SecretStr = SecretStr("")
    TELEGRAM_ALLOWED_USERS: list[int] = Field(default_factory=list)
    TELEGRAM_WEBHOOK_URL: str | None = None
    TELEGRAM_MINI_APP_URL: str | None = None

    LLM_ENABLED: bool = False
    LITELLM_API_BASE: str = "http://litellm:4000"
    LITELLM_API_KEY: SecretStr = SecretStr("")
    LITELLM_MODEL: str = "gpt-4o-mini"
    LITELLM_TIMEOUT_SECONDS: float = 15.0

    NEWS_ENABLED: bool = True
    NEWS_FEEDS: list[str] = Field(
        default_factory=lambda: [
            "https://www.coindesk.com/arc/outboundfeeds/rss/",
            "https://forklog.com/feed/",
        ]
    )
    WHALES_ENABLED: bool = True
    WHALE_ALERT_API_KEY: SecretStr = SecretStr("")
    TONAPI_KEY: SecretStr = SecretStr("")

    PAPER_TRADING: bool = True
    TRADING_ENABLED: bool = False
    STARTING_EQUITY: float = 10_000.0
    TRADING_SYMBOLS: list[str] = Field(default_factory=lambda: ["BTCUSDT", "ETHUSDT", "TONUSDT"])
    RISK_PER_TRADE_PCT: float = 0.003
    MAX_DAILY_LOSS_PCT: float = 0.02
    MAX_CONSECUTIVE_LOSSES: int = 4
    MAX_CONCURRENT_POSITIONS: int = 3
    MAX_TOTAL_EXPOSURE_PCT: float = 0.35
    CIRCUIT_BREAKER_ERRORS: int = 5
    MAX_SPREAD_BPS: float = 8.0
    EMERGENCY_SPREAD_BPS: float = 18.0
    MIN_VOLATILITY_BPS: float = 10.0
    MAX_VOLATILITY_BPS: float = 180.0
    RUNTIME_LOOP_SECONDS: int = 10

    @field_validator("SECRET_KEY", "ADMIN_API_KEY")
    @classmethod
    def validate_secret_length(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value()) < 16:
            raise ValueError("Secret must contain at least 16 characters")
        return value

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def normalize_origins(cls, value: list[str] | str) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("NEWS_FEEDS", "TRADING_SYMBOLS", mode="before")
    @classmethod
    def normalize_string_lists(cls, value: list[str] | str) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("TELEGRAM_ALLOWED_USERS", mode="before")
    @classmethod
    def normalize_int_lists(cls, value: list[int] | str) -> list[int]:
        if isinstance(value, str):
            cleaned = value.strip()
            if not cleaned:
                return []
            if cleaned.startswith("[") and cleaned.endswith("]"):
                cleaned = cleaned[1:-1]
            return [int(item.strip()) for item in cleaned.split(",") if item.strip()]
        return value

    @property
    def bybit_base_url(self) -> str:
        if self.BYBIT_DEMO:
            return "https://api-demo.bybit.com"
        if self.BYBIT_TESTNET:
            return "https://api-testnet.bybit.com"
        return "https://api.bybit.com"

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "prod"


@lru_cache
def get_settings() -> Settings:
    return Settings()
