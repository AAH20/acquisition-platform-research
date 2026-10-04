# Wave 2 — Code Quality Analysis

**Target:** `src/acquisition_platform/*.py` (9 files, 1,290 total lines)
**Date:** 2026-10-04

---

## 1. Compilation Check

**Command:** `python -m py_compile src/acquisition_platform/*.py`

**Result:** ✅ All 9 files compile successfully — zero errors, zero warnings.

---

## 2. Type Hints

**Status:** ✅ Excellent — 100% coverage on public functions/methods.

| File | Public Functions | Type Hinted | Notes |
|---|---|---|---|
| `__init__.py` | 0 (re-exports only) | N/A | Clean `__all__` list |
| `dynamic_pricing.py` | 1 (`recommend_price`) | ✅ | All params + return typed |
| `entity_resolution.py` | 1 (`resolve`) | ✅ | Uses `list[dict]`, `list[EntityCluster]` |
| `evolution.py` | 2 (`__init__`, `evolve`) | ✅ | Uses `Callable`, `Tuple` from typing |
| `fraud_detection.py` | 2 (`score`, `analyze_graph`) | ✅ | Uses `dict[str, Any]`, `list[str]` |
| `matching.py` | 1 (`match`) | ✅ | Custom dataclass types |
| `portfolio_optimizer.py` | 2 (`__init__`, `optimize`) | ✅ | |
| `search_ranking.py` | 1 (`rank`) | ✅ | Uses `dict \| None` (PEP 604) |
| `valuation.py` | 5 (`dcf_valuation`, `comparable_valuation`, `ensemble_valuation`, `sde_valuation`, `arr_valuation`) | ✅ | All fully typed |

**Minor observations:**
- `search_ranking.py` uses `dict | None` union syntax (Python 3.10+) without `from __future__ import annotations` — will fail on Python 3.9.
- `dynamic_pricing.py` and `search_ranking.py` lack `from __future__ import annotations` while other modules include it — inconsistent style.
- Private methods (`_is_feasible`, `_compute_score`, `_compute_confidence`, `_has_cycle_of_length_3_or_4`, `_normalize`, `_jaro_winkler`, `_canonical_name`) are also fully typed — exceeds expectations.

---

## 3. Docstrings

**Status:** ✅ Excellent — all public classes and functions documented.

| File | Module Docstring | Class Docstrings | Method Docstrings |
|---|---|---|---|
| `__init__.py` | ✅ | N/A | N/A |
| `dynamic_pricing.py` | ✅ | ✅ `PriceRecommendation`, `PricingEngine` | ✅ `recommend_price` (Args + Returns) |
| `entity_resolution.py` | ✅ | ✅ `ResolvedEntity`, `EntityCluster`, `EntityResolver` | ✅ `resolve`, `_canonical_name` |
| `evolution.py` | ✅ | ✅ `EvaluationResult`, `Benchmark`, `EvolutionResult`, `EvolutionEngine` | ✅ `evaluate`, `evolve` |
| `fraud_detection.py` | ✅ | ✅ `FraudSignal`, `FraudScore`, `GraphAnalysis`, `FraudDetector` | ✅ `score`, `analyze_graph` |
| `matching.py` | ✅ | ✅ `Buyer`, `Seller`, `Match`, `BuyerSellerMatcher` | ✅ `match`, `_is_feasible`, `_compute_score`, `_compute_confidence` |
| `portfolio_optimizer.py` | ✅ | ✅ `Asset`, `Portfolio`, `PortfolioOptimizer` | ✅ `optimize` |
| `search_ranking.py` | ✅ | ✅ `Listing`, `RankedListing`, `SearchRanker` | ✅ `rank` |
| `valuation.py` | ✅ | ✅ `ValuationResult`, `ValuationEngine` | ✅ All 5 valuation methods |

**Style:** Google-style docstrings with `Args:` and `Returns:` sections. Consistent across all files. Private methods also documented.

---

## 4. Hardcoded Values (Should Be Configurable)

**Status:** ⚠️ Significant — magic numbers scattered throughout.

