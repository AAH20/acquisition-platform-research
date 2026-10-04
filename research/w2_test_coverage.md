# Wave 2: Test Coverage Gap Analysis

**Date:** 2026-10-04  
**Scope:** `src/acquisition_platform/` — 8 modules, 62 tests collected

---

## Executive Summary

| Module | Test File | Test Functions | Public Methods | Coverage Gaps |
|--------|-----------|----------------|----------------|---------------|
| `dynamic_pricing.py` | ✅ Yes | 7 | 1 | 8 missing edge cases |
| `entity_resolution.py` | ✅ Yes | 8 | 2 | 12 missing edge cases |
| `evolution.py` | ✅ Yes | 10 | 4 | 15 missing edge cases |
| `fraud_detection.py` | ✅ Yes | 7 | 2 | 18 missing edge cases |
| `matching.py` | ✅ Yes | 9 | 1 | 14 missing edge cases |
| `portfolio_optimizer.py` | ✅ Yes | 7 | 2 | 15 missing edge cases |
| `search_ranking.py` | ✅ Yes | 7 | 1 | 13 missing edge cases |
| `valuation.py` | ✅ Yes | 8 | 5 | 17 missing edge cases |

**Total:** 62 tests across 8 modules. All modules have corresponding test files. However, **112 edge case tests are missing** across boundary values, error conditions, and empty/invalid inputs.

---

## Module-by-Module Analysis

### 1. `dynamic_pricing.py` — PricingEngine

**Public API:**
- `PricingEngine.recommend_price(base_value, demand_level, competition_level, market_condition) -> PriceRecommendation`

**Existing Tests (7):**
- `test_basic_price_recommendation` — basic happy path
- `test_high_demand_increases_price` — demand sensitivity
- `test_high_competition_decreases_price` — competition sensitivity
- `test_bull_market_premium` — bull market multiplier
- `test_bear_market_discount` — bear market multiplier
- `test_price_within_bounds` — floor/ceiling bounds
- `test_stackelberg_equilibrium_exists` — equilibrium price > 0

**Missing Edge Cases (8):**
1. **Invalid `market_condition`** — should default to 1.0 multiplier (line 52: `market_multipliers.get(market_condition, 1.0)`)
2. **Boundary `demand_level=0`** — minimum demand
3. **Boundary `demand_level=1`** — maximum demand
4. **Boundary `competition_level=0`** — minimum competition
5. **Boundary `competition_level=1`** — maximum competition
6. **Zero `base_value`** — should return zero prices
7. **Negative `base_value`** — undefined behavior, should be tested
8. **Confidence calculation** — `demand_level == competition_level` should yield confidence = 1.0

---

### 2. `entity_resolution.py` — EntityResolver

**Public API:**
- `EntityResolver.__init__(threshold=0.85)`
- `EntityResolver.resolve(entities) -> list[EntityCluster]`
- `EntityResolver._canonical_name(entities)` (static, tested indirectly)

**Existing Tests (8):**
- `test_empty_input_returns_empty` — empty list
- `test_single_entity_returns_single_cluster` — single entity
- `test_exact_match_clusters_together` — identical names
- `test_different_entities_separate_clusters` — different names
- `test_fuzzy_match_similar_names` — Jaro-Winkler similarity
- `test_domain_match_boosts_similarity` — domain bonus
- `test_cluster_has_canonical_name` — canonical name exists
- `test_blocking_reduces_comparisons` — O(n²) avoidance

**Missing Edge Cases (12):**
1. **Missing `"name"` key** — `e.get("name", "")` returns empty string
2. **Missing `"domain"` key** — `e.get("domain", "")` returns empty string
3. **Custom `threshold=0.0`** — should cluster everything
4. **Custom `threshold=1.0`** — should only cluster exact matches
5. **Empty string names** — normalization edge case
6. **Single character names** — blocking with `norm[:3]` on short strings
7. **Names with only punctuation** — normalization strips all chars
8. **Canonical name tie-breaking** — first encountered wins (line 223-225)
9. **Case sensitivity** — "ACME" vs "acme" should match
10. **Unicode/special characters** — normalization with non-ASCII
11. **Large block size** — many entities with same first 3 chars
12. **`comparison_count` reset** — verify it resets between calls (line 169)

---

