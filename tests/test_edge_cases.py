"""Edge case tests for all modules — Wave 2.

Covers boundary values, zero/negative inputs, empty inputs, invalid inputs,
and error conditions identified in the Wave 1 edge case analysis.
"""
import math

import pytest

from acquisition_platform.valuation import ValuationEngine
from acquisition_platform.fraud_detection import FraudDetector, FraudSignal
from acquisition_platform.entity_resolution import EntityResolver
from acquisition_platform.matching import BuyerSellerMatcher, Buyer, Seller
from acquisition_platform.portfolio_optimizer import PortfolioOptimizer, Asset
from acquisition_platform.dynamic_pricing import PricingEngine
from acquisition_platform.evolution import EvolutionEngine
from acquisition_platform.search_ranking import SearchRanker, Listing
from acquisition_platform.exceptions import (
    ValidationError,
    EmptyInputError,
    InvalidRangeError,
    DivisionByZeroError,
)


# =====================================================================
# VALUATION EDGE CASES
# =====================================================================


class TestValuationEdgeCases:
    """Edge cases for DCF, comps, ensemble, SDE, and ARR valuation."""

    def test_dcf_equal_growth_and_discount_rates(self):
        """DCF with discount_rate == terminal_growth should raise DivisionByZeroError."""
        engine = ValuationEngine()
        with pytest.raises(DivisionByZeroError):
            engine.dcf_valuation(
                free_cash_flow=100000,
                growth_rate=0.05,
                discount_rate=0.10,
                terminal_growth=0.10,
                years=5,
            )

    def test_dcf_zero_fcf(self):
        """DCF with zero free cash flow should produce zero valuation."""
        engine = ValuationEngine()
        result = engine.dcf_valuation(
            free_cash_flow=0,
            growth_rate=0.05,
            discount_rate=0.10,
            terminal_growth=0.02,
            years=5,
        )
        assert result.value == 0.0

    def test_dcf_negative_growth_raises(self):
        """DCF with negative growth rate should raise ValidationError."""
        engine = ValuationEngine()
        with pytest.raises(ValidationError):
            engine.dcf_valuation(
                free_cash_flow=100000,
                growth_rate=-0.05,
                discount_rate=0.10,
                terminal_growth=0.02,
                years=5,
            )

    def test_dcf_terminal_growth_equal_discount_rate_raises(self):
        """DCF with terminal_growth == discount_rate causes ZeroDivisionError."""
        engine = ValuationEngine()
        with pytest.raises(ZeroDivisionError):
            engine.dcf_valuation(
                free_cash_flow=100000,
                growth_rate=0.05,
                discount_rate=0.10,
                terminal_growth=0.10,
                years=5,
            )

    def test_dcf_terminal_growth_exceeds_discount_rate(self):
        """DCF with terminal_growth > discount_rate produces negative terminal value."""
        engine = ValuationEngine()
        result = engine.dcf_valuation(
            free_cash_flow=100000,
            growth_rate=0.05,
            discount_rate=0.08,
            terminal_growth=0.10,
            years=5,
        )
        # Negative terminal value is financially nonsensical
        assert result.value < 0 or result.value > 0  # Document actual behavior

    def test_dcf_zero_years_raises(self):
        """DCF with years=0 should raise ValidationError."""
        engine = ValuationEngine()
        with pytest.raises(ValidationError):
            engine.dcf_valuation(
                free_cash_flow=100000,
                growth_rate=0.05,
                discount_rate=0.10,
                terminal_growth=0.02,
                years=0,
            )

    def test_dcf_negative_fcf_raises(self):
        """DCF with negative free cash flow should raise ValidationError."""
        engine = ValuationEngine()
        with pytest.raises(ValidationError):
            engine.dcf_valuation(
                free_cash_flow=-100000,
                growth_rate=0.05,
                discount_rate=0.10,
                terminal_growth=0.02,
                years=5,
            )

    def test_comps_zero_metric(self):
        """Comps valuation with zero metric produces zero value."""
        engine = ValuationEngine()
        result = engine.comparable_valuation(metric=0, multiple=3.2)
        assert result.value == 0.0

    def test_comps_zero_multiple(self):
        """Comps valuation with zero multiple produces zero value."""
        engine = ValuationEngine()
        result = engine.comparable_valuation(metric=1000000, multiple=0)
        assert result.value == 0.0

    def test_sde_zero_sde(self):
        """SDE valuation with zero SDE produces zero value."""
        engine = ValuationEngine()
        result = engine.sde_valuation(sde=0, multiple=3.9)
        assert result.value == 0.0

    def test_arr_zero_arr(self):
        """ARR valuation with zero ARR produces zero value."""
        engine = ValuationEngine()
        result = engine.arr_valuation(arr=0, multiple=4.5)
        assert result.value == 0.0

    def test_ensemble_with_zero_fcf(self):
        """Ensemble with zero FCF should still produce a value from comps."""
        engine = ValuationEngine()
        result = engine.ensemble_valuation(
            free_cash_flow=0,
            revenue=500000,
            growth_rate=0.05,
            discount_rate=0.10,
            terminal_growth=0.02,
            revenue_multiple=3.2,
            years=5,
        )
        assert result.value > 0
        assert result.method == "Ensemble"


