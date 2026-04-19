from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str


class MessageResponse(BaseModel):
    message: str


class PaginatedResponse(BaseModel):
    items: list[Any]
    total: int


class AppInfoResponse(BaseModel):
    app_name: str
    version: str
    paper_trading: bool
    trading_enabled: bool
    server_time: datetime
