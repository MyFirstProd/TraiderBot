from __future__ import annotations

import hashlib


def make_idempotency_key(*parts: str) -> str:
    raw = ":".join(parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