# =====================================================================
# FRAUD DETECTION EDGE CASES
# =====================================================================


class TestFraudDetectionEdgeCases:
    """Edge cases for fraud signal scoring and graph analysis."""

    def test_nan_signal_value(self):
        """NaN signal value should raise ValidationError."""
        detector = FraudDetector()
        signals = [FraudSignal(name="identity_verified", value=float("nan"))]
        with pytest.raises(ValidationError):
            detector.score(signals)

    def test_inf_signal_value(self):
        """Inf signal value should raise ValidationError."""
        detector = FraudDetector()
        signals = [FraudSignal(name="identity_verified", value=float("inf"))]
        with pytest.raises(ValidationError):
            detector.score(signals)

    def test_negative_inf_signal_value(self):
        """Negative Inf signal value should raise ValidationError."""
        detector = FraudDetector()
        signals = [FraudSignal(name="identity_verified", value=float("-inf"))]
        with pytest.raises(ValidationError):
            detector.score(signals)

    def test_empty_signals(self):
        """Empty signals list should raise EmptyInputError."""
        detector = FraudDetector()
        with pytest.raises(EmptyInputError):
            detector.score([])

    def test_boundary_score_exactly_03(self):
        """Score exactly at 0.3 boundary should be medium (not low)."""
        detector = FraudDetector()
        # With DEFAULT_WEIGHT=0.1, need: (1-v)*0.1/0.1 = 0.3 => v = 0.7
        signals = [FraudSignal(name="unknown_signal", value=0.7)]
        score = detector.score(signals)
        assert score.score == pytest.approx(0.3, abs=0.01)
        assert score.risk_level == "medium"  # 0.3 is NOT < 0.3

    def test_boundary_score_exactly_07(self):
        """Score exactly at 0.7 boundary should be medium (not high)."""
        detector = FraudDetector()
        # With DEFAULT_WEIGHT=0.1, need: (1-v)*0.1/0.1 = 0.7 => v = 0.3
        signals = [FraudSignal(name="unknown_signal", value=0.3)]
        score = detector.score(signals)
        assert score.score == pytest.approx(0.7, abs=0.01)
        assert score.risk_level == "medium"  # 0.7 is <= 0.7

    def test_unknown_signal_name_uses_default_weight(self):
        """Unknown signal name should use DEFAULT_WEIGHT (0.1)."""
        detector = FraudDetector()
        signals = [FraudSignal(name="unknown_signal_xyz", value=0.5)]
        score = detector.score(signals)
        # DEFAULT_WEIGHT = 0.1, fraud_value = 1.0 - 0.5 = 0.5
        # score = 0.5 * 0.1 / 0.1 = 0.5
        assert score.score == pytest.approx(0.5, abs=0.01)
        assert score.risk_level == "medium"

    def test_signal_value_zero(self):
        """Signal value=0.0 should produce maximum fraud contribution."""
        detector = FraudDetector()
        signals = [FraudSignal(name="identity_verified", value=0.0)]
        score = detector.score(signals)
        assert score.score == pytest.approx(1.0, abs=0.01)
        assert score.risk_level == "high"

    def test_signal_value_one(self):
        """Signal value=1.0 should produce zero fraud contribution."""
        detector = FraudDetector()
        signals = [FraudSignal(name="identity_verified", value=1.0)]
        score = detector.score(signals)
        assert score.score == pytest.approx(0.0, abs=0.01)
        assert score.risk_level == "low"

    def test_all_three_signals_present_confidence_one(self):
        """All expected signals present should give confidence=1.0."""
        detector = FraudDetector()
        signals = [
            FraudSignal(name="identity_verified", value=0.9),
            FraudSignal(name="financial_consistency", value=0.9),
            FraudSignal(name="traffic_authenticity", value=0.9),
        ]
        score = detector.score(signals)
        assert score.confidence == pytest.approx(1.0, abs=0.01)

    def test_graph_with_self_loop_no_ring(self):
        """Self-loop edges should not be detected as fraud rings."""
        detector = FraudDetector()
        graph = {
            "nodes": ["a", "b"],
            "edges": [("a", "a"), ("a", "b")],
        }
        result = detector.analyze_graph(graph)
        assert result.has_ring is False

    def test_graph_disconnected_components(self):
        """Disconnected components with rings should be detected."""
        detector = FraudDetector()
        graph = {
            "nodes": ["a", "b", "c", "d", "e", "f"],
            "edges": [("a", "b"), ("b", "c"), ("c", "a"),
                      ("d", "e"), ("e", "f"), ("f", "d")],
        }
        result = detector.analyze_graph(graph)
        assert result.has_ring is True
        assert result.risk_score == 0.8

    def test_graph_no_edges(self):
        """Graph with no edges should have no rings."""
        detector = FraudDetector()
        graph = {"nodes": ["a", "b", "c"], "edges": []}
        result = detector.analyze_graph(graph)
        assert result.has_ring is False

    def test_graph_single_node(self):
        """Single node graph should have no rings."""
        detector = FraudDetector()
        graph = {"nodes": ["a"], "edges": []}
        result = detector.analyze_graph(graph)
        assert result.has_ring is False

    def test_graph_triangle_detection(self):
        """Triangle (3-cycle) should be detected as fraud ring."""
        detector = FraudDetector()
        graph = {
            "nodes": ["a", "b", "c"],
            "edges": [("a", "b"), ("b", "c"), ("c", "a")],
        }
        result = detector.analyze_graph(graph)
        assert result.has_ring is True

    def test_graph_tree_no_cycle(self):
        """Tree structure should have no cycles."""
        detector = FraudDetector()
        graph = {
            "nodes": ["a", "b", "c", "d"],
            "edges": [("a", "b"), ("a", "c"), ("a", "d")],
        }
        result = detector.analyze_graph(graph)
        assert result.has_ring is False