### 4.1 `dynamic_pricing.py`
| Line | Value | Context |
|---|---|---|
| 44 | `0.8`, `0.4` | Demand multiplier formula |
| 45 | `1.2`, `0.4` | Competition multiplier formula |
| 47–51 | `1.15`, `0.85`, `1.0` | Market condition multipliers |
| 57 | `0.7` | Floor price ratio |
| 58 | `1.5` | Ceiling price ratio |

### 4.2 `entity_resolution.py`
| Line | Value | Context |
|---|---|---|
| 153 | `0.85` | Default threshold (configurable via `__init__`) |
| 196 | `0.2` | Domain match bonus |
| 181 | `3` | Block size (first N chars) |
| 107 | `4` | Jaro-Winkler prefix length |
| 113 | `0.1` | Jaro-Winkler boost factor |

### 4.3 `evolution.py`
| Line | Value | Context |
|---|---|---|
| 129 | `0.001` | Convergence improvement threshold |
| 134 | `5` | Stagnant generations limit |
| 134 | `10` | Minimum generations before convergence check |
| 164 | `0.1` | Mutation scale factor |

### 4.4 `fraud_detection.py`
| Line | Value | Context |
|---|---|---|
| 42–46 | `0.3`, `0.3`, `0.2` | Signal weights (class constant) |
| 47 | `0.1` | Default weight (class constant) |
| 48 | `3` | Total expected signals (class constant) |
| 86–91 | `0.3`, `0.7` | Risk level thresholds |
| 118, 124 | `0.8`, `0.1` | Ring/no-ring risk scores |

### 4.5 `matching.py`
| Line | Value | Context |
|---|---|---|
| 138 | `1.0` | Category bonus (always 1.0 — dead code) |

### 4.6 `portfolio_optimizer.py`
| Line | Value | Context |
|---|---|---|
| 82 | `0.01` | Risk epsilon (prevent div-by-zero) |
| 97 | `1.5` | Diversification bonus |
| 113 | `0.01` | Sharpe ratio epsilon |

### 4.7 `search_ranking.py`
| Line | Value | Context |
|---|---|---|
| 72 | `0.7` | Diversity factor for repeat categories |
| 79 | `1.3` | Personalization factor for preferred category |

### 4.8 `valuation.py`
| Line | Value | Context |
|---|---|---|
| 75, 97, 175, 197 | `0.7`, `0.6` | Confidence values per method |
| 76–77, 98–99, 176–177, 198–199 | `0.85`, `1.15` | Low/high estimate bounds |

**Recommendation:** Extract magic numbers to class-level constants or config parameters. The `FraudDetector` class already demonstrates the right pattern with `WEIGHTS`, `DEFAULT_WEIGHT`, and `TOTAL_EXPECTED_SIGNALS` as class constants.

---

## 5. Error Handling

**Status:** ⚠️ Minimal — no exception handling anywhere.

### 5.1 Missing Input Validation
| File | Method | Risk |
|---|---|---|
| `valuation.py` | `dcf_valuation` | **Division by zero** if `discount_rate == terminal_growth` (line 68: `terminal_value = terminal_fcf / (discount_rate - terminal_growth)`) |
| `valuation.py` | `dcf_valuation` | No validation that `years > 0` |
| `valuation.py` | `comparable_valuation` | No validation that `metric > 0` or `multiple > 0` |
| `fraud_detection.py` | `analyze_graph` | No validation of graph structure (missing `nodes`/`edges` keys) |
| `fraud_detection.py` | `score` | No validation that signal values are in [0, 1] |
| `matching.py` | `match` | No validation that buyer/seller IDs are unique |
| `portfolio_optimizer.py` | `optimize` | No validation that `risk_tolerance` is in [0, 1] |
| `dynamic_pricing.py` | `recommend_price` | No validation that `demand_level`/`competition_level` are in [0, 1] |
| `search_ranking.py` | `rank` | No validation that `relevance` is non-negative |

### 5.2 Graceful Empty-Input Handling ✅
All public methods correctly handle empty inputs:
- `PricingEngine.recommend_price` — N/A (no list inputs)
- `EntityResolver.resolve` — returns `[]` for empty list
- `EvolutionEngine.evolve` — N/A
- `FraudDetector.score` — returns low-risk score with explanation
- `FraudDetector.analyze_graph` — handles missing keys via `.get()`
- `BuyerSellerMatcher.match` — returns `[]` for empty buyers/sellers
- `PortfolioOptimizer.optimize` — returns empty `Portfolio()`
- `SearchRanker.rank` — returns `[]` for empty listings
- `ValuationEngine.*` — N/A (scalar inputs)

