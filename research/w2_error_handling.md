# Wave 2: Error Handling Patterns Analysis

**Scope:** All modules in `src/acquisition_platform/`  
**Date:** 2026-10-04  
**Files Analyzed:** 9 Python source files (1,288 total lines)

---

## Executive Summary

| Metric | Count |
|--------|-------|
| Total source files | 9 |
| Files with try/except blocks | **0** |
| Files with custom exception classes | **0** |
| Files with raise statements | **0** |
| Files with bare except clauses | **0** |
| Total crash risks identified | **25** |
| High severity | 1 |
| Medium severity | 5 |
| Low severity | 19 |

**Key Finding:** The entire codebase has **zero** try/except blocks, zero custom exception classes, and zero raise statements. Error handling is entirely absent. The codebase relies on implicit Python behavior (returning empty lists, using `.get()` with defaults, and arithmetic guards like `+0.01`) rather than explicit error handling.

---

## 1. Module-by-Module Analysis

### 1.1 `__init__.py` (50 lines)
- **try/except blocks:** 0
- **Custom exceptions:** 0
- **Error handling:** None needed (pure imports/exports)
- **Crash risks:** None identified

### 1.2 `dynamic_pricing.py` (70 lines)
- **try/except blocks:** 0
- **Custom exceptions:** 0
- **Error handling:** None
- **Public methods:** `recommend_price()`
- **Crash risks:**
  - **MEDIUM:** No input validation on `base_value` (could be None), `demand_level`/`competition_level` (could be outside [0,1]), `market_condition` (any string defaults to 1.0 multiplier silently)
  - **LOW:** Division operations present but safe (no variable denominators)

### 1.3 `entity_resolution.py` (226 lines)
- **try/except blocks:** 0
- **Custom exceptions:** 0
- **Error handling:** Implicit guards only
- **Public methods:** `resolve()`, `_canonical_name()` (static)
- **Crash risks:**
  - **LOW:** `_jaro_winkler()` has proper guards for empty strings (`len1 == 0 or len2 == 0`) and zero matches (`matches == 0`)
  - **LOW:** `_canonical_name()` calls `max(counts.values())` on potentially empty Counter (unreachable in normal flow but unsafe if called directly)
  - **LOW:** `resolve()` uses `.get("name", "")` which is safe, but no validation that entities is a list of dicts
  - **LOW:** `threshold` parameter not validated (could be None or outside [0,1])

### 1.4 `evolution.py` (194 lines)
- **try/except blocks:** 0
- **Custom exceptions:** 0
- **Error handling:** Implicit guards only
- **Public methods:** `evolve()`, `Benchmark.evaluate()`
- **Crash risks:**
  - **MEDIUM:** `population_size=0` causes `max(fitness_scores)` to crash with ValueError on empty list
  - **LOW:** `elitism > population_size` could cause IndexError (though Python slicing is forgiving)
  - **LOW:** No validation on `fitness_fn` (could be None or non-callable)
  - **LOW:** No validation on `gene_range` (could be wrong length or non-numeric)
  - **LOW:** `statistics.stdev()` properly guarded with `if len(final_fitness) > 1`

### 1.5 `fraud_detection.py` (172 lines)
- **try/except blocks:** 0
- **Custom exceptions:** 0
- **Error handling:** Implicit guards only
- **Public methods:** `score()`, `analyze_graph()`
- **Crash risks:**
  - **LOW:** `score()` properly guards division with `if total_weight > 0 else 0.0`
  - **LOW:** `analyze_graph()` uses `.get()` with defaults, but no validation on edge tuples
  - **LOW:** No validation on `signal.value` (could be None or outside [0,1])

### 1.6 `matching.py` (156 lines)
- **try/except blocks:** 0
- **Custom exceptions:** 0
- **Error handling:** Implicit guards only
- **Public methods:** `match()`
- **Crash risks:**
  - **LOW:** `_compute_score()` and `_compute_confidence()` have `if buyer.budget <= 0: return 0.0` guards
  - **LOW:** No validation that `buyer.preferences` and `seller.attributes` are dicts
  - **LOW:** No validation on budget/asking_price types

