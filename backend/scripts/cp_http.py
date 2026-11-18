"""Authenticated HTTP helpers for CrowdPulse day verify scripts."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"
_TOKEN: str | None = None

# Default: control-room admin (ingest + reset-metrics for day scripts)
_USERNAME = "tsp.admin"
_PASSWORD = "Admin@TS2026"


def ensure_login(username: str = _USERNAME, password: str = _PASSWORD) -> str:
    global _TOKEN
    if _TOKEN:
        return _TOKEN
    payload = json.dumps({"username": username, "password": password}).encode()
    req = urllib.request.Request(
        BASE + "/api/v1/auth/login",
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.loads(resp.read().decode())
    _TOKEN = body["access_token"]
    return _TOKEN


def _headers(extra: dict | None = None) -> dict:
    ensure_login()
    h = {"Authorization": f"Bearer {_TOKEN}"}
    if extra:
        h.update(extra)
    return h


def get(path: str):
    req = urllib.request.Request(BASE + path, headers=_headers(), method="GET")
    with urllib.request.urlopen(req, timeout=120) as resp:
        raw = resp.read().decode()
        data = json.loads(raw) if raw else {}
        return getattr(resp, "status", 200), data


def get_json(path: str):
    """Return parsed JSON only (day12/13 style)."""
    _, data = get(path)
    return data


def post(path: str, data: bytes = b""):
    req = urllib.request.Request(BASE + path, data=data, method="POST", headers=_headers())
    with urllib.request.urlopen(req, timeout=300) as resp:
        raw = resp.read().decode()
        return json.loads(raw) if raw else {}


def post_json(path: str, payload: dict):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        BASE + path,
        data=body,
        method="POST",
        headers=_headers({"Content-Type": "application/json"}),
    )
    with urllib.request.urlopen(req, timeout=600) as resp:
        raw = resp.read().decode()
        return json.loads(raw) if raw else {}


def public_get(path: str):
    """Unauthenticated GET (e.g. /health)."""
    with urllib.request.urlopen(BASE + path, timeout=60) as resp:
        return getattr(resp, "status", 200), json.loads(resp.read().decode())
