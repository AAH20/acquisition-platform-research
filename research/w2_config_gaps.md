# Wave 2: Configuration Management Gaps — Acquisition Platform

**Date:** 2026-10-04  
**Scope:** `/home/aah/Downloads/a2z-soc-main 2/acquisition-platform-research/src/acquisition_platform/`  
**Researcher:** Wave 1 Agent (Config Gaps)

---

## Executive Summary

The acquisition-platform project has **zero configuration management infrastructure**. All solver parameters are hardcoded as class attributes, constructor defaults, or inline literals. There is no `config.py`, no `settings.py`, no `.env` support, no `config.yaml` template, and no environment variable reading anywhere in the source tree. This makes the platform impossible to tune, deploy across environments, or integrate into CI/CD pipelines without code changes.

---

## 1. Source File Inventory

| File | Lines | Hardcoded Constants | Configurable Params |
|------|-------|---------------------|---------------------|
| `__init__.py` | 50 | `__version__ = "0.1.0"` | None |
| `dynamic_pricing.py` | 70 | 7 inline literals | None |
| `entity_resolution.py` | 226 | 3 inline literals | `threshold` (constructor) |
| `evolution.py` | 194 | 3 inline literals | 4 constructor params |
| `fraud_detection.py` | 172 | 5 class attributes | None |
| `matching.py` | 156 | 2 inline literals | None |
| `portfolio_optimizer.py` | 119 | 3 inline literals | 2 constructor params |
| `search_ranking.py` | 103 | 3 inline literals | None |
| `valuation.py` | 200 | 6 inline literals | None |

**Total: 9 files, ~1,190 lines, 32+ hardcoded constants, 7 constructor params, 0 config files.**

---

## 2. Hardcoded Constants — Complete Catalog

### 2.1 `dynamic_pricing.py` — PricingEngine

| Line | Constant | Value | Should Be Configurable? |
|------|----------|-------|------------------------|
| 44 | `demand_multiplier` base | `0.8` | **Yes** — market-specific |
| 44 | `demand_multiplier` scale | `0.4` | **Yes** — market-specific |
| 45 | `competition_multiplier` base | `1.2` | **Yes** — market-specific |
| 45 | `competition_multiplier` scale | `0.4` | **Yes** — market-specific |
| 47-51 | `market_multipliers["bull"]` | `1.15` | **Yes** — market regime |
| 47-51 | `market_multipliers["bear"]` | `0.85` | **Yes** — market regime |
| 47-51 | `market_multipliers["normal"]` | `1.0` | **Yes** — market regime |
| 57 | `floor_price` factor | `0.7` | **Yes** — risk policy |
| 58 | `ceiling_price` factor | `1.5` | **Yes** — risk policy |

**Risk:** All pricing logic is baked in. Changing market conditions requires editing source.

### 2.2 `entity_resolution.py` — EntityResolver

| Line | Constant | Value | Should Be Configurable? |
|------|----------|-------|------------------------|
| 153 | `threshold` (default) | `0.85` | **Yes** — tuning param |
| 63 | `match_window` divisor | `2` | **Maybe** — algorithm tuning |
| 107 | JW prefix length | `4` | **Maybe** — algorithm tuning |
| 113 | JW boost factor | `0.1` | **Maybe** — algorithm tuning |
| 181 | blocking prefix length | `3` | **Yes** — performance/accuracy tradeoff |
| 196 | domain match bonus | `0.2` | **Yes** — domain strategy |

**Risk:** Threshold is the only constructor param. Blocking prefix length and domain bonus are hardcoded.

### 2.3 `evolution.py` — EvolutionEngine

| Line | Constant | Value | Should Be Configurable? |
|------|----------|-------|------------------------|
| 76 | `population_size` (default) | `50` | **Yes** — compute budget |
| 77 | `generations` (default) | `20` | **Yes** — compute budget |
| 78 | `mutation_rate` (default) | `0.1` | **Yes** — GA tuning |
| 79 | `elitism` (default) | `2` | **Yes** — GA tuning |
| 129 | convergence threshold | `0.001` | **Yes** — convergence policy |
| 134 | stagnation generations | `5` | **Yes** — convergence policy |
| 134 | min generations before check | `10` | **Yes** — convergence policy |
| 164 | mutation scale factor | `0.1` | **Yes** — GA tuning |

