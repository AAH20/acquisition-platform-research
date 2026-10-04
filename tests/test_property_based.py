"""Property-based tests using Hypothesis for all core modules.

These tests verify universal invariants that should hold for any valid input:
- Matching: scores in [0,1], each buyer/seller matched at most once
- Valuation: DCF value > 0 for positive inputs, ensemble confidence in [0,1]
- Fraud: score in [0,1], risk_level in {low, medium, high}
- Portfolio: total cost <= budget, len(assets) <= max_assets
- Pricing: floor <= recommended <= ceiling
- Entity resolution: clusters non-overlapping, all entities assigned
- Ranking: scores finite, no duplicates in output
- Evolution: best_fitness >= worst_fitness
"""

import math

from hypothesis import given, settings, strategies as st

from acquisition_platform.matching import Buyer, BuyerSellerMatcher, Seller
from acquisition_platform.valuation import ValuationEngine
from acquisition_platform.fraud_detection import FraudDetector, FraudSignal
from acquisition_platform.portfolio_optimizer import Asset, PortfolioOptimizer
from acquisition_platform.dynamic_pricing import PricingEngine
from acquisition_platform.entity_resolution import EntityResolver
from acquisition_platform.search_ranking import Listing, SearchRanker
from acquisition_platform.evolution import EvolutionEngine


# ---------------------------------------------------------------------------
# Matching properties
# ---------------------------------------------------------------------------

class TestMatchingProperties:
    """Property-based tests for BuyerSellerMatcher."""

    @given(
        buyers=st.lists(
            st.builds(
                Buyer,
                id=st.text(min_size=1, max_size=10),
                budget=st.floats(min_value=1.0, max_value=1e6, allow_nan=False, allow_infinity=False),
                preferences=st.fixed_dictionaries({
                    "category": st.sampled_from(["saas", "ecommerce", "fintech", "healthtech", "edtech"])
                }),
            ),
            min_size=1, max_size=20,
        ),
        sellers=st.lists(
            st.builds(
                Seller,
                id=st.text(min_size=1, max_size=10),
                asking_price=st.floats(min_value=1.0, max_value=1e6, allow_nan=False, allow_infinity=False),
                attributes=st.fixed_dictionaries({
                    "category": st.sampled_from(["saas", "ecommerce", "fintech", "healthtech", "edtech"])
                }),
            ),
            min_size=1, max_size=20,
        ),
    )
    @settings(max_examples=50)
    def test_matching_scores_in_unit_interval(self, buyers, sellers):
        """For any valid inputs, all match scores are in [0, 1]."""
        matcher = BuyerSellerMatcher()
        matches = matcher.match(buyers, sellers)
        for m in matches:
            assert 0.0 <= m.score <= 1.0, f"Score {m.score} outside [0, 1]"

    @given(
        buyers=st.lists(
            st.builds(
                Buyer,
                id=st.text(min_size=1, max_size=10),
                budget=st.floats(min_value=1.0, max_value=1e6, allow_nan=False, allow_infinity=False),
                preferences=st.fixed_dictionaries({
                    "category": st.sampled_from(["saas", "ecommerce", "fintech"])
                }),
            ),
            min_size=1, max_size=15,
        ),
        sellers=st.lists(
            st.builds(
                Seller,
                id=st.text(min_size=1, max_size=10),
                asking_price=st.floats(min_value=1.0, max_value=1e6, allow_nan=False, allow_infinity=False),
                attributes=st.fixed_dictionaries({
                    "category": st.sampled_from(["saas", "ecommerce", "fintech"])
                }),
            ),
            min_size=1, max_size=15,
        ),
    )
    @settings(max_examples=50)
    def test_each_buyer_matched_at_most_once(self, buyers, sellers):
        """Each buyer appears in at most one match."""
        matcher = BuyerSellerMatcher()
        matches = matcher.match(buyers, sellers)
        buyer_ids = [m.buyer_id for m in matches]
        assert len(buyer_ids) == len(set(buyer_ids)), "Duplicate buyer in matches"

    @given(
        buyers=st.lists(
            st.builds(
                Buyer,
                id=st.text(min_size=1, max_size=10),
                budget=st.floats(min_value=1.0, max_value=1e6, allow_nan=False, allow_infinity=False),
                preferences=st.fixed_dictionaries({
                    "category": st.sampled_from(["saas", "ecommerce", "fintech"])
                }),
            ),
            min_size=1, max_size=15,
        ),
        sellers=st.lists(
            st.builds(
                Seller,
                id=st.text(min_size=1, max_size=10),
                asking_price=st.floats(min_value=1.0, max_value=1e6, allow_nan=False, allow_infinity=False),
                attributes=st.fixed_dictionaries({
                    "category": st.sampled_from(["saas", "ecommerce", "fintech"])
                }),
            ),
            min_size=1, max_size=15,
        ),
    )
    @settings(max_examples=50)
    def test_each_seller_matched_at_most_once(self, buyers, sellers):
        """Each seller appears in at most one match."""
        matcher = BuyerSellerMatcher()
        matches = matcher.match(buyers, sellers)
        seller_ids = [m.seller_id for m in matches]
        assert len(seller_ids) == len(set(seller_ids)), "Duplicate seller in matches"