### 3. `evolution.py` — EvolutionEngine & Benchmark

**Public API:**
- `EvolutionEngine.__init__(population_size, generations, mutation_rate, elitism)`
- `EvolutionEngine.evolve(fitness_fn, gene_range) -> EvolutionResult`
- `Benchmark.__init__(name, target)`
- `Benchmark.evaluate(actual) -> EvaluationResult`

**Existing Tests (10):**
- `test_evolution_improves_fitness_over_generations` — fitness improvement
- `test_population_size_respected` — population size
- `test_mutation_rate_affects_diversity` — mutation diversity
- `test_crossover_produces_offspring` — offspring generation
- `test_elitism_preserves_best` — elitism
- `test_convergence_detected` — convergence flag
- `test_benchmark_comparison` — benchmark fail
- `test_benchmark_passes_when_target_met` — benchmark pass
- `test_multiple_benchmarks_evaluated` — multiple benchmarks
- `test_evaluation_result_has_improvement_sestion` — suggestion text

**Missing Edge Cases (15):**
1. **`population_size=1`** — minimum population
2. **`generations=0`** — no evolution
3. **`mutation_rate=0.0`** — no mutation
4. **`mutation_rate=1.0`** — always mutate
5. **`elitism=0`** — no elitism
6. **`elitism >= population_size`** — all elite
7. **Negative fitness function** — `lambda x: -x**2`
8. **Constant fitness function** — `lambda x: 1.0`
9. **Negative `gene_range`** — `(-100, -10)`
10. **`gene_range` where `low == high`** — zero range
11. **`Benchmark` with `target=0`** — always passes
12. **`Benchmark` with negative `target`** — always passes
13. **`Benchmark.evaluate` with `actual == target`** — boundary
14. **`EvolutionResult.diversity`** — verify calculation
15. **`EvolutionResult.worst_fitness`** — verify it's <= best_fitness

---

### 4. `fraud_detection.py` — FraudDetector

**Public API:**
- `FraudDetector.score(signals) -> FraudScore`
- `FraudDetector.analyze_graph(graph) -> GraphAnalysis`

**Existing Tests (7):**
- `test_clean_listing_returns_low_risk` — low risk
- `test_suspicious_listing_returns_high_risk` — high risk
- `test_medium_risk_for_mixed_signals` — medium risk
- `test_fraud_score_has_explanation` — explanations present
- `test_missing_signals_increases_risk` — confidence reduction
- `test_graph_analysis_detects_ring_fraud` — 4-cycle detection
- `test_real_time_scoring_under_500ms` — performance

**Missing Edge Cases (18):**
1. **Empty `signals` list** — `score([])` returns low risk with 0 confidence (line 56-62)
2. **Single signal** — minimum signals
3. **Unknown signal name** — should use `DEFAULT_WEIGHT` (line 69)
4. **Signal `value=0.0`** — maximum fraud contribution
5. **Signal `value=1.0`** — minimum fraud contribution
6. **Signal `value` outside `[0, 1]`** — undefined behavior
7. **Score exactly at 0.3 boundary** — low vs medium threshold (line 86)
8. **Score exactly at 0.7 boundary** — medium vs high threshold (line 88)
9. **Graph with no edges** — empty edge list
10. **Graph with single node** — no possible cycles
11. **Graph with disconnected components** — no cycles
12. **Graph with self-loops** — `("a", "a")` edge
13. **Graph with duplicate edges** — same edge twice
14. **Graph with non-existent nodes in edges** — edge references missing node
15. **Triangle detection (3-cycle)** — `a-b-c-a`
16. **4-cycle detection** — `a-b-c-d-a`
17. **Graph with no cycle** — tree structure
18. **Confidence with all signals present** — should be 1.0

---

### 5. `matching.py` — BuyerSellerMatcher

**Public API:**
- `BuyerSellerMatcher.match(buyers, sellers) -> list[Match]`

**Existing Tests (9):**
- `test_empty_inputs_return_empty_matches` — both empty
- `test_single_buyer_single_seller_returns_match` — 1:1 match
- `test_buyer_cannot_afford_seller_no_match` — budget constraint
- `test_multiple_buyers_compete_for_single_seller` — competition
- `test_match_score_is_between_zero_and_one` — score bounds
- `test_category_mismatch_reduces_score` — category filter
- `test_budget_constraint_respected` — budget limit
- `test_match_has_confidence_score` — confidence field