**Risk:** 4 constructor params exist but 4 more convergence constants are hardcoded.

### 2.4 `fraud_detection.py` — FraudDetector

| Line | Constant | Value | Should Be Configurable? |
|------|----------|-------|------------------------|
| 42-46 | `WEIGHTS["identity_verified"]` | `0.3` | **Yes** — domain tuning |
| 42-46 | `WEIGHTS["financial_consistency"]` | `0.3` | **Yes** — domain tuning |
| 42-46 | `WEIGHTS["traffic_authenticity"]` | `0.2` | **Yes** — domain tuning |
| 47 | `DEFAULT_WEIGHT` | `0.1` | **Yes** — fallback weight |
| 48 | `TOTAL_EXPECTED_SIGNALS` | `3` | **Yes** — signal schema |
| 86 | risk threshold "low" | `0.3` | **Yes** — risk policy |
| 88 | risk threshold "medium" | `0.7` | **Yes** — risk policy |
| 118 | ring risk score | `0.8` | **Yes** — risk policy |
| 124 | no-ring risk score | `0.1` | **Yes** — risk policy |

**Risk:** All weights and thresholds are class attributes. No way to add new signals or adjust risk levels without code changes.

### 2.5 `matching.py` — BuyerSellerMatcher

| Line | Constant | Value | Should Be Configurable? |
|------|----------|-------|------------------------|
| 138 | `category_bonus` | `1.0` | **Yes** — matching strategy |
| 153 | `half_budget` divisor | `2.0` | **Maybe** — confidence formula |

**Risk:** No constructor params at all. The matcher is completely inflexible.

### 2.6 `portfolio_optimizer.py` — PortfolioOptimizer

| Line | Constant | Value | Should Be Configurable? |
|------|----------|-------|------------------------|
| 44 | `max_assets` (default) | `10` | **Yes** — portfolio constraint |
| 82 | risk epsilon | `0.01` | **Maybe** — numerical stability |
| 84 | risk tolerance factor | `1 + risk_tolerance` | **Yes** — strategy |
| 97 | diversification bonus | `1.5` | **Yes** — diversification policy |
| 113 | sharpe epsilon | `0.01` | **Maybe** — numerical stability |

**Risk:** Budget and max_assets are constructor args, but diversification bonus and risk formula are hardcoded.

### 2.7 `search_ranking.py` — SearchRanker

| Line | Constant | Value | Should Be Configurable? |
|------|----------|-------|------------------------|
| 72 | diversity factor (subsequent) | `0.7` | **Yes** — ranking strategy |
| 74 | diversity factor (first) | `1.0` | **Yes** — ranking strategy |
| 79 | personalization factor | `1.3` | **Yes** — ranking strategy |

**Risk:** All ranking factors are inline literals. No way to A/B test ranking strategies.

### 2.8 `valuation.py` — ValuationEngine

| Line | Constant | Value | Should Be Configurable? |
|------|----------|-------|------------------------|
| 75 | DCF confidence | `0.7` | **Yes** — method confidence |
| 76 | DCF low estimate factor | `0.85` | **Yes** — valuation range |
| 77 | DCF high estimate factor | `1.15` | **Yes** — valuation range |
| 97 | Comps confidence | `0.6` | **Yes** — method confidence |
| 98 | Comps low estimate factor | `0.85` | **Yes** — valuation range |
| 99 | Comps high estimate factor | `1.15` | **Yes** — valuation range |
| 175 | SDE confidence | `0.6` | **Yes** — method confidence |
| 176 | SDE low estimate factor | `0.85` | **Yes** — valuation range |
| 177 | SDE high estimate factor | `1.15` | **Yes** — valuation range |
| 197 | ARR confidence | `0.6` | **Yes** — method confidence |
| 198 | ARR low estimate factor | `0.85` | **Yes** — valuation range |
| 199 | ARR high estimate factor | `1.15` | **Yes** — valuation range |

**Risk:** Confidence scores and estimate ranges are identical across methods (copy-paste). No way to adjust per-method.

---

## 3. Config Infrastructure Check

### 3.1 Config Module

