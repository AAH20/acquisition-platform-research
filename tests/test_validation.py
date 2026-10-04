"""Tests for input validation and error handling across all modules.

These tests verify that each module properly validates its inputs
and raises appropriate exceptions for invalid data.
"""
import math
import pytest

from acquisition_platform.exceptions import (
    AcquisitionPlatformError,
    ValidationError,
    DivisionByZeroError,
    EmptyInputError,
    InvalidRangeError,
)
from acquisition_platform.valuation import ValuationEngine
from acquisition_platform.matching import BuyerSellerMatcher, Buyer, Seller
from acquisition_platform.fraud_detection import FraudDetector, FraudSignal
from acquisition_platform.portfolio_optimizer import PortfolioOptimizer, Asset
from acquisition_platform.dynamic_pricing import PricingEngine
from acquisition_platform.entity_resolution import EntityResolver
from acquisition_platform.search_ranking import SearchRanker, Listing
from acquisition_platform.evolution import EvolutionEngine


class TestExceptionHierarchy:
    """Test that the exception hierarchy is correct."""

    def test_all_exceptions_inherit_from_base(self):
        """All custom exceptions should inherit from AcquisitionPlatformError."""
        assert issubclass(ValidationError, AcquisitionPlatformError)
        assert issubclass(DivisionByZeroError, AcquisitionPlatformError)
        assert issubclass(EmptyInputError, AcquisitionPlatformError)
        assert issubclass(InvalidRangeError, AcquisitionPlatformError)

    def test_validation_error_is_value_error(self):
        """ValidationError should also be a ValueError for compatibility."""
        assert issubclass(ValidationError, ValueError)

    def test_division_by_zero_is_zero_division_error(self):
        """DivisionByZeroError should also be a ZeroDivisionError."""
        assert issubclass(DivisionByZeroError, ZeroDivisionError)

    def test_empty_input_error_is_value_error(self):
        """EmptyInputError should also be a ValueError."""
        assert issubclass(EmptyInputError, ValueError)

    def test_invalid_range_error_is_value_error(self):
        """InvalidRangeError should also be a ValueError."""
        assert issubclass(InvalidRangeError, ValueError)

    def test_catch_all_with_base_exception(self):
        """Should be able to catch any custom error with the base class."""
        with pytest.raises(AcquisitionPlatformError):
            raise ValidationError("test")
        with pytest.raises(AcquisitionPlatformError):
            raise DivisionByZeroError("test")
        with pytest.raises(AcquisitionPlatformError):
            raise EmptyInputError("test")
        with pytest.raises(AcquisitionPlatformError):
            raise InvalidRangeError("test")


