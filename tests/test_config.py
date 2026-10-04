"""Tests for configuration management module."""
import json

import pytest

from acquisition_platform.config import (
    Config,
    get_config,
    load_config,
    reset_config,
    save_config,
)


class TestDefaultConfig:
    """Test default configuration values for all modules."""

    def test_default_global_settings(self):
        config = Config()
        assert config.log_level == "INFO"
        assert config.random_seed is None
        assert config.output_format == "json"

    def test_default_fraud_detection(self):
        config = Config()
        assert config.fraud_weights == {
            "identity_verified": 0.3,
            "financial_consistency": 0.3,
            "traffic_authenticity": 0.2,
        }
        assert config.fraud_default_weight == 0.1
        assert config.fraud_total_expected_signals == 3
        assert config.fraud_risk_threshold_low == 0.3
        assert config.fraud_risk_threshold_medium == 0.7
        assert config.fraud_ring_risk_score == 0.8
        assert config.fraud_no_ring_score == 0.1

    def test_default_portfolio_optimization(self):
        config = Config()
        assert config.portfolio_max_assets == 10
        assert config.portfolio_risk_tolerance == 0.5
        assert config.portfolio_diversification_bonus == 1.5
        assert config.portfolio_risk_epsilon == 0.01
        assert config.portfolio_sharpe_epsilon == 0.01

    def test_default_dynamic_pricing(self):
        config = Config()
        assert config.pricing_demand_multiplier_base == 0.8
        assert config.pricing_demand_multiplier_scale == 0.4
        assert config.pricing_competition_multiplier_base == 1.2
        assert config.pricing_competition_multiplier_scale == 0.4
        assert config.pricing_market_multiplier_bull == 1.15
        assert config.pricing_market_multiplier_bear == 0.85
        assert config.pricing_market_multiplier_normal == 1.0
        assert config.pricing_floor_factor == 0.7
        assert config.pricing_ceiling_factor == 1.5

    def test_default_entity_resolution(self):
        config = Config()
        assert config.entity_threshold == 0.85
        assert config.entity_blocking_prefix_length == 3
        assert config.entity_domain_match_bonus == 0.2
        assert config.entity_jw_prefix_length == 4
        assert config.entity_jw_boost_factor == 0.1

    def test_default_search_ranking(self):
        config = Config()
        assert config.ranking_diversity_factor_first == 1.0
        assert config.ranking_diversity_factor_subsequent == 0.7
        assert config.ranking_personalization_factor == 1.3

    def test_default_matching(self):
        config = Config()
        assert config.matching_category_bonus == 1.0
        assert config.matching_confidence_half_budget_divisor == 2.0

    def test_default_valuation(self):
        config = Config()
        assert config.valuation_dcf_confidence == 0.7
        assert config.valuation_dcf_low_factor == 0.85
        assert config.valuation_dcf_high_factor == 1.15
        assert config.valuation_comps_confidence == 0.6
        assert config.valuation_comps_low_factor == 0.85
        assert config.valuation_comps_high_factor == 1.15
        assert config.valuation_sde_confidence == 0.6
        assert config.valuation_sde_low_factor == 0.85
        assert config.valuation_sde_high_factor == 1.15
        assert config.valuation_arr_confidence == 0.6
        assert config.valuation_arr_low_factor == 0.85
        assert config.valuation_arr_high_factor == 1.15

    def test_default_evolution(self):
        config = Config()
        assert config.evolution_population_size == 50
        assert config.evolution_generations == 20
        assert config.evolution_mutation_rate == 0.1
        assert config.evolution_elitism == 2
        assert config.evolution_convergence_improvement_threshold == 0.001
        assert config.evolution_convergence_stagnation_generations == 5
        assert config.evolution_convergence_min_generations == 10
        assert config.evolution_mutation_scale_factor == 0.1


class TestLoadConfig:
    """Test load_config from dict."""

    def test_load_config_no_args_returns_defaults(self):
        config = load_config()
        assert config.log_level == "INFO"
        assert config.portfolio_max_assets == 10

    def test_load_config_from_dict(self):
        data = {
            "log_level": "DEBUG",
            "portfolio_max_assets": 20,
            "entity_threshold": 0.9,
        }
        config = load_config(data)
        assert config.log_level == "DEBUG"
        assert config.portfolio_max_assets == 20
        assert config.entity_threshold == 0.9
        # Non-overridden values remain default
        assert config.pricing_floor_factor == 0.7

    def test_load_config_from_empty_dict(self):
        config = load_config({})
        assert config.log_level == "INFO"
        assert config.portfolio_max_assets == 10

    def test_load_config_ignores_unknown_keys(self):
        data = {"unknown_key": "value", "log_level": "WARNING"}
        config = load_config(data)
        assert config.log_level == "WARNING"
        assert not hasattr(config, "unknown_key")

    def test_load_config_from_none_returns_defaults(self):
        config = load_config(None)
        assert config.log_level == "INFO"
        assert config.random_seed is None


class TestSaveConfig:
    """Test save_config and reload."""

    def test_save_and_reload(self, tmp_path):
        config = Config()
        config.log_level = "DEBUG"
        config.portfolio_max_assets = 25
        path = tmp_path / "config.json"
        save_config(config, path)
        assert path.exists()

        with open(path) as f:
            saved = json.load(f)
        assert saved["log_level"] == "DEBUG"
        assert saved["portfolio_max_assets"] == 25

    def test_save_creates_valid_json(self, tmp_path):
        config = Config()
        path = tmp_path / "config.json"
        save_config(config, path)
        with open(path) as f:
            data = json.load(f)
        assert isinstance(data, dict)
        assert "log_level" in data
        assert "portfolio_max_assets" in data

    def test_save_creates_parent_dirs(self, tmp_path):
        config = Config()
        path = tmp_path / "nested" / "dir" / "config.json"
        save_config(config, path)
        assert path.exists()

    def test_save_preserves_all_fields(self, tmp_path):
        config = Config()
        path = tmp_path / "config.json"
        save_config(config, path)
        with open(path) as f:
            data = json.load(f)
        # Verify all dataclass fields are present
        for field_name in Config.__dataclass_fields__:
            assert field_name in data, f"Missing field: {field_name}"


class TestSingleton:
    """Test singleton pattern."""

    def teardown_method(self):
        reset_config()

    def test_get_config_returns_singleton(self):
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_get_config_returns_config_instance(self):
        config = get_config()
        assert isinstance(config, Config)

    def test_reset_config_clears_singleton(self):
        config1 = get_config()
        reset_config()
        config2 = get_config()
        assert config1 is not config2

    def test_singleton_preserves_mutations(self):
        config1 = get_config()
        config1.log_level = "ERROR"
        config2 = get_config()
        assert config2.log_level == "ERROR"