| Check | Result |
|-------|--------|
| `config.py` in `src/acquisition_platform/` | ❌ **Not found** |
| `settings.py` in `src/acquisition_platform/` | ❌ **Not found** |
| `config/` directory | ❌ **Not found** |
| `constants.py` | ❌ **Not found** |
| `defaults.py` | ❌ **Not found** |

### 3.2 Environment Variable Support

| Check | Result |
|-------|--------|
| `os.environ` usage in `src/` | ❌ **None** |
| `os.getenv` usage in `src/` | ❌ **None** |
| `python-dotenv` dependency | ❌ **Not in pyproject.toml** |
| `pydantic-settings` dependency | ❌ **Not in pyproject.toml** |
| `dynaconf` dependency | ❌ **Not in pyproject.toml** |
| `python-decouple` dependency | ❌ **Not in pyproject.toml** |

### 3.3 Config File Templates

| Check | Result |
|-------|--------|
| `.env.example` | ❌ **Not found** |
| `config.yaml` / `config.yml` | ❌ **Not found** |
| `config.example.yaml` | ❌ **Not found** |
| `settings.yaml` | ❌ **Not found** |
| `default_config.py` | ❌ **Not found** |

### 3.4 pyproject.toml Dependencies

```toml
[project.optional-dependencies]
dev = ["pytest>=8.0,<9", "pytest-cov>=5.0,<6", "mypy>=1.0,<2", "ruff>=0.1,<1"]
```

**No runtime dependencies at all.** The project uses only stdlib (`dataclasses`, `random`, `statistics`, `re`, `collections`, `typing`). No YAML, no TOML reader, no env parser.

---

## 4. Gap Analysis

### 4.1 Severity Matrix

| Gap | Severity | Impact | Effort to Fix |
|-----|----------|--------|---------------|
| No config module | **Critical** | All params hardcoded | Medium |
| No env var support | **High** | No env-specific config | Low |
| No config file support | **High** | No persisted config | Medium |
| No `.env.example` | **Medium** | No onboarding guide | Low |
| No `config.yaml` template | **Medium** | No config discovery | Low |
| No secrets management | **Medium** | Future API keys | Low |
| No config validation | **High** | Silent failures | Medium |
| No config versioning | **Medium** | No audit trail | Medium |
| No per-environment config | **High** | Dev/staging/prod identical | Medium |
| No config CLI | **Medium** | No runtime inspection | Low |

### 4.2 Impact by Stakeholder

- **End users:** Cannot tune any solver without editing source code
- **DevOps/SRE:** Cannot configure per-environment behavior
- **QA:** Cannot inject test configurations
- **CI/CD:** Cannot parameterize pipeline runs
- **New developers:** No documented defaults or config options

---

## 5. Recommended Config System Design

### 5.1 Architecture

```
src/acquisition_platform/
├── __init__.py
├── config.py              # NEW: Config loader + schema
├── config_schema.py       # NEW: Pydantic/dataclass schema (optional)
├── dynamic_pricing.py
├── entity_resolution.py
├── evolution.py
├── fraud_detection.py
├── matching.py
├── portfolio_optimizer.py
├── search_ranking.py
└── valuation.py

config.yaml                # NEW: Default config file
config.example.yaml        # NEW: Documented template
.env.example               # NEW: Secrets template (future)
```

### 5.2 Config Schema (YAML)

