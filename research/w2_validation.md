# Wave 2: Validation & Input Sanitization Analysis

**Scope:** `src/acquisition_platform/*.py` (9 files)  
**Date:** 2026-10-04  
**Method:** Manual code review of all public methods accepting external input

---

## Summary

The acquisition platform has **minimal input validation** across all modules. Most methods accept parameters with documented constraints (e.g., "normalized in [0, 1]") but perform zero runtime checks. This creates crash risks, silent incorrect results, and potential division-by-zero errors.

---

## File-by-File Analysis

### 1. `dynamic_pricing.py` — `PricingEngine.recommend_price()`

| Parameter | Documented Constraint | Actual Validation | Risk |
|---|---|---|---|
| `base_value: float` | None | None | Negative/zero values produce nonsensical prices |
| `demand_level: float` | [0, 1] | **NONE** | Values outside range distort pricing |
| `competition_level: float` | [0, 1] | **NONE** | Values outside range distort pricing |
| `market_condition: str` | "bull", "bear", "normal" | Silent fallback to 1.0 | Invalid strings silently accepted |

**Critical gaps:**
- No range check on `demand_level` or `competition_level` (documented as [0, 1])
- Invalid `market_condition` silently defaults to 1.0 multiplier — no error raised
- No type validation (passing `None` or strings causes `TypeError` on arithmetic)

---

### 2. `entity_resolution.py` — `EntityResolver`

| Method/Parameter | Validation Present | Missing Validation |
|---|---|---|
| `__init__(threshold)` | Default 0.85 | No range check — threshold could be negative or > 1 |
| `resolve(entities)` | `if not entities: return []` | No type check on entities; no check that items are dicts |
| `_normalize(name)` | None | `re.sub` crashes if `name` is not a string |
| `_canonical_name(entities)` | None | Assumes all names are strings for `Counter` |

**Critical gaps:**
- `threshold` not validated to [0, 1] — negative threshold matches everything, > 1 matches nothing
- `e.get("name", "")` returns `""` for missing key, but if `name` is explicitly `None`, `re.sub` crashes
- No validation that `entities` is a list (could be `None`, dict, etc.)

---

### 3. `evolution.py` — `EvolutionEngine`

| Method/Parameter | Validation Present | Missing Validation |
|---|---|---|
| `__init__(population_size)` | Default 50 | No check for 0 or negative |
| `__init__(generations)` | Default 20 | No check for 0 or negative |
| `__init__(mutation_rate)` | Default 0.1 | No range check — should be [0, 1] |
| `__init__(elitism)` | Default 2 | No check for negative or > population_size |
| `evolve(fitness_fn, gene_range)` | None | No check that `fitness_fn` is callable; no check that `gene_range` is a 2-tuple |

**Critical gaps:**
- `low, high = gene_range` crashes with `ValueError` if `gene_range` doesn't have exactly 2 elements
- `mutation_rate` outside [0, 1] causes unexpected behavior (negative = never mutates, > 1 = always mutates)
- `population_size <= 0` causes `random.sample` to crash or produce empty population
- `elitism > population_size` causes `sorted_indices[:self.elitism]` to silently return fewer elites

---

### 4. `fraud_detection.py` — `FraudDetector`

| Method/Parameter | Validation Present | Missing Validation |
|---|---|---|
| `score(signals)` | `if not signals: return ...` | No type check; no validation of signal attributes |
| `signal.name` | Used as dict key | No check for `None` or non-string |
| `signal.value` | Used in arithmetic | No range check — should be [0, 1] |
| `analyze_graph(graph)` | None | No check that `graph` is a dict |
| `graph["nodes"]` | Default `[]` | No check that it's a list |
| `graph["edges"]` | Default `[]` | No check that it's a list of 2-tuples |

**Critical gaps:**
- `signal.value` outside [0, 1] produces fraud scores outside expected range
- `src, dst = edge` crashes if edge is not a 2-element tuple/list
- `adjacency[node]` crashes if `node` is unhashable (e.g., a list)
- `graph.get("nodes", [])` returns `[]` for missing key, but if `nodes` is explicitly `None`, `{node: set() for node in None}` crashes