# ---------------------------------------------------------------------------
# Valuation properties
# ---------------------------------------------------------------------------

class TestValuationProperties:
    """Property-based tests for ValuationEngine."""

    @given(
        free_cash_flow=st.floats(min_value=1.0, max_value=1e9, allow_nan=False, allow_infinity=False),
        growth_rate=st.floats(min_value=0.0, max_value=0.5, allow_nan=False, allow_infinity=False),
        discount_rate=st.floats(min_value=0.01, max_value=0.5, allow_nan=False, allow_infinity=False),
        terminal_growth=st.floats(min_value=0.0, max_value=0.05, allow_nan=False, allow_infinity=False),
        years=st.integers(min_value=1, max_value=30),
    )
    @settings(max_examples=50)
    def test_dcf_value_positive_for_positive_inputs(
        self, free_cash_flow, growth_rate, discount_rate, terminal_growth, years
    ):
        """DCF value > 0 for any positive FCF and valid parameters."""
        if abs(discount_rate - terminal_growth) < 1e-10:
            return  # Skip the degenerate case that raises DivisionByZeroError
        engine = ValuationEngine()
        result = engine.dcf_valuation(
            free_cash_flow=free_cash_flow,
            growth_rate=growth_rate,
            discount_rate=discount_rate,
            terminal_growth=terminal_growth,
            years=years,
        )
        assert result.value > 0, f"DCF value {result.value} should be > 0"

    @given(
        free_cash_flow=st.floats(min_value=1.0, max_value=1e9, allow_nan=False, allow_infinity=False),
        revenue=st.floats(min_value=1.0, max_value=1e9, allow_nan=False, allow_infinity=False),
        growth_rate=st.floats(min_value=0.0, max_value=0.5, allow_nan=False, allow_infinity=False),
        discount_rate=st.floats(min_value=0.01, max_value=0.5, allow_nan=False, allow_infinity=False),
        terminal_growth=st.floats(min_value=0.0, max_value=0.05, allow_nan=False, allow_infinity=False),
        revenue_multiple=st.floats(min_value=0.1, max_value=50.0, allow_nan=False, allow_infinity=False),
        years=st.integers(min_value=1, max_value=30),
    )
    @settings(max_examples=50)
    def test_ensemble_confidence_in_unit_interval(
        self, free_cash_flow, revenue, growth_rate, discount_rate,
        terminal_growth, revenue_multiple, years
    ):
        """Ensemble confidence is always in [0, 1]."""
        if abs(discount_rate - terminal_growth) < 1e-10:
            return
        engine = ValuationEngine()
        result = engine.ensemble_valuation(
            free_cash_flow=free_cash_flow,
            revenue=revenue,
            growth_rate=growth_rate,
            discount_rate=discount_rate,
            terminal_growth=terminal_growth,
            revenue_multiple=revenue_multiple,
            years=years,
        )
        assert 0.0 <= result.confidence <= 1.0, (
            f"Confidence {result.confidence} outside [0, 1]"
        )


# ---------------------------------------------------------------------------
# Fraud detection properties
# ---------------------------------------------------------------------------

class TestFraudProperties:
    """Property-based tests for FraudDetector."""

    @given(
        signals=st.lists(
            st.builds(
                FraudSignal,
                name=st.sampled_from([
                    "identity_verified", "financial_consistency",
                    "traffic_authenticity", "custom_signal",
                ]),
                value=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
            ),
            min_size=1, max_size=10,
        ),
    )
    @settings(max_examples=50)
    def test_fraud_score_in_unit_interval(self, signals):
        """Fraud score is always in [0, 1] for valid signals."""
        detector = FraudDetector()
        result = detector.score(signals)
        assert 0.0 <= result.score <= 1.0, f"Score {result.score} outside [0, 1]"

    @given(
        signals=st.lists(
            st.builds(
                FraudSignal,
                name=st.sampled_from([
                    "identity_verified", "financial_consistency",
                    "traffic_authenticity", "custom_signal",
                ]),
                value=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
            ),
            min_size=1, max_size=10,
        ),
    )
    @settings(max_examples=50)
    def test_risk_level_in_valid_set(self, signals):
        """Risk level is always one of {low, medium, high}."""
        detector = FraudDetector()
        result = detector.score(signals)
        assert result.risk_level in {"low", "medium", "high"}, (
            f"Invalid risk_level: {result.risk_level}"
        )


