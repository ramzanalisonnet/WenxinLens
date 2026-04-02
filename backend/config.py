"""
WenxinLens – Global Configuration
Loads from environment variables (via .env file in development).
"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide settings resolved from environment variables."""

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), "..", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ────────────────────────────────────────────
    app_env: Literal["development", "staging", "production"] = "development"
    app_secret_key: str = Field(default="dev-secret-key-change-in-production!!", min_length=16)
    app_debug: bool = False
    frontend_url: str = "http://localhost:3000"
    fast_startup: bool = False

    # ── Server ─────────────────────────────────────────────────
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            raw = v.strip()
            if raw.startswith("[") and raw.endswith("]"):
                raw = raw[1:-1]
            origins = []
            for origin in raw.split(","):
                cleaned = origin.strip().strip('"').strip("'")
                if cleaned:
                    origins.append(cleaned)
            return origins
        return v

    # ── Redis ──────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"
    redis_password: str = ""

    # ── Neo4j ─────────────────────────────────────────────────
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "wenxinlens123"

    # ── Milvus ────────────────────────────────────────────────
    milvus_host: str = "localhost"
    milvus_port: int = 19530
    milvus_collection: str = "wenxinlens_architecture"

    # ── LLM Providers ─────────────────────────────────────────
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    dashscope_api_key: str = ""
    qwen_model: str = "qwen2.5-72b-instruct"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b"

    @property
    def llm_provider(self) -> Literal["openai", "qwen", "ollama"]:
        if self.openai_api_key:
            return "openai"
        if self.dashscope_api_key:
            return "qwen"
        return "ollama"

    # ── Embeddings ────────────────────────────────────────────
    embedding_model: str = "BAAI/bge-large-zh-v1.5"
    embedding_dim: int = 1024
    embedding_device: str = "cpu"

    # ── Vision ────────────────────────────────────────────────
    yolo_model_path: str = "models/yolov8_architecture.pt"
    clip_model_name: str = "openai/clip-vit-large-patch14"
    vision_confidence_threshold: float = 0.7
    max_image_size_mb: int = 10

    # ── TTS ───────────────────────────────────────────────────
    tts_provider: Literal["azure", "elevenlabs", "coqui"] = "azure"
    azure_tts_key: str = ""
    azure_tts_region: str = "eastasia"
    elevenlabs_api_key: str = ""

    # ── Auth ──────────────────────────────────────────────────
    jwt_secret_key: str = Field(default="dev-secret-key", min_length=8)
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440
    master_api_key: str = "dev-master-key"

    # ── Rate Limiting ─────────────────────────────────────────
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 500

    # ── RAG ───────────────────────────────────────────────────
    rag_chunk_size: int = 512
    rag_chunk_overlap: int = 64
    rag_top_k: int = 5

    # ── Monitoring ────────────────────────────────────────────
    sentry_dsn: str = ""
    log_level: str = "INFO"

    # ── Advanced Feature Layer ───────────────────────────────
    advanced_feature_cache_ttl_seconds: int = 7200
    advanced_feature_parallelism: int = 5
    time_reconstruction_model: str = "stabilityai/stable-diffusion-xl-base-1.0"
    time_reconstruction_controlnet: str = "lllyasviel/control_v11p_sd15_canny"
    enable_gpu_diffusion: bool = False
    cinematic_tts_provider: str = "coqui"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings singleton."""
    return Settings()
