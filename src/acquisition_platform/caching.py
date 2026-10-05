"""Caching layer for the acquisition platform.

Provides a TTL-based cache with LRU eviction, a decorator for caching
function results, and global cache management utilities.
"""

from __future__ import annotations

import json
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


@dataclass
class CacheEntry:
    """A single cache entry with metadata."""

    key: str
    value: Any
    ttl: Optional[int]
    created_at: str
    access_count: int = 0


@dataclass
class CacheStats:
    """Statistics for cache operations."""

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate hit rate as hits / (hits + misses)."""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total


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


class CacheManager:
    """High-level cache manager with monitoring, reporting, and warming."""

    def __init__(
        self,
        ttl: Optional[int] = 300,
        max_size: Optional[int] = 1024,
    ) -> None:
        self._ttl = ttl
        self._max_size = max_size
        self._store: OrderedDict[str, CacheEntry] = OrderedDict()
        self._stats = CacheStats()
        self._lock = threading.Lock()

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> CacheEntry:
        """Store a value in the cache.

        Parameters
        ----------
        key : str
            Cache key.
        value : Any
            Value to cache.
        ttl : int or None
            Time-to-live in seconds. None means no expiration.
            If not provided, uses the manager's default TTL.

        Returns
        -------
        CacheEntry
            The created cache entry.
        """
        with self._lock:
            effective_ttl = ttl if ttl is not None else self._ttl
            entry = CacheEntry(
                key=key,
                value=value,
                ttl=effective_ttl,
                created_at=datetime.now(timezone.utc).isoformat(),
            )
            if key in self._store:
                del self._store[key]
            self._store[key] = entry
            self._store.move_to_end(key)
            self._stats.size = len(self._store)
            self._evict_if_needed()
            return entry

    def get(self, key: str) -> Any:
        """Get a value from the cache.

        Returns the cached value or None if not found or expired.
        """
        with self._lock:
            if key not in self._store:
                self._stats.misses += 1
                return None

            entry = self._store[key]
            if self._is_expired(entry):
                del self._store[key]
                self._stats.misses += 1
                self._stats.size = len(self._store)
                return None

            entry.access_count += 1
            self._store.move_to_end(key)
            self._stats.hits += 1
            return entry.value

    def invalidate(self, key: str) -> bool:
        """Remove an entry from the cache.

        Returns True if the key was found and removed, False otherwise.
        """
        with self._lock:
            if key in self._store:
                del self._store[key]
                self._stats.size = len(self._store)
                return True
            return False

    def get_stats(self) -> CacheStats:
        """Return current cache statistics."""
        with self._lock:
            return CacheStats(
                hits=self._stats.hits,
                misses=self._stats.misses,
                evictions=self._stats.evictions,
                size=len(self._store),
            )

    def warm_cache(self, keys: list[str], values: list[Any]) -> int:
        """Pre-populate the cache with multiple key-value pairs.

        Parameters
        ----------
        keys : list of str
            Cache keys.
        values : list of Any
            Corresponding values.

        Returns
        -------
        int
            Number of entries warmed.

        Raises
        ------
        ValueError
            If keys and values have different lengths.
        """
        if len(keys) != len(values):
            raise ValueError("keys and values must have the same length")

        count = 0
        for key, value in zip(keys, values):
            self.set(key, value)
            count += 1
        return count

    def evict_entries(self, policy: str) -> int:
        """Evict entries based on the given policy.

        Parameters
        ----------
        policy : str
            Eviction policy: "lru" (least recently used) or "ttl" (expired).

        Returns
        -------
        int
            Number of entries evicted.
        """
        with self._lock:
            if policy == "lru":
                return self._evict_lru()
            elif policy == "ttl":
                return self._evict_ttl()
            else:
                raise ValueError(f"Unknown eviction policy: {policy}")

    def serialize_cache(self) -> str:
        """Serialize the cache to a JSON string.

        Returns
        -------
        str
            JSON representation of all cache entries.
        """
        with self._lock:
            data = {}
            for key, entry in self._store.items():
                data[key] = {
                    "key": entry.key,
                    "value": entry.value,
                    "ttl": entry.ttl,
                    "created_at": entry.created_at,
                    "access_count": entry.access_count,
                }
            return json.dumps(data)

    def monitor_cache(self) -> dict[str, Any]:
        """Return monitoring data for the cache.

        Returns
        -------
        dict[str, Any]
            Dictionary with hits, misses, size, and hit_rate.
        """
        with self._lock:
            total = self._stats.hits + self._stats.misses
            hit_rate = self._stats.hits / total if total > 0 else 0.0
            return {
                "hits": self._stats.hits,
                "misses": self._stats.misses,
                "size": len(self._store),
                "hit_rate": hit_rate,
            }

    def generate_cache_report(self) -> dict[str, Any]:
        """Generate a comprehensive cache report.

        Returns
        -------
        dict[str, Any]
            Dictionary with stats and all cache entries.
        """
        with self._lock:
            entries = []
            for key, entry in self._store.items():
                entries.append({
                    "key": entry.key,
                    "value": entry.value,
                    "ttl": entry.ttl,
                    "created_at": entry.created_at,
                    "access_count": entry.access_count,
                })
            total = self._stats.hits + self._stats.misses
            hit_rate = self._stats.hits / total if total > 0 else 0.0
            return {
                "stats": {
                    "hits": self._stats.hits,
                    "misses": self._stats.misses,
                    "evictions": self._stats.evictions,
                    "size": len(self._store),
                    "hit_rate": hit_rate,
                },
                "entries": entries,
            }

    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if a cached entry has expired."""
        if entry.ttl is None:
            return False
        try:
            created = datetime.fromisoformat(entry.created_at)
            elapsed = (datetime.now(timezone.utc) - created).total_seconds()
            return elapsed > entry.ttl
        except (ValueError, TypeError):
            return False

    def _evict_if_needed(self) -> None:
        """Evict least recently used entries if over capacity."""
        if self._max_size is None:
            return
        while len(self._store) > self._max_size:
            self._store.popitem(last=False)
            self._stats.evictions += 1

    def _evict_lru(self) -> int:
        """Evict the least recently used entry."""
        if not self._store:
            return 0
        self._store.popitem(last=False)
        self._stats.evictions += 1
        self._stats.size = len(self._store)
        return 1

    def _evict_ttl(self) -> int:
        """Evict all expired entries."""
        expired_keys = [
            key for key, entry in self._store.items()
            if self._is_expired(entry)
        ]
        for key in expired_keys:
            del self._store[key]
        self._stats.evictions += len(expired_keys)
        self._stats.size = len(self._store)
        return len(expired_keys)
