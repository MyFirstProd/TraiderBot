from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.execution.paper import ClosedTrade, PaperExecutionEngine, PaperPosition
from app.models.audit_log import AuditLog
from app.models.llm_inference import LlmInference
from app.models.market_snapshot import MarketSnapshot
from app.models.news_event import NewsEvent
from app.models.position import Position
from app.models.risk_event import RiskEvent
from app.models.signal import Signal
from app.models.trade import Trade
from app.models.whale_event import WhaleEvent
from app.repositories.analytics import AnalyticsRepository
from app.repositories.config import ConfigRepository
from app.repositories.trading import TradingRepository
from app.risk.manager import RiskManager
from app.ml.service import MLModelService
from app.services.llm_service import LLMService
from app.services.market_data import MarketDataService
from app.services.news_service import NewsService
from app.services.whale_service import WhaleService
from app.strategies.scalping import ScalpingStrategy
from app.utils.idempotency import make_idempotency_key


class TradingRuntimeService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.market = MarketDataService()
        self.news = NewsService()
        self.whales = WhaleService()
        self.llm = LLMService()
        self.risk = RiskManager()
        self.paper = PaperExecutionEngine()
        self.ml = MLModelService()
        self.equity = self.settings.STARTING_EQUITY
        self.trading_enabled = self.settings.TRADING_ENABLED

    async def cycle(self, session: AsyncSession) -> dict:
        trading_repo = TradingRepository(session)
        analytics_repo = AnalyticsRepository(session)
        config_repo = ConfigRepository(session)

        news_events = await self.news.collect() if self.settings.NEWS_ENABLED else []
        whale_events = await self.whales.collect() if self.settings.WHALES_ENABLED else []
        for event in news_events:
            await analytics_repo.create_news_event(NewsEvent(**event.model_dump()))
        for event in whale_events:
            await analytics_repo.create_whale_event(WhaleEvent(**event.model_dump()))

        decisions = []
        for symbol in self.settings.TRADING_SYMBOLS:
            try:
                state = await self.market.get_symbol_state(symbol)
                await trading_repo.create_snapshot(
                    MarketSnapshot(
                        symbol=symbol,
                        observed_at=state["observed_at"],
                        price=state["current_price"],
                        bid=state["bid"],
                        ask=state["ask"],
                        high=state["high"],
                        low=state["low"],
                        volume=state["volume"],
                        volatility_bps=state["volatility_bps"],
                        orderbook_imbalance=state["orderbook_imbalance"],
                        trade_imbalance=state["trade_imbalance"],
                        is_synthetic=state["synthetic"],
                    )
                )
                config = await config_repo.get_strategy_config(symbol)
                strategy_config = (
                    {
                        "ema_fast": config.ema_fast,
                        "ema_slow": config.ema_slow,
                        "sma_fast": config.sma_fast,
                        "sma_slow": config.sma_slow,
                        "wma_period": config.wma_period,
                        "rsi_period": config.rsi_period,
                        "signal_threshold": config.min_model_score,
                        "max_spread_pct": config.max_spread_bps / 10_000,
                    }
                    if config
                    else {}
                )
                strategy = ScalpingStrategy(symbol, strategy_config)
                news_score = self.news.score_for_symbol(news_events, symbol)
                whale_score = self.whales.score_for_symbol(whale_events, symbol)
                signal = await strategy.generate_signal(state, news_score, whale_score)
                model_score = await self.ml.predict_score(
                    symbol,
                    state["closes"],
                    state["highs"],
                    state["lows"],
                    news_score,
                    whale_score,
                )
                signal.rationale["model_score"] = model_score
                signal.rationale["model_gate_passed"] = model_score >= (config.min_model_score if config else 0.55)
                signal.should_trade = signal.should_trade and signal.rationale["model_gate_passed"]
                await trading_repo.create_signal(
                    Signal(
                        symbol=symbol,
                        observed_at=state["observed_at"],
                        direction=signal.direction.value,
                        score=signal.score,
                        confidence=signal.confidence,
                        should_trade=signal.should_trade,
                        rationale=signal.rationale,
                        indicators_snapshot=signal.indicators_snapshot,
                    )
                )

                closed = self.paper.check_exit(symbol, state["current_price"], state["observed_at"])
                if closed:
                    await self._persist_closed_trade(trading_repo, closed)

                if not self.trading_enabled:
                    decisions.append({"symbol": symbol, "status": "disabled"})
                    continue

                stop_distance = max((state["current_price"] * 0.002), (signal.indicators_snapshot.get("atr14") or 0.0) * 1.2)
                spread_bps = ((state["ask"] - state["bid"]) / state["current_price"]) * 10_000
                decision = self.risk.evaluate(
                    should_trade=signal.should_trade,
                    symbol=symbol,
                    equity=self.equity,
                    price=state["current_price"],
                    stop_distance=stop_distance,
                    spread_bps=spread_bps,
                    open_positions=len(self.paper.positions),
                    total_exposure=self.paper.exposure(),
                )
                if not decision.approved:
                    await trading_repo.create_risk_event(
                        RiskEvent(
                            event_type="entry_rejected",
                            severity="info",
                            symbol=symbol,
                            details={"reason": decision.reason},
                        )
                    )
                    decisions.append({"symbol": symbol, "status": decision.reason})
                    continue

                side = "long" if signal.direction.value == "long" else "short"
                explanation = {
                    "indicators": signal.indicators_snapshot,
                    "rationale": signal.rationale,
                    "news_score": news_score,
                    "whale_score": whale_score,
                    "model_score": model_score,
                    "idempotency_key": make_idempotency_key(symbol, side, state["observed_at"].isoformat()),
                }
                self.paper.open_position(
                    PaperPosition(
                        symbol=symbol,
                        side=side,
                        quantity=decision.quantity,
                        entry_price=state["ask"] if side == "long" else state["bid"],
                        stop_price=state["current_price"] - stop_distance if side == "long" else state["current_price"] + stop_distance,
                        take_price=state["current_price"] + stop_distance * 1.8 if side == "long" else state["current_price"] - stop_distance * 1.8,
                        opened_at=state["observed_at"],
                        explanation=explanation,
                    )
                )
                await trading_repo.create_position(
                    Position(
                        symbol=symbol,
                        side=side,
                        quantity=decision.quantity,
                        entry_price=state["ask"] if side == "long" else state["bid"],
                        stop_price=state["current_price"] - stop_distance if side == "long" else state["current_price"] + stop_distance,
                        take_price=state["current_price"] + stop_distance * 1.8 if side == "long" else state["current_price"] - stop_distance * 1.8,
                        opened_at=state["observed_at"],
                        is_open=True,
                        explanation=explanation,
                    )
                )
                await analytics_repo.create_audit_log(
                    AuditLog(actor="runtime", action="position_opened", target=symbol, details=explanation)
                )
                decisions.append({"symbol": symbol, "status": "opened", "side": side, "qty": decision.quantity})
            except Exception as exc:
                await trading_repo.create_risk_event(
                    RiskEvent(
                        event_type="runtime_error",
                        severity="error",
                        symbol=symbol,
                        details={"reason": str(exc)},
                    )
                )
                decisions.append({"symbol": symbol, "status": "runtime_error", "error": str(exc)})

        if news_events:
            summary = " | ".join(event.title for event in news_events[:3])
            assessment, prompt_hash = await self.llm.analyze_event(summary)
            await analytics_repo.create_llm_inference(
                LlmInference(
                    provider="litellm",
                    model=self.settings.LITELLM_MODEL,
                    task_type="news_summary",
                    prompt_hash=prompt_hash,
                    input_excerpt=summary[:2000],
                    response_json=assessment.model_dump(),
                )
            )
        return {"equity": self.equity, "decisions": decisions}

    async def _persist_closed_trade(self, trading_repo: TradingRepository, closed: ClosedTrade) -> None:
        self.equity += closed.pnl
        self.risk.register_trade_result(closed.pnl)
        await trading_repo.create_trade(
            Trade(
                symbol=closed.symbol,
                side=closed.side,
                quantity=closed.quantity,
                entry_price=closed.entry_price,
                exit_price=closed.exit_price,
                pnl=closed.pnl,
                opened_at=closed.opened_at,
                closed_at=closed.closed_at,
                reason=closed.reason,
                explanation=closed.explanation,
            )
        )