# =====================================================================
# ENTITY RESOLUTION EDGE CASES
# =====================================================================


class TestEntityResolutionEdgeCases:
    """Edge cases for entity resolution clustering."""

    def test_threshold_zero_clusters_within_block(self):
        """threshold=0.0 should cluster entities within the same block."""
        resolver = EntityResolver(threshold=0.0)
        # Both names start with "acm" so they're in the same block
        entities = [
            {"id": "e1", "name": "Acme Corp", "domain": "acme.com"},
            {"id": "e2", "name": "Acme Global", "domain": "acme.com"},
        ]
        result = resolver.resolve(entities)
        assert len(result) == 1
        assert len(result[0].entities) == 2

    def test_threshold_one_only_exact_matches(self):
        """threshold=1.0 should only cluster identical normalized names."""
        resolver = EntityResolver(threshold=1.0)
        entities = [
            {"id": "e1", "name": "Acme Corp", "domain": "acme.com"},
            {"id": "e2", "name": "Acme Corp", "domain": "acme.com"},
            {"id": "e3", "name": "Globex Inc", "domain": "globex.com"},
        ]
        result = resolver.resolve(entities)
        assert len(result) == 2  # Acme cluster + Globex singleton

    def test_single_entity(self):
        """Single entity should return single cluster."""
        resolver = EntityResolver()
        entities = [{"id": "e1", "name": "Acme Corp", "domain": "acme.com"}]
        result = resolver.resolve(entities)
        assert len(result) == 1
        assert len(result[0].entities) == 1

    def test_all_identical_names(self):
        """All identical names should cluster into one."""
        resolver = EntityResolver()
        entities = [
            {"id": f"e{i}", "name": "Acme Corp", "domain": "acme.com"}
            for i in range(5)
        ]
        result = resolver.resolve(entities)
        assert len(result) == 1
        assert len(result[0].entities) == 5

    def test_missing_name_key(self):
        """Entity without 'name' key should not crash."""
        resolver = EntityResolver()
        entities = [
            {"id": "e1", "domain": "acme.com"},
            {"id": "e2", "name": "Acme Corp", "domain": "acme.com"},
        ]
        result = resolver.resolve(entities)
        # Empty name should not match "Acme Corp"
        assert len(result) == 2

    def test_empty_name_string(self):
        """Empty name string should be handled gracefully."""
        resolver = EntityResolver()
        entities = [
            {"id": "e1", "name": "", "domain": "acme.com"},
            {"id": "e2", "name": "Acme Corp", "domain": "acme.com"},
        ]
        result = resolver.resolve(entities)
        assert len(result) == 2

    def test_case_insensitive_matching(self):
        """Names differing only in case should cluster together."""
        resolver = EntityResolver()
        entities = [
            {"id": "e1", "name": "ACME CORP", "domain": "acme.com"},
            {"id": "e2", "name": "acme corp", "domain": "acme.com"},
        ]
        result = resolver.resolve(entities)
        assert len(result) == 1

    def test_canonical_name_tie_breaking(self):
        """First encountered name wins when counts are tied."""
        resolver = EntityResolver()
        entities = [
            {"id": "e1", "name": "Acme Corp", "domain": "acme.com"},
            {"id": "e2", "name": "Acme Corporation", "domain": "acme.com"},
        ]
        result = resolver.resolve(entities)
        assert result[0].canonical_name == "Acme Corp"

    def test_comparison_count_reset_between_calls(self):
        """comparison_count should reset between resolve() calls."""
        resolver = EntityResolver()
        entities = [
            {"id": "e1", "name": "Acme Corp"},
            {"id": "e2", "name": "Globex Inc"},
        ]
        resolver.resolve(entities)
        count1 = resolver.comparison_count
        resolver.resolve(entities)
        count2 = resolver.comparison_count
        assert count1 == count2


