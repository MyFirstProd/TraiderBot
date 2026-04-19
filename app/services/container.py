from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from app.ml.service import MLModelService
from app.services.trading_runtime import TradingRuntimeService


@dataclass(slots=True)
class ServiceContainer:
    runtime: TradingRuntimeService
    ml: MLModelService


@lru_cache
def get_container() -> ServiceContainer:
    return ServiceContainer(runtime=TradingRuntimeService(), ml=MLModelService())
