from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class NewsEventCreate(BaseModel):
    source: str
    title: str
    summary: str
    published_at: datetime
    language: str = "en"
    sentiment: float = Field(default=0.0, ge=-1.0, le=1.0)
    relevance: float = Field(default=0.0, ge=0.0, le=1.0)
    novelty: float = Field(default=0.0, ge=0.0, le=1.0)
    entities: list[str] = Field(default_factory=list)
    symbol_relevance: list[str] = Field(default_factory=list)


class NewsEventRead(ORMModel):
    id: int
    source: str
    title: str
    summary: str
    published_at: datetime
    language: str
    sentiment: float
    relevance: float
    novelty: float
    entities: list[str]
    symbol_relevance: list[str]