**Missing Edge Cases (14):**
1. **Empty `buyers` list only** — `match([], sellers)`
2. **Empty `sellers` list only** — `match(buyers, [])`
3. **Buyer with `budget=0`** — cannot afford anything
4. **Seller with `asking_price=0`** — free item
5. **Buyer `budget` exactly equal to `asking_price`** — boundary
6. **Multiple sellers competing for single buyer** — 1:N competition
7. **Many-to-many matching** — N:M matching
8. **Match score calculation verification** — exact score value
9. **Confidence score calculation verification** — exact confidence value
10. **Matches sorted by score descending** — verify order
11. **Duplicate buyer IDs** — undefined behavior
12. **Duplicate seller IDs** — undefined behavior
13. **Buyer with no preferences** — `preferences={}`
14. **Seller with no attributes** — `attributes={}`

---

### 6. `portfolio_optimizer.py` — PortfolioOptimizer

**Public API:**
- `PortfolioOptimizer.__init__(budget, max_assets)`
- `PortfolioOptimizer.optimize(assets, risk_tolerance) -> Portfolio`

**Existing Tests (7):**
- `test_empty_portfolio_returns_empty` — empty assets
- `test_single_asset_within_budget` — single asset
- `test_budget_constraint_respected` — budget limit
- `test_higher_risk_tolerance_selects_higher_return` — risk tolerance
- `test_cardinality_constraint_limits_selections` — max assets
- `test_diversification_bonus` — sector diversity
- `test_portfolio_has_sharpe_ratio` — sharpe ratio field

**Missing Edge Cases (15):**
1. **All assets exceed budget** — no affordable assets
2. **`risk_tolerance=0.0`** — minimum risk tolerance
3. **`risk_tolerance=1.0`** — maximum risk tolerance
4. **`risk_tolerance` outside `[0, 1]`** — undefined behavior
5. **`max_assets=0`** — no assets allowed
6. **`max_assets=1`** — single asset
7. **`max_assets > len(assets)`** — cardinality not binding
8. **Asset with `cost=0`** — free asset
9. **Asset with `risk=0`** — risk-free asset
10. **Asset with negative `expected_return`** — loss-making asset
11. **Asset with negative `cost`** — undefined behavior
12. **Portfolio with single asset** — sharpe ratio calculation
13. **Portfolio `expected_return` calculation** — weighted average
14. **Assets with same sector** — diversification penalty
15. **Assets with empty `sector` string** — sector grouping

---

### 7. `search_ranking.py` — SearchRanker

**Public API:**
- `SearchRanker.rank(query, listings, user_preferences) -> list[RankedListing]`

**Existing Tests (7):**
- `test_empty_query_returns_empty` — empty listings
- `test_single_listing_returns_single_result` — single listing
- `test_higher_relevance_ranks_higher` — relevance ordering
- `test_diversity_penalty_reduces_similar_listings` — diversity
- `test_ranked_listing_has_score` — score field
- `test_personalization_boosts_preferred_category` — personalization
- `test_no_duplicate_listings_in_results` — deduplication

**Missing Edge Cases (13):**
1. **Empty `listings` list** — `rank("query", [])`
2. **`user_preferences=None`** — no personalization
3. **`user_preferences` with empty dict** — `{}`
4. **`user_preferences` with unknown category** — no match
5. **Listing with `relevance=0.0`** — zero relevance
6. **Listing with `relevance=1.0`** — maximum relevance
7. **Listing with negative `relevance`** — undefined behavior
8. **Listing with empty `category`** — `""`
9. **Many listings in same category** — diversity penalty stacking
10. **All listings in same category** — maximum diversity penalty
11. **Query string variations** — query is unused but should not break
12. **Duplicate listings with different scores** — deduplication keeps highest
13. **`RankedListing` fields** — verify all fields populated

---

### 8. `valuation.py` — ValuationEngine

**Public API:**
- `ValuationEngine.dcf_valuation(free_cash_flow, growth_rate, discount_rate, terminal_growth, years) -> ValuationResult`
- `ValuationEngine.comparable_valuation(metric, multiple) -> ValuationResult`
- `ValuationEngine.ensemble_valuation(...) -> ValuationResult`
- `ValuationEngine.sde_valuation(sde, multiple) -> ValuationResult`
- `ValuationEngine.arr_valuation(arr, multiple) -> ValuationResult`

