from __future__ import annotations

from datetime import UTC, datetime

import feedparser
import httpx

from app.config.settings import get_settings
from app.schemas.news import NewsEventCreate
from app.utils.text import clip_text, detect_language, keyword_sentiment, news_fingerprint, repair_mojibake, strip_html


class RssNewsProvider:
    def __init__(self) -> None:
        self.feeds = get_settings().NEWS_FEEDS
        self._client = httpx.AsyncClient(timeout=15.0, follow_redirects=True)

    async def fetch(self) -> list[NewsEventCreate]:
        events: list[NewsEventCreate] = []
        seen: set[str] = set()
        for feed_url in self.feeds:
            try:
                response = await self._client.get(feed_url)
                response.raise_for_status()
                parsed = feedparser.parse(response.content)
            except Exception:
                parsed = feedparser.parse(feed_url)
            for entry in parsed.entries[:10]:
                published = getattr(entry, "published_parsed", None)
                published_at = datetime(*published[:6], tzinfo=UTC) if published else datetime.now(UTC)
                title = repair_mojibake(getattr(entry, "title", "")) or feed_url
                summary = strip_html(repair_mojibake(getattr(entry, "summary", title)))
                fingerprint = news_fingerprint(feed_url, title, published_at.isoformat())
                if fingerprint in seen:
                    continue
                seen.add(fingerprint)
                combined_text = f"{title} {summary}"
                symbols = _extract_symbols(combined_text)
                language = detect_language(combined_text)
                events.append(
                    NewsEventCreate(
                        source=feed_url,
                        title=clip_text(title, 500),
                        summary=clip_text(summary or title, 4000),
                        published_at=published_at,
                        language=language,
                        sentiment=keyword_sentiment(combined_text),
                        relevance=0.6 if symbols else 0.2,
                        novelty=0.5,
                        entities=symbols,
                        symbol_relevance=symbols,
                    )
                )
        return events


def _extract_symbols(text: str) -> list[str]:
    normalized = text.upper()
    symbols = []
    if "BTC" in normalized or "BITCOIN" in normalized:
        symbols.append("BTCUSDT")
    if "ETH" in normalized or "ETHEREUM" in normalized:
        symbols.append("ETHUSDT")
    if "TON" in normalized:
        symbols.append("TONUSDT")
    return sorted(set(symbols))
