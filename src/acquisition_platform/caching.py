"""Caching layer for the acquisition platform.

Provides a TTL-based cache with LRU eviction, a decorator for caching
function results, and global cache management utilities.
"""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


@dataclass
class CacheStats:
    """Statistics for cache operations."""

    hits: int = 0
    misses: int = 0
    evictions: int = 0


class Cache:
    """Thread-safe TTL cache with LRU eviction.

    Parameters
    ----------
    ttl : float or None
        Time-to-live in seconds. None means no expiration.
    max_size : int or None
        Maximum number of entries. None means unlimited.
    """

    def __init__(
        self,
        ttl: Optional[float] = 300.0,
        max_size: Optional[int] = 1024,
    ) -> None:
        self.ttl = ttl
        self.max_size = max_size
        self._store: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self._stats = CacheStats()
        self._lock = threading.Lock()

    def get(self, key: str) -> Any:
        """Get a value from the cache.

        Returns the cached value or None if not found or expired.
        """
        with self._lock:
            if key not in self._store:
                self._stats.misses += 1
                return None

            timestamp, value = self._store[key]
            if self._is_expired(timestamp):
                del self._store[key]
                self._stats.misses += 1
                return None

            # Move to end (most recently used)
            self._store.move_to_end(key)
            self._stats.hits += 1
            return value

    def set(self, key: str, value: Any) -> None:
        """Store a value in the cache."""
        with self._lock:
            now = time.monotonic()
            if key in self._store:
                del self._store[key]
            self._store[key] = (now, value)
            self._store.move_to_end(key)
            self._evict_if_needed()

    def clear(self) -> None:
        """Remove all entries and reset statistics."""
        with self._lock:
            self._store.clear()
            self._stats = CacheStats()

    @property
    def stats(self) -> CacheStats:
        """Return current cache statistics."""
        with self._lock:
            return CacheStats(
                hits=self._stats.hits,
                misses=self._stats.misses,
                evictions=self._stats.evictions,
            )

    def _is_expired(self, timestamp: float) -> bool:
        """Check if a cached entry has expired."""
        if self.ttl is None:
            return False
        return (time.monotonic() - timestamp) > self.ttl

    def _evict_if_needed(self) -> None:
        """Evict least recently used entries if over capacity."""
        if self.max_size is None:
            return
        while len(self._store) > self.max_size:
            self._store.popitem(last=False)
            self._stats.evictions += 1


# Global cache instance
_global_cache: Cache = Cache()


def cached(
    ttl: Optional[float] = 300.0,
    max_size: Optional[int] = 1024,
    cache_instance: Optional[Cache] = None,
) -> Callable[[F], F]:
    """Decorator that caches function results.

    Parameters
    ----------
    ttl : float or None
        Time-to-live in seconds. None means no expiration.
    max_size : int or None
        Maximum cache size. None means unlimited.
    cache_instance : Cache or None
        Custom cache instance. If None, a new Cache is created with the
        given ttl and max_size.

    Returns
    -------
    Callable
        Decorated function with caching behavior.
    """
    def decorator(func: F) -> F:
        _cache = cache_instance if cache_instance is not None else Cache(ttl=ttl, max_size=max_size)

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Build a cache key from function name and arguments
            key_parts = [func.__qualname__]
            key_parts.extend(str(a) for a in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            key = "|".join(key_parts)

            result = _cache.get(key)
            if result is not None:
                return result

            result = func(*args, **kwargs)
            _cache.set(key, result)
            return result

        return wrapper  # type: ignore[return-value]
    return decorator


def clear_cache() -> None:
    """Clear the global cache."""
    _global_cache.clear()


def get_cache_stats() -> CacheStats:
    """Get statistics for the global cache."""
    return _global_cache.stats
