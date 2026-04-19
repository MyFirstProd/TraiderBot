from __future__ import annotations

from pydantic import BaseModel, Field


class StructuredEventAssessment(BaseModel):
    event_type: str
    sentiment: float = Field(ge=-1.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    novelty: float = Field(ge=0.0, le=1.0)
    source_reliability: float = Field(ge=0.0, le=1.0)
    market_relevance: float = Field(ge=0.0, le=1.0)
    contradiction_flag: bool = False
    summary: str
    affected_symbols: list[str] = Field(default_factory=list)


class ExplainabilityPayload(BaseModel):
    summary: str
    factors: list[str]
    score_adjustment: float = Field(ge=-1.0, le=1.0)
