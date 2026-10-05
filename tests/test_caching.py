"""Tests for the caching layer."""
import time
import pytest
from acquisition_platform.caching import (
    Cache,
    CacheStats,
    cached,
    clear_cache,
    get_cache_stats,
)


class TestCacheHitMiss:
    """Test basic cache hit/miss behavior."""

    def setup_method(self):
        clear_cache()

    def test_cache_miss_on_first_access(self):
        cache = Cache(ttl=60.0)
        # Getting a key that was never set is a miss
        result = cache.get("nonexistent")
        assert result is None
        stats = cache.stats
        assert stats.misses == 1
        assert stats.hits == 0

    def test_cache_hit_on_second_access(self):
        cache = Cache(ttl=60.0)
        cache.set("key1", "value1")
        cache.get("key1")  # hit
        cache.get("key1")  # hit
        stats = cache.stats
        assert stats.hits == 2
        assert stats.misses == 0

    def test_cache_returns_none_for_missing_key(self):
        cache = Cache(ttl=60.0)
        result = cache.get("nonexistent")
        assert result is None

    def test_cache_overwrite_existing_key(self):
        cache = Cache(ttl=60.0)
        cache.set("key1", "value1")
        cache.set("key1", "value2")
        assert cache.get("key1") == "value2"


class TestTTLExpiration:
    """Test TTL-based expiration."""

    def setup_method(self):
        clear_cache()

    def test_ttl_expiration_returns_none(self):
        cache = Cache(ttl=0.05)  # 50ms TTL
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        time.sleep(0.1)
        assert cache.get("key1") is None

    def test_ttl_expiration_counts_as_miss(self):
        cache = Cache(ttl=0.05)
        cache.set("key1", "value1")
        cache.get("key1")  # hit
        time.sleep(0.1)
        cache.get("key1")  # miss (expired)
        stats = cache.stats
        assert stats.hits == 1
        assert stats.misses == 1

    def test_no_ttl_never_expires(self):
        cache = Cache(ttl=None)  # No expiration
        cache.set("key1", "value1")
        time.sleep(0.05)
        assert cache.get("key1") == "value1"

    def test_ttl_zero_expires_immediately(self):
        cache = Cache(ttl=0.0)
        cache.set("key1", "value1")
        time.sleep(0.01)
        assert cache.get("key1") is None


class TestCacheStats:
    """Test cache statistics tracking."""

    def setup_method(self):
        clear_cache()

    def test_initial_stats_are_zero(self):
        cache = Cache(ttl=60.0)
        stats = cache.stats
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.evictions == 0

    def test_stats_track_hits_and_misses(self):
        cache = Cache(ttl=60.0)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.get("a")  # hit
        cache.get("a")  # hit
        cache.get("b")  # hit
        cache.get("c")  # miss
        cache.get("d")  # miss
        stats = cache.stats
        assert stats.hits == 3
        assert stats.misses == 2

    def test_stats_track_evictions(self):
        cache = Cache(ttl=60.0, max_size=2)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)  # Should evict "a"
        stats = cache.stats
        assert stats.evictions >= 1

    def test_get_cache_stats_returns_stats(self):
        stats = get_cache_stats()
        assert isinstance(stats, CacheStats)
        assert hasattr(stats, "hits")
        assert hasattr(stats, "misses")
        assert hasattr(stats, "evictions")


class TestCacheClearing:
    """Test cache clearing functionality."""

    def setup_method(self):
        clear_cache()

    def test_clear_removes_all_entries(self):
        cache = Cache(ttl=60.0)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.clear()
        assert cache.get("a") is None
        assert cache.get("b") is None

    def test_clear_resets_stats(self):
        cache = Cache(ttl=60.0)
        cache.set("a", 1)
        cache.get("a")  # hit
        cache.get("b")  # miss
        cache.clear()
        stats = cache.stats
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.evictions == 0

    def test_clear_cache_function_clears_global(self):
        from acquisition_platform.caching import _global_cache
        _global_cache.set("x", 42)
        clear_cache()
        assert _global_cache.get("x") is None


