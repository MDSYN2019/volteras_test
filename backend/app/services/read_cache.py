from __future__ import annotations

from collections.abc import Callable
from threading import RLock
from time import monotonic
from typing import TypeVar

T = TypeVar("T")


class TTLCache:
    """Small thread-safe TTL cache for common read-heavy API responses."""

    def __init__(self, ttl_seconds: int, max_entries: int = 256) -> None:
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self._items: dict[str, tuple[float, object]] = {}
        self._lock = RLock()

    @property
    def enabled(self) -> bool:
        return self.ttl_seconds > 0

    def get_or_set(self, key: str, factory: Callable[[], T]) -> T:
        if not self.enabled:
            return factory()

        now = monotonic()
        with self._lock:
            cached = self._items.get(key)
            if cached and cached[0] > now:
                return cached[1]  # type: ignore[return-value]

        value = factory()
        expires_at = now + self.ttl_seconds
        with self._lock:
            if len(self._items) >= self.max_entries:
                self._evict_expired_or_oldest(now)
            self._items[key] = (expires_at, value)
        return value

    def clear(self) -> None:
        with self._lock:
            self._items.clear()

    def _evict_expired_or_oldest(self, now: float) -> None:
        expired_keys = [key for key, (expires_at, _) in self._items.items() if expires_at <= now]
        for key in expired_keys:
            self._items.pop(key, None)
        if len(self._items) >= self.max_entries and self._items:
            oldest_key = min(self._items, key=lambda key: self._items[key][0])
            self._items.pop(oldest_key, None)
