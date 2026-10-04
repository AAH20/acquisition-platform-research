"""Tests for dataclass serialization (to_dict/from_dict) and the reporting module.

Covers the roundtrip contract for every result type in the platform plus the
JSON/CSV/Markdown export surfaces of :class:`acquisition_platform.reporting.Report`.
"""

import json

import pytest

from acquisition_platform.matching import Buyer, Seller, Match
from acquisition_platform.valuation import ValuationResult
from acquisition_platform.fraud_detection import FraudSignal, FraudScore
from acquisition_platform.portfolio_optimizer import Asset, Portfolio
from acquisition_platform.dynamic_pricing import PriceRecommendation
from acquisition_platform.entity_resolution import EntityCluster
from acquisition_platform.search_ranking import Listing, RankedListing
from acquisition_platform.evolution import Benchmark, EvaluationResult, EvolutionResult
from acquisition_platform.reporting import Report, generate_report


# ---------------------------------------------------------------------------
# to_dict / from_dict roundtrip contract for every serializable type
# ---------------------------------------------------------------------------


class TestRoundtrip:
    """Every type must survive dict -> object -> dict without loss."""

    def test_buyer_roundtrip(self):
        obj = Buyer(id="b1", budget=100000.0, preferences={"category": "saas"})
        data = obj.to_dict()
        assert data == {
            "id": "b1",
            "budget": 100000.0,
            "preferences": {"category": "saas"},
        }
        assert Buyer.from_dict(data) == obj

    def test_seller_roundtrip(self):
        obj = Seller(id="s1", asking_price=80000.0, attributes={"category": "saas"})
        data = obj.to_dict()
        assert data == {
            "id": "s1",
            "asking_price": 80000.0,
            "attributes": {"category": "saas"},
        }
        assert Seller.from_dict(data) == obj

    def test_match_roundtrip(self):
        obj = Match(buyer_id="b1", seller_id="s1", score=0.5, confidence=0.75)
        data = obj.to_dict()
        assert data == {
            "buyer_id": "b1",
            "seller_id": "s1",
            "score": 0.5,
            "confidence": 0.75,
        }
        assert Match.from_dict(data) == obj

    def test_valuation_result_roundtrip(self):
        obj = ValuationResult(
            value=1_000_000.0,
            method="DCF",
            confidence=0.7,
            low_estimate=850_000.0,
            high_estimate=1_150_000.0,
        )
        assert ValuationResult.from_dict(obj.to_dict()) == obj

    def test_fraud_signal_roundtrip(self):
        obj = FraudSignal(name="identity_verified", value=0.9)
        assert obj.to_dict() == {"name": "identity_verified", "value": 0.9}
        assert FraudSignal.from_dict(obj.to_dict()) == obj

    def test_fraud_score_roundtrip(self):
        obj = FraudScore(
            score=0.42,
            risk_level="medium",
            confidence=1.0,
            explanations=["identity_verified: value=0.90"],
        )
        data = obj.to_dict()
        assert data["explanations"] == ["identity_verified: value=0.90"]
        assert FraudScore.from_dict(data) == obj

    def test_fraud_score_from_dict_defaults_explanations(self):
        # explanations is the only optional field; from_dict must tolerate absence.
        obj = FraudScore.from_dict(
            {"score": 0.1, "risk_level": "low", "confidence": 0.0}
        )
        assert obj.explanations == []

    def test_asset_roundtrip(self):
        obj = Asset(
            id="a1", cost=500000.0, expected_return=0.12, risk=0.3, sector="saas"
        )
        assert Asset.from_dict(obj.to_dict()) == obj

    def test_portfolio_roundtrip_nested_assets(self):
        assets = [
            Asset(id="a1", cost=500000.0, expected_return=0.12, risk=0.3, sector="saas"),
            Asset(id="a2", cost=250000.0, expected_return=0.08, risk=0.2, sector="ecom"),
        ]
        obj = Portfolio(assets=assets, expected_return=0.1, sharpe_ratio=0.25)
        data = obj.to_dict()
        assert isinstance(data["assets"][0], dict)
        assert Portfolio.from_dict(data) == obj

    def test_price_recommendation_roundtrip(self):
        obj = PriceRecommendation(
            recommended_price=1_050_000.0,
            confidence=0.8,
            floor_price=700_000.0,
            ceiling_price=1_500_000.0,
            equilibrium_price=1_000_000.0,
        )
        assert PriceRecommendation.from_dict(obj.to_dict()) == obj

    def test_entity_cluster_roundtrip(self):
        entities = [
            {"id": "e1", "name": "Acme Corp", "domain": "acme.com"},
            {"id": "e2", "name": "Acme Corporation", "domain": "acme.com"},
        ]
        obj = EntityCluster(entities=entities, canonical_name="Acme Corp")
        data = obj.to_dict()
        assert data["entities"] == entities
        assert EntityCluster.from_dict(data) == obj

    def test_listing_roundtrip(self):
        obj = Listing(id="l1", title="SaaS Co", relevance=0.9, category="saas")
        assert Listing.from_dict(obj.to_dict()) == obj

    def test_ranked_listing_roundtrip(self):
        obj = RankedListing(id="l1", title="SaaS Co", score=1.17, category="saas")
        assert RankedListing.from_dict(obj.to_dict()) == obj

    def test_benchmark_roundtrip(self):
        obj = Benchmark(name="accuracy", target=0.95)
        assert obj.to_dict() == {"name": "accuracy", "target": 0.95}
        assert Benchmark.from_dict(obj.to_dict()) == obj

    def test_evaluation_result_roundtrip(self):
        obj = EvaluationResult(passed=False, gap=0.05, suggestion="Improve accuracy by 0.05")
        assert EvaluationResult.from_dict(obj.to_dict()) == obj

    def test_evolution_result_roundtrip(self):
        obj = EvolutionResult(
            best_fitness=0.98,
            generation_count=20,
            population_size=50,
            diversity=0.01,
            offspring_count=960,
            converged=True,
            worst_fitness=0.5,
        )
        data = obj.to_dict()
        assert data["converged"] is True
        assert EvolutionResult.from_dict(data) == obj


