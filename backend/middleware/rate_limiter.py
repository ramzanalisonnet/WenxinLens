"""SlowAPI rate limiter configuration."""
from slowapi import Limiter
from slowapi.util import get_remote_address

from config import get_settings

settings = get_settings()

# Redis URL includes auth credentials; falls back to in-memory if unavailable
_redis_url = settings.redis_url

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[
        f"{settings.rate_limit_per_minute}/minute",
        f"{settings.rate_limit_per_hour}/hour",
    ],
    storage_uri=_redis_url,
)
