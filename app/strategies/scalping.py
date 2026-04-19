from __future__ import annotations

from app.indicators.ma import EMA, SMA, WMA
from app.indicators.rsi import RSI
from app.indicators.volatility import ATR, SpreadFilter, VolatilityFilter
from app.strategies.base import BaseStrategy, SignalDirection, SignalResult


class ScalpingStrategy(BaseStrategy):
    def __init__(self, symbol: str, config: dict) -> None:
        super().__init__(config)
        self.symbol = symbol
        self.ema_fast = EMA(config.get("ema_fast", 9))
        self.ema_slow = EMA(config.get("ema_slow", 21))
        self.sma_fast = SMA(config.get("sma_fast", 20))
        self.sma_slow = SMA(config.get("sma_slow", 50))
        self.wma = WMA(config.get("wma_period", 21))
        self.rsi = RSI(config.get("rsi_period", 14))
        self.atr = ATR(14)
        self.spread_filter = SpreadFilter(max_spread_pct=config.get("max_spread_pct", 0.001))
        self.volatility_filter = VolatilityFilter()
        self.signal_threshold = config.get("signal_threshold", 0.35)

    async def generate_signal(
        self,
        market_data: dict,
        news_sentiment: float | None = None,
        whale_flow: float | None = None,
    ) -> SignalResult:
        closes = market_data["closes"]
        highs = market_data["highs"]
        lows = market_data["lows"]
        price = market_data.get("current_price", closes[-1])
        bid = market_data.get("bid", price)
        ask = market_data.get("ask", price)

        if len(closes) < 60:
            return SignalResult(SignalDirection.NEUTRAL, 0.0, {"reason": "insufficient_data"}, {}, 0.0, False)

        ema_fast = self.ema_fast.compute(closes)
        ema_slow = self.ema_slow.compute(closes)
        sma_fast = self.sma_fast.compute(closes)
        sma_slow = self.sma_slow.compute(closes)
        wma_vals = self.wma.compute(closes)
        rsi_vals = self.rsi.compute(closes)
        atr_vals = self.atr.compute(highs, lows, closes)
        ema_fast_cur, ema_slow_cur, rsi_cur, atr_cur = ema_fast[-1], ema_slow[-1], rsi_vals[-1], atr_vals[-1]
        if None in {ema_fast_cur, ema_slow_cur, rsi_cur, atr_cur}:
            return SignalResult(SignalDirection.NEUTRAL, 0.0, {"reason": "indicators_not_ready"}, {}, 0.0, False)

        if not self.spread_filter.is_acceptable(bid, ask):
            return SignalResult(SignalDirection.NEUTRAL, 0.0, {"reason": "spread_too_wide"}, {}, 0.0, False)
        if not self.volatility_filter.is_tradeable(atr_cur, price):
            return SignalResult(SignalDirection.NEUTRAL, 0.0, {"reason": "volatility_out_of_range"}, {}, 0.0, False)

        crossover_up = self.ema_fast.crossover_up(ema_fast, ema_slow)
        crossover_down = self.ema_fast.crossover_down(ema_fast, ema_slow)
        oversold_exit = self.rsi.is_exiting_oversold(rsi_vals, 35)
        overbought_exit = self.rsi.is_exiting_overbought(rsi_vals, 65)

        score = 0.0
        if price > ema_slow_cur:
            score += 0.3
        else:
            score -= 0.3

        if crossover_up:
            score += 0.2
        elif ema_fast_cur > ema_slow_cur:
            score += 0.1
        elif crossover_down:
            score -= 0.2
        else:
            score -= 0.1

        if oversold_exit:
            score += 0.25
        elif 40 <= rsi_cur <= 60 and score > 0:
            score += 0.1
        if overbought_exit:
            score -= 0.25
        elif 40 <= rsi_cur <= 60 and score < 0:
            score -= 0.1

        if news_sentiment is not None:
            score += news_sentiment * 0.1
        if whale_flow is not None:
            score += whale_flow * 0.1

        score = max(-1.0, min(1.0, score))
        direction = SignalDirection.NEUTRAL
        should_trade = False
        if score >= self.signal_threshold:
            direction = SignalDirection.LONG
            should_trade = True
        elif score <= -self.signal_threshold:
            direction = SignalDirection.SHORT
            should_trade = True

        rationale = {
            "price_vs_ema21": price > ema_slow_cur,
            "ema9_gt_ema21": ema_fast_cur > ema_slow_cur,
            "ema_crossover_up": crossover_up,
            "ema_crossover_down": crossover_down,
            "rsi": rsi_cur,
            "news_sentiment": news_sentiment,
            "whale_flow": whale_flow,
        }
        indicators = {
            "ema9": ema_fast_cur,
            "ema21": ema_slow_cur,
            "sma20": sma_fast[-1],
            "sma50": sma_slow[-1],
            "wma": wma_vals[-1],
            "rsi14": rsi_cur,
            "atr14": atr_cur,
        }
        return SignalResult(direction, score, rationale, indicators, abs(score), should_trade)
