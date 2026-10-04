"""Configuration management for acquisition platform.

Provides a Config dataclass with all module parameters, load/save functions,
and a singleton accessor. All solver parameters that were previously hardcoded
are now configurable through this module.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any


@dataclass
class Config:
    """Configuration for all acquisition platform modules.

    Each field corresponds to a parameter that was previously hardcoded
    in the solver modules. Default values match the original hardcoded
    constants to preserve backward compatibility.
    """

    # Global settings
    log_level: str = "INFO"
    random_seed: int | None = None
    output_format: str = "json"

    # Fraud detection
    fraud_weights: dict[str, float] = field(
        default_factory=lambda: {
            "identity_verified": 0.3,
            "financial_consistency": 0.3,
            "traffic_authenticity": 0.2,
        }
    )
    fraud_default_weight: float = 0.1
    fraud_total_expected_signals: int = 3
    fraud_risk_threshold_low: float = 0.3
    fraud_risk_threshold_medium: float = 0.7
    fraud_ring_risk_score: float = 0.8
    fraud_no_ring_score: float = 0.1

    # Portfolio optimization
    portfolio_max_assets: int = 10
    portfolio_risk_tolerance: float = 0.5
    portfolio_diversification_bonus: float = 1.5
    portfolio_risk_epsilon: float = 0.01
    portfolio_sharpe_epsilon: float = 0.01

    # Dynamic pricing
    pricing_demand_multiplier_base: float = 0.8
    pricing_demand_multiplier_scale: float = 0.4
    pricing_competition_multiplier_base: float = 1.2
    pricing_competition_multiplier_scale: float = 0.4
    pricing_market_multiplier_bull: float = 1.15
    pricing_market_multiplier_bear: float = 0.85
    pricing_market_multiplier_normal: float = 1.0
    pricing_floor_factor: float = 0.7
    pricing_ceiling_factor: float = 1.5

    # Entity resolution
    entity_threshold: float = 0.85
    entity_blocking_prefix_length: int = 3
    entity_domain_match_bonus: float = 0.2
    entity_jw_prefix_length: int = 4
    entity_jw_boost_factor: float = 0.1

    # Search ranking
    ranking_diversity_factor_first: float = 1.0
    ranking_diversity_factor_subsequent: float = 0.7
    ranking_personalization_factor: float = 1.3

    # Matching
    matching_category_bonus: float = 1.0
    matching_confidence_half_budget_divisor: float = 2.0

    # Valuation
    valuation_dcf_confidence: float = 0.7
    valuation_dcf_low_factor: float = 0.85
    valuation_dcf_high_factor: float = 1.15
    valuation_comps_confidence: float = 0.6
    valuation_comps_low_factor: float = 0.85
    valuation_comps_high_factor: float = 1.15
    valuation_sde_confidence: float = 0.6
    valuation_sde_low_factor: float = 0.85
    valuation_sde_high_factor: float = 1.15
    valuation_arr_confidence: float = 0.6
    valuation_arr_low_factor: float = 0.85
    valuation_arr_high_factor: float = 1.15

    # Evolution (genetic algorithm)
    evolution_population_size: int = 50
    evolution_generations: int = 20
    evolution_mutation_rate: float = 0.1
    evolution_elitism: int = 2
    evolution_convergence_improvement_threshold: float = 0.001
    evolution_convergence_stagnation_generations: int = 5
    evolution_convergence_min_generations: int = 10
    evolution_mutation_scale_factor: float = 0.1


def load_config(data: dict[str, Any] | None = None) -> Config:
    """Load configuration from a dict or return defaults.

    Args:
        data: Optional dict of config overrides. Only keys matching
            Config dataclass fields are applied; unknown keys are ignored.

    Returns:
        Config instance with defaults overridden by provided values.
    """
    config = Config()
    if data is None:
        return config

    valid_fields = {f.name for f in fields(Config)}
    for key, value in data.items():
        if key in valid_fields:
            setattr(config, key, value)
    return config


def save_config(config: Config, path: str | Path) -> None:
    """Save configuration to a JSON file.

    Args:
        config: Config instance to serialize.
        path: Destination file path. Parent directories are created.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(asdict(config), f, indent=2)


# Singleton instance
_config: Config | None = None


def get_config() -> Config:
    """Get the global configuration singleton.

    On first call, creates a Config with defaults. Subsequent calls
    return the same instance.

    Returns:
        The global Config singleton.
    """
    global _config
    if _config is None:
        _config = Config()
    return _config


def reset_config() -> None:
    """Reset the global configuration singleton.

    Useful for testing. The next call to get_config() will create
    a fresh Config instance.
    """
    global _config
    _config = None
