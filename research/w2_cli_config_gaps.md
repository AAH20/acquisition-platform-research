# Wave 2: CLI & Configuration Gaps — Acquisition Platform

**Date:** 2026-10-04  
**Scope:** `/home/aah/Downloads/a2z-soc-main 2/acquisition-platform-research/`  
**Researcher:** Wave 1 Agent (Config & CLI Gaps)

---

## Executive Summary

The acquisition-platform project is a **pure library** with **no CLI entry point**, **no configuration system**, and **no `__main__.py`**. All 8 solver modules are programmatic-only. This creates a significant usability gap: users must write Python scripts to invoke any solver. A CLI layer and config system would make the platform accessible to non-developers and enable batch/CI workflows.

---

## 1. Config / Settings Module

### Finding: **MISSING**

| Aspect | Status |
|--------|--------|
| `config.yaml` / `config.yml` | ❌ Not present |
| `settings.py` / `settings/` module | ❌ Not present |
| `.env` support | ❌ Not present |
| `pydantic-settings` / `dynaconf` / `python-decouple` | ❌ Not in dependencies |
| Default parameter constants | ⚠️ Hardcoded in class bodies (e.g., `FraudDetector.WEIGHTS`) |

### Current State

All module parameters are **hardcoded as class attributes or function defaults**:

- `FraudDetector.WEIGHTS` — hardcoded dict
- `FraudDetector.DEFAULT_WEIGHT = 0.1`
- `FraudDetector.TOTAL_EXPECTED_SIGNALS = 3`
- `PortfolioOptimizer.__init__` — `budget` and `max_assets` are constructor args
- `PricingEngine` — market multipliers hardcoded in method body
- `EntityResolver` — `threshold` is constructor arg
- `BuyerSellerMatcher` — no configurable parameters at all

### Gap Impact

- No way to tune weights/thresholds without code changes
- No environment-specific configs (dev/staging/prod)
- No way to persist or version configurations
- No secrets management (if API keys needed later)

---

## 2. CLI Entry Point (argparse / click / typer)

### Finding: **MISSING**

| Aspect | Status |
|--------|--------|
| `argparse` usage | ❌ None |
| `click` / `typer` dependency | ❌ Not in dependencies |
| `if __name__ == "__main__"` blocks | ❌ None in any module |
| Console script entry point | ❌ Not in `pyproject.toml` |

### Current State

The project has **zero CLI surface**. Users must:

```python
from acquisition_platform.valuation import ValuationEngine
engine = ValuationEngine()
result = engine.dcf_valuation(free_cash_flow=100000, growth_rate=0.05, ...)
```

### Gap Impact

- Non-technical users cannot use the platform
- No batch processing capability
- No CI/CD integration path
- No way to run solvers from shell scripts

---

## 3. `__main__.py` for `python -m` Execution

### Finding: **MISSING**

| Aspect | Status |
|--------|--------|
| `src/acquisition_platform/__main__.py` | ❌ Not present |
| `python -m acquisition_platform` | ❌ Does not work |

### Current State

The package has `__init__.py` (exports all public API) but no `__main__.py`. Running `python -m acquisition_platform` produces:

```
No module named acquisition_platform.__main__; 'acquisition_platform' is a package and cannot be directly executed
```

---

## 4. `setup.py` / Entry Points in `pyproject.toml`

### Finding: **PARTIAL — No Entry Points**

| Aspect | Status |
|--------|--------|
| `pyproject.toml` | ✅ Present |
| `[project.scripts]` | ❌ **Missing** |
| `setup.py` | ❌ Not present |
| `setup.cfg` | ❌ Not present |
| Package discovery | ✅ `[tool.setuptools.packages.find] where = ["src"]` |

### Current `pyproject.toml` Structure

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "acquisition-platform"
version = "0.1.0"
# ... metadata ...

[project.optional-dependencies]
dev = ["pytest>=8.0,<9", "pytest-cov>=5.0,<6", "mypy>=1.0,<2", "ruff>=0.1,<1"]

[tool.setuptools.packages.find]
where = ["src"]
```

**No `[project.scripts]` section exists.** The package is installable but provides no command-line tools.

---

## 5. Recommended CLI Commands

Based on the 8 solver modules and their domains, the following CLI commands would provide the most value:

### Core Solver Commands

| Command | Module | Description |
|---------|--------|-------------|
| `acq match` | `matching.py` | Run buyer-seller matching (GAP solver) |
| `acq value` | `valuation.py` | Run DCF / comparable valuation |
| `acq fraud-check` | `fraud_detection.py` | Score fraud risk from signals |
| `acq optimize` | `portfolio_optimizer.py` | Optimize acquisition portfolio (MIQP) |
| `acq price` | `dynamic_pricing.py` | Get dynamic price recommendation |
| `acq resolve` | `entity_resolution.py` | Resolve entity clusters |
| `acq rank` | `search_ranking.py` | Rank listings by relevance |
| `acq evolve` | `evolution.py` | Run genetic algorithm optimization |

### Utility Commands

| Command | Description |
|---------|-------------|
| `acq config show` | Display current configuration |
| `acq config set <key> <value>` | Update a config value |
| `acq benchmark` | Run all benchmarks |
| `acq validate` | Validate input data formats |

### Example CLI Design (argparse-based)

```python
# src/acquisition_platform/__main__.py
import argparse
import json
import sys

