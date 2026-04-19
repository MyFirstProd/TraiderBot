from fastapi import APIRouter

from app.api.routes import admin, health, market, telegram

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(market.router, prefix="/market", tags=["market"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(telegram.router, prefix="/telegram", tags=["telegram"])
