from __future__ import annotations

from sqlalchemy import desc, select

from app.models.market_snapshot import MarketSnapshot
from app.models.position import Position
from app.models.risk_event import RiskEvent
from app.models.signal import Signal
from app.models.trade import Trade
from app.repositories.base import BaseRepository


class TradingRepository(BaseRepository):
    async def create_snapshot(self, snapshot: MarketSnapshot) -> MarketSnapshot:
        return await self.add(snapshot)

    async def create_signal(self, signal: Signal) -> Signal:
        return await self.add(signal)

    async def create_position(self, position: Position) -> Position:
        return await self.add(position)

    async def create_trade(self, trade: Trade) -> Trade:
        return await self.add(trade)

    async def create_risk_event(self, event: RiskEvent) -> RiskEvent:
        return await self.add(event)

    async def list_open_positions(self) -> list[Position]:
        return await self.list_by_stmt(select(Position).where(Position.is_open.is_(True)).order_by(Position.opened_at))

    async def list_trades(self, limit: int = 100) -> list[Trade]:
        return await self.list_by_stmt(select(Trade).order_by(desc(Trade.closed_at)).limit(limit))

    async def list_signals(self, limit: int = 100) -> list[Signal]:
        return await self.list_by_stmt(select(Signal).order_by(desc(Signal.observed_at)).limit(limit))

    async def list_recent_snapshots(self, limit: int = 100) -> list[MarketSnapshot]:
        return await self.list_by_stmt(select(MarketSnapshot).order_by(desc(MarketSnapshot.observed_at)).limit(limit))

    async def list_recent_snapshots_for_symbol(self, symbol: str, limit: int = 60) -> list[MarketSnapshot]:
        return await self.list_by_stmt(
            select(MarketSnapshot)
            .where(MarketSnapshot.symbol == symbol)
            .order_by(desc(MarketSnapshot.observed_at))
            .limit(limit)
        )

    async def list_latest_snapshots_by_symbol(self) -> list[MarketSnapshot]:
        rows = await self.list_recent_snapshots(limit=300)
        latest: dict[str, MarketSnapshot] = {}
        for row in rows:
            latest.setdefault(row.symbol, row)
        return list(sorted(latest.values(), key=lambda item: item.symbol))
