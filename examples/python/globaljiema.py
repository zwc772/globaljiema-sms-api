"""Tiny GlobalJiema API wrapper. Reference: https://globaljiema.com/apidoc"""
import os
import secrets
import time

import requests

API = "https://globaljiema.com"


class APIError(RuntimeError):
    """code=0 business error or HTTP error."""


def _session():
    key = os.getenv("GLOBALJIEMA_API_KEY")
    if not key:
        raise APIError("environment variable GLOBALJIEMA_API_KEY is not set")
    s = requests.Session()
    s.headers.update({"X-API-Key": key, "User-Agent": "globaljiema-examples/1.0"})
    return s


_S = None


def call(method, path, **fields):
    global _S
    _S = _S or _session()
    kw = {"params": fields} if method == "GET" else {"data": fields}
    for _ in range(4):
        resp = _S.request(method, API + path, timeout=45, **kw)
        if resp.status_code == 429:
            time.sleep(float(resp.headers.get("Retry-After", 5)))
            continue
        if resp.status_code in (401, 403):
            raise APIError(f"HTTP {resp.status_code} - invalid key or developer access not enabled")
        payload = resp.json()
        if payload.get("code") != 1:
            raise APIError(payload.get("msg", "unknown error"))
        return payload.get("data") or {}
    raise APIError("rate limited, try again later")


def idem_key():
    """Generate once per paid order and REUSE it when retrying after a timeout."""
    return secrets.token_hex(16)


def paid_call(path, **fields):
    """POST a paid request; retries a network timeout with the same idempotency key."""
    fields.setdefault("idempotency_key", idem_key())
    for attempt in range(3):
        try:
            return call("POST", path, **fields)
        except requests.exceptions.RequestException:
            if attempt == 2:
                raise
            time.sleep(2)