# ---------------------------------------------------------------------------
# Portfolio properties
# ---------------------------------------------------------------------------

class TestPortfolioProperties:
    """Property-based tests for PortfolioOptimizer."""

    @given(
        assets=st.lists(
            st.builds(
                Asset,
                id=st.text(min_size=1, max_size=10),
                cost=st.floats(min_value=0.0, max_value=1e6, allow_nan=False, allow_infinity=False),
                expected_return=st.floats(min_value=0.0, max_value=1e6, allow_nan=False, allow_infinity=False),
                risk=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
                sector=st.sampled_from(["tech", "health", "finance", "retail"]),
            ),
            min_size=1, max_size=20,
        ),
        budget=st.floats(min_value=1.0, max_value=1e7, allow_nan=False, allow_infinity=False),
        max_assets=st.integers(min_value=1, max_value=10),
        risk_tolerance=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=50)
    def test_total_cost_within_budget(self, assets, budget, max_assets, risk_tolerance):
        """Total cost of selected assets never exceeds budget."""
        optimizer = PortfolioOptimizer(budget=budget, max_assets=max_assets)
        portfolio = optimizer.optimize(assets, risk_tolerance=risk_tolerance)
        total_cost = sum(a.cost for a in portfolio.assets)
        assert total_cost <= budget + 1e-9, (
            f"Total cost {total_cost} exceeds budget {budget}"
        )

    @given(
        assets=st.lists(
            st.builds(
                Asset,
                id=st.text(min_size=1, max_size=10),
                cost=st.floats(min_value=0.0, max_value=1e6, allow_nan=False, allow_infinity=False),
                expected_return=st.floats(min_value=0.0, max_value=1e6, allow_nan=False, allow_infinity=False),
                risk=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
                sector=st.sampled_from(["tech", "health", "finance"]),
            ),
            min_size=1, max_size=20,
        ),
        budget=st.floats(min_value=1.0, max_value=1e7, allow_nan=False, allow_infinity=False),
        max_assets=st.integers(min_value=1, max_value=10),
        risk_tolerance=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=50)
    def test_asset_count_within_limit(self, assets, budget, max_assets, risk_tolerance):
        """Number of selected assets never exceeds max_assets."""
        optimizer = PortfolioOptimizer(budget=budget, max_assets=max_assets)
        portfolio = optimizer.optimize(assets, risk_tolerance=risk_tolerance)
        assert len(portfolio.assets) <= max_assets, (
            f"Selected {len(portfolio.assets)} assets, max allowed {max_assets}"
        )


# ---------------------------------------------------------------------------
# Pricing properties
# ---------------------------------------------------------------------------

class TestPricingProperties:
    """Property-based tests for PricingEngine."""

    @given(
        base_value=st.floats(min_value=1.0, max_value=1e9, allow_nan=False, allow_infinity=False),
        demand_level=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        competition_level=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        market_condition=st.sampled_from(["bull", "bear", "normal"]),
    )
    @settings(max_examples=50)
    def test_recommended_price_within_bounds(
        self, base_value, demand_level, competition_level, market_condition
    ):
        """floor <= recommended_price <= ceiling for any valid inputs."""
        engine = PricingEngine()
        result = engine.recommend_price(
            base_value=base_value,
            demand_level=demand_level,
            competition_level=competition_level,
            market_condition=market_condition,
        )
        assert result.floor_price <= result.recommended_price <= result.ceiling_price, (
            f"Recommended {result.recommended_price} not in "
            f"[{result.floor_price}, {result.ceiling_price}]"
        )


# ---------------------------------------------------------------------------
# Entity resolution properties
# ---------------------------------------------------------------------------