class TestValuationValidation:
    """Test validation in the valuation engine."""

    def test_dcf_discount_rate_equals_terminal_growth_raises(self):
        """DCF with discount_rate == terminal_growth should raise DivisionByZeroError."""
        engine = ValuationEngine()
        with pytest.raises(DivisionByZeroError):
            engine.dcf_valuation(
                free_cash_flow=100000,
                growth_rate=0.05,
                discount_rate=0.02,
                terminal_growth=0.02,
                years=5,
            )

    def test_dcf_negative_free_cash_flow_raises(self):
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

    def test_dcf_negative_discount_rate_raises(self):
        """DCF with negative discount rate should raise ValidationError."""
        engine = ValuationEngine()
        with pytest.raises(ValidationError):
            engine.dcf_valuation(
                free_cash_flow=100000,
                growth_rate=0.05,
                discount_rate=-0.10,
                terminal_growth=0.02,
                years=5,
            )

    def test_dcf_negative_terminal_growth_raises(self):
        """DCF with negative terminal growth should raise ValidationError."""
        engine = ValuationEngine()
        with pytest.raises(ValidationError):
            engine.dcf_valuation(
                free_cash_flow=100000,
                growth_rate=0.05,
                discount_rate=0.10,
                terminal_growth=-0.02,
                years=5,
            )

    def test_dcf_negative_years_raises(self):
        """DCF with negative years should raise ValidationError."""
        engine = ValuationEngine()
        with pytest.raises(ValidationError):
            engine.dcf_valuation(
                free_cash_flow=100000,
                growth_rate=0.05,
                discount_rate=0.10,
                terminal_growth=0.02,
                years=-5,
            )

    def test_dcf_zero_years_raises(self):
        """DCF with zero years should raise ValidationError."""
        engine = ValuationEngine()
        with pytest.raises(ValidationError):
            engine.dcf_valuation(
                free_cash_flow=100000,
                growth_rate=0.05,
                discount_rate=0.10,
                terminal_growth=0.02,
                years=0,
            )

    def test_comparable_negative_metric_raises(self):
        """Comps valuation with negative metric should raise ValidationError."""
        engine = ValuationEngine()
        with pytest.raises(ValidationError):
            engine.comparable_valuation(metric=-1000000, multiple=3.2)

    def test_comparable_negative_multiple_raises(self):
        """Comps valuation with negative multiple should raise ValidationError."""
        engine = ValuationEngine()
        with pytest.raises(ValidationError):
            engine.comparable_valuation(metric=1000000, multiple=-3.2)

    def test_ensemble_negative_revenue_raises(self):
        """Ensemble valuation with negative revenue should raise ValidationError."""
        engine = ValuationEngine()
        with pytest.raises(ValidationError):
            engine.ensemble_valuation(
                free_cash_flow=100000,
                revenue=-500000,
                growth_rate=0.05,
                discount_rate=0.10,
                terminal_growth=0.02,
                revenue_multiple=3.2,
                years=5,
            )

    def test_sde_negative_sde_raises(self):
        """SDE valuation with negative SDE should raise ValidationError."""
        engine = ValuationEngine()
        with pytest.raises(ValidationError):
            engine.sde_valuation(sde=-50000, multiple=3.9)

    def test_arr_negative_arr_raises(self):
        """ARR valuation with negative ARR should raise ValidationError."""
        engine = ValuationEngine()
        with pytest.raises(ValidationError):
            engine.arr_valuation(arr=-1200000, multiple=4.5)


class TestMatchingValidation:
    """Test validation in the matching engine."""

    def test_match_empty_buyers_raises(self):
        """Matching with empty buyers list should raise EmptyInputError."""
        matcher = BuyerSellerMatcher()
        sellers = [Seller(id="s1", asking_price=80000, attributes={"category": "saas"})]
        with pytest.raises(EmptyInputError):
            matcher.match([], sellers)

    def test_match_empty_sellers_raises(self):
        """Matching with empty sellers list should raise EmptyInputError."""
        matcher = BuyerSellerMatcher()
        buyers = [Buyer(id="b1", budget=100000, preferences={"category": "saas"})]
        with pytest.raises(EmptyInputError):
            matcher.match(buyers, [])

    def test_match_both_empty_raises(self):
        """Matching with both lists empty should raise EmptyInputError."""
        matcher = BuyerSellerMatcher()
        with pytest.raises(EmptyInputError):
            matcher.match([], [])

    def test_buyer_negative_budget_raises(self):
        """Buyer with negative budget should raise ValidationError."""
        matcher = BuyerSellerMatcher()
        buyers = [Buyer(id="b1", budget=-100000, preferences={"category": "saas"})]
        sellers = [Seller(id="s1", asking_price=80000, attributes={"category": "saas"})]
        with pytest.raises(ValidationError):
            matcher.match(buyers, sellers)

    def test_seller_negative_asking_price_raises(self):
        """Seller with negative asking price should raise ValidationError."""
        matcher = BuyerSellerMatcher()
        buyers = [Buyer(id="b1", budget=100000, preferences={"category": "saas"})]
        sellers = [Seller(id="s1", asking_price=-80000, attributes={"category": "saas"})]
        with pytest.raises(ValidationError):
            matcher.match(buyers, sellers)

    def test_buyer_zero_budget_raises(self):
        """Buyer with zero budget should raise ValidationError."""
        matcher = BuyerSellerMatcher()
        buyers = [Buyer(id="b1", budget=0, preferences={"category": "saas"})]
        sellers = [Seller(id="s1", asking_price=80000, attributes={"category": "saas"})]
        with pytest.raises(ValidationError):
            matcher.match(buyers, sellers)

    def test_seller_zero_asking_price_raises(self):
        """Seller with zero asking price should raise ValidationError."""
        matcher = BuyerSellerMatcher()
        buyers = [Buyer(id="b1", budget=100000, preferences={"category": "saas"})]
        sellers = [Seller(id="s1", asking_price=0, attributes={"category": "saas"})]
        with pytest.raises(ValidationError):
            matcher.match(buyers, sellers)


