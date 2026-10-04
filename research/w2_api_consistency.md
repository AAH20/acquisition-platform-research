# Wave 2: API Consistency Analysis

**Scope:** `src/acquisition_platform/*.py` (9 modules)
**Focus:** Naming conventions, parameter ordering, return types, error handling, and API inconsistencies

---

## 1. Naming Conventions

### 1.1 Module Names
All modules use `snake_case` — **consistent**.

| Module | Pattern |
|--------|---------|
| `matching.py` | snake_case |
| `valuation.py` | snake_case |
| `fraud_detection.py` | snake_case |
| `portfolio_optimizer.py` | snake_case |
| `dynamic_pricing.py` | snake_case |
| `entity_resolution.py` | snake_case |
| `search_ranking.py` | snake_case |
| `evolution.py` | snake_case |

### 1.2 Class Names
All classes use `PascalCase` — **consistent**.

### 1.3 Method Names — INCONSISTENT

Two competing patterns coexist:

| Pattern | Methods |
|---------|---------|
| `verb_noun` (ValuationEngine) | `dcf_valuation`, `comparable_valuation`, `ensemble_valuation`, `sde_valuation`, `arr_valuation` |
| `verb` (all other engines) | `match`, `optimize`, `resolve`, `score`, `rank`, `recommend_price`, `evolve` |

**Impact:** Users must remember which engine uses which pattern. The ValuationEngine's `*_valuation` suffix is redundant — the class name already implies valuation.

### 1.4 Private Methods
All use `_underscore_prefix` — **consistent**.

### 1.5 Constants
All use `UPPER_SNAKE_CASE` — **consistent** (`WEIGHTS`, `DEFAULT_WEIGHT`, `TOTAL_EXPECTED_SIGNALS`).

---

## 2. Parameter Ordering

### 2.1 Primary Value First — CONSISTENT within ValuationEngine

All ValuationEngine methods put the primary financial metric first:

```python
dcf_valuation(free_cash_flow, growth_rate, discount_rate, terminal_growth, years)
comparable_valuation(metric, multiple)
sde_valuation(sde, multiple)
arr_valuation(arr, multiple)
```

### 2.2 Ensemble Method — INCONSISTENT

`ensemble_valuation` mixes DCF and Comps parameters without clear grouping:

```python
ensemble_valuation(free_cash_flow, revenue, growth_rate, discount_rate, terminal_growth, revenue_multiple, years)
```

The DCF params (`free_cash_flow`, `growth_rate`, `discount_rate`, `terminal_growth`, `years`) and Comps params (`revenue`, `revenue_multiple`) are interleaved. A clearer ordering would group by method:

```python
# Proposed: group DCF params, then Comps params
ensemble_valuation(free_cash_flow, growth_rate, discount_rate, terminal_growth, years, revenue, revenue_multiple)
```

### 2.3 Cross-Module Comparison — CONSISTENT

All engines follow a "data first, config second" pattern:

| Method | Data Params | Config Params |
|--------|-------------|---------------|
| `PortfolioOptimizer.optimize` | `assets` | `risk_tolerance` |
| `BuyerSellerMatcher.match` | `buyers`, `sellers` | — |
| `EntityResolver.resolve` | `entities` | — |
| `PricingEngine.recommend_price` | `base_value` | `demand_level`, `competition_level`, `market_condition` |
| `SearchRanker.rank` | `query`, `listings` | `user_preferences` |
| `EvolutionEngine.evolve` | `fitness_fn` | `gene_range` |

---

## 3. Return Types

### 3.1 Result Dataclasses — CONSISTENT

Every public method returns a dedicated result dataclass:

| Method | Return Type |
|--------|-------------|
| `PortfolioOptimizer.optimize` | `Portfolio` |
| `BuyerSellerMatcher.match` | `list[Match]` |
| `EntityResolver.resolve` | `list[EntityCluster]` |
| `ValuationEngine.*` | `ValuationResult` |
| `PricingEngine.recommend_price` | `PriceRecommendation` |
| `FraudDetector.score` | `FraudScore` |
| `FraudDetector.analyze_graph` | `GraphAnalysis` |
| `SearchRanker.rank` | `list[RankedListing]` |
| `EvolutionEngine.evolve` | `EvolutionResult` |
| `Benchmark.evaluate` | `EvaluationResult` |

### 3.2 GraphAnalysis Inheritance — INCONSISTENT