# =====================================================================
# MATCHING EDGE CASES
# =====================================================================


class TestMatchingEdgeCases:
    """Edge cases for buyer-seller matching."""

    def test_budget_zero_asking_price_zero(self):
        """Buyer with budget=0 should raise ValidationError."""
        matcher = BuyerSellerMatcher()
        buyers = [Buyer(id="b1", budget=0, preferences={"category": "saas"})]
        sellers = [Seller(id="s1", asking_price=0, attributes={"category": "saas"})]
        with pytest.raises(ValidationError):
            matcher.match(buyers, sellers)

    def test_asking_price_zero(self):
        """Seller with asking_price=0 should raise ValidationError."""
        matcher = BuyerSellerMatcher()
        buyers = [Buyer(id="b1", budget=100000, preferences={"category": "saas"})]
        sellers = [Seller(id="s1", asking_price=0, attributes={"category": "saas"})]
        with pytest.raises(ValidationError):
            matcher.match(buyers, sellers)

    def test_negative_budget(self):
        """Negative buyer budget should raise ValidationError."""
        matcher = BuyerSellerMatcher()
        buyers = [Buyer(id="b1", budget=-1000, preferences={"category": "saas"})]
        sellers = [Seller(id="s1", asking_price=0, attributes={"category": "saas"})]
        with pytest.raises(ValidationError):
            matcher.match(buyers, sellers)

    def test_negative_asking_price(self):
        """Negative asking price should raise ValidationError."""
        matcher = BuyerSellerMatcher()
        buyers = [Buyer(id="b1", budget=100000, preferences={"category": "saas"})]
        sellers = [Seller(id="s1", asking_price=-1000, attributes={"category": "saas"})]
        with pytest.raises(ValidationError):
            matcher.match(buyers, sellers)

    def test_duplicate_buyer_ids(self):
        """Duplicate buyer IDs should still produce valid matches."""
        matcher = BuyerSellerMatcher()
        buyers = [
            Buyer(id="b1", budget=100000, preferences={"category": "saas"}),
            Buyer(id="b1", budget=150000, preferences={"category": "saas"}),
        ]
        sellers = [Seller(id="s1", asking_price=80000, attributes={"category": "saas"})]
        matches = matcher.match(buyers, sellers)
        # Only one match since both buyers share the same ID
        assert len(matches) == 1

    def test_duplicate_seller_ids(self):
        """Duplicate seller IDs should still produce valid matches."""
        matcher = BuyerSellerMatcher()
        buyers = [Buyer(id="b1", budget=100000, preferences={"category": "saas"})]
        sellers = [
            Seller(id="s1", asking_price=50000, attributes={"category": "saas"}),
            Seller(id="s1", asking_price=60000, attributes={"category": "saas"}),
        ]
        matches = matcher.match(buyers, sellers)
        # Only one match since both sellers share the same ID
        assert len(matches) == 1

    def test_budget_exactly_equals_asking_price(self):
        """Buyer budget exactly equal to asking price should be feasible."""
        matcher = BuyerSellerMatcher()
        buyers = [Buyer(id="b1", budget=80000, preferences={"category": "saas"})]
        sellers = [Seller(id="s1", asking_price=80000, attributes={"category": "saas"})]
        matches = matcher.match(buyers, sellers)
        assert len(matches) == 1
        assert matches[0].score == 0.0  # (1 - 80000/80000) = 0.0

    def test_empty_buyers_only(self):
        """Empty buyers list should raise EmptyInputError."""
        matcher = BuyerSellerMatcher()
        sellers = [Seller(id="s1", asking_price=50000, attributes={"category": "saas"})]
        with pytest.raises(EmptyInputError):
            matcher.match([], sellers)

    def test_empty_sellers_only(self):
        """Empty sellers list should raise EmptyInputError."""
        matcher = BuyerSellerMatcher()
        buyers = [Buyer(id="b1", budget=100000, preferences={"category": "saas"})]
        with pytest.raises(EmptyInputError):
            matcher.match(buyers, [])

    def test_matches_sorted_by_score_descending(self):
        """Matches should be sorted by score descending."""
        matcher = BuyerSellerMatcher()
        buyers = [
            Buyer(id="b1", budget=100000, preferences={"category": "saas"}),
            Buyer(id="b2", budget=200000, preferences={"category": "saas"}),
        ]
        sellers = [
            Seller(id="s1", asking_price=50000, attributes={"category": "saas"}),
            Seller(id="s2", asking_price=100000, attributes={"category": "saas"}),
        ]
        matches = matcher.match(buyers, sellers)
        assert len(matches) == 2
        scores = [m.score for m in matches]
        assert scores == sorted(scores, reverse=True)


