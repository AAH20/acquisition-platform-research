"""Comprehensive benchmark suite for all acquisition platform modules.

Uses pytest-benchmark to measure performance across all engines.
Run with: pytest tests/test_benchmarks.py -v --benchmark-only
"""
from __future__ import annotations

import random

import pytest

from acquisition_platform.matching import Buyer, Seller, BuyerSellerMatcher
from acquisition_platform.valuation import ValuationEngine
from acquisition_platform.fraud_detection import FraudDetector, FraudSignal
from acquisition_platform.portfolio_optimizer import Asset, PortfolioOptimizer
from acquisition_platform.dynamic_pricing import PricingEngine
from acquisition_platform.entity_resolution import EntityResolver
from acquisition_platform.search_ranking import Listing, SearchRanker
from acquisition_platform.evolution import EvolutionEngine
from acquisition_platform.auction_design import Bid, AuctionConfig, AuctionDesigner
from acquisition_platform.due_diligence import (
    DueDiligenceTask,
    Reviewer,
    DueDiligenceScheduler,
)
from acquisition_platform.cross_border import (
    CrossBorderAnalyzer,
    CrossBorderDeal,
)
from acquisition_platform.recommendation import (
    UserProfile,
    ItemProfile,
    RecommendationEngine,
)
from acquisition_platform.orchestrator import AcquisitionPipeline, PipelineConfig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_buyers(n: int, seed: int = 42) -> list[Buyer]:
    """Generate n buyers with varied budgets and preferences."""
    rng = random.Random(seed)
    categories = ["saas", "fintech", "ecommerce", "healthtech", "edtech"]
    return [
        Buyer(
            id=f"b{i}",
            budget=rng.uniform(50_000, 500_000),
            preferences={"category": rng.choice(categories)},
        )
        for i in range(n)
    ]


def _make_sellers(n: int, seed: int = 42) -> list[Seller]:
    """Generate n sellers with varied asking prices and attributes."""
    rng = random.Random(seed)
    categories = ["saas", "fintech", "ecommerce", "healthtech", "edtech"]
    return [
        Seller(
            id=f"s{i}",
            asking_price=rng.uniform(30_000, 400_000),
            attributes={
                "category": rng.choice(categories),
                "expected_return": rng.uniform(0.05, 0.25),
            },
        )
        for i in range(n)
    ]


def _make_signals(n: int, seed: int = 42) -> list[list[FraudSignal]]:
    """Generate n sets of fraud signals."""
    rng = random.Random(seed)
    signal_names = ["identity_verified", "financial_consistency", "traffic_authenticity"]
    return [
        [
            FraudSignal(name=name, value=rng.random())
            for name in signal_names
        ]
        for _ in range(n)
    ]


def _make_assets(n: int, seed: int = 42) -> list[Asset]:
    """Generate n assets for portfolio optimization."""
    rng = random.Random(seed)
    sectors = ["saas", "fintech", "ecommerce", "healthtech", "edtech"]
    return [
        Asset(
            id=f"a{i}",
            cost=rng.uniform(10_000, 200_000),
            expected_return=rng.uniform(0.05, 0.30),
            risk=rng.uniform(0.1, 0.5),
            sector=rng.choice(sectors),
        )
        for i in range(n)
    ]


def _make_listings(n: int, seed: int = 42) -> list[Listing]:
    """Generate n listings for search ranking."""
    rng = random.Random(seed)
    categories = ["saas", "fintech", "ecommerce", "healthtech", "edtech"]
    return [
        Listing(
            id=f"l{i}",
            title=f"Listing {i}",
            relevance=rng.random(),
            category=rng.choice(categories),
        )
        for i in range(n)
    ]


def _make_bids(n: int, seed: int = 42) -> list[Bid]:
    """Generate n bids for auction design."""
    rng = random.Random(seed)
    return [
        Bid(bidder_id=f"bidder_{i}", amount=rng.uniform(100, 10_000))
        for i in range(n)
    ]


