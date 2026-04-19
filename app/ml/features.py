from __future__ import annotations

from collections.abc import Sequence
from typing import Union

from app.indicators.ma import EMA, SMA, WMA
from app.indicators.rsi import RSI
from app.indicators.volatility import ATR

ScoreArg = Union[float, list[float]]


def build_feature_rows(
    closes: Sequence[float],
    highs: Sequence[float],
    lows: Sequence[float],
    news_score: ScoreArg,
    whale_score: ScoreArg,
) -> tuple[list[list[float]], list[int]]:
    ema9 = EMA(9).compute(closes)
    ema21 = EMA(21).compute(closes)
    sma20 = SMA(20).compute(closes)
    sma50 = SMA(50).compute(closes)
    wma21 = WMA(21).compute(closes)
    rsi14 = RSI(14).compute(closes)
    atr14 = ATR(14).compute(highs, lows, closes)

    news_is_list = isinstance(news_score, list)
    whale_is_list = isinstance(whale_score, list)

    features: list[list[float]] = []
    labels: list[int] = []
    for idx in range(55, len(closes) - 2):
        current = closes[idx]
        future = closes[idx + 2]
        ns = news_score[idx] if news_is_list and idx < len(news_score) else (news_score if not news_is_list else 0.0)  # type: ignore[index]
        ws = whale_score[idx] if whale_is_list and idx < len(whale_score) else (whale_score if not whale_is_list else 0.0)  # type: ignore[index]
        row = [
            _safe_ratio(current, closes[idx - 1]),
            _safe_ratio(current, closes[idx - 5]),
            _spread(current, ema9[idx]),
            _spread(current, ema21[idx]),
            _spread(current, sma20[idx]),
            _spread(current, sma50[idx]),
            _spread(current, wma21[idx]),
            (rsi14[idx] or 50.0) / 100.0,
            _safe_ratio(atr14[idx] or 0.0, current),
            float(ns),
            float(ws),
        ]
        features.append(row)
        labels.append(1 if future > current else 0)
    return features, labels


def build_latest_feature_vector(
    closes: Sequence[float],
    highs: Sequence[float],
    lows: Sequence[float],
    news_score: float,
    whale_score: float,
) -> list[float]:
    features, _ = build_feature_rows(closes, highs, lows, news_score, whale_score)
    return features[-1] if features else [0.0] * 11


def _spread(left: float, right: float | None) -> float:
    if right in (None, 0):
        return 0.0
    return (left - right) / right


def _safe_ratio(left: float, right: float) -> float:
    if right == 0:
        return 0.0
    return (left - right) / right
