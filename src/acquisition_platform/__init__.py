"""Acquisition Platform Research & Optimization.

Unified optimization engine for acquisition/auction platforms.
Solves NP-hard problems: matching, valuation, fraud detection,
portfolio optimization, dynamic pricing, entity resolution,
search ranking, and due diligence scheduling.
"""

from acquisition_platform.matching import Buyer, Seller, Match, BuyerSellerMatcher
from acquisition_platform.valuation import ValuationResult, ValuationEngine
from acquisition_platform.fraud_detection import FraudSignal, FraudScore, FraudDetector
from acquisition_platform.portfolio_optimizer import Asset, Portfolio, PortfolioOptimizer
from acquisition_platform.dynamic_pricing import PriceRecommendation, PricingEngine
from acquisition_platform.entity_resolution import EntityCluster, EntityResolver, ResolvedEntity
from acquisition_platform.search_ranking import Listing, RankedListing, SearchRanker
from acquisition_platform.evolution import (
    Benchmark,
    EvaluationResult,
    EvolutionEngine,
    EvolutionResult,
)

__all__ = [
    "Asset",
    "Benchmark",
    "Buyer",
    "BuyerSellerMatcher",
    "EntityCluster",
    "EntityResolver",
    "EvaluationResult",
    "EvolutionEngine",
    "EvolutionResult",
    "FraudDetector",
    "FraudScore",
    "FraudSignal",
    "Listing",
    "Match",
    "Portfolio",
    "PortfolioOptimizer",
    "PriceRecommendation",
    "PricingEngine",
    "RankedListing",
    "ResolvedEntity",
    "SearchRanker",
    "Seller",
    "ValuationEngine",
    "ValuationResult",
]

__version__ = "0.1.0"