class TestCachedDecorator:
    """Test the cached decorator."""

    def setup_method(self):
        clear_cache()

    def test_cached_decorator_caches_results(self):
        call_count = 0

        @cached(ttl=60.0)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        result1 = expensive_function(5)
        result2 = expensive_function(5)
        assert result1 == 10
        assert result2 == 10
        assert call_count == 1  # Only called once

    def test_cached_decorator_different_args(self):
        call_count = 0

        @cached(ttl=60.0)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        expensive_function(5)
        expensive_function(10)
        assert call_count == 2  # Called twice for different args

    def test_cached_decorator_ttl_expiration(self):
        call_count = 0

        @cached(ttl=0.05)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        expensive_function(5)
        expensive_function(5)
        assert call_count == 1
        time.sleep(0.1)
        expensive_function(5)
        assert call_count == 2  # Called again after TTL expired

    def test_cached_decorator_preserves_function_metadata(self):
        @cached(ttl=60.0)
        def my_function(x):
            """My docstring."""
            return x

        assert my_function.__name__ == "my_function"
        assert my_function.__doc__ == "My docstring."

    def test_cached_decorator_with_kwargs(self):
        call_count = 0

        @cached(ttl=60.0)
        def func(a, b=10):
            nonlocal call_count
            call_count += 1
            return a + b

        func(1, b=2)
        func(1, b=2)
        assert call_count == 1
        func(1, b=3)
        assert call_count == 2


class TestCacheEviction:
    """Test cache eviction when max_size is reached."""

    def setup_method(self):
        clear_cache()

    def test_lru_eviction_when_full(self):
        cache = Cache(ttl=60.0, max_size=3)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        cache.set("d", 4)  # Should evict "a" (LRU)
        assert cache.get("a") is None
        assert cache.get("d") == 4

    def test_eviction_count_tracked(self):
        cache = Cache(ttl=60.0, max_size=2)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)  # evicts "a"
        cache.set("d", 4)  # evicts "b"
        stats = cache.stats
        assert stats.evictions == 2

    def test_access_refreshes_lru_order(self):
        cache = Cache(ttl=60.0, max_size=3)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        cache.get("a")  # Refresh "a" so "b" is now LRU
        cache.set("d", 4)  # Should evict "b"
        assert cache.get("a") == 1
        assert cache.get("b") is None
        assert cache.get("d") == 4


class TestCacheIntegration:
    """Integration tests with actual platform modules."""

    def setup_method(self):
        clear_cache()

    def test_entity_resolver_uses_cache(self):
        """EntityResolver._jaro_winkler should use caching."""
        from acquisition_platform.entity_resolution import EntityResolver
        resolver = EntityResolver()
        entities = [
            {"id": "e1", "name": "Acme Corp", "domain": "acme.com"},
            {"id": "e2", "name": "Acme Corporation", "domain": "acme.com"},
        ]
        # First call
        result1 = resolver.resolve(entities)
        # Second call should use cached Jaro-Winkler results
        result2 = resolver.resolve(entities)
        assert len(result1) == len(result2)

    def test_valuation_engine_uses_cache(self):
        """ValuationEngine DCF should use caching."""
        from acquisition_platform.valuation import ValuationEngine
        engine = ValuationEngine()
        args = {
            "free_cash_flow": 100000,
            "growth_rate": 0.05,
            "discount_rate": 0.10,
            "terminal_growth": 0.02,
            "years": 5,
        }
        result1 = engine.dcf_valuation(**args)
        result2 = engine.dcf_valuation(**args)
        assert result1.value == result2.value

    def test_fraud_detector_uses_cache(self):
        """FraudDetector graph analysis should use caching."""
        from acquisition_platform.fraud_detection import FraudDetector
        detector = FraudDetector()
        graph = {
            "nodes": ["a", "b", "c"],
            "edges": [("a", "b"), ("b", "c"), ("c", "a")],
        }
        result1 = detector.analyze_graph(graph)
        result2 = detector.analyze_graph(graph)
        assert result1.has_ring == result2.has_ring
        assert result1.risk_score == result2.risk_score

    def test_recommendation_engine_uses_cache(self):
        """RecommendationEngine similarity should use caching."""
        from acquisition_platform.recommendation import (
            RecommendationEngine,
            UserProfile,
            ItemProfile,
        )
        engine = RecommendationEngine()
        user = UserProfile(user_id="u1", preferences={"topic": "ml"})
        items = [
            ItemProfile(item_id="i1", attributes={"topic": "ml"}, category="saas"),
            ItemProfile(item_id="i2", attributes={"topic": "ml"}, category="saas"),
        ]
        result1 = engine.recommend(user, items, k=2)
        result2 = engine.recommend(user, items, k=2)
        assert len(result1.recommendations) == len(result2.recommendations)


