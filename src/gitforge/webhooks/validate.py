from __future__ import annotations

import hashlib
import hmac
import time
from typing import Optional


def validate_webhook_signature(payload: str, signature: str, secret: str) -> bool:
    if not signature.startswith("sha256="):
        return False

    expected = "sha256=" + hmac.new(
        secret.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, signature)


def validate_webhook(
    payload: str,
    secret: str,
    signature: str,
    *,
    timestamp: Optional[str] = None,
    max_age_seconds: int = 300,
) -> bool:
    if not validate_webhook_signature(payload, signature, secret):
        return False

    if timestamp and max_age_seconds > 0:
        try:
            ts = int(timestamp)
        except ValueError:
            return False
        now = int(time.time())
        if abs(now - ts) > max_age_seconds:
            return False

    return True