### 1.7 `portfolio_optimizer.py` (119 lines)
- **try/except blocks:** 0
- **Custom exceptions:** 0
- **Error handling:** Implicit guards only
- **Public methods:** `optimize()`
- **Crash risks:**
  - **LOW:** `asset.expected_return / (asset.risk + 0.01)` properly guarded with +0.01
  - **LOW:** `a.cost / total_cost` could divide by zero if all selected assets have cost=0 (guarded by `if not selected` but not by total_cost check)
  - **LOW:** No validation on `risk_tolerance` (could be None or outside [0,1])

### 1.8 `search_ranking.py` (103 lines)
- **try/except blocks:** 0
- **Custom exceptions:** 0
- **Error handling:** None
- **Public methods:** `rank()`
- **Crash risks:**
  - **MEDIUM:** No validation that listing objects have required attributes (id, title, relevance, category)
  - **LOW:** No validation on `user_preferences` structure

### 1.9 `valuation.py` (200 lines)
- **try/except blocks:** 0
- **Custom exceptions:** 0
- **Error handling:** None
- **Public methods:** `dcf_valuation()`, `comparable_valuation()`, `ensemble_valuation()`, `sde_valuation()`, `arr_valuation()`
- **Crash risks:**
  - **HIGH:** `dcf_valuation()` line 68: `terminal_value = terminal_fcf / (discount_rate - terminal_growth)` — **ZeroDivisionError** if `discount_rate == terminal_growth`
  - **MEDIUM:** `ensemble_valuation()` line 147: `confidence = 1 - (high_estimate - low_estimate) / (2 * value)` — **ZeroDivisionError** if `value == 0`
  - **MEDIUM:** `dcf_valuation()` line 68: If `discount_rate < terminal_growth`, terminal_value becomes negative, producing nonsensical valuation
  - **LOW:** No validation on any input parameters across all valuation methods
  - **LOW:** `years=0` produces unexpected results (loop doesn't execute but terminal value still calculated)

---

## 2. Modules WITH try/except Blocks

**None.** Zero modules contain try/except blocks.

---

## 3. Modules LACKING Error Handling

**All 9 modules** lack explicit error handling. The codebase relies on:

1. **Implicit guards:** `if not entities: return []`, `if not signals: return FraudScore(...)`
2. **Default values:** `.get("name", "")`, `.get("category")`
3. **Arithmetic guards:** `+ 0.01` to prevent division by zero
4. **Python's forgiving behavior:** Slicing beyond bounds, `.get()` returning None

---

## 4. Custom Exception Classes

**None found.** The codebase defines zero custom exception classes. All exceptions would be built-in Python exceptions (ZeroDivisionError, ValueError, TypeError, etc.).

---

## 5. Edge Cases That Could Crash

### 5.1 Division by Zero (2 unmitigated cases)

| Location | Function | Line | Trigger |
|----------|----------|------|---------|
| `valuation.py` | `dcf_valuation` | 68 | `discount_rate == terminal_growth` |
| `valuation.py` | `ensemble_valuation` | 147 | `value == 0` (both DCF and comps return 0) |

### 5.2 Empty Lists (1 unmitigated case)

| Location | Function | Line | Trigger |
|----------|----------|------|---------|
| `evolution.py` | `evolve` | 123 | `population_size=0` → `max([])` raises ValueError |

### 5.3 None Values (widespread)

Multiple functions accept parameters that could be None without validation:
- `dynamic_pricing.recommend_price(base_value=None, ...)`
- `search_ranker.rank(query, [None], ...)`
- `entity_resolution.resolve([None, ...])`
- `matching.match([Buyer(..., preferences=None)], ...)`
- `fraud_detection.score([FraudSignal(..., value=None)])`

### 5.4 Type Errors (widespread)

No type validation on any public method parameters. Examples:
- `evolution.evolve(fitness_fn=None, ...)` → TypeError when calling None
- `evolution.evolve(..., gene_range=(1,))` → ValueError on unpacking
- `valuation.comparable_valuation(metric=None, ...)` → TypeError on multiplication

### 5.5 Range Validation (widespread)

Parameters documented as normalized to [0,1] have no range checking:
- `dynamic_pricing.recommend_price(demand_level=2.0, competition_level=-1.0, ...)`
- `portfolio_optimizer.optimize(assets, risk_tolerance=100)`
- `entity_resolution.EntityResolver(threshold=2.0)`

---

## 6. Input Validation in Public Methods

| Module | Public Method | Validation Present | Missing Validation |
|--------|---------------|--------------------|--------------------|
| `dynamic_pricing` | `recommend_price` | None | All parameters |
| `entity_resolution` | `resolve` | `if not entities: return []` | Entity structure, threshold range |
| `entity_resolution` | `_canonical_name` | None | Empty list (unreachable in normal flow) |
| `evolution` | `evolve` | `if len(final_fitness) > 1` | fitness_fn callable, gene_range valid, population_size > 0 |
| `evolution` | `Benchmark.evaluate` | None | actual is numeric |
| `fraud_detection` | `score` | `if not signals: return ...`, `if total_weight > 0` | Signal value range |
| `fraud_detection` | `analyze_graph` | `.get()` defaults | Edge tuple validity |
| `matching` | `match` | `if not buyers or not sellers: return []` | Buyer/seller attribute types |
| `matching` | `_compute_score` | `if buyer.budget <= 0: return 0.0` | budget is numeric |
| `matching` | `_compute_confidence` | `if buyer.budget <= 0: return 0.0` | budget is numeric |
| `portfolio_optimizer` | `optimize` | `if not assets: return Portfolio()`, `if not affordable: return Portfolio()`, `if not selected: return Portfolio()` | risk_tolerance range, asset attribute types |
| `search_ranking` | `rank` | `if not listings: return []` | Listing attribute types |
| `valuation` | `dcf_valuation` | None | All parameters, discount_rate != terminal_growth |
| `valuation` | `comparable_valuation` | None | All parameters |
| `valuation` | `ensemble_valuation` | None | All parameters, value != 0 |
| `valuation` | `sde_valuation` | None | All parameters |
| `valuation` | `arr_valuation` | None | All parameters |

---

## 7. Summary of Findings

### Strengths
- Consistent use of `.get()` with defaults for dict access
- Guard clauses for empty collections (`if not X: return ...`)
- Arithmetic guards (`+ 0.01`) to prevent division by zero in most cases
- Proper handling of edge cases in `_jaro_winkler()` (empty strings, zero matches)
- `statistics.stdev()` properly guarded against single-element lists

### Weaknesses
- **Zero try/except blocks** across 1,288 lines of code
- **Zero custom exception classes** — no domain-specific error types
- **Zero raise statements** — no explicit error signaling
- **No input validation** on any public method parameters
- **Two unmitigated ZeroDivisionError risks** in valuation.py
- **One unmitigated ValueError risk** in evolution.py (empty population)
- **Silent failures** — invalid inputs produce wrong results rather than errors (e.g., `market_condition="invalid"` defaults to 1.0 multiplier)
- **No type checking** — None values propagate until they cause TypeError/AttributeError deep in call stack

### Risk Distribution
- **HIGH:** 1 (valuation.py dcf_valuation division by zero)
- **MEDIUM:** 5 (ensemble_valuation division by zero, negative terminal value, empty population, no input validation in dynamic_pricing, no validation in search_ranking)
- **LOW:** 19 (various missing validations, mitigated division risks, type safety issues)

---

## 8. Recommendations

1. **Add input validation** to all public methods using `isinstance()` checks and range validation
2. **Define custom exception classes** (e.g., `ValidationError`, `ComputationError`) for domain-specific errors
3. **Add try/except blocks** around division operations in `valuation.py`
4. **Validate constructor parameters** (e.g., `population_size > 0`, `threshold` in [0,1])
5. **Add type hints enforcement** or runtime type checking for critical parameters
6. **Raise ValueError** for invalid inputs rather than silently producing wrong results
7. **Add unit tests** for edge cases (empty lists, None values, boundary conditions)
