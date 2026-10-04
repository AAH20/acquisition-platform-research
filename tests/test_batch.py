"""Tests for batch processing module."""

import time
import pytest

from acquisition_platform.batch import (
    BatchConfig,
    BatchProcessor,
    BatchResult,
    process_in_batches,
    process_in_parallel,
)
from acquisition_platform.entity_resolution import EntityResolver
from acquisition_platform.matching import Buyer, Seller, BuyerSellerMatcher
from acquisition_platform.valuation import ValuationEngine


class TestBatchConfig:
    """Tests for BatchConfig dataclass."""

    def test_default_values(self):
        config = BatchConfig()
        assert config.chunk_size == 100
        assert config.max_workers == 4
        assert config.parallel is False

    def test_custom_values(self):
        config = BatchConfig(chunk_size=10, max_workers=2, parallel=True)
        assert config.chunk_size == 10
        assert config.max_workers == 2
        assert config.parallel is True

    def test_invalid_chunk_size_raises(self):
        from acquisition_platform.exceptions import ValidationError
        with pytest.raises(ValidationError):
            BatchConfig(chunk_size=0)
        with pytest.raises(ValidationError):
            BatchConfig(chunk_size=-1)

    def test_invalid_max_workers_raises(self):
        from acquisition_platform.exceptions import ValidationError
        with pytest.raises(ValidationError):
            BatchConfig(max_workers=0)
        with pytest.raises(ValidationError):
            BatchConfig(max_workers=-1)


class TestBatchResult:
    """Tests for BatchResult dataclass."""

    def test_creation(self):
        result = BatchResult(results=[1, 2], errors=[], processing_time=0.5)
        assert result.results == [1, 2]
        assert result.errors == []
        assert result.processing_time == 0.5

    def test_with_errors(self):
        err = ValueError("bad item")
        result = BatchResult(results=[1], errors=[(2, err)], processing_time=0.1)
        assert result.results == [1]
        assert len(result.errors) == 1
        assert result.errors[0][0] == 2
        assert isinstance(result.errors[0][1], ValueError)


class TestProcessInBatches:
    """Tests for process_in_batches function."""

    def test_empty_list_returns_empty(self):
        result = process_in_batches([], lambda x: x * 2, BatchConfig())
        assert result == []

    def test_single_item(self):
        result = process_in_batches([5], lambda x: x * 2, BatchConfig())
        assert result == [10]

    def test_even_split(self):
        items = list(range(10))
        result = process_in_batches(items, lambda x: x * 2, BatchConfig(chunk_size=5))
        assert result == [0, 2, 4, 6, 8, 10, 12, 14, 16, 18]

    def test_uneven_split(self):
        items = list(range(7))
        result = process_in_batches(items, lambda x: x + 1, BatchConfig(chunk_size=3))
        assert result == [1, 2, 3, 4, 5, 6, 7]

    def test_chunk_size_larger_than_list(self):
        items = [1, 2, 3]
        result = process_in_batches(items, lambda x: x * 10, BatchConfig(chunk_size=100))
        assert result == [10, 20, 30]

    def test_preserves_order(self):
        items = list(range(20))
        result = process_in_batches(items, lambda x: x ** 2, BatchConfig(chunk_size=4))
        assert result == [x ** 2 for x in range(20)]

    def test_with_strings(self):
        items = ["a", "b", "c", "d", "e"]
        result = process_in_batches(items, str.upper, BatchConfig(chunk_size=2))
        assert result == ["A", "B", "C", "D", "E"]


class TestProcessInParallel:
    """Tests for process_in_parallel function."""

    def test_empty_list_returns_empty(self):
        result = process_in_parallel([], lambda x: x * 2, max_workers=2)
        assert result == []

    def test_single_item(self):
        result = process_in_parallel([5], lambda x: x * 2, max_workers=2)
        assert result == [10]

    def test_multiple_items(self):
        items = list(range(10))
        result = process_in_parallel(items, lambda x: x * 3, max_workers=4)
        assert result == [x * 3 for x in range(10)]

    def test_preserves_order(self):
        items = list(range(15))
        result = process_in_parallel(items, lambda x: x + 100, max_workers=3)
        assert result == [x + 100 for x in range(15)]

    def test_with_sleep(self):
        items = [1, 2, 3, 4]
        result = process_in_parallel(items, lambda x: x ** 2, max_workers=4)
        assert result == [1, 4, 9, 16]