# ---------------------------------------------------------------------------
# Report aggregation + export
# ---------------------------------------------------------------------------


def _sample_report() -> Report:
    report = Report(title="Deal Screening Report", metadata={"analyst": "wave2"})
    report.add_matches(
        [
            Match(buyer_id="b1", seller_id="s1", score=0.5, confidence=0.75),
            Match(buyer_id="b2", seller_id="s2", score=0.4, confidence=0.6),
        ]
    )
    report.add_valuation(
        ValuationResult(
            value=1_000_000.0,
            method="DCF",
            confidence=0.7,
            low_estimate=850_000.0,
            high_estimate=1_150_000.0,
        )
    )
    report.add_fraud_scores(
        [FraudScore(score=0.1, risk_level="low", confidence=1.0, explanations=[])]
    )
    report.add_portfolio(
        Portfolio(
            assets=[Asset(id="a1", cost=100.0, expected_return=0.1, risk=0.2, sector="saas")],
            expected_return=0.1,
            sharpe_ratio=0.5,
        )
    )
    report.add_price_recommendation(
        PriceRecommendation(
            recommended_price=1_050_000.0,
            confidence=0.8,
            floor_price=700_000.0,
            ceiling_price=1_500_000.0,
            equilibrium_price=1_000_000.0,
        )
    )
    report.add_entity_clusters(
        [EntityCluster(entities=[{"id": "e1", "name": "Acme"}], canonical_name="Acme")]
    )
    report.add_ranked_listings(
        [RankedListing(id="l1", title="SaaS Co", score=1.17, category="saas")]
    )
    report.add_evolution(
        EvolutionResult(
            best_fitness=0.9,
            generation_count=10,
            population_size=20,
            diversity=0.02,
            offspring_count=180,
            converged=False,
            worst_fitness=0.3,
        )
    )
    return report


class TestReportStructure:
    def test_report_records_sections(self):
        report = _sample_report()
        data = report.to_dict()
        assert data["title"] == "Deal Screening Report"
        assert data["metadata"] == {"analyst": "wave2"}
        for section in (
            "matches",
            "valuation",
            "fraud_scores",
            "portfolio",
            "price_recommendation",
            "entity_clusters",
            "ranked_listings",
            "evolution",
        ):
            assert section in data["sections"], section

    def test_add_section_accepts_plain_dicts(self):
        report = Report(title="T")
        report.add_section("custom", [{"a": 1}, {"a": 2}])
        assert report.to_dict()["sections"]["custom"] == [{"a": 1}, {"a": 2}]

    def test_generate_report_builds_from_results(self):
        report = generate_report(
            title="Auto",
            matches=[Match(buyer_id="b1", seller_id="s1", score=0.5, confidence=0.5)],
            valuations=[
                ValuationResult(
                    value=10.0,
                    method="SDE",
                    confidence=0.6,
                    low_estimate=8.5,
                    high_estimate=11.5,
                )
            ],
            fraud_scores=[FraudScore(score=0.2, risk_level="low", confidence=1.0)],
        )
        data = report.to_dict()
        assert data["title"] == "Auto"
        assert len(data["sections"]["matches"]) == 1
        assert data["sections"]["valuation"][0]["method"] == "SDE"
        assert data["sections"]["fraud_scores"][0]["risk_level"] == "low"


class TestJsonExport:
    def test_to_json_is_valid_json(self):
        report = _sample_report()
        parsed = json.loads(report.to_json())
        assert parsed["title"] == "Deal Screening Report"
        assert parsed["sections"]["matches"][0]["buyer_id"] == "b1"

    def test_to_json_indent(self):
        report = Report(title="T")
        assert "\n" in report.to_json(indent=2)

    def test_to_json_default_str_handles_non_serializable(self):
        report = Report(title="T")
        report.add_section("meta", [{"when": object()}])
        # Should not raise thanks to default=str.
        json.loads(report.to_json())


class TestCsvExport:
    def test_to_csv_has_section_and_columns(self):
        report = _sample_report()
        csv_text = report.to_csv()
        lines = csv_text.strip().splitlines()
        header = lines[0]
        assert "section" in header
        assert "buyer_id" in header
        assert "matches" in csv_text
        assert "valuation" in csv_text

    def test_to_csv_quotes_embedded_values(self):
        report = Report(title="T")
        report.add_section("s", [{"note": "a,b", "n": 1}])
        csv_text = report.to_csv()
        assert '"a,b"' in csv_text

    def test_to_csv_nested_values_serialized_as_json(self):
        report = _sample_report()
        csv_text = report.to_csv()
        # Portfolio assets are a nested list -> JSON-encoded inside the cell.
        assert "a1" in csv_text

    def test_empty_report_csv_has_header_only(self):
        report = Report(title="Empty")
        csv_text = report.to_csv()
        assert csv_text.strip() == "section"


class TestMarkdownExport:
    def test_to_markdown_contains_title_and_tables(self):
        report = _sample_report()
        md = report.to_markdown()
        assert "# Deal Screening Report" in md
        assert "## Matches" in md
        assert "## Valuation" in md
        assert "| buyer_id |" in md
        assert "| b1 |" in md

    def test_to_markdown_empty_report(self):
        md = Report(title="Empty").to_markdown()
        assert "# Empty" in md