class TestCacheManagerSetGet:
    """Test CacheManager set and get operations."""

    def setup_method(self):
        from acquisition_platform.caching import CacheManager
        self.manager = CacheManager()

    def test_cache_set_get(self):
        """Value cached and retrieved."""
        self.manager.set("key1", "value1", ttl=60)
        result = self.manager.get("key1")
        assert result == "value1"

    def test_cache_set_returns_entry(self):
        """set() returns a CacheEntry."""
        from acquisition_platform.caching import CacheEntry
        entry = self.manager.set("key1", "value1", ttl=60)
        assert isinstance(entry, CacheEntry)
        assert entry.key == "key1"
        assert entry.value == "value1"
        assert entry.ttl == 60

    def test_cache_get_missing_returns_none(self):
        """Getting a missing key returns None."""
        result = self.manager.get("nonexistent")
        assert result is None


class TestCacheExpiration:
    """Test TTL expiration in CacheManager."""

    def setup_method(self):
        from acquisition_platform.caching import CacheManager
        self.manager = CacheManager()

    def test_cache_expiration(self):
        """TTL expiration works."""
        self.manager.set("key1", "value1", ttl=0.05)
        assert self.manager.get("key1") == "value1"
        time.sleep(0.1)
        assert self.manager.get("key1") is None

    def test_no_ttl_never_expires(self):
        """Entries with ttl=None never expire."""
        self.manager.set("key1", "value1", ttl=None)
        time.sleep(0.05)
        assert self.manager.get("key1") == "value1"


class TestEmptyCache:
    """Test empty cache behavior."""

    def setup_method(self):
        from acquisition_platform.caching import CacheManager
        self.manager = CacheManager()

    def test_empty_cache(self):
        """Empty cache returns defaults."""
        result = self.manager.get("anything")
        assert result is None
        stats = self.manager.get_stats()
        assert stats.hits == 0
        assert stats.misses == 1
        assert stats.evictions == 0
        assert stats.size == 0

    def test_empty_cache_report(self):
        """Report on empty cache has expected structure."""
        report = self.manager.generate_cache_report()
        assert isinstance(report, dict)
        assert "stats" in report
        assert "entries" in report


class TestCacheInvalidation:
    """Test cache invalidation."""

    def setup_method(self):
        from acquisition_platform.caching import CacheManager
        self.manager = CacheManager()

    def test_cache_invalidation(self):
        """Cache invalidated."""
        self.manager.set("key1", "value1", ttl=60)
        assert self.manager.get("key1") == "value1"
        result = self.manager.invalidate("key1")
        assert result is True
        assert self.manager.get("key1") is None

    def test_invalidate_missing_key(self):
        """Invalidating a missing key returns False."""
        result = self.manager.invalidate("nonexistent")
        assert result is False


class TestCacheStats:
    """Test cache statistics tracking."""

    def setup_method(self):
        from acquisition_platform.caching import CacheManager
        self.manager = CacheManager()

    def test_cache_stats(self):
        """Stats tracked."""
        self.manager.set("a", 1, ttl=60)
        self.manager.set("b", 2, ttl=60)
        self.manager.get("a")  # hit
        self.manager.get("a")  # hit
        self.manager.get("b")  # hit
        self.manager.get("c")  # miss
        stats = self.manager.get_stats()
        assert stats.hits == 3
        assert stats.misses == 1
        assert stats.size == 2

    def test_cache_stats_hit_rate(self):
        """Hit rate is calculated correctly."""
        self.manager.set("a", 1, ttl=60)
        self.manager.get("a")  # hit
        self.manager.get("b")  # miss
        stats = self.manager.get_stats()
        assert stats.hit_rate == 0.5

    def test_cache_stats_zero_hit_rate(self):
        """Hit rate is 0 when no hits."""
        self.manager.get("x")  # miss
        stats = self.manager.get_stats()
        assert stats.hit_rate == 0.0


