"""Acquisition Platform Research & Optimization.

Unified optimization engine for acquisition/auction platforms.
Solves NP-hard problems: matching, valuation, fraud detection,
portfolio optimization, dynamic pricing, entity resolution,
search ranking, and due diligence scheduling.
"""

from acquisition_platform.matching import (
    Buyer,
    BuyerSellerMatcher,
    Match,
    MatchingPolicy,
    Seller,
)
from acquisition_platform.valuation import ValuationResult, ValuationEngine
from acquisition_platform.fraud_detection import FraudSignal, FraudScore, FraudDetector
from acquisition_platform.portfolio_optimizer import Asset, Portfolio, PortfolioOptimizer
from acquisition_platform.dynamic_pricing import PriceRecommendation, PricingEngine
from acquisition_platform.entity_resolution import EntityCluster, EntityResolver, ResolvedEntity
from acquisition_platform.search_ranking import Listing, RankedListing, SearchRanker
from acquisition_platform.evolution import (
    Alpha,
    AlphaEvolver,
    Benchmark,
    Constraint,
    EvaluationResult,
    EvolutionConfig,
    EvolutionEngine,
    EvolutionReport,
    EvolutionResult,
    Objective,
    ParamSpec,
)
from acquisition_platform.evaluation import (
    ClassificationMetrics,
    ConfusionMatrix,
    Interval,
    average_precision,
    bootstrap_ci,
    classification_metrics,
    cohens_d,
    expected_calibration_error,
    mae,
    mean_average_precision,
    ndcg_at_k,
    paired_bootstrap_pvalue,
    r2,
    rmse,
    roc_auc,
    spearman_correlation,
)
from acquisition_platform.benchmark_suite import (
    BenchmarkCase,
    BenchmarkSuite,
    CaseResult,
    Regression,
    SuiteReport,
)
from acquisition_platform.alpha_lab import AlphaLab, MatchingBenchmark, PolicyEvolution

__all__ = [
    "Alpha",
    "AlphaEvolver",
    "AlphaLab",
    "Asset",
    "Benchmark",
    "BenchmarkCase",
    "BenchmarkSuite",
    "Buyer",
    "BuyerSellerMatcher",
    "CaseResult",
    "ClassificationMetrics",
    "ConfusionMatrix",
    "Constraint",
    "EntityCluster",
    "EntityResolver",
    "EvaluationResult",
    "EvolutionConfig",
    "EvolutionEngine",
    "EvolutionReport",
    "EvolutionResult",
    "FraudDetector",
    "FraudScore",
    "FraudSignal",
    "Interval",
    "Listing",
    "Match",
    "MatchingBenchmark",
    "MatchingPolicy",
    "Objective",
    "ParamSpec",
    "PolicyEvolution",
    "Portfolio",
    "PortfolioOptimizer",
    "PriceRecommendation",
    "PricingEngine",
    "RankedListing",
    "Regression",
    "ResolvedEntity",
    "SearchRanker",
    "Seller",
    "SuiteReport",
    "ValuationEngine",
    "ValuationResult",
    "average_precision",
    "bootstrap_ci",
    "classification_metrics",
    "cohens_d",
    "expected_calibration_error",
    "mae",
    "mean_average_precision",
    "ndcg_at_k",
    "paired_bootstrap_pvalue",
    "r2",
    "rmse",
    "roc_auc",
    "spearman_correlation",
]

__version__ = "0.2.0"
