from __future__ import annotations

import bisect
from datetime import UTC, datetime
from pathlib import Path

import joblib
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import cross_val_score
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.analytics import AnalyticsRepository
from app.services.market_data import MarketDataService
from app.ml.features import build_feature_rows, build_latest_feature_vector

_ASSET_MAP = {"BTCUSDT": "BTC", "ETHUSDT": "ETH", "TONUSDT": "TON"}


class MLModelService:
    def __init__(self) -> None:
        self.market = MarketDataService()
        self.model_path = Path("artifacts/gbdt_model.joblib")
        self.model_path.parent.mkdir(parents=True, exist_ok=True)

    async def train(self, symbols: list[str], session: AsyncSession | None = None) -> dict:
        features: list[list[float]] = []
        labels: list[int] = []

        news_events: list = []
        whale_events: list = []
        if session is not None:
            repo = AnalyticsRepository(session)
            news_events = await repo.list_news(limit=200)
            whale_events = await repo.list_whales(limit=200)
            # Sort ascending for bisect
            news_events = sorted(news_events, key=lambda e: e.published_at)
            whale_events = sorted(whale_events, key=lambda e: e.timestamp)

        for symbol in symbols:
            state = await self.market.get_symbol_state(symbol)
            timestamps = state.get("timestamps", [])
            news_score: float | list[float] = 0.0
            whale_score: float | list[float] = 0.0

            if news_events and timestamps:
                news_score = _compute_per_row_news(news_events, timestamps, symbol)
            if whale_events and timestamps:
                whale_score = _compute_per_row_whale(whale_events, timestamps, symbol)

            rows, targets = build_feature_rows(
                state["closes"],
                state["highs"],
                state["lows"],
                news_score,
                whale_score,
            )
            features.extend(rows)
            labels.extend(targets)

        if len(features) < 50:
            return {"trained": False, "reason": "Недостаточно данных для обучения"}

        model = HistGradientBoostingClassifier(max_depth=4, random_state=42)
        model.fit(features, labels)

        cv_scores = cross_val_score(model, features, labels, cv=3, scoring="accuracy")
        cv_mean = float(cv_scores.mean())

        joblib.dump(model, self.model_path)
        return {
            "trained": True,
            "samples": len(features),
            "features": len(features[0]) if features else 0,
            "path": str(self.model_path),
            "trained_at": datetime.now(UTC).isoformat(),
            "model_type": "HistGradientBoostingClassifier",
            "cv_accuracy": round(cv_mean, 4),
            "news_rows": len(news_events),
            "whale_rows": len(whale_events),
        }

    def status(self) -> dict:
        exists = self.model_path.exists()
        updated_at = None
        size_bytes = 0
        if exists:
            stat = self.model_path.stat()
            updated_at = datetime.fromtimestamp(stat.st_mtime, tz=UTC)
            size_bytes = stat.st_size
        return {
            "trained": exists,
            "path": str(self.model_path),
            "updated_at": updated_at,
            "size_bytes": size_bytes,
            "model_type": "HistGradientBoostingClassifier",
        }

    async def predict_score(
        self,
        symbol: str,
        closes: list[float],
        highs: list[float],
        lows: list[float],
        news_score: float,
        whale_score: float,
    ) -> float:
        if len(closes) < 20 or len(highs) < 20 or len(lows) < 20:
            return 0.5
        if not self.model_path.exists():
            return 0.5
        model = joblib.load(self.model_path)
        vector = build_latest_feature_vector(closes, highs, lows, news_score, whale_score)
        probabilities = model.predict_proba([vector])[0]
        return float(probabilities[1])


def _ts_ms(dt: datetime) -> float:
    return dt.timestamp()


def _compute_per_row_news(
    news_sorted: list,
    timestamps: list[datetime],
    symbol: str,
) -> list[float]:
    ts_list = [_ts_ms(e.published_at) for e in news_sorted]
    scores: list[float] = []
    for ts in timestamps:
        cutoff = _ts_ms(ts)
        idx = bisect.bisect_right(ts_list, cutoff)
        recent = [e for e in news_sorted[max(0, idx - 5):idx] if symbol in (e.symbol_relevance or [])]
        if recent:
            val = sum(e.sentiment + e.relevance * 0.2 for e in recent) / len(recent)
            val = max(-1.0, min(1.0, val))
        else:
            val = 0.0
        scores.append(val)
    return scores


def _compute_per_row_whale(
    whales_sorted: list,
    timestamps: list[datetime],
    symbol: str,
) -> list[float]:
    asset = _ASSET_MAP.get(symbol, symbol[:3])
    ts_list = [_ts_ms(e.timestamp) for e in whales_sorted]
    scores: list[float] = []
    for ts in timestamps:
        cutoff = _ts_ms(ts)
        idx = bisect.bisect_right(ts_list, cutoff)
        recent = [e for e in whales_sorted[max(0, idx - 5):idx] if e.asset == asset]
        if recent:
            val = sum(e.significance_score for e in recent) / len(recent)
            val = min(1.0, val)
        else:
            val = 0.0
        scores.append(val)
    return scores
