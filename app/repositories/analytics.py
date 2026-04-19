from __future__ import annotations

from sqlalchemy import desc, select

from app.models.audit_log import AuditLog
from app.models.llm_inference import LlmInference
from app.models.news_event import NewsEvent
from app.models.whale_event import WhaleEvent
from app.repositories.base import BaseRepository
from app.utils.text import repair_mojibake, strip_html


class AnalyticsRepository(BaseRepository):
    async def create_news_event(self, event: NewsEvent) -> NewsEvent:
        existing_rows = await self.list_by_stmt(
            select(NewsEvent)
            .where(
                NewsEvent.source == event.source,
                NewsEvent.title == event.title,
                NewsEvent.published_at == event.published_at,
            )
            .limit(1)
        )
        if existing_rows:
            return existing_rows[0]
        return await self.add(event)

    async def create_whale_event(self, event: WhaleEvent) -> WhaleEvent:
        existing_rows = await self.list_by_stmt(
            select(WhaleEvent)
            .where(
                WhaleEvent.asset == event.asset,
                WhaleEvent.timestamp == event.timestamp,
                WhaleEvent.amount == event.amount,
                WhaleEvent.to_type == event.to_type,
            )
            .limit(1)
        )
        if existing_rows:
            return existing_rows[0]
        return await self.add(event)

    async def create_llm_inference(self, inference: LlmInference) -> LlmInference:
        return await self.add(inference)

    async def create_audit_log(self, log: AuditLog) -> AuditLog:
        return await self.add(log)

    async def list_news(self, limit: int = 50) -> list[NewsEvent]:
        rows = await self.list_by_stmt(select(NewsEvent).order_by(desc(NewsEvent.published_at)).limit(limit * 3))
        unique: list[NewsEvent] = []
        seen: set[tuple[str, str, object]] = set()
        for row in rows:
            row.title = repair_mojibake(row.title)
            row.summary = strip_html(repair_mojibake(row.summary))
            key = (row.source, row.title, row.published_at)
            if key in seen:
                continue
            seen.add(key)
            unique.append(row)
            if len(unique) >= limit:
                break
        return unique

    async def list_whales(self, limit: int = 50) -> list[WhaleEvent]:
        rows = await self.list_by_stmt(select(WhaleEvent).order_by(desc(WhaleEvent.timestamp)).limit(limit * 3))
        unique: list[WhaleEvent] = []
        seen: set[tuple[str, object, float, str]] = set()
        for row in rows:
            key = (row.asset, row.timestamp, row.amount, row.to_type)
            if key in seen:
                continue
            seen.add(key)
            unique.append(row)
            if len(unique) >= limit:
                break
        return unique

    async def list_audit_logs(self, limit: int = 100) -> list[AuditLog]:
        return await self.list_by_stmt(select(AuditLog).order_by(desc(AuditLog.created_at)).limit(limit))