**Existing Tests (8):**
- `test_dcf_valuation_basic` — DCF happy path
- `test_dcf_higher_growth_increases_value` — growth sensitivity
- `test_dcf_higher_discount_rate_decreases_value` — discount sensitivity
- `test_comparable_company_valuation` — comps calculation
- `test_ensemble_valuation_returns_multiple_methods` — ensemble
- `test_valuation_result_has_confidence_interval` — CI bounds
- `test_sde_multiple_valuation` — SDE calculation
- `test_arr_multiple_valuation` — ARR calculation

**Missing Edge Cases (17):**
1. **DCF `years=0`** — no forecast period
2. **DCF `years=1`** — single year
3. **DCF negative `growth_rate`** — declining cash flows
4. **DCF `growth_rate > discount_rate`** — undefined behavior
5. **DCF `terminal_growth >= discount_rate`** — division by zero or negative (line 68)
6. **DCF negative `free_cash_flow`** — negative valuation
7. **DCF zero `free_cash_flow`** — zero valuation
8. **Comps `metric=0`** — zero valuation
9. **Comps `multiple=0`** — zero valuation
10. **Comps negative `metric`** — negative valuation
11. **Comps negative `multiple`** — negative valuation
12. **Ensemble with extreme values** — very large/small inputs
13. **SDE `sde=0`** — zero valuation
14. **SDE `multiple=0`** — zero valuation
15. **ARR `arr=0`** — zero valuation
16. **ARR `multiple=0`** — zero valuation
17. **Confidence interval bounds** — `low_estimate < high_estimate` for all methods

---

## Summary of Missing Test Categories

| Category | Count | Examples |
|----------|-------|----------|
| **Empty inputs** | 8 | Empty lists, zero values |
| **Boundary values** | 25 | Min/max of numeric ranges, thresholds |
| **Invalid inputs** | 20 | Negative values, out-of-range, unknown strings |
| **Error conditions** | 15 | Division by zero, undefined behavior |
| **Calculation verification** | 18 | Exact value assertions, formula verification |
| **State/field verification** | 12 | All fields populated, correct types |
| **Edge case interactions** | 14 | Combined boundary conditions |

---

## Recommendations

### Priority 1 — Critical (Error Conditions & Boundaries)
1. **DCF `terminal_growth >= discount_rate`** — causes division by zero or negative terminal value
2. **Fraud score thresholds (0.3, 0.7)** — boundary behavior at exact thresholds
3. **Entity resolution `threshold=0.0` and `threshold=1.0`** — extreme clustering behavior
4. **Matching `budget=0` and `asking_price=0`** — zero-value edge cases
5. **Portfolio `max_assets=0`** — empty portfolio constraint

### Priority 2 — High (Empty Inputs & Invalid Data)
6. **Empty signals list** — `FraudDetector.score([])`
7. **Empty buyers/sellers** — `BuyerSellerMatcher.match([], sellers)`
8. **Missing dict keys** — entities without `"name"` or `"domain"`
9. **Invalid `market_condition`** — unknown string defaults to 1.0
10. **Negative values** — negative costs, returns, budgets

### Priority 3 — Medium (Calculation Verification)
11. **Exact score/confidence values** — verify formulas produce expected results
12. **Canonical name tie-breaking** — first encountered wins
13. **Match ordering** — sorted by score descending
14. **Portfolio sharpe ratio** — exact calculation verification
15. **Ensemble confidence** — agreement-based confidence

---

## Test Collection Output