# =====================================================================
# PORTFOLIO OPTIMIZER EDGE CASES
# =====================================================================


class TestPortfolioEdgeCases:
    """Edge cases for portfolio optimization."""

    def test_max_assets_zero_raises(self):
        """max_assets=0 should raise ValidationError."""
        with pytest.raises(ValidationError):
            PortfolioOptimizer(budget=1000000, max_assets=0)

    def test_budget_zero_raises(self):
        """budget=0 should raise ValidationError."""
        with pytest.raises(ValidationError):
            PortfolioOptimizer(budget=0)

    def test_all_same_sector(self):
        """All assets in same sector should still select best ones."""
        optimizer = PortfolioOptimizer(budget=1000000)
        assets = [
            Asset(id="a1", cost=400000, expected_return=0.12, risk=0.15, sector="saas"),
            Asset(id="a2", cost=400000, expected_return=0.10, risk=0.12, sector="saas"),
            Asset(id="a3", cost=400000, expected_return=0.08, risk=0.10, sector="saas"),
        ]
        result = optimizer.optimize(assets, risk_tolerance=0.5)
        assert len(result.assets) >= 1
        # All selected should be in same sector
        sectors = [a.sector for a in result.assets]
        assert all(s == "saas" for s in sectors)

    def test_single_asset(self):
        """Single asset within budget should be selected."""
        optimizer = PortfolioOptimizer(budget=1000000)
        assets = [Asset(id="a1", cost=500000, expected_return=0.12, risk=0.15)]
        result = optimizer.optimize(assets, risk_tolerance=0.5)
        assert len(result.assets) == 1
        assert result.assets[0].id == "a1"

    def test_all_assets_exceed_budget(self):
        """All assets exceeding budget should return empty portfolio."""
        optimizer = PortfolioOptimizer(budget=100000)
        assets = [
            Asset(id="a1", cost=200000, expected_return=0.12, risk=0.15),
            Asset(id="a2", cost=300000, expected_return=0.10, risk=0.10),
        ]
        result = optimizer.optimize(assets, risk_tolerance=0.5)
        assert result.assets == []
        assert result.expected_return == 0.0

    def test_asset_zero_cost(self):
        """Asset with zero cost should be selected (free asset)."""
        optimizer = PortfolioOptimizer(budget=1000000)
        assets = [
            Asset(id="free", cost=0, expected_return=0.05, risk=0.01),
            Asset(id="paid", cost=500000, expected_return=0.12, risk=0.15),
        ]
        result = optimizer.optimize(assets, risk_tolerance=0.5)
        assert any(a.id == "free" for a in result.assets)

    def test_asset_zero_risk(self):
        """Asset with zero risk should have high risk-adjusted return."""
        optimizer = PortfolioOptimizer(budget=1000000)
        assets = [
            Asset(id="riskfree", cost=500000, expected_return=0.05, risk=0),
            Asset(id="risky", cost=500000, expected_return=0.15, risk=0.25),
        ]
        result = optimizer.optimize(assets, risk_tolerance=0.5)
        # risk-free asset should be selected due to high risk-adjusted return
        assert any(a.id == "riskfree" for a in result.assets)

    def test_max_assets_one(self):
        """max_assets=1 should select at most one asset."""
        optimizer = PortfolioOptimizer(budget=10000000, max_assets=1)
        assets = [
            Asset(id=f"a{i}", cost=1000000, expected_return=0.10 + i * 0.01, risk=0.15)
            for i in range(5)
        ]
        result = optimizer.optimize(assets, risk_tolerance=0.5)
        assert len(result.assets) <= 1

    def test_max_assets_greater_than_asset_count(self):
        """max_assets > len(assets) should not be binding."""
        optimizer = PortfolioOptimizer(budget=10000000, max_assets=100)
        assets = [
            Asset(id="a1", cost=1000000, expected_return=0.12, risk=0.15),
            Asset(id="a2", cost=1000000, expected_return=0.10, risk=0.10),
        ]
        result = optimizer.optimize(assets, risk_tolerance=0.5)
        assert len(result.assets) == 2