class TestBatchProcessor:
    """Tests for BatchProcessor class."""

    def test_process_sequential(self):
        processor = BatchProcessor(BatchConfig(chunk_size=3, parallel=False))
        items = list(range(9))
        result = processor.process(items, lambda x: x * 2)
        assert isinstance(result, BatchResult)
        assert result.results == [x * 2 for x in range(9)]
        assert result.errors == []
        assert result.processing_time >= 0

    def test_process_parallel(self):
        processor = BatchProcessor(BatchConfig(chunk_size=3, parallel=True, max_workers=2))
        items = list(range(9))
        result = processor.process(items, lambda x: x * 2)
        assert isinstance(result, BatchResult)
        assert result.results == [x * 2 for x in range(9)]
        assert result.errors == []

    def test_process_empty(self):
        processor = BatchProcessor(BatchConfig())
        result = processor.process([], lambda x: x)
        assert result.results == []
        assert result.errors == []

    def test_process_with_errors(self):
        def fail_on_odd(x):
            if x % 2 != 0:
                raise ValueError(f"odd: {x}")
            return x * 2

        processor = BatchProcessor(BatchConfig(chunk_size=2))
        items = [1, 2, 3, 4, 5, 6]
        result = processor.process(items, fail_on_odd)
        assert 4 in result.results
        assert 8 in result.results
        assert 12 in result.results
        assert len(result.errors) == 3
        error_indices = [idx for idx, _ in result.errors]
        assert 0 in error_indices
        assert 2 in error_indices
        assert 4 in error_indices

    def test_process_single_item(self):
        processor = BatchProcessor(BatchConfig(chunk_size=10))
        result = processor.process([42], lambda x: x + 1)
        assert result.results == [43]
        assert result.errors == []

    def test_processing_time_recorded(self):
        processor = BatchProcessor(BatchConfig())
        result = processor.process([1], lambda x: x)
        assert result.processing_time >= 0


class TestEntityResolverBatch:
    """Tests for EntityResolver.resolve_batch."""

    def test_resolve_batch_empty_raises(self):
        resolver = EntityResolver()
        with pytest.raises(Exception):
            resolver.resolve_batch([], chunk_size=5)

    def test_resolve_batch_single_chunk(self):
        resolver = EntityResolver()
        entities = [
            {"id": "e1", "name": "Acme Corp", "domain": "acme.com"},
            {"id": "e2", "name": "Acme Corp", "domain": "acme.com"},
            {"id": "e3", "name": "Globex Inc", "domain": "globex.com"},
        ]
        result = resolver.resolve_batch(entities, chunk_size=10)
        assert len(result) == 2

    def test_resolve_batch_multiple_chunks(self):
        resolver = EntityResolver()
        entities = [
            {"id": f"e{i}", "name": f"Company {i}", "domain": f"c{i}.com"}
            for i in range(10)
        ]
        result = resolver.resolve_batch(entities, chunk_size=3)
        # With chunk_size=3, entities are split into 4 chunks (3+3+3+1).
        # Within each chunk, similar names are clustered together.
        assert len(result) >= 4

    def test_resolve_batch_preserves_all_entities(self):
        resolver = EntityResolver()
        entities = [
            {"id": f"e{i}", "name": f"Company {i}", "domain": f"c{i}.com"}
            for i in range(7)
        ]
        result = resolver.resolve_batch(entities, chunk_size=2)
        all_ids = set()
        for cluster in result:
            for entity in cluster.entities:
                all_ids.add(entity["id"])
        assert all_ids == {f"e{i}" for i in range(7)}

    def test_resolve_batch_chunk_size_one(self):
        resolver = EntityResolver()
        entities = [
            {"id": "e1", "name": "Acme Corp", "domain": "acme.com"},
            {"id": "e2", "name": "Acme Corp", "domain": "acme.com"},
        ]
        result = resolver.resolve_batch(entities, chunk_size=1)
        assert len(result) == 2


