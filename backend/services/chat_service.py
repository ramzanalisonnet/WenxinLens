"""
ChatService — manages conversation sessions via Redis.

Each session stores:
  - Message history (list of role/content dicts)
  - Language preference
  - Building context (if any)
  - TTL of 24 hours
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional

import redis.asyncio as aioredis
from loguru import logger
from pydantic import BaseModel

from config import get_settings

settings = get_settings()

SESSION_TTL_SECONDS = 86400  # 24 hours
MAX_HISTORY_MESSAGES = 20


class SessionData(BaseModel):
    session_id: str
    language: str = "en"
    created_at: str
    updated_at: str
    message_count: int = 0
    messages: list[dict] = []


class ChatService:
    def __init__(self) -> None:
        self._redis: Optional[aioredis.Redis] = None

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = await aioredis.from_url(
                settings.redis_url,
                password=settings.redis_password or None,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._redis

    def _key(self, session_id: str) -> str:
        return f"wenxinlens:session:{session_id}"

    async def create_session(self, session_id: str, language: str = "en", user: dict | None = None) -> SessionData:
        now = datetime.now(timezone.utc).isoformat()
        session = SessionData(
            session_id=session_id,
            language=language,
            created_at=now,
            updated_at=now,
        )
        redis = await self._get_redis()
        await redis.setex(self._key(session_id), SESSION_TTL_SECONDS, session.model_dump_json())
        return session

    async def get_session(self, session_id: str) -> Optional[SessionData]:
        try:
            redis = await self._get_redis()
            data = await redis.get(self._key(session_id))
            if not data:
                return None
            return SessionData.model_validate_json(data)
        except Exception as exc:
            logger.warning(f"Failed to get session {session_id}: {exc}")
            return None

    async def add_message(self, session_id: str, role: str, content: str) -> None:
        session = await self.get_session(session_id)
        if not session:
            session = await self.create_session(session_id)

        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        session.messages.append(message)
        session.message_count += 1
        session.updated_at = datetime.now(timezone.utc).isoformat()

        # Trim to max history
        if len(session.messages) > MAX_HISTORY_MESSAGES:
            session.messages = session.messages[-MAX_HISTORY_MESSAGES:]

        redis = await self._get_redis()
        await redis.setex(self._key(session_id), SESSION_TTL_SECONDS, session.model_dump_json())

    async def get_history(self, session_id: str) -> list[dict]:
        session = await self.get_session(session_id)
        if not session:
            return []
        return [{"role": m["role"], "content": m["content"]} for m in session.messages]

    async def delete_session(self, session_id: str) -> None:
        redis = await self._get_redis()
        await redis.delete(self._key(session_id))