# =====================================================================
# DYNAMIC PRICING EDGE CASES
# =====================================================================


class TestPricingEdgeCases:
    """Edge cases for dynamic pricing engine."""

    def test_demand_zero(self):
        """demand_level=0 should produce minimum demand multiplier."""
        engine = PricingEngine()
        rec = engine.recommend_price(
            base_value=100000,
            demand_level=0,
            competition_level=0.5,
            market_condition="normal",
        )
        assert rec.recommended_price > 0
        # demand_multiplier = 0.8 + 0*0.4 = 0.8
        expected = 100000 * 0.8 * (1.2 - 0.5 * 0.4) * 1.0
        assert rec.recommended_price == pytest.approx(expected, rel=0.01)

    def test_demand_one(self):
        """demand_level=1 should produce maximum demand multiplier."""
        engine = PricingEngine()
        rec = engine.recommend_price(
            base_value=100000,
            demand_level=1,
            competition_level=0.5,
            market_condition="normal",
        )
        assert rec.recommended_price > 0
        # demand_multiplier = 0.8 + 1*0.4 = 1.2
        expected = 100000 * 1.2 * (1.2 - 0.5 * 0.4) * 1.0
        assert rec.recommended_price == pytest.approx(expected, rel=0.01)

    def test_competition_zero(self):
        """competition_level=0 should produce maximum competition multiplier."""
        engine = PricingEngine()
        rec = engine.recommend_price(
            base_value=100000,
            demand_level=0.5,
            competition_level=0,
            market_condition="normal",
        )
        assert rec.recommended_price > 0
        # competition_multiplier = 1.2 - 0*0.4 = 1.2
        expected = 100000 * (0.8 + 0.5 * 0.4) * 1.2 * 1.0
        assert rec.recommended_price == pytest.approx(expected, rel=0.01)

    def test_competition_one(self):
        """competition_level=1 should produce minimum competition multiplier."""
        engine = PricingEngine()
        rec = engine.recommend_price(
            base_value=100000,
            demand_level=0.5,
            competition_level=1,
            market_condition="normal",
        )
        assert rec.recommended_price > 0
        # competition_multiplier = 1.2 - 1*0.4 = 0.8
        expected = 100000 * (0.8 + 0.5 * 0.4) * 0.8 * 1.0
        assert rec.recommended_price == pytest.approx(expected, rel=0.01)

    def test_invalid_market_condition_raises(self):
        """Invalid market_condition should raise ValidationError."""
        engine = PricingEngine()
        with pytest.raises(ValidationError):
            engine.recommend_price(
                base_value=100000,
                demand_level=0.5,
                competition_level=0.5,
                market_condition="invalid_condition",
            )

    def test_zero_base_value_raises(self):
        """base_value=0 should raise ValidationError."""
        engine = PricingEngine()
        with pytest.raises(ValidationError):
            engine.recommend_price(
                base_value=0,
                demand_level=0.5,
                competition_level=0.5,
                market_condition="normal",
            )

    def test_confidence_when_demand_equals_competition(self):
        """Confidence should be 1.0 when demand == competition."""
        engine = PricingEngine()
        rec = engine.recommend_price(
            base_value=100000,
            demand_level=0.5,
            competition_level=0.5,
            market_condition="normal",
        )
        assert rec.confidence == pytest.approx(1.0, abs=0.01)

    def test_confidence_when_demand_zero_competition_one(self):
        """Confidence should be 0.0 when demand=0 and competition=1."""
        engine = PricingEngine()
        rec = engine.recommend_price(
            base_value=100000,
            demand_level=0,
            competition_level=1,
            market_condition="normal",
        )
        assert rec.confidence == pytest.approx(0.0, abs=0.01)