def main():
    parser = argparse.ArgumentParser(prog="acq", description="Acquisition Platform CLI")
    subparsers = parser.add_subparsers(dest="command")
    
    # match
    match_parser = subparsers.add_parser("match", help="Run buyer-seller matching")
    match_parser.add_argument("--buyers", required=True, help="Path to buyers JSON")
    match_parser.add_argument("--sellers", required=True, help="Path to sellers JSON")
    match_parser.add_argument("--output", default="-", help="Output file (default: stdout)")
    
    # value
    value_parser = subparsers.add_parser("value", help="Run valuation")
    value_parser.add_argument("--fcf", type=float, required=True, help="Free cash flow")
    value_parser.add_argument("--growth", type=float, required=True, help="Growth rate")
    value_parser.add_argument("--discount", type=float, required=True, help="Discount rate")
    value_parser.add_argument("--terminal-growth", type=float, required=True)
    value_parser.add_argument("--years", type=int, required=True)
    
    # fraud-check
    fraud_parser = subparsers.add_parser("fraud-check", help="Check fraud risk")
    fraud_parser.add_argument("--signals", required=True, help="Path to signals JSON")
    
    # optimize
    opt_parser = subparsers.add_parser("optimize", help="Optimize portfolio")
    opt_parser.add_argument("--assets", required=True, help="Path to assets JSON")
    opt_parser.add_argument("--budget", type=float, required=True)
    opt_parser.add_argument("--max-assets", type=int, default=10)
    opt_parser.add_argument("--risk-tolerance", type=float, default=0.5)
    
    args = parser.parse_args()
    # ... dispatch to solvers ...
```

---

## 6. Config System for Module Parameters

### Finding: **MISSING**

### Current Parameter Locations

| Module | Parameter | Location | Configurable? |
|--------|-----------|----------|---------------|
| `FraudDetector` | `WEIGHTS` | Class attribute | ❌ Hardcoded |
| `FraudDetector` | `DEFAULT_WEIGHT` | Class attribute | ❌ Hardcoded |
| `FraudDetector` | `TOTAL_EXPECTED_SIGNALS` | Class attribute | ❌ Hardcoded |
| `PortfolioOptimizer` | `budget` | Constructor arg | ⚠️ Code only |
| `PortfolioOptimizer` | `max_assets` | Constructor arg | ⚠️ Code only |
| `PricingEngine` | market multipliers | Method body | ❌ Hardcoded |
| `EntityResolver` | `threshold` | Constructor arg | ⚠️ Code only |
| `BuyerSellerMatcher` | (none) | N/A | ❌ No params |
| `SearchRanker` | diversity/personalization factors | Method body | ❌ Hardcoded |
| `ValuationEngine` | (none) | N/A | ❌ No params |

### Recommended Config Schema

```yaml
# config.yaml
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

portfolio_optimization:
  max_assets: 10
  risk_tolerance: 0.5
  diversification_bonus: 0.1

dynamic_pricing:
  demand_multiplier_base: 0.8
  demand_multiplier_scale: 0.4
  competition_multiplier_base: 1.2
  competition_multiplier_scale: 0.4
  market_multipliers:
    bull: 1.15
    bear: 0.85
    normal: 1.0

entity_resolution:
  threshold: 0.85
  blocking_prefix_length: 3

search_ranking:
  diversity_factor_first: 1.0
  diversity_factor_subsequent: 0.7
  personalization_factor: 1.3

matching:
  category_bonus: 0.1
  price_ratio_weight: 0.5
```

---

## 7. Gap Summary Matrix

| Gap | Severity | Effort to Fix | Impact |
|-----|----------|---------------|--------|
| No CLI entry point | **Critical** | Medium | Enables non-dev usage |
| No `__main__.py` | **High** | Low | Enables `python -m` |
| No `[project.scripts]` | **High** | Low | Enables `acq` command |
| No config system | **High** | Medium | Enables parameter tuning |
| No config file support | **Medium** | Medium | Enables env-specific configs |
| No batch input/output | **Medium** | Medium | Enables CI/CD integration |
| No JSON/YAML I/O helpers | **Medium** | Low | Simplifies data exchange |

---

## 8. Recommended Implementation Priority

### Phase 1: Minimal CLI (1-2 days)
1. Add `src/acquisition_platform/__main__.py` with argparse
2. Add `[project.scripts]` to `pyproject.toml`
3. Support JSON input/output for all solvers
4. Test with `python -m acquisition_platform <command>`

### Phase 2: Config System (2-3 days)
1. Add `config.yaml` support with `pyyaml`
2. Create `acquisition_platform/config.py` with loader
3. Wire config into all solver constructors
4. Add `acq config show/set` commands

### Phase 3: Advanced Features (3-5 days)
1. Add batch processing mode
2. Add `--format json|yaml|table` output options
3. Add `acq benchmark` command
4. Add `acq validate` command

---

## 9. Comparison with Hermes Agent (Reference)

The Hermes Agent project (at `/home/aah/.hermes/hermes-agent/`) provides a mature reference implementation:

| Feature | Hermes Agent | Acquisition Platform |
|---------|-------------|---------------------|
| CLI framework | `argparse` + custom mixins | ❌ None |
| Entry point | `hermes_cli/main.py` | ❌ None |
| Config system | `config.yaml` + `.env` + migrations | ❌ None |
| Config CLI | `hermes config get/set/unset` | ❌ None |
| Slash commands | 60+ commands | ❌ None |
| `__main__.py` | N/A (uses `hermes` script) | ❌ None |

---

## 10. Conclusion

The acquisition-platform project has **strong solver logic** but **zero CLI/config infrastructure**. Adding a CLI layer and config system would:

1. **Democratize access** — non-developers can use solvers
2. **Enable automation** — CI/CD pipelines can invoke solvers
3. **Improve testability** — CLI commands are easier to integration-test
4. **Support tuning** — config files enable parameter experimentation

The recommended approach is to add a minimal `__main__.py` with argparse first, then layer on config support. This follows the "CLI command + skill" pattern from the Hermes Agent Footprint Ladder (Rung 2).

---

*End of report.*
