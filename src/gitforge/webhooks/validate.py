from __future__ import annotations

import hashlib
import hmac
import time
from typing import Optional


def validate_webhook_signature(payload: str, signature: str, secret: str) -> bool:
    """Validate the HMAC-SHA256 signature of a webhook payload.

    ``payload`` is the raw signed content (may include a timestamp prefix).
    """
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
    tolerance: int = 300,
) -> bool:
    """Full webhook validation with replay protection.

    When *timestamp* (the ``X-GitForge-Timestamp`` header) is provided, the
    signature is verified over ``"<timestamp>.<payload>"`` and the timestamp
    freshness is checked against *tolerance* seconds.

    When *timestamp* is ``None``, the signature is verified over the raw
    *payload* only (backward compatibility with old deliveries).

    Set *tolerance* to ``0`` to skip the freshness check while still
    verifying the timestamp-inclusive signature.
    """
    # Build the signed content the same way the server does
    signed_payload = f"{timestamp}.{payload}" if timestamp else payload

    if not validate_webhook_signature(signed_payload, signature, secret):
        return False

    if timestamp and tolerance > 0:
        try:
            ts = int(timestamp)
        except ValueError:
            return False
        now = int(time.time())
        if abs(now - ts) > tolerance:
            return False

    return True