def _make_dd_tasks(n: int, seed: int = 42) -> list[DueDiligenceTask]:
    """Generate n due diligence tasks with feasible scheduling constraints."""
    rng = random.Random(seed)
    expertise_domains = ["finance", "legal", "technical", "operations", "hr"]
    tasks = []
    for i in range(n):
        deps = []
        # Limit dependencies to ensure schedulability
        if i > 0 and rng.random() < 0.15:
            deps.append(f"t{rng.randint(0, i - 1)}")
        tasks.append(
            DueDiligenceTask(
                id=f"t{i}",
                name=f"Task {i}",
                duration=rng.uniform(1.0, 4.0),
                expertise=rng.choice(expertise_domains),
                dependencies=deps,
            )
        )
    return tasks


def _make_reviewers(n: int, seed: int = 42) -> list[Reviewer]:
    """Generate n reviewers with varied expertise and sufficient availability."""
    rng = random.Random(seed)
    expertise_domains = ["finance", "legal", "technical", "operations", "hr"]
    reviewers = []
    for i in range(n):
        # Ensure each reviewer covers at least 2 domains and has ample availability
        expertise = rng.sample(expertise_domains, k=rng.randint(2, 4))
        reviewers.append(
            Reviewer(
                id=f"r{i}",
                name=f"Reviewer {i}",
                expertise=expertise,
                availability=rng.uniform(100.0, 200.0),
            )
        )
    return reviewers


def _make_deals(n: int) -> list[CrossBorderDeal]:
    """Generate n cross-border deals for benchmarking."""
    acquirers = ["US", "DE", "UK", "FR", "JP", "CN", "BR", "IN", "AU", "CA"]
    targets = ["DE", "US", "FR", "UK", "CN", "JP", "IN", "BR", "CA", "AU"]
    currencies = ["EUR", "USD", "GBP", "EUR", "JPY", "CNY", "BRL", "INR", "AUD", "CAD"]
    industries = ["technology", "healthcare", "finance", "energy", "consumer"]
    return [
        CrossBorderDeal(
            acquirer_country=acquirers[i],
            target_country=targets[i],
            deal_value=100_000_000,
            currency=currencies[i],
            industry=industries[i % len(industries)],
        )
        for i in range(n)
    ]


def _make_items(n: int, seed: int = 42) -> list[ItemProfile]:
    """Generate n items for recommendation engine."""
    rng = random.Random(seed)
    topics = ["ml", "web", "data", "cloud", "security"]
    difficulties = ["beginner", "intermediate", "advanced"]
    categories = ["saas", "ecommerce", "content", "service", "platform"]
    return [
        ItemProfile(
            item_id=f"item_{i}",
            attributes={
                "topic": rng.choice(topics),
                "difficulty": rng.choice(difficulties),
            },
            category=rng.choice(categories),
        )
        for i in range(n)
    ]


def _make_users(n: int, seed: int = 42) -> list[UserProfile]:
    """Generate n users for recommendation engine."""
    rng = random.Random(seed)
    topics = ["ml", "web", "data", "cloud", "security"]
    difficulties = ["beginner", "intermediate", "advanced"]
    return [
        UserProfile(
            user_id=f"user_{i}",
            preferences={
                "topic": rng.choice(topics),
                "difficulty": rng.choice(difficulties),
            },
            history=[f"item_{rng.randint(0, 99)}" for _ in range(5)],
        )
        for i in range(n)
    ]


def _make_entities_for_pipeline(n_buyers: int, n_sellers: int) -> list[dict]:
    """Generate entity dicts for the full pipeline."""
    rng = random.Random(42)
    categories = ["saas", "fintech", "ecommerce", "healthtech", "edtech"]
    entities = []
    for i in range(n_buyers):
        entities.append({
            "id": f"b{i}",
            "budget": rng.uniform(50_000, 500_000),
            "preferences": {"category": rng.choice(categories)},
        })
    for i in range(n_sellers):
        entities.append({
            "id": f"s{i}",
            "asking_price": rng.uniform(30_000, 400_000),
            "attributes": {
                "category": rng.choice(categories),
                "expected_return": rng.uniform(0.05, 0.25),
            },
        })
    return entities


# ---------------------------------------------------------------------------
# Benchmark: Matching
# ---------------------------------------------------------------------------