class TestFraudDetectionValidation:
    """Test validation in the fraud detection engine."""

    def test_signal_value_above_one_raises(self):
        """Signal value > 1 should raise InvalidRangeError."""
        detector = FraudDetector()
        signals = [FraudSignal(name="test", value=1.5)]
        with pytest.raises(InvalidRangeError):
            detector.score(signals)

    def test_signal_value_below_zero_raises(self):
        """Signal value < 0 should raise InvalidRangeError."""
        detector = FraudDetector()
        signals = [FraudSignal(name="test", value=-0.5)]
        with pytest.raises(InvalidRangeError):
            detector.score(signals)

    def test_signal_nan_value_raises(self):
        """Signal value NaN should raise ValidationError."""
        detector = FraudDetector()
        signals = [FraudSignal(name="test", value=float("nan"))]
        with pytest.raises(ValidationError):
            detector.score(signals)

    def test_signal_inf_value_raises(self):
        """Signal value Inf should raise ValidationError."""
        detector = FraudDetector()
        signals = [FraudSignal(name="test", value=float("inf"))]
        with pytest.raises(ValidationError):
            detector.score(signals)

    def test_signal_negative_inf_raises(self):
        """Signal value -Inf should raise ValidationError."""
        detector = FraudDetector()
        signals = [FraudSignal(name="test", value=float("-inf"))]
        with pytest.raises(ValidationError):
            detector.score(signals)

    def test_empty_signals_raises(self):
        """Empty signals list should raise EmptyInputError."""
        detector = FraudDetector()
        with pytest.raises(EmptyInputError):
            detector.score([])

    def test_valid_signal_values_accepted(self):
        """Signal values in [0, 1] should be accepted."""
        detector = FraudDetector()
        signals = [
            FraudSignal(name="identity_verified", value=0.0),
            FraudSignal(name="financial_consistency", value=0.5),
            FraudSignal(name="traffic_authenticity", value=1.0),
        ]
        result = detector.score(signals)
        assert result.score >= 0.0
        assert result.score <= 1.0


class TestPortfolioOptimizerValidation:
    """Test validation in the portfolio optimizer."""

    def test_negative_budget_raises(self):
        """Negative budget should raise ValidationError."""
        with pytest.raises(ValidationError):
            PortfolioOptimizer(budget=-1000000)

    def test_zero_budget_raises(self):
        """Zero budget should raise ValidationError."""
        with pytest.raises(ValidationError):
            PortfolioOptimizer(budget=0)

    def test_negative_max_assets_raises(self):
        """Negative max_assets should raise ValidationError."""
        with pytest.raises(ValidationError):
            PortfolioOptimizer(budget=1000000, max_assets=-5)

    def test_zero_max_assets_raises(self):
        """Zero max_assets should raise ValidationError."""
        with pytest.raises(ValidationError):
            PortfolioOptimizer(budget=1000000, max_assets=0)

    def test_negative_risk_tolerance_raises(self):
        """Negative risk_tolerance should raise InvalidRangeError."""
        optimizer = PortfolioOptimizer(budget=1000000)
        assets = [Asset(id="a1", cost=500000, expected_return=0.12, risk=0.15)]
        with pytest.raises(InvalidRangeError):
            optimizer.optimize(assets, risk_tolerance=-0.5)

    def test_risk_tolerance_above_one_raises(self):
        """risk_tolerance > 1 should raise InvalidRangeError."""
        optimizer = PortfolioOptimizer(budget=1000000)
        assets = [Asset(id="a1", cost=500000, expected_return=0.12, risk=0.15)]
        with pytest.raises(InvalidRangeError):
            optimizer.optimize(assets, risk_tolerance=1.5)

    def test_empty_assets_raises(self):
        """Empty assets list should raise EmptyInputError."""
        optimizer = PortfolioOptimizer(budget=1000000)
        with pytest.raises(EmptyInputError):
            optimizer.optimize([], risk_tolerance=0.5)

    def test_negative_asset_cost_raises(self):
        """Asset with negative cost should raise ValidationError."""
        optimizer = PortfolioOptimizer(budget=1000000)
        assets = [Asset(id="a1", cost=-500000, expected_return=0.12, risk=0.15)]
        with pytest.raises(ValidationError):
            optimizer.optimize(assets, risk_tolerance=0.5)

    def test_negative_asset_risk_raises(self):
        """Asset with negative risk should raise ValidationError."""
        optimizer = PortfolioOptimizer(budget=1000000)
        assets = [Asset(id="a1", cost=500000, expected_return=0.12, risk=-0.15)]
        with pytest.raises(ValidationError):
            optimizer.optimize(assets, risk_tolerance=0.5)


