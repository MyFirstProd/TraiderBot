from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health
from app.api.router import api_router
from app.config.settings import get_settings
from app.core.middleware import InMemoryRateLimitMiddleware, RequestContextMiddleware
from app.db.bootstrap import create_all
from app.db.session import engine
from app.utils.logging import configure_logging


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    configure_logging(settings.DEBUG)
    await create_all(engine)
    yield


settings = get_settings()
app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, debug=settings.DEBUG, lifespan=lifespan)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(InMemoryRateLimitMiddleware, requests_per_minute=settings.REQUESTS_PER_MINUTE)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key", "X-Request-ID", "X-Telegram-Init-Data"],
)
app.include_router(api_router, prefix=settings.API_PREFIX)
app.include_router(health.router)