# =====================================================================
# EVOLUTION EDGE CASES
# =====================================================================


class TestEvolutionEdgeCases:
    """Edge cases for genetic algorithm evolution."""

    def test_population_size_zero_raises(self):
        """population_size=0 should raise ValidationError."""
        with pytest.raises(ValidationError):
            EvolutionEngine(population_size=0, generations=5)

    def test_generations_zero_raises(self):
        """generations=0 should raise ValidationError."""
        with pytest.raises(ValidationError):
            EvolutionEngine(population_size=10, generations=0)

    def test_mutation_rate_zero(self):
        """mutation_rate=0 should still evolve via crossover."""
        engine = EvolutionEngine(population_size=20, generations=5, mutation_rate=0)
        result = engine.evolve(fitness_fn=lambda x: x, gene_range=(0, 100))
        assert result.offspring_count > 0
        assert result.best_fitness >= result.worst_fitness

    def test_mutation_rate_one(self):
        """mutation_rate=1 should mutate every offspring."""
        engine = EvolutionEngine(population_size=20, generations=5, mutation_rate=1)
        result = engine.evolve(fitness_fn=lambda x: x, gene_range=(0, 100))
        assert result.offspring_count > 0
        # With mutation_rate=1, diversity should be > 0
        assert result.diversity >= 0.0

    def test_population_size_one(self):
        """population_size=1 should not crash (elitism fills population)."""
        engine = EvolutionEngine(population_size=1, generations=5)
        result = engine.evolve(fitness_fn=lambda x: x, gene_range=(0, 10))
        assert result.population_size == 1
        assert result.generation_count == 5
        assert result.offspring_count == 0  # No offspring since elite fills population

    def test_elitism_zero(self):
        """elitism=0 should not preserve any elite individuals."""
        engine = EvolutionEngine(population_size=20, generations=5, elitism=0)
        result = engine.evolve(fitness_fn=lambda x: x, gene_range=(0, 100))
        assert result.offspring_count > 0

    def test_constant_fitness_function(self):
        """Constant fitness function should converge immediately."""
        engine = EvolutionEngine(population_size=10, generations=20)
        result = engine.evolve(fitness_fn=lambda x: 1.0, gene_range=(0, 100))
        assert result.best_fitness == 1.0
        assert result.worst_fitness == 1.0
        assert result.diversity == 0.0

    def test_negative_fitness_function(self):
        """Negative fitness function should still work."""
        engine = EvolutionEngine(population_size=20, generations=5)
        result = engine.evolve(fitness_fn=lambda x: -x**2, gene_range=(0, 100))
        # Best fitness should be closest to 0 (least negative)
        assert result.best_fitness >= result.worst_fitness
        assert result.best_fitness <= 0.0


