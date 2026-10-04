"""Tests for type safety improvements (Wave 2).

Verifies:
- TypedDicts exist with correct fields
- py.typed marker for PEP 561 compliance
- mypy strict mode passes
- Existing functionality preserved after type annotations
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from acquisition_platform.entity_resolution import (
    EntityCluster,
    EntityResolver,
    ResolvedEntity,
)
from acquisition_platform.fraud_detection import FraudDetector
from acquisition_platform.matching import Buyer, BuyerSellerMatcher, Seller
from acquisition_platform.search_ranking import SearchRanker


class TestTypedDictsExist:
    """Verify TypedDicts are defined and importable."""

    def test_entity_dict_importable(self):
        from acquisition_platform.entity_resolution import EntityDict

        assert EntityDict is not None

    def test_entity_dict_has_name_field(self):
        from acquisition_platform.entity_resolution import EntityDict

        annotations = EntityDict.__annotations__
        assert "name" in annotations

    def test_entity_dict_has_domain_field(self):
        from acquisition_platform.entity_resolution import EntityDict

        annotations = EntityDict.__annotations__
        assert "domain" in annotations

    def test_entity_dict_has_id_field(self):
        from acquisition_platform.entity_resolution import EntityDict

        annotations = EntityDict.__annotations__
        assert "id" in annotations

    def test_graph_dict_importable(self):
        from acquisition_platform.fraud_detection import GraphDict

        assert GraphDict is not None

    def test_graph_dict_has_nodes_field(self):
        from acquisition_platform.fraud_detection import GraphDict

        annotations = GraphDict.__annotations__
        assert "nodes" in annotations

    def test_graph_dict_has_edges_field(self):
        from acquisition_platform.fraud_detection import GraphDict

        annotations = GraphDict.__annotations__
        assert "edges" in annotations


class TestPyTypedMarker:
    """Verify PEP 561 py.typed marker exists."""

    def test_py_typed_marker_exists(self):
        package_dir = Path(__file__).parent.parent / "src" / "acquisition_platform"
        py_typed = package_dir / "py.typed"
        assert py_typed.exists(), f"py.typed marker not found at {py_typed}"

    def test_py_typed_marker_is_empty_or_whitespace(self):
        package_dir = Path(__file__).parent.parent / "src" / "acquisition_platform"
        py_typed = package_dir / "py.typed"
        if py_typed.exists():
            content = py_typed.read_text()
            assert content.strip() == ""


class TestMypyCompliance:
    """Verify mypy strict mode passes."""

    def test_mypy_passes_on_source(self):
        project_root = Path(__file__).parent.parent
        result = subprocess.run(
            [sys.executable, "-m", "mypy", "src/acquisition_platform/"],
            capture_output=True,
            text=True,
            cwd=project_root,
        )
        assert result.returncode == 0, (
            f"mypy failed with exit code {result.returncode}:\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )


class TestFunctionalityPreserved:
    """Verify existing functionality still works after type changes."""

    def test_buyer_seller_matcher_still_works(self):
        matcher = BuyerSellerMatcher()
        buyers = [Buyer(id="b1", budget=100.0, preferences={"category": "saas"})]
        sellers = [Seller(id="s1", asking_price=50.0, attributes={"category": "saas"})]
        matches = matcher.match(buyers, sellers)
        assert len(matches) == 1
        assert matches[0].buyer_id == "b1"
        assert matches[0].seller_id == "s1"

    def test_search_ranker_still_works(self):
        ranker = SearchRanker()
        from acquisition_platform.search_ranking import Listing

        listings = [
            Listing(id="l1", title="Test", relevance=0.9, category="saas"),
        ]
        results = ranker.rank("test", listings, {"category": "saas"})
        assert len(results) == 1
        assert results[0].id == "l1"

    def test_entity_resolver_still_works(self):
        resolver = EntityResolver()
        entities = [
            {"id": "e1", "name": "Acme Corp", "domain": "acme.com"},
            {"id": "e2", "name": "Acme Corp", "domain": "acme.com"},
        ]
        result = resolver.resolve(entities)
        assert len(result) == 1
        assert len(result[0].entities) == 2

    def test_fraud_detector_still_works(self):
        detector = FraudDetector()
        graph = {
            "nodes": ["a", "b", "c"],
            "edges": [("a", "b"), ("b", "c"), ("c", "a")],
        }
        result = detector.analyze_graph(graph)
        assert result.has_ring is True
        assert result.risk_score > 0.5

    def test_entity_cluster_dataclass_still_works(self):
        entities = [{"id": "e1", "name": "Acme", "domain": "acme.com"}]
        cluster = EntityCluster(entities=entities, canonical_name="Acme")
        assert cluster.canonical_name == "Acme"
        assert len(cluster.entities) == 1

    def test_resolved_entity_dataclass_still_works(self):
        entities = [{"id": "e1", "name": "Acme", "domain": "acme.com"}]
        resolved = ResolvedEntity(entities=entities, canonical_name="Acme")
        assert resolved.canonical_name == "Acme"
        assert len(resolved.entities) == 1