`GraphAnalysis` inherits from `FraudScore` but adds `has_ring` and `risk_score` fields. The `risk_score` field **duplicates** the inherited `score` field:

```python
@dataclass
class GraphAnalysis(FraudScore):
    has_ring: bool = False
    risk_score: float = 0.0  # Duplicates FraudScore.score
```

**Impact:** Callers see two fields with the same semantic meaning. The `analyze_graph` method sets both `score=risk_score` and `risk_score=risk_score`, which is redundant and confusing.

### 3.3 Dead Code — `ResolvedEntity`

`ResolvedEntity` dataclass is defined in `entity_resolution.py` but **never used**. `EntityCluster` is the actual return type. This is dead code that confuses users about which type to expect.

---

## 4. Error Handling Patterns

### 4.1 Empty Input Handling — INCONSISTENT

| Method | Empty Input Behavior |
|--------|---------------------|
| `PortfolioOptimizer.optimize` | Returns `Portfolio()` (empty) |
| `BuyerSellerMatcher.match` | Returns `[]` |
| `EntityResolver.resolve` | Returns `[]` |
| `FraudDetector.score` | Returns `FraudScore(score=0, risk_level="low", confidence=0)` |
| `SearchRanker.rank` | Returns `[]` |
| `ValuationEngine.*` | **No handling** — will crash on division by zero |
| `PricingEngine.recommend_price` | **No handling** — will produce NaN/inf |
| `FraudDetector.analyze_graph` | **No handling** — will crash on malformed graph |
| `EvolutionEngine.evolve` | **No handling** — will crash on invalid `gene_range` |

### 4.2 Division by Zero Risk

`ValuationEngine.dcf_valuation` will raise `ZeroDivisionError` if `discount_rate == terminal_growth`:

```python
terminal_value = terminal_fcf / (discount_rate - terminal_growth)  # Crash if equal
```

### 4.3 Type Validation — ABSENT

No method validates input types or ranges. For example:
- `PricingEngine.recommend_price` accepts any `market_condition` string (uses `.get()` with default 1.0, silently ignoring invalid values)
- `SearchRanker.rank` accepts any `user_preferences` dict
- `FraudDetector.score` accepts any `FraudSignal` list without validating signal names

---

## 5. API Inconsistencies That Would Confuse Users

### 5.1 Confidence Semantics — INCONSISTENT

| Method | Confidence Calculation |
|--------|----------------------|
| `ValuationEngine.dcf_valuation` | Hardcoded `0.7` |
| `ValuationEngine.comparable_valuation` | Hardcoded `0.6` |
| `ValuationEngine.sde_valuation` | Hardcoded `0.6` |
| `ValuationEngine.arr_valuation` | Hardcoded `0.6` |
| `ValuationEngine.ensemble_valuation` | Calculated from method agreement |
| `PricingEngine.recommend_price` | `1 - abs(demand_level - competition_level)` |
| `FraudDetector.score` | `1 - (missing_signals / total_expected)` |
| `FraudDetector.analyze_graph` | Hardcoded `1.0` |

**Problem:** "Confidence" means different things in different methods. Users cannot compare confidence scores across modules.

### 5.2 Risk Level Taxonomy — INCONSISTENT

| Module | Risk Levels |
|--------|-------------|
| `FraudDetector.score` | `low` (< 0.3), `medium` (0.3-0.7), `high` (> 0.7) |
| `FraudDetector.analyze_graph` | `low` (0.1), `high` (0.8) — binary |

**Problem:** The same `risk_level` string has different meanings depending on which method produced it.

### 5.3 Field Naming for Equivalent Concepts — INCONSISTENT

| Concept | ValuationResult | PriceRecommendation |
|---------|----------------|---------------------|
| Lower bound | `low_estimate` | `floor_price` |
| Upper bound | `high_estimate` | `ceiling_price` |

**Problem:** Users must remember different field names for the same semantic concept.

### 5.4 Constructor Configurability — INCONSISTENT

| Engine | Constructor Params |
|--------|-------------------|
| `PortfolioOptimizer` | `budget` (required), `max_assets=10` |
| `EntityResolver` | `threshold=0.85` |
| `EvolutionEngine` | `population_size=50`, `generations=20`, `mutation_rate=0.1`, `elitism=2` |
| `BuyerSellerMatcher` | None (default) |
| `ValuationEngine` | None (default) |
| `PricingEngine` | None (default) |
| `FraudDetector` | None (default) |
| `SearchRanker` | None (default) |

