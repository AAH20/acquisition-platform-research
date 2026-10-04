"""Tests for entity resolution module."""
import pytest

from acquisition_platform.exceptions import EmptyInputError
from acquisition_platform.entity_resolution import EntityResolver, ResolvedEntity, EntityCluster


class TestEntityResolver:
    """TDD tests for the entity resolution engine (O(n²) pairwise)."""

    def test_empty_input_raises(self):
        resolver = EntityResolver()
        with pytest.raises(EmptyInputError):
            resolver.resolve([])

    def test_single_entity_returns_single_cluster(self):
        resolver = EntityResolver()
        entities = [{"id": "e1", "name": "Acme Corp", "domain": "acme.com"}]
        result = resolver.resolve(entities)
        assert len(result) == 1
        assert len(result[0].entities) == 1

    def test_exact_match_clusters_together(self):
        resolver = EntityResolver()
        entities = [
            {"id": "e1", "name": "Acme Corp", "domain": "acme.com"},
            {"id": "e2", "name": "Acme Corp", "domain": "acme.com"},
        ]
        result = resolver.resolve(entities)
        assert len(result) == 1
        assert len(result[0].entities) == 2

    def test_different_entities_separate_clusters(self):
        resolver = EntityResolver()
        entities = [
            {"id": "e1", "name": "Acme Corp", "domain": "acme.com"},
            {"id": "e2", "name": "Globex Inc", "domain": "globex.com"},
        ]
        result = resolver.resolve(entities)
        assert len(result) == 2

    def test_fuzzy_match_similar_names(self):
        resolver = EntityResolver(threshold=0.8)
        entities = [
            {"id": "e1", "name": "Acme Corporation", "domain": "acme.com"},
            {"id": "e2", "name": "Acme Corp", "domain": "acme.com"},
        ]
        result = resolver.resolve(entities)
        assert len(result) == 1

    def test_domain_match_boosts_similarity(self):
        resolver = EntityResolver()
        entities = [
            {"id": "e1", "name": "Acme", "domain": "acme.com"},
            {"id": "e2", "name": "Acme", "domain": "acme.com"},
        ]
        result = resolver.resolve(entities)
        assert len(result) == 1

    def test_cluster_has_canonical_name(self):
        resolver = EntityResolver()
        entities = [
            {"id": "e1", "name": "Acme Corp", "domain": "acme.com"},
            {"id": "e2", "name": "Acme Corporation", "domain": "acme.com"},
        ]
        result = resolver.resolve(entities)
        assert result[0].canonical_name is not None

    def test_blocking_reduces_comparisons(self):
        resolver = EntityResolver()
        entities = [
            {"id": f"e{i}", "name": f"Company {i}", "domain": f"company{i}.com"}
            for i in range(100)
        ]
        result = resolver.resolve(entities)
        # With blocking, should not do O(n²) = 10000 comparisons
        assert resolver.comparison_count < 10000