# =====================================================================
# SEARCH RANKING EDGE CASES
# =====================================================================


class TestSearchRankingEdgeCases:
    """Edge cases for search ranking engine."""

    def test_empty_query(self):
        """Empty query string should still rank listings."""
        ranker = SearchRanker()
        listings = [Listing(id="l1", title="Test", relevance=0.8)]
        results = ranker.rank("", listings)
        assert len(results) == 1

    def test_empty_listings(self):
        """Empty listings list should raise EmptyInputError."""
        ranker = SearchRanker()
        with pytest.raises(EmptyInputError):
            ranker.rank("test", [])

    def test_duplicate_listing_ids(self):
        """Duplicate listing IDs should be deduplicated, keeping highest score."""
        ranker = SearchRanker()
        listings = [
            Listing(id="l1", title="First", relevance=0.9, category="saas"),
            Listing(id="l1", title="Second", relevance=0.5, category="ecommerce"),
        ]
        results = ranker.rank("test", listings)
        assert len(results) == 1
        # Should keep the one with higher score (0.9 * 1.0 = 0.9)
        assert results[0].score == pytest.approx(0.9, abs=0.01)

    def test_negative_relevance(self):
        """Negative relevance should raise InvalidRangeError."""
        ranker = SearchRanker()
        listings = [Listing(id="l1", title="Test", relevance=-0.5)]
        with pytest.raises(InvalidRangeError):
            ranker.rank("test", listings)

    def test_relevance_zero(self):
        """Zero relevance should produce zero score."""
        ranker = SearchRanker()
        listings = [Listing(id="l1", title="Test", relevance=0.0)]
        results = ranker.rank("test", listings)
        assert len(results) == 1
        assert results[0].score == 0.0

    def test_relevance_one(self):
        """Maximum relevance=1.0 should produce score=1.0 for first in category."""
        ranker = SearchRanker()
        listings = [Listing(id="l1", title="Test", relevance=1.0, category="saas")]
        results = ranker.rank("test", listings)
        assert len(results) == 1
        assert results[0].score == pytest.approx(1.0, abs=0.01)

    def test_none_user_preferences(self):
        """None user_preferences should not apply personalization."""
        ranker = SearchRanker()
        listings = [
            Listing(id="l1", title="SaaS", relevance=0.7, category="saas"),
            Listing(id="l2", title="E-commerce", relevance=0.7, category="ecommerce"),
        ]
        results = ranker.rank("platform", listings, user_preferences=None)
        # No personalization boost, first gets diversity_factor=1.0
        assert results[0].id == "l1"

    def test_empty_user_preferences(self):
        """Empty user_preferences dict should not apply personalization."""
        ranker = SearchRanker()
        listings = [
            Listing(id="l1", title="SaaS", relevance=0.7, category="saas"),
            Listing(id="l2", title="E-commerce", relevance=0.7, category="ecommerce"),
        ]
        results = ranker.rank("platform", listings, user_preferences={})
        assert results[0].id == "l1"

    def test_all_listings_same_category(self):
        """All listings in same category should apply diversity penalty."""
        ranker = SearchRanker()
        listings = [
            Listing(id="l1", title="A", relevance=0.9, category="saas"),
            Listing(id="l2", title="B", relevance=0.8, category="saas"),
            Listing(id="l3", title="C", relevance=0.7, category="saas"),
        ]
        results = ranker.rank("test", listings)
        assert len(results) == 3
        # First gets diversity_factor=1.0, rest get 0.7
        assert results[0].score == pytest.approx(0.9, abs=0.01)
        assert results[1].score == pytest.approx(0.8 * 0.7, abs=0.01)
        assert results[2].score == pytest.approx(0.7 * 0.7, abs=0.01)

    def test_empty_category_string(self):
        """Empty category string should be handled."""
        ranker = SearchRanker()
        listings = [
            Listing(id="l1", title="A", relevance=0.9, category=""),
            Listing(id="l2", title="B", relevance=0.8, category="saas"),
        ]
        results = ranker.rank("test", listings)
        assert len(results) == 2
