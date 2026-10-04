"""Tests for data export/import module (data_io)."""

import json
import os
import tempfile

import pytest

from acquisition_platform.data_io import (
    export_to_json,
    import_from_json,
    export_to_csv,
    import_from_csv,
    export_to_yaml,
    import_from_yaml,
    validate_schema,
)
from acquisition_platform.entity_resolution import EntityResolver, EntityCluster
from acquisition_platform.matching import BuyerSellerMatcher, Buyer, Seller, Match
from acquisition_platform.valuation import ValuationEngine, ValuationResult


class TestJSONExportImport:
    """Test JSON export/import roundtrip."""

    def test_export_import_roundtrip_dict(self, tmp_path):
        data = {"name": "Acme Corp", "value": 1000000, "tags": ["saas", "b2b"]}
        path = tmp_path / "data.json"
        export_to_json(data, str(path))
        result = import_from_json(str(path))
        assert result == data

    def test_export_import_roundtrip_list(self, tmp_path):
        data = [{"id": "a", "score": 0.9}, {"id": "b", "score": 0.8}]
        path = tmp_path / "list.json"
        export_to_json(data, str(path))
        result = import_from_json(str(path))
        assert result == data

    def test_export_creates_file(self, tmp_path):
        data = {"key": "value"}
        path = tmp_path / "output.json"
        export_to_json(data, str(path))
        assert path.exists()
        assert path.stat().st_size > 0

    def test_import_nonexistent_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            import_from_json(str(tmp_path / "nonexistent.json"))

    def test_export_import_nested_structure(self, tmp_path):
        data = {
            "company": {
                "name": "Acme",
                "financials": {"revenue": 1000000, "ebitda": 200000},
            },
            "scores": [0.1, 0.5, 0.9],
        }
        path = tmp_path / "nested.json"
        export_to_json(data, str(path))
        result = import_from_json(str(path))
        assert result == data


class TestCSVExportImport:
    """Test CSV export/import."""

    def test_export_import_roundtrip(self, tmp_path):
        data = [
            {"name": "Alice", "age": 30, "city": "NYC"},
            {"name": "Bob", "age": 25, "city": "LA"},
        ]
        path = tmp_path / "data.csv"
        export_to_csv(data, str(path))
        result = import_from_csv(str(path))
        assert len(result) == 2
        assert result[0]["name"] == "Alice"
        assert result[1]["name"] == "Bob"

    def test_export_creates_file(self, tmp_path):
        data = [{"col1": "val1", "col2": "val2"}]
        path = tmp_path / "output.csv"
        export_to_csv(data, str(path))
        assert path.exists()

    def test_import_nonexistent_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            import_from_csv(str(tmp_path / "nonexistent.csv"))

    def test_export_empty_list_creates_empty_file(self, tmp_path):
        path = tmp_path / "empty.csv"
        export_to_csv([], str(path))
        assert path.exists()

    def test_import_returns_list_of_dicts(self, tmp_path):
        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        path = tmp_path / "data.csv"
        export_to_csv(data, str(path))
        result = import_from_csv(str(path))
        assert isinstance(result, list)
        assert all(isinstance(row, dict) for row in result)


class TestYAMLExportImport:
    """Test YAML export/import."""

    def test_export_import_roundtrip_dict(self, tmp_path):
        data = {"name": "Acme Corp", "value": 1000000, "active": True}
        path = tmp_path / "data.yaml"
        export_to_yaml(data, str(path))
        result = import_from_yaml(str(path))
        assert result == data

    def test_export_import_roundtrip_list(self, tmp_path):
        data = [{"id": "x", "val": 1.5}, {"id": "y", "val": 2.5}]
        path = tmp_path / "list.yaml"
        export_to_yaml(data, str(path))
        result = import_from_yaml(str(path))
        assert result == data

    def test_export_creates_file(self, tmp_path):
        data = {"key": "value"}
        path = tmp_path / "output.yaml"
        export_to_yaml(data, str(path))
        assert path.exists()

    def test_import_nonexistent_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            import_from_yaml(str(tmp_path / "nonexistent.yaml"))

    def test_export_import_nested(self, tmp_path):
        data = {
            "root": {
                "child": [1, 2, 3],
                "meta": {"version": "1.0"},
            }
        }
        path = tmp_path / "nested.yaml"
        export_to_yaml(data, str(path))
        result = import_from_yaml(str(path))
        assert result == data


class TestSchemaValidation:
    """Test schema validation."""

    def test_valid_data_passes(self):
        data = {"name": "Acme", "age": 30, "active": True}
        schema = {"name": str, "age": int, "active": bool}
        assert validate_schema(data, schema) is True

    def test_missing_field_fails(self):
        data = {"name": "Acme"}
        schema = {"name": str, "age": int}
        assert validate_schema(data, schema) is False

    def test_wrong_type_fails(self):
        data = {"name": "Acme", "age": "thirty"}
        schema = {"name": str, "age": int}
        assert validate_schema(data, schema) is False

    def test_empty_schema_passes(self):
        data = {"any": "thing"}
        assert validate_schema(data, {}) is True

    def test_extra_fields_allowed(self):
        data = {"name": "Acme", "extra": "field"}
        schema = {"name": str}
        assert validate_schema(data, schema) is True

    def test_nested_dict_validation(self):
        data = {"user": {"name": "Alice", "id": 1}}
        schema = {"user": dict}
        assert validate_schema(data, schema) is True