```yaml
# config.yaml — Default configuration for acquisition platform

# Global settings
global:
  log_level: INFO
  random_seed: null          # Set for reproducibility
  output_format: json        # json | yaml | table

# Fraud detection
fraud_detection:
  weights:
    identity_verified: 0.3
    financial_consistency: 0.3
    traffic_authenticity: 0.2
  default_weight: 0.1
  total_expected_signals: 3
  risk_thresholds:
    low: 0.3
    medium: 0.7
    high: 0.9
  ring_detection:
    risk_score: 0.8
    no_ring_score: 0.1

# Portfolio optimization
portfolio_optimization:
  max_assets: 10
  risk_tolerance: 0.5
  diversification_bonus: 1.5
  risk_epsilon: 0.01
  sharpe_epsilon: 0.01

# Dynamic pricing
dynamic_pricing:
  demand_multiplier_base: 0.8
  demand_multiplier_scale: 0.4
  competition_multiplier_base: 1.2
  competition_multiplier_scale: 0.4
  market_multipliers:
    bull: 1.15
    bear: 0.85
    normal: 1.0
  floor_factor: 0.7
  ceiling_factor: 1.5

# Entity resolution
entity_resolution:
  threshold: 0.85
  blocking_prefix_length: 3
  domain_match_bonus: 0.2
  jaro_winkler:
    prefix_length: 4
    boost_factor: 0.1

# Search ranking
search_ranking:
  diversity_factor_first: 1.0
  diversity_factor_subsequent: 0.7
  personalization_factor: 1.3

# Matching
matching:
  category_bonus: 1.0
  confidence_half_budget_divisor: 2.0

# Valuation
valuation:
  dcf:
    confidence: 0.7
    low_factor: 0.85
    high_factor: 1.15
  comps:
    confidence: 0.6
    low_factor: 0.85
    high_factor: 1.15
  sde:
    confidence: 0.6
    low_factor: 0.85
    high_factor: 1.15
  arr:
    confidence: 0.6
    low_factor: 0.85
    high_factor: 1.15

# Evolution (genetic algorithm)
evolution:
  population_size: 50
  generations: 20
  mutation_rate: 0.1
  elitism: 2
  convergence:
    improvement_threshold: 0.001
    stagnation_generations: 5
    min_generations: 10
  mutation_scale_factor: 0.1
```

### 5.3 Config Loader Implementation

```python
# src/acquisition_platform/config.py
"""Configuration loader for acquisition platform.

Loads configuration from (in priority order):
1. Environment variables (ACQ_*)
2. Config file (config.yaml)
3. Default values
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


DEFAULT_CONFIG: dict[str, Any] = {
    "global": {
        "log_level": "INFO",
        "random_seed": None,
        "output_format": "json",
    },
    "fraud_detection": {
        "weights": {
            "identity_verified": 0.3,
            "financial_consistency": 0.3,
            "traffic_authenticity": 0.2,
        },
        "default_weight": 0.1,
        "total_expected_signals": 3,
        "risk_thresholds": {"low": 0.3, "medium": 0.7, "high": 0.9},
        "ring_detection": {"risk_score": 0.8, "no_ring_score": 0.1},
    },
    "portfolio_optimization": {
        "max_assets": 10,
        "risk_tolerance": 0.5,
        "diversification_bonus": 1.5,
        "risk_epsilon": 0.01,
        "sharpe_epsilon": 0.01,
    },
    "dynamic_pricing": {
        "demand_multiplier_base": 0.8,
        "demand_multiplier_scale": 0.4,
        "competition_multiplier_base": 1.2,
        "competition_multiplier_scale": 0.4,
        "market_multipliers": {"bull": 1.15, "bear": 0.85, "normal": 1.0},
        "floor_factor": 0.7,
        "ceiling_factor": 1.5,
    },
    "entity_resolution": {
        "threshold": 0.85,
        "blocking_prefix_length": 3,
        "domain_match_bonus": 0.2,
        "jaro_winkler": {"prefix_length": 4, "boost_factor": 0.1},
    },
    "search_ranking": {
        "diversity_factor_first": 1.0,
        "diversity_factor_subsequent": 0.7,
        "personalization_factor": 1.3,
    },
    "matching": {
        "category_bonus": 1.0,
        "confidence_half_budget_divisor": 2.0,
    },
    "valuation": {
        "dcf": {"confidence": 0.7, "low_factor": 0.85, "high_factor": 1.15},
        "comps": {"confidence": 0.6, "low_factor": 0.85, "high_factor": 1.15},
        "sde": {"confidence": 0.6, "low_factor": 0.85, "high_factor": 1.15},
        "arr": {"confidence": 0.6, "low_factor": 0.85, "high_factor": 1.15},
    },
    "evolution": {
        "population_size": 50,
        "generations": 20,
        "mutation_rate": 0.1,
        "elitism": 2,
        "convergence": {
            "improvement_threshold": 0.001,
            "stagnation_generations": 5,
            "min_generations": 10,
        },
        "mutation_scale_factor": 0.1,
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into base."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _env_var_name(section: str, key: str) -> str:
    """Convert section.key to ACQ_SECTION_KEY env var name."""
    return f"ACQ_{section.upper()}_{key.upper()}"


def _apply_env_overrides(config: dict) -> dict:
    """Override config values from ACQ_* environment variables."""
    for section, values in config.items():
        if not isinstance(values, dict):
            continue
        for key, _ in values.items():
            env_name = _env_var_name(section, key)
            env_value = os.getenv(env_name)
            if env_value is not None:
                # Try to parse as number/bool
                try:
                    parsed: Any = yaml.safe_load(env_value)
                except yaml.YAMLError:
                    parsed = env_value
                config[section][key] = parsed
    return config


def load_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Load configuration from file and environment.

    Args:
        config_path: Path to config.yaml. If None, searches default locations.

    Returns:
        Merged configuration dict.
    """
    config = DEFAULT_CONFIG.copy()

    if config_path is None:
        # Search default locations
        search_paths = [
            Path.cwd() / "config.yaml",
            Path.cwd() / "config.yml",
            Path.home() / ".config" / "acquisition-platform" / "config.yaml",
            Path("/etc/acquisition-platform/config.yaml"),
        ]
        for path in search_paths:
            if path.exists():
                config_path = path
                break

    if config_path is not None and Path(config_path).exists():
        with open(config_path) as f:
            file_config = yaml.safe_load(f) or {}
        config = _deep_merge(config, file_config)

    config = _apply_env_overrides(config)
    return config


# Singleton instance
_config: dict[str, Any] | None = None


def get_config() -> dict[str, Any]:
    """Get the global configuration singleton."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reset_config() -> None:
    """Reset the global configuration singleton (for testing)."""
    global _config
    _config = None
```

