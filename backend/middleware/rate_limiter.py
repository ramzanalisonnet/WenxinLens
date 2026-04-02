"""SlowAPI rate limiter configuration."""
import os

from slowapi import Limiter
from slowapi.util import get_remote_address

from config import get_settings

settings = get_settings()

# Use Redis-backed limiter only when explicitly enabled.
_use_redis_limiter = os.getenv("WENXINLENS_USE_REDIS_LIMITER", "").lower() in {"1", "true", "yes"}
_storage_uri = settings.redis_url if _use_redis_limiter else None

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[
        f"{settings.rate_limit_per_minute}/minute",
        f"{settings.rate_limit_per_hour}/hour",
    ],
    storage_uri=_storage_uri,
)