---

### 5. `matching.py` — `BuyerSellerMatcher`

| Method/Parameter | Validation Present | Missing Validation |
|---|---|---|
| `match(buyers, sellers)` | `if not buyers or not sellers: return []` | No type validation on list elements |
| `buyer.budget` | Checked in `_compute_score` (`<= 0`) | No check in `_is_feasible` — negative budget passes feasibility |
| `seller.asking_price` | None | No check for negative values |
| `buyer.preferences` | None | `.get()` crashes if `preferences` is `None` |
| `seller.attributes` | None | `.get()` crashes if `attributes` is `None` |

**Critical gaps:**
- `buyer.preferences.get("category")` raises `AttributeError` if `preferences` is `None`
- `seller.attributes.get("category")` raises `AttributeError` if `attributes` is `None`
- Negative `asking_price` produces inflated match scores
- Negative `budget` not filtered in `_is_feasible` — only caught later in scoring

---

### 6. `portfolio_optimizer.py` — `PortfolioOptimizer`

| Method/Parameter | Validation Present | Missing Validation |
|---|---|---|
| `__init__(budget)` | None | No check for negative or zero budget |
| `__init__(max_assets)` | Default 10 | No check for 0 or negative |
| `optimize(assets, risk_tolerance)` | `if not assets: return Portfolio()` | No range check on `risk_tolerance` |
| `asset.cost` | Filtered by `a.cost <= self.budget` | No check for negative cost |
| `asset.risk` | Used in denominator (`risk + 0.01`) | No range check — should be [0, 1] |
| `asset.expected_return` | None | No check for negative values |

**Critical gaps:**
- `risk_tolerance` documented as "0-1" but no validation — negative values invert risk preference
- `budget <= 0` causes all assets to be filtered out (silent empty portfolio)
- `max_assets <= 0` causes immediate break in selection loop
- Negative `asset.risk` produces negative `total_risk`, making `sharpe_ratio` negative

---

### 7. `search_ranking.py` — `SearchRanker`

| Method/Parameter | Validation Present | Missing Validation |
|---|---|---|
| `rank(query, listings, user_preferences)` | `if not listings: return []` | `query` is accepted but **never used** (dead parameter) |
| `listing.relevance` | None | No range check — should be [0, 1] |
| `user_preferences` | None | No type check — `.get()` crashes if not a dict |

**Critical gaps:**
- `query` parameter is completely ignored — misleading API
- `listing.relevance` outside [0, 1] produces unexpected ranking scores
- `user_preferences.get("category")` crashes if `user_preferences` is a non-dict truthy value

---

### 8. `valuation.py` — `ValuationEngine`

| Method/Parameter | Validation Present | Missing Validation |
|---|---|---|
| `dcf_valuation(free_cash_flow, ...)` | None | No validation on any parameter |
| `discount_rate` | None | **Division by zero risk** if `discount_rate == terminal_growth` |
| `terminal_growth` | None | Must be < `discount_rate` for valid terminal value |
| `years` | None | `range(1, years + 1)` crashes if `years` is not int; empty if negative |
| `comparable_valuation(metric, multiple)` | None | No check for negative metric or multiple |
| `ensemble_valuation(...)` | None | Inherits all DCF issues; no validation on revenue/multiple |
| `sde_valuation(sde, multiple)` | None | No validation |
| `arr_valuation(arr, multiple)` | None | No validation |

**Critical gaps:**
- `discount_rate - terminal_growth == 0` causes `ZeroDivisionError` in terminal value calculation
- `terminal_growth >= discount_rate` produces negative terminal value (mathematically invalid)
- `years` as non-integer crashes `range()`; negative `years` produces empty range (silent wrong result)
- Negative `free_cash_flow` produces negative valuation (mathematically valid but likely unintended)
- Negative `multiple` produces negative valuation

---

## Top 15 Most Critical Validation Gaps

Ranked by severity (crash risk > silent incorrect results > API misuse):

