"""Simple TTL cache — no external dependency."""

import time
import hashlib
import asyncio
from functools import wraps


class TTLCache:
    """In-memory TTL cache with max size."""

    def __init__(self, maxsize: int = 512, ttl: float = 300):
        self._store: dict[str, tuple[float, object]] = {}
        self._maxsize = maxsize
        self._ttl = ttl

    def get(self, key: str):
        entry = self._store.get(key)
        if entry is None:
            return None
        expiry, value = entry
        if time.monotonic() > expiry:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: object, ttl: float | None = None):
        if len(self._store) >= self._maxsize:
            # Evict oldest entry
            oldest = min(self._store.items(), key=lambda x: x[1][0])
            del self._store[oldest[0]]
        expiry = time.monotonic() + (ttl if ttl is not None else self._ttl)
        self._store[key] = (expiry, value)

    def clear(self):
        self._store.clear()


# Global caches
embedding_cache = TTLCache(maxsize=500, ttl=3600)       # 1 hour
profile_cache = TTLCache(maxsize=10, ttl=300)            # 5 minutes
article_cache = TTLCache(maxsize=50, ttl=30)             # 30 seconds
keyword_cache = TTLCache(maxsize=50, ttl=60)             # 1 minute


def cache_key(*args, **kwargs) -> str:
    raw = str(args) + str(sorted(kwargs.items()))
    return hashlib.md5(raw.encode()).hexdigest()[:16]


def async_ttl_cache(cache: TTLCache):
    """Decorator for async functions — caches return value by cache_key(args, kwargs)."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = cache_key(func.__name__, *args, **kwargs)
            hit = cache.get(key)
            if hit is not None:
                return hit
            result = await func(*args, **kwargs)
            cache.set(key, result)
            return result
        return wrapper
    return decorator