class TestDynamicPricingValidation:
    """Test validation in the dynamic pricing engine."""

    def test_negative_base_value_raises(self):
        """Negative base_value should raise ValidationError."""
        engine = PricingEngine()
        with pytest.raises(ValidationError):
            engine.recommend_price(
                base_value=-100000,
                demand_level=0.5,
                competition_level=0.5,
                market_condition="normal",
            )

    def test_zero_base_value_raises(self):
        """Zero base_value should raise ValidationError."""
        engine = PricingEngine()
        with pytest.raises(ValidationError):
            engine.recommend_price(
                base_value=0,
                demand_level=0.5,
                competition_level=0.5,
                market_condition="normal",
            )

    def test_demand_level_above_one_raises(self):
        """demand_level > 1 should raise InvalidRangeError."""
        engine = PricingEngine()
        with pytest.raises(InvalidRangeError):
            engine.recommend_price(
                base_value=100000,
                demand_level=1.5,
                competition_level=0.5,
                market_condition="normal",
            )

    def test_demand_level_below_zero_raises(self):
        """demand_level < 0 should raise InvalidRangeError."""
        engine = PricingEngine()
        with pytest.raises(InvalidRangeError):
            engine.recommend_price(
                base_value=100000,
                demand_level=-0.5,
                competition_level=0.5,
                market_condition="normal",
            )

    def test_competition_level_above_one_raises(self):
        """competition_level > 1 should raise InvalidRangeError."""
        engine = PricingEngine()
        with pytest.raises(InvalidRangeError):
            engine.recommend_price(
                base_value=100000,
                demand_level=0.5,
                competition_level=1.5,
                market_condition="normal",
            )

    def test_competition_level_below_zero_raises(self):
        """competition_level < 0 should raise InvalidRangeError."""
        engine = PricingEngine()
        with pytest.raises(InvalidRangeError):
            engine.recommend_price(
                base_value=100000,
                demand_level=0.5,
                competition_level=-0.5,
                market_condition="normal",
            )

    def test_invalid_market_condition_raises(self):
        """Invalid market_condition should raise ValidationError."""
        engine = PricingEngine()
        with pytest.raises(ValidationError):
            engine.recommend_price(
                base_value=100000,
                demand_level=0.5,
                competition_level=0.5,
                market_condition="invalid",
            )

    def test_valid_market_conditions_accepted(self):
        """Valid market conditions should be accepted."""
        engine = PricingEngine()
        for condition in ["bull", "bear", "normal"]:
            result = engine.recommend_price(
                base_value=100000,
                demand_level=0.5,
                competition_level=0.5,
                market_condition=condition,
            )
            assert result.recommended_price > 0


