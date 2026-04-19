from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
import urllib.parse
from typing import Annotated, Any

from fastapi import Depends, Header, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.config.settings import get_settings
from app.core.exceptions import UnauthorizedError

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_admin_api_key(api_key: str | None) -> bool:
    settings = get_settings()
    if not api_key:
        return False
    return hmac.compare_digest(api_key, settings.ADMIN_API_KEY.get_secret_value())


def create_mini_app_token(user_id: int, purpose: str = "admin", ttl_seconds: int = 3600) -> str:
    settings = get_settings()
    payload = {
        "user_id": user_id,
        "purpose": purpose,
        "exp": int(time.time()) + ttl_seconds,
    }
    raw_payload = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    encoded_payload = base64.urlsafe_b64encode(raw_payload).decode("ascii").rstrip("=")
    signature = hmac.new(
        settings.SECRET_KEY.get_secret_value().encode("utf-8"),
        encoded_payload.encode("ascii"),
        hashlib.sha256,
    ).hexdigest()
    return f"{encoded_payload}.{signature}"


def validate_mini_app_token(token: str | None, expected_purpose: str = "admin") -> dict[str, Any] | None:
    if not token:
        return None

    try:
        encoded_payload, signature = token.split(".", 1)
    except ValueError:
        return None

    settings = get_settings()
    expected_signature = hmac.new(
        settings.SECRET_KEY.get_secret_value().encode("utf-8"),
        encoded_payload.encode("ascii"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected_signature, signature):
        return None

    try:
        padded = encoded_payload + "=" * (-len(encoded_payload) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded.encode("ascii")))
    except Exception:
        return None

    if payload.get("purpose") != expected_purpose:
        return None
    if int(payload.get("exp", 0)) < int(time.time()):
        return None

    allowed = settings.TELEGRAM_ALLOWED_USERS
    user_id = int(payload.get("user_id", 0))
    if allowed and user_id not in allowed:
        return None
    return payload


def validate_telegram_init_data(init_data: str, bot_token: str, max_age_seconds: int) -> dict[str, Any]:
    parsed = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise UnauthorizedError("Missing hash in initData")

    auth_date = parsed.get("auth_date")
    if auth_date is None:
        raise UnauthorizedError("Missing auth_date in initData")
    if int(time.time()) - int(auth_date) > max_age_seconds:
        raise UnauthorizedError("Telegram initData has expired")

    check_string = "\n".join(f"{key}={value}" for key, value in sorted(parsed.items()))
    secret = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    expected_hash = hmac.new(secret, check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected_hash, received_hash):
        raise UnauthorizedError("Invalid Telegram initData signature")

    raw_user = parsed.get("user")
    if not raw_user:
        raise UnauthorizedError("Missing Telegram user payload")
    return json.loads(raw_user)


async def require_admin(
    api_key: Annotated[str | None, Security(api_key_header)] = None,
    x_miniapp_token: Annotated[str | None, Header()] = None,
) -> str:
    if verify_admin_api_key(api_key):
        return "admin"
    if validate_mini_app_token(x_miniapp_token):
        return "miniapp_admin"
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid admin access token")


async def optional_request_id(x_request_id: Annotated[str | None, Header()] = None) -> str | None:
    return x_request_id
