from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings

# Limits are per client IP and kept in memory (per process).
# Behind a reverse proxy, run uvicorn with --proxy-headers so the real
# client IP is used instead of the proxy's.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.rate_limit_default],
    enabled=settings.rate_limit_enabled,
)
