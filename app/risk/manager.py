from __future__ import annotations

from dataclasses import dataclass

from app.config.settings import get_settings


@dataclass(slots=True)
class RiskDecision:
    approved: bool
    quantity: float = 0.0
    order_type: str = "limit_post_only"
    reason: str | None = None


class RiskManager:
    def __init__(self) -> None:
        settings = get_settings()
        self.daily_realized_pnl = 0.0
        self.consecutive_losses = 0
        self.circuit_breaker_open = False
        self.max_daily_loss_pct = settings.MAX_DAILY_LOSS_PCT
        self.max_concurrent_positions = settings.MAX_CONCURRENT_POSITIONS
        self.max_total_exposure_pct = settings.MAX_TOTAL_EXPOSURE_PCT
        self.risk_per_trade_pct = settings.RISK_PER_TRADE_PCT
        self.emergency_spread_bps = settings.EMERGENCY_SPREAD_BPS

    def evaluate(
        self,
        *,
        should_trade: bool,
        symbol: str,
        equity: float,
        price: float,
        stop_distance: float,
        spread_bps: float,
        open_positions: int,
        total_exposure: float,
    ) -> RiskDecision:
        if self.circuit_breaker_open:
            return RiskDecision(False, reason="circuit_breaker_open")
        if not should_trade:
            return RiskDecision(False, reason="strategy_hold")
        if self.daily_realized_pnl <= -(equity * self.max_daily_loss_pct):
            return RiskDecision(False, reason="daily_loss_limit")
        if self.consecutive_losses >= get_settings().MAX_CONSECUTIVE_LOSSES:
            return RiskDecision(False, reason="consecutive_losses_limit")
        if open_positions >= self.max_concurrent_positions:
            return RiskDecision(False, reason="max_positions_limit")
        if spread_bps >= self.emergency_spread_bps:
            return RiskDecision(False, reason="emergency_spread")

        risk_budget = equity * self.risk_per_trade_pct
        quantity = risk_budget / max(stop_distance, price * 0.001)
        if (quantity * price) + total_exposure > equity * self.max_total_exposure_pct:
            return RiskDecision(False, reason="exposure_limit")
        return RiskDecision(True, quantity=round(quantity, 6), order_type="limit_post_only")

    def register_trade_result(self, pnl: float) -> None:
        self.daily_realized_pnl += pnl
        self.consecutive_losses = self.consecutive_losses + 1 if pnl < 0 else 0

    def record_runtime_failure(self) -> None:
        self.circuit_breaker_open = True

    def reset_circuit_breaker(self) -> None:
        self.circuit_breaker_open = False