### 5.4 Environment Variable Convention

| Env Var | Overrides | Example |
|---------|-----------|---------|
| `ACQ_GLOBAL_LOG_LEVEL` | `global.log_level` | `DEBUG` |
| `ACQ_GLOBAL_RANDOM_SEED` | `global.random_seed` | `42` |
| `ACQ_FRAUD_DETECTION_WEIGHTS` | `fraud_detection.weights` | `{"identity_verified": 0.4}` |
| `ACQ_PORTFOLIO_OPTIMIZATION_MAX_ASSETS` | `portfolio_optimization.max_assets` | `20` |
| `ACQ_DYNAMIC_PRICING_MARKET_MULTIPLIERS` | `dynamic_pricing.market_multipliers` | `{"bull": 1.2}` |
| `ACQ_ENTITY_RESOLUTION_THRESHOLD` | `entity_resolution.threshold` | `0.9` |
| `ACQ_EVOLUTION_POPULATION_SIZE` | `evolution.population_size` | `100` |

### 5.5 `.env.example`

```bash
# Acquisition Platform Environment Variables
# Copy to .env and fill in values

# Global
ACQ_GLOBAL_LOG_LEVEL=INFO
ACQ_GLOBAL_RANDOM_SEED=
ACQ_GLOBAL_OUTPUT_FORMAT=json

# Fraud Detection
ACQ_FRAUD_DETECTION_DEFAULT_WEIGHT=0.1
ACQ_FRAUD_DETECTION_TOTAL_EXPECTED_SIGNALS=3

# Portfolio Optimization
ACQ_PORTFOLIO_OPTIMIZATION_MAX_ASSETS=10
ACQ_PORTFOLIO_OPTIMIZATION_RISK_TOLERANCE=0.5

# Dynamic Pricing
ACQ_DYNAMIC_PRICING_FLOOR_FACTOR=0.7
ACQ_DYNAMIC_PRICING_CEILING_FACTOR=1.5

# Entity Resolution
ACQ_ENTITY_RESOLUTION_THRESHOLD=0.85
ACQ_ENTITY_RESOLUTION_BLOCKING_PREFIX_LENGTH=3

# Evolution
ACQ_EVOLUTION_POPULATION_SIZE=50
ACQ_EVOLUTION_GENERATIONS=20
ACQ_EVOLUTION_MUTATION_RATE=0.1
```

### 5.6 Required New Dependencies

