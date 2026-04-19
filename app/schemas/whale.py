from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class WhaleEventCreate(BaseModel):
    asset: str
    chain: str
    amount: float = Field(gt=0)
    usd_value: float = Field(ge=0)
    from_type: str
    to_type: str
    exchange_related: bool = False
    timestamp: datetime
    significance_score: float = Field(default=0.0, ge=0.0, le=1.0)


class WhaleEventRead(ORMModel):
    id: int
    asset: str
    chain: str
    amount: float
    usd_value: float
    from_type: str
    to_type: str
    exchange_related: bool
    timestamp: datetime
    significance_score: float
