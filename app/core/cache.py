import asyncio
import json
import time
from typing import Any

from app.core.config import get_settings


class InMemoryTTLCache:
    """Async in-memory TTL cache with prefix invalidation and hit/miss metrics."""

    def __init__(self, default_ttl: int = 60) -> None:
        self._default_ttl = default_ttl
        self._store: dict[str, tuple[Any, float]] = {}
        self._lock = asyncio.Lock()
        self.hits = 0
        self.misses = 0

    def _evict_expired_unlocked(self, now: float) -> None:
        expired = [k for k, (_, expires_at) in self._store.items() if expires_at <= now]
        for k in expired:
            del self._store[k]

    async def get(self, key: str) -> Any | None:
        async with self._lock:
            now = time.monotonic()
            entry = self._store.get(key)
            if entry is None:
                self.misses += 1
                return None
            value, expires_at = entry
            if expires_at <= now:
                del self._store[key]
                self.misses += 1
                return None
            self.hits += 1
            return value

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        ttl_seconds = ttl if ttl is not None else self._default_ttl
        async with self._lock:
            now = time.monotonic()
            self._evict_expired_unlocked(now)
            self._store[key] = (value, now + ttl_seconds)

    async def delete(self, key: str) -> None:
        async with self._lock:
            self._store.pop(key, None)

    async def delete_prefix(self, prefix: str) -> int:
        async with self._lock:
            matching = [k for k in self._store if k.startswith(prefix)]
            for k in matching:
                del self._store[k]
            return len(matching)

    async def clear(self) -> None:
        async with self._lock:
            self._store.clear()

    async def stats(self) -> dict[str, Any]:
        async with self._lock:
            self._evict_expired_unlocked(time.monotonic())
            total = self.hits + self.misses
            hit_rate = round((self.hits / total) * 100, 2) if total > 0 else 0.0
            return {
                "backend": "memory",
                "keys": len(self._store),
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate_percent": hit_rate,
            }


class RedisTTLCache:
    """Optional Redis-backed cache with JSON serialization and in-memory fallback."""

    def __init__(self, redis_url: str, default_ttl: int = 60) -> None:
        import redis.asyncio as aioredis  # type: ignore[import-not-found]

        self._client = aioredis.from_url(redis_url, decode_responses=True)
        self._default_ttl = default_ttl
        self.hits = 0
        self.misses = 0

    async def get(self, key: str) -> Any | None:
        raw = await self._client.get(key)
        if raw is None:
            self.misses += 1
            return None
        self.hits += 1
        return json.loads(raw)

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        ttl_seconds = ttl if ttl is not None else self._default_ttl
        await self._client.set(key, json.dumps(value, default=str), ex=ttl_seconds)

    async def delete(self, key: str) -> None:
        await self._client.delete(key)

    async def delete_prefix(self, prefix: str) -> int:
        keys = [k async for k in self._client.scan_iter(match=f"{prefix}*")]
        if not keys:
            return 0
        return int(await self._client.delete(*keys))

    async def clear(self) -> None:
        await self._client.flushdb()

    async def stats(self) -> dict[str, Any]:
        total = self.hits + self.misses
        hit_rate = round((self.hits / total) * 100, 2) if total > 0 else 0.0
        size = await self._client.dbsize()
        return {
            "backend": "redis",
            "keys": size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate_percent": hit_rate,
        }


def _create_cache() -> InMemoryTTLCache | RedisTTLCache:
    settings = get_settings()
    if settings.redis_url:
        try:
            return RedisTTLCache(
                settings.redis_url,
                default_ttl=settings.cache_default_ttl_seconds,
            )
        except Exception:
            pass
    return InMemoryTTLCache(default_ttl=settings.cache_default_ttl_seconds)


cache = _create_cache()


def user_tasks_cache_prefix(user_id: int) -> str:
    return f"tasks:user:{user_id}:"


def task_detail_cache_key(task_id: int) -> str:
    return f"tasks:detail:{task_id}"


async def invalidate_user_task_cache(user_id: int, task_id: int | None = None) -> None:
    await cache.delete_prefix(user_tasks_cache_prefix(user_id))
    if task_id is not None:
        await cache.delete(task_detail_cache_key(task_id))