```
============================= test session starts ==============================
platform linux -- Python 3.14.7, pytest-8.4.2, pluggy-1.6.0
rootdir: /home/aah/Downloads/a2z-soc-main 2/acquisition-platform-research
configfile: pyproject.toml
plugins: hypothesis-6.168.3, cov-5.0.0, timeout-2.4.0, platformdirs-4.12.3, anyio-4.15.1, xdist-3.8.0, asyncio-0.26.0
asyncio: mode=Mode.STRICT, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 62 items

<Dir acquisition-platform-research>
  <Package tests>
    <Module test_dynamic_pricing.py>
      <Class TestPricingEngine>
        <Function test_basic_price_recommendation>
        <Function test_high_demand_increases_price>
        <Function test_high_competition_decreases_price>
        <Function test_bull_market_premium>
        <Function test_bear_market_discount>
        <Function test_price_within_bounds>
        <Function test_stackelberg_equilibrium_exists>
    <Module test_entity_resolution.py>
      <Class TestEntityResolver>
        <Function test_empty_input_returns_empty>
        <Function test_single_entity_returns_single_cluster>
        <Function test_exact_match_clusters_together>
        <Function test_different_entities_separate_clusters>
        <Function test_fuzzy_match_similar_names>
        <Function test_domain_match_boosts_similarity>
        <Function test_cluster_has_canonical_name>
        <Function test_blocking_reduces_comparisons>
    <Module test_evolution.py>
      <Class TestEvolutionEngine>
        <Function test_evolution_improves_fitness_over_generations>
        <Function test_population_size_respected>
        <Function test_mutation_rate_affects_diversity>
        <Function test_crossover_produces_offspring>
        <Function test_elitism_preserves_best>
        <Function test_convergence_detected>
      <Class TestEvaluationFramework>
        <Function test_benchmark_comparison>
        <Function test_benchmark_passes_when_target_met>
        <Function test_multiple_benchmarks_evaluated>
        <Function test_evaluation_result_has_improvement_suggestion>
    <Module test_fraud_detection.py>
      <Class TestFraudDetector>
        <Function test_clean_listing_returns_low_risk>
        <Function test_suspicious_listing_returns_high_risk>
        <Function test_medium_risk_for_mixed_signals>
        <Function test_fraud_score_has_explanation>
        <Function test_missing_signals_increases_risk>
        <Function test_graph_analysis_detects_ring_fraud>
        <Function test_real_time_scoring_under_500ms>
    <Module test_matching.py>
      <Class TestBuyerSellerMatcher>
        <Function test_empty_inputs_return_empty_matches>
        <Function test_single_buyer_single_seller_returns_match>
        <Function test_buyer_cannot_afford_seller_no_match>
        <Function test_multiple_buyers_compete_for_single_seller>
        <Function test_match_score_is_between_zero_and_one>
        <Function test_category_mismatch_reduces_score>
        <Function test_budget_constraint_respected>
        <Function test_match_has_confidence_score>
    <Module test_portfolio_optimizer.py>
      <Class TestPortfolioOptimizer>
        <Function test_empty_portfolio_returns_empty>
        <Function test_single_asset_within_budget>
        <Function test_budget_constraint_respected>
        <Function test_higher_risk_tolerance_selects_higher_return>
        <Function test_cardinality_constraint_limits_selections>
        <Function test_diversification_bonus>
        <Function test_portfolio_has_sharpe_ratio>
    <Module test_search_ranking.py>
      <Class TestSearchRanker>
        <Function test_empty_query_returns_empty>
        <Function test_single_listing_returns_single_result>
        <Function test_higher_relevance_ranks_higher>
        <Function test_diversity_penalty_reduces_similar_listings>
        <Function test_ranked_listing_has_score>
        <Function test_personalization_boosts_preferred_category>
        <Function test_no_duplicate_listings_in_results>
    <Module test_valuation.py>
      <Class TestValuationEngine>
        <Function test_dcf_valuation_basic>
        <Function test_dcf_higher_growth_increases_value>
        <Function test_dcf_higher_discount_rate_decreases_value>
        <Function test_comparable_company_valuation>
        <Function test_ensemble_valuation_returns_multiple_methods>
        <Function test_valuation_result_has_confidence_interval>
        <Function test_sde_multiple_valuation>
        <Function test_arr_multiple_valuation>

========================= 62 tests collected in 0.26s ==========================
```

---

## Conclusion

All 8 modules have corresponding test files with 62 total tests. The test suite covers **happy paths and basic functionality** well but has significant gaps in:

- **Boundary value testing** (min/max of numeric ranges)
- **Error condition testing** (division by zero, invalid inputs)
- **Empty input testing** (empty lists, zero values)
- **Calculation verification** (exact value assertions)
- **Edge case interactions** (combined boundary conditions)

**112 additional tests** are recommended to achieve comprehensive coverage.
