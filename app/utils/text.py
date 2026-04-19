from __future__ import annotations

from html import unescape
from html.parser import HTMLParser
import re


class _HTMLStripper(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def get_text(self) -> str:
        return "".join(self.parts)


def repair_mojibake(text: str) -> str:
    if not text:
        return ""
    normalized = unescape(text).replace("\x00", "").strip()
    direct_replacements = {
        "â": "’",
        "â": "‘",
        "â": "“",
        "â": "”",
        "â": "—",
        "â": "–",
        "â": "→",
    }
    for source, target in direct_replacements.items():
        normalized = normalized.replace(source, target)
    suspicious = ("Ð", "Ñ", "â", "Ã", "�")
    if any(token in normalized for token in suspicious):
        for encoding in ("latin1", "cp1252"):
            try:
                candidate = normalized.encode(encoding).decode("utf-8")
            except Exception:
                continue
            if _looks_better(candidate, normalized):
                normalized = candidate
                break
    return normalize_whitespace(normalized)


def strip_html(text: str) -> str:
    if not text:
        return ""
    stripper = _HTMLStripper()
    stripper.feed(text)
    return normalize_whitespace(unescape(stripper.get_text()))


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def detect_language(text: str) -> str:
    return "ru" if re.search(r"[А-Яа-яЁё]", text) else "en"


def keyword_sentiment(text: str) -> float:
    normalized = text.casefold()
    positive = [
        "рост",
        "ралли",
        "прибыль",
        "одобр",
        "запуск",
        "integration",
        "launch",
        "surge",
        "gain",
        "approval",
        "bull",
        "inflow",
    ]
    negative = [
        "взлом",
        "hack",
        "exploit",
        "drain",
        "drop",
        "паден",
        "убыт",
        "ban",
        "probe",
        "lawsuit",
        "outflow",
        "слив",
    ]
    score = 0.0
    score += sum(0.12 for word in positive if word in normalized)
    score -= sum(0.12 for word in negative if word in normalized)
    return max(min(score, 1.0), -1.0)


def clip_text(text: str, limit: int) -> str:
    clean = normalize_whitespace(text)
    if len(clean) <= limit:
        return clean
    return clean[: max(limit - 1, 1)].rstrip() + "…"


def news_fingerprint(source: str, title: str, published_at: str) -> str:
    return normalize_whitespace(f"{source}|{title.casefold()}|{published_at}")


def _looks_better(candidate: str, original: str) -> bool:
    candidate_hits = sum(candidate.count(token) for token in ("Ð", "Ñ", "â", "Ã", "�"))
    original_hits = sum(original.count(token) for token in ("Ð", "Ñ", "â", "Ã", "�"))
    return candidate_hits < original_hits