class TestEntityResolutionProperties:
    """Property-based tests for EntityResolver."""

    @given(
        entities=st.lists(
            st.fixed_dictionaries({
                "name": st.text(min_size=1, max_size=30),
                "domain": st.sampled_from(["example.com", "test.org", "foo.net", ""]),
            }),
            min_size=1, max_size=30,
        ),
        threshold=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=50)
    def test_clusters_non_overlapping(self, entities, threshold):
        """No entity appears in more than one cluster."""
        resolver = EntityResolver(threshold=threshold)
        clusters = resolver.resolve(entities)
        seen = set()
        for cluster in clusters:
            for entity in cluster.entities:
                key = id(entity)
                assert key not in seen, "Entity appears in multiple clusters"
                seen.add(key)

    @given(
        entities=st.lists(
            st.fixed_dictionaries({
                "name": st.text(min_size=1, max_size=30),
                "domain": st.sampled_from(["example.com", "test.org", ""]),
            }),
            min_size=1, max_size=30,
        ),
        threshold=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=50)
    def test_all_entities_assigned(self, entities, threshold):
        """Every input entity appears in exactly one cluster."""
        resolver = EntityResolver(threshold=threshold)
        clusters = resolver.resolve(entities)
        total_in_clusters = sum(len(c.entities) for c in clusters)
        assert total_in_clusters == len(entities), (
            f"Expected {len(entities)} entities in clusters, got {total_in_clusters}"
        )


# ---------------------------------------------------------------------------
# Ranking properties
# ---------------------------------------------------------------------------

class TestRankingProperties:
    """Property-based tests for SearchRanker."""

    @given(
        listings=st.lists(
            st.builds(
                Listing,
                id=st.text(min_size=1, max_size=10),
                title=st.text(min_size=1, max_size=50),
                relevance=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
                category=st.sampled_from(["saas", "ecommerce", "fintech", "healthtech"]),
            ),
            min_size=1, max_size=30,
        ),
    )
    @settings(max_examples=50)
    def test_ranking_scores_finite(self, listings):
        """All ranking scores are finite (not NaN or Inf)."""
        ranker = SearchRanker()
        results = ranker.rank("test query", listings)  # type: ignore[attr-defined]
        for r in results:
            assert math.isfinite(r.score), f"Score {r.score} is not finite"

    @given(
        listings=st.lists(
            st.builds(
                Listing,
                id=st.text(min_size=1, max_size=10),
                title=st.text(min_size=1, max_size=50),
                relevance=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
                category=st.sampled_from(["saas", "ecommerce", "fintech"]),
            ),
            min_size=1, max_size=30,
        ),
    )
    @settings(max_examples=50)
    def test_no_duplicate_ids_in_output(self, listings):
        """Output contains no duplicate listing IDs."""
        ranker = SearchRanker()
        results = ranker.rank("test query", listings)
        ids = [r.id for r in results]
        assert len(ids) == len(set(ids)), "Duplicate IDs in ranking output"


# ---------------------------------------------------------------------------
# Evolution properties
# ---------------------------------------------------------------------------

class TestEvolutionProperties:
    """Property-based tests for EvolutionEngine."""

    @given(
        population_size=st.integers(min_value=5, max_value=30),
        generations=st.integers(min_value=5, max_value=30),
        mutation_rate=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        gene_low=st.floats(min_value=-100.0, max_value=0.0, allow_nan=False, allow_infinity=False),
        gene_high=st.floats(min_value=0.1, max_value=100.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=30)
    def test_best_fitness_at_least_worst_fitness(
        self, population_size, generations, mutation_rate, gene_low, gene_high
    ):
        """best_fitness >= worst_fitness for any fitness function and valid params."""
        engine = EvolutionEngine(
            population_size=population_size,
            generations=generations,
            mutation_rate=mutation_rate,
        )
        # Use a simple quadratic fitness function
        result = engine.evolve(
            fitness_fn=lambda x: -(x - 10) ** 2,
            gene_range=(gene_low, gene_high),
        )
        assert result.best_fitness >= result.worst_fitness, (
            f"best_fitness {result.best_fitness} < worst_fitness {result.worst_fitness}"
        )

    @given(
        population_size=st.integers(min_value=5, max_value=20),
        generations=st.integers(min_value=5, max_value=20),
        mutation_rate=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=30)
    def test_evolution_result_population_size_matches(
        self, population_size, generations, mutation_rate
    ):
        """Result population_size matches the engine configuration."""
        engine = EvolutionEngine(
            population_size=population_size,
            generations=generations,
            mutation_rate=mutation_rate,
        )
        result = engine.evolve(
            fitness_fn=lambda x: x ** 2,
            gene_range=(0.0, 100.0),
        )
        assert result.population_size == population_size
