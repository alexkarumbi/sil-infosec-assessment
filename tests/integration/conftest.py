"""Shared fixtures for tests that run against the live lab (scripts/lab_up.sh first).

Environment: BASE_URL (default http://localhost:8080, the WAF), KC_URL (default http://localhost:8081),
LAB_USER_PASSWORD (default: read from lab/.env).
"""
import os
import pathlib

import httpx
import pytest

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8080")
KC_URL = os.environ.get("KC_URL", "http://localhost:8081")


def _password() -> str:
    if os.environ.get("LAB_USER_PASSWORD"):
        return os.environ["LAB_USER_PASSWORD"]
    env = pathlib.Path(__file__).resolve().parents[2] / "lab" / ".env"
    for line in env.read_text().splitlines():
        if line.startswith("LAB_USER_PASSWORD="):
            return line.split("=", 1)[1].strip()
    raise RuntimeError("Set LAB_USER_PASSWORD or create lab/.env")


@pytest.fixture(scope="session")
def tokens() -> dict[str, str]:
    out = {}
    for user in ("dr.wanjiru", "reception.otieno", "dr.kamau"):
        resp = httpx.post(
            f"{KC_URL}/realms/sil/protocol/openid-connect/token",
            data={"grant_type": "password", "client_id": "sil-portal", "username": user, "password": _password()},
            timeout=15,
        )
        resp.raise_for_status()
        out[user] = resp.json()["access_token"]
    return out


@pytest.fixture(scope="session")
def client():
    with httpx.Client(base_url=BASE_URL, timeout=120) as c:
        yield c


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
