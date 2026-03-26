import hashlib
import hmac
import time

import pytest
from gitforge.webhooks.validate import validate_webhook, validate_webhook_signature


def sign(payload: str, secret: str) -> str:
    return "sha256=" + hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()


def test_valid_signature():
    payload = '{"event":"push"}'
    secret = "my-secret"
    sig = sign(payload, secret)
    assert validate_webhook_signature(payload, sig, secret) is True


def test_tampered_payload():
    sig = sign('{"event":"push"}', "my-secret")
    assert validate_webhook_signature('{"event":"hack"}', sig, "my-secret") is False


def test_wrong_secret():
    sig = sign('{"event":"push"}', "correct")
    assert validate_webhook_signature('{"event":"push"}', sig, "wrong") is False


def test_missing_prefix():
    payload = '{"event":"push"}'
    raw_hex = hmac.new(b"my-secret", payload.encode(), hashlib.sha256).hexdigest()
    assert validate_webhook_signature(payload, raw_hex, "my-secret") is False


def test_full_validation_with_timestamp():
    payload = '{"event":"push"}'
    secret = "my-secret"
    sig = sign(payload, secret)
    ts = str(int(time.time()))
    assert validate_webhook(payload, secret, sig, timestamp=ts) is True


def test_expired_timestamp():
    payload = '{"event":"push"}'
    secret = "my-secret"
    sig = sign(payload, secret)
    old_ts = str(int(time.time()) - 600)
    assert validate_webhook(payload, secret, sig, timestamp=old_ts, max_age_seconds=300) is False


def test_skip_timestamp_when_zero():
    payload = '{"event":"push"}'
    secret = "my-secret"
    sig = sign(payload, secret)
    old_ts = str(int(time.time()) - 99999)
    assert validate_webhook(payload, secret, sig, timestamp=old_ts, max_age_seconds=0) is True


def test_skip_timestamp_when_not_provided():
    payload = '{"event":"push"}'
    secret = "my-secret"
    sig = sign(payload, secret)
    assert validate_webhook(payload, secret, sig) is True
