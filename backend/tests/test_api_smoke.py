from __future__ import annotations

import os

import pytest
import requests


BASE_URL = os.getenv("WENXINLENS_BASE_URL", "http://127.0.0.1:8010")
TIMEOUT_SECONDS = float(os.getenv("WENXINLENS_SMOKE_TIMEOUT", "20"))


def _url(path: str) -> str:
    return f"{BASE_URL.rstrip('/')}{path}"


@pytest.fixture(scope="module", autouse=True)
def require_running_backend() -> None:
    """Skip smoke tests if the backend server is not reachable."""
    try:
        response = requests.get(_url("/health"), timeout=TIMEOUT_SECONDS)
        if response.status_code != 200:
            pytest.skip(f"Backend not ready at {BASE_URL}: /health -> {response.status_code}")
    except requests.RequestException as exc:
        pytest.skip(f"Backend not reachable at {BASE_URL}: {exc}")


def test_health_endpoint() -> None:
    response = requests.get(_url("/health"), timeout=TIMEOUT_SECONDS)
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("status") == "ok"


def test_avatar_chat_endpoint() -> None:
    response = requests.post(
        _url("/api/v1/avatar/chat"),
        json={
            "building_name": "Temple of Heaven",
            "dynasty": "Ming Dynasty",
            "character_type": "architect",
            "message": "Share one key architectural idea.",
            "language": "en",
        },
        timeout=TIMEOUT_SECONDS,
    )
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload.get("reply"), str) and payload["reply"].strip()


def test_avatar_chat_endpoint_minimal_payload() -> None:
    response = requests.post(
        _url("/api/v1/avatar/chat"),
        json={"message": "Give me a short overview."},
        timeout=TIMEOUT_SECONDS,
    )
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload.get("reply"), str) and payload["reply"].strip()


def test_avatar_lipsync_endpoint() -> None:
    response = requests.post(
        _url("/api/v1/avatar/lipsync"),
        json={"text": "Welcome to WenxinLens", "duration_ms": 1800},
        timeout=TIMEOUT_SECONDS,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("duration_ms", 0) > 0
    assert isinstance(payload.get("visemes"), list) and len(payload["visemes"]) > 0


def test_historical_character_endpoint() -> None:
    response = requests.post(
        _url("/api/v1/advanced/historical-character"),
        json={
            "building_name": "Forbidden City",
            "dynasty": "Ming Dynasty",
            "character_type": "architect",
            "message": "Why was this design significant?",
            "language": "en",
        },
        timeout=TIMEOUT_SECONDS,
    )
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload.get("persona_name"), str) and payload["persona_name"].strip()
    assert isinstance(payload.get("reply"), str) and payload["reply"].strip()


def test_historical_character_endpoint_minimal_payload() -> None:
    response = requests.post(
        _url("/api/v1/advanced/historical-character"),
        json={"message": "Why does this architecture matter?"},
        timeout=TIMEOUT_SECONDS,
    )
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload.get("persona_name"), str) and payload["persona_name"].strip()
    assert isinstance(payload.get("reply"), str) and payload["reply"].strip()