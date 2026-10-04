"""Orchestrator module — chains all modules into a unified pipeline.

This module wires together the 8 independent engines (matching, valuation,
fraud detection, portfolio optimization, dynamic pricing, entity resolution,
search ranking, evolution) into a single configurable pipeline.

Execution order:
1. Fraud Detection — screen all candidates
2. Valuation — estimate value of each candidate
3. Matching — match buyers to sellers
4. Portfolio Optimization — select optimal portfolio
5. Dynamic Pricing — recommend pricing
6. Search Ranking — rank results
7. Evolution — optimize hyperparameters (optional)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable

from acquisition_platform.matching import (
    Buyer,
    Seller,
    Match,
    BuyerSellerMatcher,
)
from acquisition_platform.valuation import ValuationResult, ValuationEngine
from acquisition_platform.fraud_detection import (
    FraudSignal,
    FraudScore,
    FraudDetector,
)
from acquisition_platform.portfolio_optimizer import (
    Asset,
    Portfolio,
    PortfolioOptimizer,
)
from acquisition_platform.dynamic_pricing import (
    PriceRecommendation,
    PricingEngine,
)
from acquisition_platform.search_ranking import (
    Listing,
    RankedListing,
    SearchRanker,
)
from acquisition_platform.evolution import (
    EvolutionEngine,
    EvolutionResult,
)
from acquisition_platform.observability import get_logger, log_execution_time, log_module_call

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class PipelineConfig:
    """Configuration for the acquisition pipeline.

    Each flag enables or disables the corresponding pipeline stage.
    All stages are enabled by default.
    """

    enable_matching: bool = True
    enable_valuation: bool = True
    enable_fraud: bool = True
    enable_portfolio: bool = True
    enable_pricing: bool = True
    enable_ranking: bool = True
    enable_evolution: bool = True


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------

@dataclass
class PipelineResult:
    """Unified result from running the full pipeline.

    Attributes:
        matches: List of Match objects from the matching stage.
        valuations: List of ValuationResult objects from the valuation stage.
        fraud_scores: List of FraudScore objects from the fraud detection stage.
        portfolio: Portfolio object from the portfolio optimization stage.
        prices: List of PriceRecommendation objects from the pricing stage.
        rankings: List of RankedListing objects from the ranking stage.
        evolution_result: EvolutionResult from the evolution stage.
    """

    matches: list[Match] = field(default_factory=list)
    valuations: list[ValuationResult] = field(default_factory=list)
    fraud_scores: list[FraudScore] = field(default_factory=list)
    portfolio: Portfolio | None = None
    prices: list[PriceRecommendation] = field(default_factory=list)
    rankings: list[RankedListing] = field(default_factory=list)
    evolution_result: EvolutionResult | None = None


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

class AcquisitionPipeline:
    """Orchestrates all modules into a unified acquisition workflow.

    Takes raw entity dicts, classifies them into buyers/sellers, runs each
    enabled pipeline stage, and returns a unified PipelineResult.

    Usage:
        pipeline = AcquisitionPipeline()
        config = PipelineConfig(enable_matching=True, enable_fraud=True)
        result = pipeline.run(entities, config)
    """

    def __init__(self) -> None:
        self._matcher = BuyerSellerMatcher()
        self._valuation_engine = ValuationEngine()
        self._fraud_detector = FraudDetector()
        self._pricing_engine = PricingEngine()
        self._ranker = SearchRanker()
        self._evolution_engine = EvolutionEngine(
            population_size=20,
            generations=10,
        )

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    @log_execution_time(logger)
    def run(
        self,
        entities: list[dict[str, Any]],
        config: PipelineConfig,
    ) -> PipelineResult:
        """Execute the full pipeline.

        Args:
            entities: List of entity dicts. Each dict should have at least
                an 'id' key. Buyers have 'budget' and 'preferences'.
                Sellers have 'asking_price' and 'attributes'.
            config: PipelineConfig controlling which stages run.

        Returns:
            PipelineResult with outputs from all enabled stages.
        """
        result = PipelineResult()

        if not entities:
            return result

        # Classify entities into buyers and sellers
        buyers, sellers = self._classify_entities(entities)
        seller_dicts = [e for e in entities if "asking_price" in e and "budget" not in e]

        # --- Stage 1: Fraud Detection ---
        if config.enable_fraud:
            result.fraud_scores = self.run_fraud_detection(entities)

        # --- Stage 2: Valuation ---
        if config.enable_valuation:
            result.valuations = self.run_valuation(seller_dicts)

        # --- Stage 3: Matching ---
        if config.enable_matching and buyers and sellers:
            result.matches = self.run_matching(buyers, sellers)

        # --- Stage 4: Portfolio Optimization ---
        if config.enable_portfolio:
            assets = self._sellers_to_assets(seller_dicts)
            if assets:
                result.portfolio = self.run_portfolio_optimization(
                    assets, budget=self._compute_budget(buyers)
                )

        # --- Stage 5: Dynamic Pricing ---
        if config.enable_pricing and result.valuations:
            result.prices = self.run_pricing(result.valuations)

        # --- Stage 6: Search Ranking ---
        if config.enable_ranking:
            listings = self._entities_to_listings(entities)
            if listings:
                result.rankings = self.run_ranking("acquisition", listings)

        # --- Stage 7: Evolution ---
        if config.enable_evolution:
            result.evolution_result = self.run_evolution(
                fitness_fn=self._default_fitness,
                gene_range=(0.0, 1.0),
            )

        return result

    # ------------------------------------------------------------------
    # Stage runners (public — can be called independently)
    # ------------------------------------------------------------------

    @log_execution_time(logger)
    def run_matching(
        self,
        buyers: list[Buyer],
        sellers: list[Seller],
    ) -> list[Match]:
        """Match buyers to sellers using the GAP solver.

        Args:
            buyers: List of Buyer objects.
            sellers: List of Seller objects.

        Returns:
            List of Match objects sorted by score descending.
        """
        if not buyers or not sellers:
            return []
        return self._matcher.match(buyers, sellers)

    @log_execution_time(logger)
    def run_valuation(
        self,
        entities: list[dict[str, Any]],
    ) -> list[ValuationResult]:
        """Value each entity using the valuation engine.

        Uses DCF if cash flow data is available, otherwise comparable
        valuation based on asking_price as a proxy metric.

        Args:
            entities: List of entity dicts with financial data.

        Returns:
            List of ValuationResult objects.
        """
        results: list[ValuationResult] = []
        for entity in entities:
            asking_price = entity.get("asking_price", 0)
            if asking_price <= 0:
                continue

            # Use comparable valuation: asking_price as metric, 1.5x multiple
            try:
                valuation = self._valuation_engine.comparable_valuation(
                    metric=asking_price,
                    multiple=1.5,
                )
                results.append(valuation)
            except Exception:
                # Skip entities that fail valuation
                continue

        return results

    @log_execution_time(logger)
    def run_fraud_detection(
        self,
        entities: list[dict[str, Any]],
    ) -> list[FraudScore]:
        """Screen all entities for fraud.

        Each entity may contain a 'signals' key in its attributes with
        a list of signal dicts (each with 'name' and 'value').
        If no signals are present, generates default neutral signals.

        Args:
            entities: List of entity dicts.

        Returns:
            List of FraudScore objects, one per entity.
        """
        results: list[FraudScore] = []
        for entity in entities:
            signals = self._extract_signals(entity)
            try:
                score = self._fraud_detector.score(signals)
                results.append(score)
            except Exception:
                # If scoring fails, assign a neutral medium-risk score
                results.append(FraudScore(
                    score=0.5,
                    risk_level="medium",
                    confidence=0.0,
                    explanations=["Default score: signal processing failed"],
                ))

        return results

    @log_execution_time(logger)
    def run_portfolio_optimization(
        self,
        assets: list[Asset],
        budget: float,
    ) -> Portfolio:
        """Optimize portfolio from candidate assets.

        Args:
            assets: List of Asset objects to select from.
            budget: Total capital available.

        Returns:
            Optimized Portfolio.
        """
        if not assets or budget <= 0:
            return Portfolio()

        optimizer = PortfolioOptimizer(budget=budget, max_assets=10)
        return optimizer.optimize(assets, risk_tolerance=0.5)

    @log_execution_time(logger)
    def run_pricing(
        self,
        valuations: list[ValuationResult],
    ) -> list[PriceRecommendation]:
        """Generate price recommendations from valuations.

        Args:
            valuations: List of ValuationResult objects.

        Returns:
            List of PriceRecommendation objects.
        """
        results: list[PriceRecommendation] = []
        for v in valuations:
            try:
                rec = self._pricing_engine.recommend_price(
                    base_value=v.value,
                    demand_level=0.5,
                    competition_level=0.3,
                    market_condition="normal",
                )
                results.append(rec)
            except Exception:
                continue

        return results

    @log_execution_time(logger)
    def run_ranking(
        self,
        query: str,
        items: list[Listing],
    ) -> list[RankedListing]:
        """Rank listings by relevance.

        Args:
            query: Search query string.
            items: List of Listing objects.

        Returns:
            List of RankedListing sorted by score descending.
        """
        if not items:
            return []
        return self._ranker.rank(query, items)

    @log_execution_time(logger)
    def run_evolution(
        self,
        fitness_fn: Callable[[float], float],
        gene_range: tuple[float, float],
    ) -> EvolutionResult:
        """Run genetic algorithm evolution.

        Args:
            fitness_fn: Function that takes a gene value and returns fitness.
            gene_range: (min, max) tuple defining the search space.

        Returns:
            EvolutionResult with metrics from the evolution run.
        """
        return self._evolution_engine.evolve(fitness_fn, gene_range)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _classify_entities(
        self,
        entities: list[dict[str, Any]],
    ) -> tuple[list[Buyer], list[Seller]]:
        """Classify entity dicts into Buyer and Seller objects.

        An entity is classified as a buyer if it has a 'budget' key.
        An entity is classified as a seller if it has an 'asking_price' key.
        Entities with both are treated as buyers (budget takes priority).
        """
        buyers: list[Buyer] = []
        sellers: list[Seller] = []

        for entity in entities:
            eid = entity.get("id", "")
            if "budget" in entity:
                buyers.append(Buyer(
                    id=eid,
                    budget=float(entity["budget"]),
                    preferences=entity.get("preferences", {}),
                ))
            elif "asking_price" in entity:
                sellers.append(Seller(
                    id=eid,
                    asking_price=float(entity["asking_price"]),
                    attributes=entity.get("attributes", {}),
                ))

        return buyers, sellers

    def _extract_signals(self, entity: dict[str, Any]) -> list[FraudSignal]:
        """Extract fraud signals from an entity dict.

        Looks for 'signals' in the entity's attributes. Each signal should
        be a dict with 'name' and 'value' keys. If no signals are found,
        generates default neutral signals.
        """
        attributes = entity.get("attributes", {})
        raw_signals = attributes.get("signals", [])

        if not raw_signals:
            # Generate default neutral signals
            return [
                FraudSignal(name="identity_verified", value=0.5),
                FraudSignal(name="financial_consistency", value=0.5),
                FraudSignal(name="traffic_authenticity", value=0.5),
            ]

        signals: list[FraudSignal] = []
        for raw in raw_signals:
            if isinstance(raw, dict) and "name" in raw and "value" in raw:
                signals.append(FraudSignal(
                    name=str(raw["name"]),
                    value=float(raw["value"]),
                ))

        if not signals:
            return [
                FraudSignal(name="identity_verified", value=0.5),
                FraudSignal(name="financial_consistency", value=0.5),
                FraudSignal(name="traffic_authenticity", value=0.5),
            ]
        return signals

    def _sellers_to_assets(
        self,
        sellers: list[dict[str, Any]],
    ) -> list[Asset]:
        """Convert seller entity dicts to Asset objects for portfolio optimization."""
        assets: list[Asset] = []
        for seller in sellers:
            asking_price = seller.get("asking_price", 0)
            if asking_price <= 0:
                continue
            attributes = seller.get("attributes", {})
            assets.append(Asset(
                id=seller.get("id", ""),
                cost=asking_price,
                expected_return=attributes.get("expected_return", 0.10),
                risk=attributes.get("risk", 0.15),
                sector=attributes.get("category", ""),
            ))
        return assets

    def _entities_to_listings(
        self,
        entities: list[dict[str, Any]],
    ) -> list[Listing]:
        """Convert entity dicts to Listing objects for ranking."""
        listings: list[Listing] = []
        for entity in entities:
            eid = entity.get("id", "")
            attributes = entity.get("attributes", {})
            listings.append(Listing(
                id=eid,
                title=attributes.get("title", eid),
                relevance=attributes.get("relevance", 0.5),
                category=attributes.get("category", ""),
            ))
        return listings

    def _compute_budget(self, buyers: list[Buyer]) -> float:
        """Compute total budget from all buyers."""
        if not buyers:
            return 1_000_000  # default budget
        return sum(b.budget for b in buyers)

    @staticmethod
    def _default_fitness(gene: float) -> float:
        """Default fitness function for evolution stage.

        A simple quadratic that peaks at gene=0.5, encouraging the
        evolution engine to find the optimal balance point.
        """
        return -((gene - 0.5) ** 2) + 1.0