class TestBuyerSellerMatcherBatch:
    """Tests for BuyerSellerMatcher.match_batch."""

    def test_match_batch_empty_buyers_raises(self):
        matcher = BuyerSellerMatcher()
        with pytest.raises(Exception):
            matcher.match_batch([], [Seller(id="s1", asking_price=100, attributes={})], chunk_size=5)

    def test_match_batch_empty_sellers_raises(self):
        matcher = BuyerSellerMatcher()
        with pytest.raises(Exception):
            matcher.match_batch([Buyer(id="b1", budget=1000, preferences={})], [], chunk_size=5)

    def test_match_batch_basic(self):
        matcher = BuyerSellerMatcher()
        buyers = [
            Buyer(id="b1", budget=1000, preferences={"category": "tech"}),
            Buyer(id="b2", budget=2000, preferences={"category": "tech"}),
        ]
        sellers = [
            Seller(id="s1", asking_price=500, attributes={"category": "tech"}),
            Seller(id="s2", asking_price=800, attributes={"category": "tech"}),
        ]
        result = matcher.match_batch(buyers, sellers, chunk_size=1)
        # With chunk_size=1, each buyer is matched with each seller separately
        assert len(result) == 4

    def test_match_batch_single_chunk(self):
        matcher = BuyerSellerMatcher()
        buyers = [Buyer(id="b1", budget=1000, preferences={"category": "retail"})]
        sellers = [Seller(id="s1", asking_price=500, attributes={"category": "retail"})]
        result = matcher.match_batch(buyers, sellers, chunk_size=10)
        assert len(result) == 1

    def test_match_batch_multiple_chunks(self):
        matcher = BuyerSellerMatcher()
        buyers = [
            Buyer(id=f"b{i}", budget=1000 + i * 100, preferences={"category": "tech"})
            for i in range(5)
        ]
        sellers = [
            Seller(id=f"s{i}", asking_price=200 + i * 50, attributes={"category": "tech"})
            for i in range(5)
        ]
        result = matcher.match_batch(buyers, sellers, chunk_size=2)
        # With chunk_size=2, buyers and sellers are split into 3 chunks each (2+2+1)
        # Each chunk pair produces matches, resulting in more than 5 total
        assert len(result) >= 5


class TestValuationEngineBatch:
    """Tests for ValuationEngine.value_batch."""

    def test_value_batch_empty_raises(self):
        engine = ValuationEngine()
        with pytest.raises(Exception):
            engine.value_batch([], chunk_size=5)

    def test_value_batch_single_item(self):
        engine = ValuationEngine()
        financials = [{"free_cash_flow": 100, "growth_rate": 0.05, "discount_rate": 0.1,
                       "terminal_growth": 0.02, "years": 5}]
        result = engine.value_batch(financials, chunk_size=10)
        assert len(result) == 1
        assert result[0].method == "DCF"

    def test_value_batch_multiple_items(self):
        engine = ValuationEngine()
        financials = [
            {"free_cash_flow": 100 + i * 50, "growth_rate": 0.05, "discount_rate": 0.1,
             "terminal_growth": 0.02, "years": 5}
            for i in range(6)
        ]
        result = engine.value_batch(financials, chunk_size=2)
        assert len(result) == 6
        for r in result:
            assert r.method == "DCF"
            assert r.value > 0

    def test_value_batch_with_comps(self):
        engine = ValuationEngine()
        financials = [
            {"metric": 1000, "multiple": 3.0},
            {"metric": 2000, "multiple": 2.5},
        ]
        result = engine.value_batch(financials, chunk_size=1)
        assert len(result) == 2
        assert all(r.method == "Comps" for r in result)

    def test_value_batch_mixed_methods(self):
        engine = ValuationEngine()
        financials = [
            {"free_cash_flow": 100, "growth_rate": 0.05, "discount_rate": 0.1,
             "terminal_growth": 0.02, "years": 5},
            {"metric": 500, "multiple": 4.0},
        ]
        result = engine.value_batch(financials, chunk_size=1)
        assert len(result) == 2
        methods = {r.method for r in result}
        assert "DCF" in methods
        assert "Comps" in methods