class TestBenchmarkMatching:
    """Benchmarks for buyer-seller matching engine."""

    def test_benchmark_matching_100(self, benchmark):
        """Benchmark matching with 100 buyers x 100 sellers."""
        matcher = BuyerSellerMatcher()
        buyers = _make_buyers(100)
        sellers = _make_sellers(100)
        result = benchmark(matcher.match, buyers, sellers)
        assert isinstance(result, list)

    def test_benchmark_matching_1000(self, benchmark):
        """Benchmark matching with 1000 buyers x 1000 sellers."""
        matcher = BuyerSellerMatcher()
        buyers = _make_buyers(1000)
        sellers = _make_sellers(1000)
        result = benchmark(matcher.match, buyers, sellers)
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# Benchmark: Valuation
# ---------------------------------------------------------------------------

class TestBenchmarkValuation:
    """Benchmarks for DCF valuation engine."""

    def test_benchmark_valuation_1000(self, benchmark):
        """Benchmark 1000 DCF calculations."""
        engine = ValuationEngine()

        def run_valuations():
            results = []
            for i in range(1000):
                result = engine.dcf_valuation(
                    free_cash_flow=100_000 + i * 100,
                    growth_rate=0.05,
                    discount_rate=0.10,
                    terminal_growth=0.02,
                    years=5,
                )
                results.append(result)
            return results

        results = benchmark(run_valuations)
        assert len(results) == 1000


# ---------------------------------------------------------------------------
# Benchmark: Fraud Detection
# ---------------------------------------------------------------------------

class TestBenchmarkFraudDetection:
    """Benchmarks for fraud detection engine."""

    def test_benchmark_fraud_1000(self, benchmark):
        """Benchmark 1000 fraud score calculations."""
        detector = FraudDetector()
        all_signals = _make_signals(1000)

        def run_fraud_scores():
            results = []
            for signals in all_signals:
                result = detector.score(signals)
                results.append(result)
            return results

        results = benchmark(run_fraud_scores)
        assert len(results) == 1000


# ---------------------------------------------------------------------------
# Benchmark: Portfolio Optimization
# ---------------------------------------------------------------------------

class TestBenchmarkPortfolio:
    """Benchmarks for portfolio optimization engine."""

    def test_benchmark_portfolio_100(self, benchmark):
        """Benchmark portfolio optimization with 100 assets."""
        assets = _make_assets(100)
        optimizer = PortfolioOptimizer(budget=1_000_000, max_assets=10)
        result = benchmark(optimizer.optimize, assets, 0.5)
        assert result is not None


# ---------------------------------------------------------------------------
# Benchmark: Dynamic Pricing
# ---------------------------------------------------------------------------

class TestBenchmarkPricing:
    """Benchmarks for dynamic pricing engine."""

    def test_benchmark_pricing_10000(self, benchmark):
        """Benchmark 10000 price recommendations."""
        engine = PricingEngine()

        def run_pricing():
            results = []
            for i in range(10000):
                result = engine.recommend_price(
                    base_value=100_000 + i * 10,
                    demand_level=(i % 100) / 100.0,
                    competition_level=((i * 7) % 100) / 100.0,
                    market_condition=["bull", "bear", "normal"][i % 3],
                )
                results.append(result)
            return results

        results = benchmark(run_pricing)
        assert len(results) == 10000


# ---------------------------------------------------------------------------
# Benchmark: Entity Resolution
# ---------------------------------------------------------------------------

class TestBenchmarkEntityResolution:
    """Benchmarks for entity resolution engine."""

    def test_benchmark_entity_resolution_100(self, benchmark):
        """Benchmark entity resolution with 100 entities."""
        resolver = EntityResolver(threshold=0.85)
        entities = [
            {"id": f"e{i}", "name": f"Company {i % 20}", "domain": f"domain{i % 5}.com"}
            for i in range(100)
        ]
        result = benchmark(resolver.resolve, entities)
        assert isinstance(result, list)

    def test_benchmark_entity_resolution_1000(self, benchmark):
        """Benchmark entity resolution with 1000 entities."""
        resolver = EntityResolver(threshold=0.85)
        entities = [
            {"id": f"e{i}", "name": f"Company {i % 100}", "domain": f"domain{i % 20}.com"}
            for i in range(1000)
        ]
        result = benchmark(resolver.resolve, entities)
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# Benchmark: Search Ranking
# ---------------------------------------------------------------------------