class TestInvalidFileHandling:
    """Test handling of invalid/corrupted files."""

    def test_import_invalid_json_raises(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("not valid json {{{")
        with pytest.raises(json.JSONDecodeError):
            import_from_json(str(path))

    def test_import_invalid_yaml_raises(self, tmp_path):
        path = tmp_path / "bad.yaml"
        path.write_text(":\n  - invalid: [yaml")
        with pytest.raises(Exception):
            import_from_yaml(str(path))

    def test_export_to_invalid_path_raises(self, tmp_path):
        data = {"key": "value"}
        with pytest.raises(OSError):
            export_to_json(data, str(tmp_path / "nonexistent_dir" / "file.json"))


class TestEntityResolverExportImport:
    """Test EntityResolver export_clusters and import_entities."""

    def test_export_clusters(self, tmp_path):
        resolver = EntityResolver()
        entities = [
            {"id": "e1", "name": "Acme Corp", "domain": "acme.com"},
            {"id": "e2", "name": "Acme Corp", "domain": "acme.com"},
        ]
        clusters = resolver.resolve(entities)
        path = tmp_path / "clusters.json"
        resolver.export_clusters(clusters, str(path))
        assert path.exists()

    def test_import_entities(self, tmp_path):
        entities = [
            {"id": "e1", "name": "Acme Corp", "domain": "acme.com"},
            {"id": "e2", "name": "Globex Inc", "domain": "globex.com"},
        ]
        path = tmp_path / "entities.json"
        export_to_json(entities, str(path))
        resolver = EntityResolver()
        result = resolver.import_entities(str(path))
        assert len(result) == 2
        assert result[0]["name"] == "Acme Corp"

    def test_export_import_roundtrip(self, tmp_path):
        resolver = EntityResolver()
        entities = [
            {"id": "e1", "name": "Acme Corp", "domain": "acme.com"},
            {"id": "e2", "name": "Acme Corp", "domain": "acme.com"},
            {"id": "e3", "name": "Globex Inc", "domain": "globex.com"},
        ]
        clusters = resolver.resolve(entities)
        path = tmp_path / "clusters.json"
        resolver.export_clusters(clusters, str(path))
        result = import_from_json(str(path))
        assert isinstance(result, list)
        assert len(result) == len(clusters)


class TestBuyerSellerMatcherExportImport:
    """Test BuyerSellerMatcher export_matches and import_buyers_sellers."""

    def test_export_matches(self, tmp_path):
        matcher = BuyerSellerMatcher()
        buyers = [Buyer(id="b1", budget=100000, preferences={"category": "saas"})]
        sellers = [Seller(id="s1", asking_price=80000, attributes={"category": "saas"})]
        matches = matcher.match(buyers, sellers)
        path = tmp_path / "matches.json"
        matcher.export_matches(matches, str(path))
        assert path.exists()

    def test_import_buyers_sellers(self, tmp_path):
        data = {
            "buyers": [
                {"id": "b1", "budget": 100000, "preferences": {"category": "saas"}}
            ],
            "sellers": [
                {"id": "s1", "asking_price": 80000, "attributes": {"category": "saas"}}
            ],
        }
        path = tmp_path / "bs_data.json"
        export_to_json(data, str(path))
        matcher = BuyerSellerMatcher()
        buyers, sellers = matcher.import_buyers_sellers(str(path))
        assert len(buyers) == 1
        assert len(sellers) == 1
        assert buyers[0].id == "b1"
        assert sellers[0].id == "s1"

    def test_export_import_roundtrip(self, tmp_path):
        matcher = BuyerSellerMatcher()
        buyers = [Buyer(id="b1", budget=100000, preferences={"category": "saas"})]
        sellers = [Seller(id="s1", asking_price=80000, attributes={"category": "saas"})]
        matches = matcher.match(buyers, sellers)
        path = tmp_path / "matches.json"
        matcher.export_matches(matches, str(path))
        result = import_from_json(str(path))
        assert isinstance(result, list)
        assert len(result) == len(matches)


class TestValuationEngineExportImport:
    """Test ValuationEngine export_valuations and import_financials."""

    def test_export_valuations(self, tmp_path):
        engine = ValuationEngine()
        result = engine.dcf_valuation(
            free_cash_flow=100000,
            growth_rate=0.05,
            discount_rate=0.10,
            terminal_growth=0.02,
            years=5,
        )
        path = tmp_path / "valuations.json"
        engine.export_valuations([result], str(path))
        assert path.exists()

    def test_import_financials(self, tmp_path):
        data = {
            "free_cash_flow": 100000,
            "growth_rate": 0.05,
            "discount_rate": 0.10,
            "terminal_growth": 0.02,
            "years": 5,
        }
        path = tmp_path / "financials.json"
        export_to_json(data, str(path))
        engine = ValuationEngine()
        result = engine.import_financials(str(path))
        assert result["free_cash_flow"] == 100000
        assert result["growth_rate"] == 0.05

    def test_export_import_roundtrip(self, tmp_path):
        engine = ValuationEngine()
        result = engine.dcf_valuation(
            free_cash_flow=100000,
            growth_rate=0.05,
            discount_rate=0.10,
            terminal_growth=0.02,
            years=5,
        )
        path = tmp_path / "valuations.json"
        engine.export_valuations([result], str(path))
        imported = import_from_json(str(path))
        assert isinstance(imported, list)
        assert len(imported) == 1
        assert imported[0]["method"] == "DCF"
