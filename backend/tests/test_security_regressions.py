from __future__ import annotations

import pytest
from pydantic import ValidationError

from config import Settings
from services.vision_service import VisionService


def test_production_rejects_development_secret_defaults() -> None:
    with pytest.raises(ValidationError):
        Settings(app_env="production")


def test_production_accepts_distinct_strong_secrets() -> None:
    settings = Settings(
        app_env="production",
        app_debug=False,
        app_secret_key="app-secret-" + "a" * 40,
        jwt_secret_key="jwt-secret-" + "b" * 40,
        master_api_key="master-key-" + "c" * 40,
        redis_password="redis-password-" + "d" * 40,
        neo4j_password="neo4j-password-" + "e" * 40,
        cors_origins=["https://example.org"],
    )
    assert settings.is_production


def test_production_rejects_reused_secrets() -> None:
    secret = "same-secret-" + "x" * 40
    with pytest.raises(ValidationError):
        Settings(
            app_env="production",
            app_debug=False,
            app_secret_key=secret,
            jwt_secret_key=secret,
            master_api_key="master-key-" + "c" * 40,
            redis_password="redis-password-" + "d" * 40,
            neo4j_password="neo4j-password-" + "e" * 40,
            cors_origins=["https://example.org"],
        )


def test_mock_vision_prediction_never_claims_a_building_identity() -> None:
    prediction = VisionService._mock_prediction()
    assert prediction.building_name.startswith("Unknown architecture")
    assert prediction.confidence_score == 0.0
    assert prediction.top_k == []