```toml
[project]
dependencies = [
    "pyyaml>=6.0,<7",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0,<9",
    "pytest-cov>=5.0,<6",
    "mypy>=1.0,<2",
    "ruff>=0.1,<1",
]
```

---

## 6. Migration Plan

### Phase 1: Config Module (2-3 days)

1. Add `pyyaml` to `pyproject.toml` dependencies
2. Create `src/acquisition_platform/config.py` with `DEFAULT_CONFIG`, `load_config()`, `get_config()`
3. Create `config.yaml` with all default values
4. Create `config.example.yaml` with documentation comments
5. Create `.env.example`
6. Write unit tests for config loading, merging, env overrides

### Phase 2: Wire Config into Solvers (3-4 days)

1. **FraudDetector:** Replace class attributes with config-driven values
2. **PricingEngine:** Accept config dict in constructor, use for multipliers
3. **EntityResolver:** Use config for threshold, blocking prefix, domain bonus
4. **EvolutionEngine:** Use config for convergence constants
5. **PortfolioOptimizer:** Use config for diversification bonus, epsilons
6. **SearchRanker:** Accept config dict, use for diversity/personalization factors
7. **ValuationEngine:** Use config for confidence scores and estimate factors
8. **BuyerSellerMatcher:** Accept config dict for category bonus

### Phase 3: CLI Integration (2-3 days)

1. Add `acq config show` command
2. Add `acq config get <key>` command
3. Add `acq config set <key> <value>` command
4. Add `--config <path>` global flag to all solver commands
5. Add `--format json|yaml|table` output option

### Phase 4: Advanced Features (3-5 days)

1. Config validation with clear error messages
2. Config versioning/migration support
3. Per-environment config profiles (dev/staging/prod)
4. Config diff command (`acq config diff`)
5. Config export command (`acq config export --format yaml`)

---

## 7. Gap Summary

| # | Gap | Status | Priority |
|---|-----|--------|----------|
| 1 | No config module | ❌ Missing | **P0** |
| 2 | No env var support | ❌ Missing | **P0** |
| 3 | No config file support | ❌ Missing | **P0** |
| 4 | No `.env.example` | ❌ Missing | **P1** |
| 5 | No `config.yaml` template | ❌ Missing | **P1** |
| 6 | No config validation | ❌ Missing | **P1** |
| 7 | No per-environment config | ❌ Missing | **P2** |
| 8 | No config CLI | ❌ Missing | **P2** |
| 9 | No secrets management | ❌ Missing | **P2** |
| 10 | No config versioning | ❌ Missing | **P3** |
| 11 | No `pyyaml` dependency | ❌ Missing | **P0** |
| 12 | No random seed control | ❌ Missing | **P1** |
| 13 | No log level control | ❌ Missing | **P2** |
| 14 | No output format control | ❌ Missing | **P2** |

---

## 8. Comparison with Reference Projects

| Feature | Hermes Agent | Acquisition Platform | Gap |
|---------|-------------|---------------------|-----|
| Config file | `config.yaml` | ❌ None | Critical |
| Env var support | `.env` + `HERMES_*` | ❌ None | Critical |
| Config CLI | `hermes config get/set` | ❌ None | High |
| Config validation | Pydantic | ❌ None | High |
| Config migrations | `_config_version` | ❌ None | Medium |
| Per-profile config | `profiles/` | ❌ None | Medium |
| Secrets management | Vault integration | ❌ None | Medium |
| Default config | `DEFAULT_CONFIG` dict | ❌ None | Critical |
| Config documentation | `website/docs/` | ❌ None | Medium |

---

## 9. Conclusion

The acquisition-platform project is a **pure algorithm library** with **zero configuration management**. Every parameter — from fraud weights to pricing multipliers to GA convergence thresholds — is hardcoded. This is the single largest infrastructure gap after the missing CLI (documented in `w2_cli_config_gaps.md`).

**Recommended priority:**
1. Add `pyyaml` dependency and `config.py` module (P0)
2. Create `config.yaml` and `.env.example` (P0)
3. Wire config into all 8 solver modules (P1)
4. Add config CLI commands (P2)

**Estimated total effort:** 7-12 days for full config system integration.

---

*End of report.*