**Problem:** Some engines are configurable at construction time, others are not. Users cannot predict which engines accept configuration.

### 5.5 Type Hint Coverage — INCONSISTENT

| Module | Parameter Type Hints |
|--------|---------------------|
| `ValuationEngine` | **None** (only return types) |
| `PortfolioOptimizer` | Full |
| `BuyerSellerMatcher` | Full |
| `EntityResolver` | Full |
| `PricingEngine` | Full |
| `FraudDetector` | Full |
| `SearchRanker` | Full |
| `EvolutionEngine` | Full |
| `Benchmark` | Full |

**Problem:** ValuationEngine is the only module without parameter type hints, making it harder to use with IDEs and type checkers.

### 5.6 Docstring Style — INCONSISTENT

| Module | Style |
|--------|-------|
| `EntityResolver` | NumPy-style (`Parameters`, `Returns` with type annotations) |
| All others | Google-style (`Args:`, `Returns:`) |

**Problem:** Users must parse different docstring formats depending on which module they're reading.

### 5.7 `from __future__ import annotations` — INCONSISTENT

| Module | Has Future Import |
|--------|------------------|
| `matching.py` | Yes |
| `entity_resolution.py` | Yes |
| `evolution.py` | Yes |
| `portfolio_optimizer.py` | Yes |
| `fraud_detection.py` | Yes |
| `valuation.py` | **No** |
| `dynamic_pricing.py` | **No** |
| `search_ranking.py` | **No** (but uses `dict \| None` syntax) |

**Problem:** `search_ranking.py` uses `dict | None` (Python 3.10+ union syntax) without the future import, which will fail on Python < 3.10. The future import is present in some files but not others.

### 5.8 Method Signature for Similar Operations — INCONSISTENT

`FraudDetector` has two analysis methods with different input types:

```python
def score(self, signals: list[FraudSignal]) -> FraudScore
def analyze_graph(self, graph: dict[str, Any]) -> GraphAnalysis
```

**Problem:** Both methods "analyze" fraud but take completely different input types. Users must know which method to call based on their data format.

---

## 6. Summary of Findings

### Critical Inconsistencies (Would Confuse Users)

1. **Method naming:** ValuationEngine uses `*_valuation` suffix; all others use simple verbs
2. **Confidence semantics:** Same field name, different calculation methods across modules
3. **Risk level taxonomy:** Different thresholds and level counts across modules
4. **Field naming:** `low_estimate`/`high_estimate` vs `floor_price`/`ceiling_price` for equivalent concepts
5. **Error handling:** Some methods handle empty inputs gracefully; others crash
6. **Type hints:** ValuationEngine lacks parameter type hints; all others have them
7. **Docstring style:** EntityResolver uses NumPy-style; all others use Google-style
8. **Dead code:** `ResolvedEntity` is defined but never used
9. **GraphAnalysis field duplication:** `risk_score` duplicates inherited `score` field

### Minor Inconsistencies (Code Quality)

10. **Constructor configurability:** Some engines accept config, others don't
11. **`from __future__ import annotations`:** Present in some files, absent in others
12. **Ensemble parameter ordering:** DCF and Comps params interleaved without grouping

### Consistent Patterns (Good)

- Module names: all `snake_case`
- Class names: all `PascalCase`
- Private methods: all `_underscore_prefix`
- Constants: all `UPPER_SNAKE_CASE`
- Return types: all dedicated result dataclasses
- Parameter ordering: "data first, config second" across all engines

---

## 7. Recommendations

1. **Standardize method naming:** Rename ValuationEngine methods to `dcf`, `comparable`, `ensemble`, `sde`, `arr` (drop `_valuation` suffix)
2. **Standardize confidence:** Define a common confidence calculation strategy or document the differences
3. **Standardize risk levels:** Use a shared enum or constant set across modules
4. **Standardize field names:** Use `low_estimate`/`high_estimate` or `floor_price`/`ceiling_price` consistently
5. **Add input validation:** All methods should handle empty/invalid inputs gracefully
6. **Add type hints to ValuationEngine:** Match the coverage in other modules
7. **Standardize docstring style:** Convert EntityResolver to Google-style
8. **Remove dead code:** Delete `ResolvedEntity` or use it as the return type
9. **Fix GraphAnalysis:** Remove `risk_score` field or make it a property alias
10. **Add `from __future__ import annotations`:** To all modules for consistency
11. **Group ensemble parameters:** Order DCF params together, then Comps params