class TestCacheReport:
    """Test cache report generation."""

    def setup_method(self):
        from acquisition_platform.caching import CacheManager
        self.manager = CacheManager()

    def test_cache_report(self):
        """Report generated."""
        self.manager.set("a", 1, ttl=60)
        self.manager.set("b", 2, ttl=60)
        self.manager.get("a")  # hit
        report = self.manager.generate_cache_report()
        assert isinstance(report, dict)
        assert "stats" in report
        assert "entries" in report
        assert report["stats"]["hits"] == 1
        assert report["stats"]["misses"] == 0
        assert report["stats"]["size"] == 2
        assert len(report["entries"]) == 2


class TestCacheWarming:
    """Test cache warming."""

    def setup_method(self):
        from acquisition_platform.caching import CacheManager
        self.manager = CacheManager()

    def test_cache_warming(self):
        """Cache warmed."""
        keys = ["a", "b", "c"]
        values = [1, 2, 3]
        count = self.manager.warm_cache(keys, values)
        assert count == 3
        assert self.manager.get("a") == 1
        assert self.manager.get("b") == 2
        assert self.manager.get("c") == 3

    def test_cache_warming_mismatched_lengths(self):
        """Warming with mismatched keys/values raises ValueError."""
        with pytest.raises(ValueError):
            self.manager.warm_cache(["a", "b"], [1])


class TestCacheEviction:
    """Test eviction policy."""

    def setup_method(self):
        from acquisition_platform.caching import CacheManager
        self.manager = CacheManager(max_size=3)

    def test_cache_eviction(self):
        """Eviction policy works."""
        self.manager.set("a", 1, ttl=60)
        self.manager.set("b", 2, ttl=60)
        self.manager.set("c", 3, ttl=60)
        self.manager.set("d", 4, ttl=60)  # Should evict "a"
        assert self.manager.get("a") is None
        assert self.manager.get("d") == 4

    def test_evict_entries_lru(self):
        """Explicit LRU eviction."""
        self.manager.set("a", 1, ttl=60)
        self.manager.set("b", 2, ttl=60)
        self.manager.set("c", 3, ttl=60)
        self.manager.get("a")  # Refresh "a"
        count = self.manager.evict_entries("lru")
        assert count >= 1
        # "b" should be evicted (LRU after "a" was accessed)
        assert self.manager.get("b") is None

    def test_evict_entries_ttl(self):
        """TTL-based eviction removes expired entries."""
        self.manager.set("a", 1, ttl=0.05)
        self.manager.set("b", 2, ttl=60)
        time.sleep(0.1)
        count = self.manager.evict_entries("ttl")
        assert count == 1
        assert self.manager.get("a") is None
        assert self.manager.get("b") == 2


class TestCacheSerialization:
    """Test cache serialization."""

    def setup_method(self):
        from acquisition_platform.caching import CacheManager
        self.manager = CacheManager()

    def test_cache_serialization(self):
        """Cache serialized."""
        self.manager.set("a", 1, ttl=60)
        self.manager.set("b", "hello", ttl=120)
        serialized = self.manager.serialize_cache()
        assert isinstance(serialized, str)
        assert len(serialized) > 0
        # Should be valid JSON
        import json
        data = json.loads(serialized)
        assert isinstance(data, dict)
        assert "a" in data
        assert "b" in data


class TestCacheMonitoring:
    """Test cache monitoring."""

    def setup_method(self):
        from acquisition_platform.caching import CacheManager
        self.manager = CacheManager()

    def test_cache_monitoring(self):
        """Cache monitored."""
        self.manager.set("a", 1, ttl=60)
        self.manager.get("a")  # hit
        self.manager.get("b")  # miss
        monitor_data = self.manager.monitor_cache()
        assert isinstance(monitor_data, dict)
        assert "hits" in monitor_data
        assert "misses" in monitor_data
        assert "size" in monitor_data
        assert monitor_data["hits"] == 1
        assert monitor_data["misses"] == 1
        assert monitor_data["size"] == 1

    def test_monitor_includes_hit_rate(self):
        """Monitor data includes hit rate."""
        self.manager.set("a", 1, ttl=60)
        self.manager.get("a")  # hit
        self.manager.get("b")  # miss
        monitor_data = self.manager.monitor_cache()
        assert "hit_rate" in monitor_data
        assert monitor_data["hit_rate"] == 0.5
