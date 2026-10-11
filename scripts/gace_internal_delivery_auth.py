#!/usr/bin/env python3
"""Shared webhook-gateway outbound delivery HMAC verification for server-core receivers."""
import base64
import binascii
import hashlib
import hmac
import os
import time
from pathlib import Path


class DeliveryAuthError(RuntimeError):
    def __init__(self, code, status):
        super().__init__(code)
        self.code = code
        self.status = status


def fail(code, status):
    raise DeliveryAuthError(code, status)


def decode_secret(value):
    if not isinstance(value, str) or not value:
        fail("DELIVERY_SECRET_MISSING", 503)
    if value.startswith("base64:"):
        try:
            decoded = base64.b64decode(value[len("base64:"):], validate=True)
        except (binascii.Error, ValueError):
            fail("DELIVERY_SECRET_INVALID", 503)
        if not decoded:
            fail("DELIVERY_SECRET_INVALID", 503)
        return decoded
    return value.encode("utf-8")


def read_delivery_key(*, env_prefix="GACE_BOUNDED_HOST"):
    direct = os.environ.get(f"{env_prefix}_HMAC_KEY")
    file_path = os.environ.get(f"{env_prefix}_HMAC_KEY_FILE")
    if direct and file_path:
        fail("DELIVERY_SECRET_SOURCE_AMBIGUOUS", 503)
    if file_path:
        try:
            direct = Path(file_path).read_text(encoding="utf-8").strip()
        except Exception:
            fail("DELIVERY_SECRET_FILE_UNREADABLE", 503)
    return decode_secret(direct)


def verify_delivery(
    headers,
    body,
    *,
    expected_destination,
    delivery_key=None,
    now=None,
    tolerance_seconds=300,
):
    if headers.get("x-gace-destination") != expected_destination:
        fail("DELIVERY_DESTINATION_INVALID", 401)
    message_id = headers.get("webhook-id")
    timestamp = headers.get("webhook-timestamp")
    signature = headers.get("webhook-signature")
    if not message_id or not timestamp or not signature:
        fail("DELIVERY_SIGNATURE_HEADERS_MISSING", 401)
    try:
        timestamp_int = int(timestamp)
    except ValueError:
        fail("DELIVERY_TIMESTAMP_INVALID", 401)
    current = int(time.time() if now is None else now)
    tolerance = int(tolerance_seconds)
    if tolerance < 1 or tolerance > 900:
        fail("DELIVERY_TOLERANCE_INVALID", 503)
    if abs(current - timestamp_int) > tolerance:
        fail("DELIVERY_TIMESTAMP_OUT_OF_RANGE", 401)
    if not signature.startswith("v1,"):
        fail("DELIVERY_SIGNATURE_INVALID", 401)
    try:
        supplied = base64.b64decode(signature[3:], validate=True)
    except (binascii.Error, ValueError):
        fail("DELIVERY_SIGNATURE_INVALID", 401)
    key = delivery_key if delivery_key is not None else read_delivery_key(env_prefix="GACE_BOUNDED_HOST")
    expected = hmac.new(
        key,
        message_id.encode() + b"." + timestamp.encode() + b"." + body,
        hashlib.sha256,
    ).digest()
    if not hmac.compare_digest(supplied, expected):
        fail("DELIVERY_SIGNATURE_INVALID", 401)