class TestBenchmarkRanking:
    """Benchmarks for search ranking engine."""

    def test_benchmark_ranking_1000(self, benchmark):
        """Benchmark ranking with 1000 listings."""
        ranker = SearchRanker()
        listings = _make_listings(1000)
        result = benchmark(ranker.rank, "acquisition", listings)
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# Benchmark: Evolution
# ---------------------------------------------------------------------------

class TestBenchmarkEvolution:
    """Benchmarks for genetic algorithm evolution engine."""

    def test_benchmark_evolution_100(self, benchmark):
        """Benchmark evolution with 100 population, 50 generations."""
        engine = EvolutionEngine(population_size=100, generations=50)
        result = benchmark(engine.evolve, lambda x: x ** 2, (0.0, 100.0))
        assert result is not None


# ---------------------------------------------------------------------------
# Benchmark: Auction Design
# ---------------------------------------------------------------------------

class TestBenchmarkAuction:
    """Benchmarks for auction design engine."""

    def test_benchmark_auction_100(self, benchmark):
        """Benchmark auction with 100 bids."""
        designer = AuctionDesigner()
        bids = _make_bids(100)
        config = AuctionConfig(format="vickrey", reserve_price=100.0, min_increment=1.0)
        result = benchmark(designer.design_auction, bids, config)
        assert result is not None


# ---------------------------------------------------------------------------
# Benchmark: Due Diligence
# ---------------------------------------------------------------------------

class TestBenchmarkDueDiligence:
    """Benchmarks for due diligence scheduling engine."""

    def test_benchmark_due_diligence_50(self, benchmark):
        """Benchmark due diligence with 50 tasks and 10 reviewers."""
        scheduler = DueDiligenceScheduler()
        tasks = _make_dd_tasks(50)
        reviewers = _make_reviewers(10)
        result = benchmark(scheduler.schedule, tasks, reviewers)
        assert result is not None


# ---------------------------------------------------------------------------
# Benchmark: Cross-Border
# ---------------------------------------------------------------------------

class TestBenchmarkCrossBorder:
    """Benchmarks for cross-border deal analysis engine."""

    def test_benchmark_cross_border_10(self, benchmark):
        """Benchmark cross-border analysis with 10 deals."""
        analyzer = CrossBorderAnalyzer()
        deals = _make_deals(10)
        result = benchmark(analyzer.generate_cross_border_report, deals[0])
        assert result is not None


# ---------------------------------------------------------------------------
# Benchmark: Recommendation
# ---------------------------------------------------------------------------

class TestBenchmarkRecommendation:
    """Benchmarks for recommendation engine."""

    def test_benchmark_recommendation_100(self, benchmark):
        """Benchmark recommendation with 100 items and 10 users."""
        engine = RecommendationEngine()
        items = _make_items(100)
        users = _make_users(10)

        def run_recommendations():
            results = []
            for user in users:
                result = engine.recommend(user, items, k=10)
                results.append(result)
            return results

        results = benchmark(run_recommendations)
        assert len(results) == 10


# ---------------------------------------------------------------------------
# Benchmark: Full Pipeline (Orchestrator)
# ---------------------------------------------------------------------------

class TestBenchmarkOrchestrator:
    """Benchmarks for the full acquisition pipeline."""

    def test_benchmark_orchestrator_full(self, benchmark):
        """Benchmark the full pipeline with all stages enabled."""
        pipeline = AcquisitionPipeline()
        config = PipelineConfig(
            enable_matching=True,
            enable_valuation=True,
            enable_fraud=True,
            enable_portfolio=True,
            enable_pricing=True,
            enable_ranking=True,
            enable_evolution=True,
        )
        entities = _make_entities_for_pipeline(50, 50)
        result = benchmark(pipeline.run, entities, config)
        assert result is not None