| # | Location | Issue | Severity | Impact |
|---|---|---|---|---|
| 1 | `valuation.py:68` | `discount_rate - terminal_growth` can be zero → `ZeroDivisionError` | **CRASH** | DCF valuation crashes |
| 2 | `evolution.py:108` | `low, high = gene_range` crashes if not exactly 2 elements | **CRASH** | Evolution engine crashes |
| 3 | `matching.py:118-119` | `buyer.preferences.get()` / `seller.attributes.get()` crash if `None` | **CRASH** | Matching crashes on malformed input |
| 4 | `fraud_detection.py:110` | `src, dst = edge` crashes if edge is not a 2-tuple | **CRASH** | Graph analysis crashes |
| 5 | `entity_resolution.py:47` | `re.sub` crashes if `name` is not a string | **CRASH** | Entity resolution crashes |
| 6 | `valuation.py:63` | `range(1, years + 1)` crashes if `years` is not int; silent empty if negative | **CRASH/SILENT** | DCF produces wrong result or crashes |
| 7 | `dynamic_pricing.py:44-45` | `demand_level`/`competition_level` not validated to [0, 1] | **SILENT** | Pricing produces out-of-range multipliers |
| 8 | `portfolio_optimizer.py:55` | `risk_tolerance` not validated to [0, 1] | **SILENT** | Risk preference inverted or amplified |
| 9 | `portfolio_optimizer.py:44` | `budget` not validated to be > 0 | **SILENT** | All assets filtered out, empty portfolio |
| 10 | `entity_resolution.py:153` | `threshold` not validated to [0, 1] | **SILENT** | Negative threshold matches all; > 1 matches none |
| 11 | `fraud_detection.py:71` | `signal.value` not validated to [0, 1] | **SILENT** | Fraud score outside expected range |
| 12 | `dynamic_pricing.py:52` | Invalid `market_condition` silently defaults to 1.0 | **SILENT** | Wrong market multiplier applied |
| 13 | `evolution.py:76-79` | `population_size`, `generations`, `mutation_rate` not validated | **SILASH** | GA produces invalid population or never converges |
| 14 | `search_ranking.py:42` | `query` parameter accepted but never used | **API MISLEAD** | Callers believe query affects ranking |
| 15 | `valuation.py:80-100` | `comparable_valuation` has no validation on `metric` or `multiple` | **SILENT** | Negative multiples produce negative valuations |

---

## Recommendations

### Immediate (Crash Prevention)
1. Add type hints enforcement or `isinstance()` checks at method entry points
2. Validate `gene_range` is a 2-tuple before unpacking
3. Check `discount_rate > terminal_growth` before DCF calculation
4. Validate `preferences` and `attributes` are dicts before calling `.get()`
5. Validate edge tuples have exactly 2 elements before unpacking

### High Priority (Silent Correctness)
6. Add range validation for all parameters documented as [0, 1] (`demand_level`, `competition_level`, `risk_tolerance`, `threshold`, `signal.value`, `listing.relevance`)
7. Validate `budget > 0` in `PortfolioOptimizer.__init__`
8. Validate `years` is a positive integer in DCF methods
9. Raise `ValueError` for invalid `market_condition` instead of silent fallback

### Medium Priority (API Quality)
10. Remove or implement the unused `query` parameter in `SearchRanker.rank()`
11. Add `__post_init__` validation to dataclasses (`Buyer`, `Seller`, `Asset`, `Listing`, `FraudSignal`)
12. Consider using `pydantic` or `attrs` validators for declarative validation

---

## Files Analyzed

- `src/acquisition_platform/__init__.py` (no validation needed — pure exports)
- `src/acquisition_platform/dynamic_pricing.py`
- `src/acquisition_platform/entity_resolution.py`
- `src/acquisition_platform/evolution.py`
- `src/acquisition_platform/fraud_detection.py`
- `src/acquisition_platform/matching.py`
- `src/acquisition_platform/portfolio_optimizer.py`
- `src/acquisition_platform/search_ranking.py`
- `src/acquisition_platform/valuation.py`