### 5.3 No Try/Except Blocks
Zero exception handling across all 9 files. Potential runtime crashes:
- `ZeroDivisionError` in `dcf_valuation` (discount_rate == terminal_growth)
- `ZeroDivisionError` in `_compute_score` if budget is 0 (guarded by `<= 0` check ✅)
- `ZeroDivisionError` in `_compute_confidence` if budget is 0 (guarded by `<= 0` check ✅)
- `KeyError` in `analyze_graph` if graph dict is malformed (partially guarded by `.get()`)
- `TypeError` if wrong types passed (no isinstance checks)

---

## 6. Line Counts

| File | Lines |
|---|---|
| `__init__.py` | 50 |
| `dynamic_pricing.py` | 70 |
| `entity_resolution.py` | 226 |
| `evolution.py` | 194 |
| `fraud_detection.py` | 172 |
| `matching.py` | 156 |
| `portfolio_optimizer.py` | 119 |
| `search_ranking.py` | 103 |
| `valuation.py` | 200 |
| **Total** | **1,290** |

---

## 7. Additional Observations

### 7.1 Dead Code
- `matching.py:138` — `category_bonus = 1.0` is always 1.0 because `_is_feasible` already filters out category mismatches. The variable and multiplication are dead code.

### 7.2 Code Duplication
- `valuation.py` — `comparable_valuation`, `sde_valuation`, and `arr_valuation` are nearly identical (multiply metric by multiple, return with confidence=0.6, bounds=0.85/1.15). Could be refactored into a shared `_simple_multiple_valuation` helper.

### 7.3 Inconsistent `from __future__ import annotations`
- Present in: `entity_resolution.py`, `evolution.py`, `fraud_detection.py`, `matching.py`, `portfolio_optimizer.py`
- Missing in: `dynamic_pricing.py`, `search_ranking.py`, `valuation.py`

### 7.4 `search_ranking.py` Python Version Requirement
- Uses `dict | None` (PEP 604 union syntax) which requires Python 3.10+. Other files use `Optional[dict]` or `from __future__ import annotations` for compatibility.

### 7.5 `fraud_detection.py` Class Constants
- Good pattern: `WEIGHTS`, `DEFAULT_WEIGHT`, `TOTAL_EXPECTED_SIGNALS` are class-level constants. Other modules should follow this pattern for configurability.

### 7.6 `entity_resolution.py` Algorithmic Efficiency
- Jaro-Winkler implementation is O(n*m) per pair comparison — acceptable for the blocking approach but could be optimized with early termination.

### 7.7 `evolution.py` Random Seed
- No way to set random seed for reproducibility. Consider adding a `seed` parameter to `__init__`.

### 7.8 `valuation.py` Confidence Calculation
- `ensemble_valuation` confidence formula: `1 - (high_estimate - low_estimate) / (2 * value)` — if `value` is 0 or negative, this produces incorrect results. No guard.

---

## 8. Summary Scorecard

| Criterion | Rating | Notes |
|---|---|---|
| Compilation | ✅ Pass | All files compile cleanly |
| Type Hints | ✅ Excellent | 100% coverage, including private methods |
| Docstrings | ✅ Excellent | All public + private methods documented |
| Hardcoded Values | ⚠️ Needs Work | Magic numbers throughout; extract to constants |
| Error Handling | ⚠️ Minimal | No try/except, no input validation, potential div-by-zero |
| Code Duplication | ⚠️ Minor | `valuation.py` has 3 near-identical methods |
| Dead Code | ⚠️ Minor | `matching.py` category_bonus always 1.0 |
| Consistency | ⚠️ Minor | `from __future__ import annotations` usage inconsistent |

**Overall:** Well-structured, well-documented, fully typed codebase. Primary gaps are error handling (no exception handling, no input validation) and configurability (magic numbers). The `FraudDetector` class demonstrates the desired pattern for constants — other modules should follow suit.