class TestEntityResolutionValidation:
    """Test validation in the entity resolution engine."""

    def test_threshold_above_one_raises(self):
        """Threshold > 1 should raise InvalidRangeError."""
        with pytest.raises(InvalidRangeError):
            EntityResolver(threshold=1.5)

    def test_threshold_below_zero_raises(self):
        """Threshold < 0 should raise InvalidRangeError."""
        with pytest.raises(InvalidRangeError):
            EntityResolver(threshold=-0.5)

    def test_empty_entities_raises(self):
        """Empty entities list should raise EmptyInputError."""
        resolver = EntityResolver()
        with pytest.raises(EmptyInputError):
            resolver.resolve([])

    def test_valid_threshold_accepted(self):
        """Threshold in [0, 1] should be accepted."""
        resolver = EntityResolver(threshold=0.0)
        assert resolver.threshold == 0.0
        resolver = EntityResolver(threshold=1.0)
        assert resolver.threshold == 1.0
        resolver = EntityResolver(threshold=0.5)
        assert resolver.threshold == 0.5


class TestSearchRankingValidation:
    """Test validation in the search ranking engine."""

    def test_empty_listings_raises(self):
        """Empty listings list should raise EmptyInputError."""
        ranker = SearchRanker()
        with pytest.raises(EmptyInputError):
            ranker.rank("test", [])

    def test_negative_relevance_raises(self):
        """Negative relevance should raise InvalidRangeError."""
        ranker = SearchRanker()
        listings = [Listing(id="l1", title="Test", relevance=-0.5)]
        with pytest.raises(InvalidRangeError):
            ranker.rank("test", listings)

    def test_relevance_above_one_raises(self):
        """Relevance > 1 should raise InvalidRangeError."""
        ranker = SearchRanker()
        listings = [Listing(id="l1", title="Test", relevance=1.5)]
        with pytest.raises(InvalidRangeError):
            ranker.rank("test", listings)

    def test_valid_relevance_accepted(self):
        """Relevance in [0, 1] should be accepted."""
        ranker = SearchRanker()
        listings = [
            Listing(id="l1", title="Test", relevance=0.0),
            Listing(id="l2", title="Test", relevance=0.5),
            Listing(id="l3", title="Test", relevance=1.0),
        ]
        results = ranker.rank("test", listings)
        assert len(results) == 3


class TestEvolutionValidation:
    """Test validation in the evolution engine."""

    def test_negative_population_size_raises(self):
        """Negative population_size should raise ValidationError."""
        with pytest.raises(ValidationError):
            EvolutionEngine(population_size=-10)

    def test_zero_population_size_raises(self):
        """Zero population_size should raise ValidationError."""
        with pytest.raises(ValidationError):
            EvolutionEngine(population_size=0)

    def test_negative_generations_raises(self):
        """Negative generations should raise ValidationError."""
        with pytest.raises(ValidationError):
            EvolutionEngine(generations=-10)

    def test_zero_generations_raises(self):
        """Zero generations should raise ValidationError."""
        with pytest.raises(ValidationError):
            EvolutionEngine(generations=0)

    def test_negative_mutation_rate_raises(self):
        """Negative mutation_rate should raise InvalidRangeError."""
        with pytest.raises(InvalidRangeError):
            EvolutionEngine(mutation_rate=-0.1)

    def test_mutation_rate_above_one_raises(self):
        """mutation_rate > 1 should raise InvalidRangeError."""
        with pytest.raises(InvalidRangeError):
            EvolutionEngine(mutation_rate=1.5)

    def test_valid_parameters_accepted(self):
        """Valid parameters should be accepted."""
        engine = EvolutionEngine(
            population_size=10,
            generations=5,
            mutation_rate=0.1,
        )
        assert engine.population_size == 10
        assert engine.generations == 5
        assert engine.mutation_rate == 0.1

    def test_mutation_rate_boundary_values_accepted(self):
        """mutation_rate of 0.0 and 1.0 should be accepted."""
        engine = EvolutionEngine(mutation_rate=0.0)
        assert engine.mutation_rate == 0.0
        engine = EvolutionEngine(mutation_rate=1.0)
        assert engine.mutation_rate == 1.0
