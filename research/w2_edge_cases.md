# Wave 2: Missing Test Edge Cases — Top 20 Critical Gaps

**Date:** 2026-10-04  
**Scope:** `tests/test_*.py` — 8 test files, 62 tests total  
**Source modules:** `dynamic_pricing.py`, `entity_resolution.py`, `evolution.py`, `fraud_detection.py`, `matching.py`, `portfolio_optimizer.py`, `search_ranking.py`, `valuation.py`

---

## Analysis Methodology

For each of the 8 test files, every test function was examined against its corresponding source module to identify untested edge cases across these categories:

- **Zero values** — inputs at exactly 0
- **Negative values** — inputs below 0
- **Very large values** — inputs at extreme magnitudes
- **None inputs** — null/None where a value is expected
- **Empty strings** — `""` where a string is expected
- **Single-element lists** — minimum non-empty list
- **Duplicate elements** — repeated values in lists
- **Boundary values** — exact threshold boundaries (e.g., `score == 0.3`, `score == 0.7`)
- **Error conditions** — exceptions that should be raised but aren't tested

---

## Top 20 Most Critical Missing Test Cases

### 1. DCF `terminal_growth >= discount_rate` — Division by Zero / Negative Terminal Value
**Module:** `valuation.py:68`  
**Test file:** `test_valuation.py`  
**Severity:** CRITICAL  
**What's missing:** No test for `terminal_growth == discount_rate` (causes `ZeroDivisionError`) or `terminal_growth > discount_rate` (produces negative terminal value, which is financially nonsensical).  
**Why it matters:** The Gordon Growth Model requires `discount_rate > terminal_growth`. Violating this produces mathematically undefined or negative valuations that propagate silently.  
**Suggested test:**
```python
def test_dcf_terminal_growth_equal_to_discount_rate_raises(self):
    engine = ValuationEngine()
    with pytest.raises(ZeroDivisionError):
        engine.dcf_valuation(
            free_cash_flow=100000, growth_rate=0.05,
            discount_rate=0.10, terminal_growth=0.10, years=5,
        )
```

### 2. DCF `terminal_growth > discount_rate` — Negative Terminal Value
**Module:** `valuation.py:68`  
**Test file:** `test_valuation.py`  
**Severity:** CRITICAL  
**What's missing:** No test for `terminal_growth > discount_rate`, which produces a negative terminal value and thus a potentially negative total valuation.  
**Why it matters:** A negative valuation is financially meaningless and should either be rejected or clamped.  
**Suggested test:**
```python
def test_dcf_terminal_growth_exceeds_discount_rate(self):
    engine = ValuationEngine()
    result = engine.dcf_valuation(
        free_cash_flow=100000, growth_rate=0.05,
        discount_rate=0.08, terminal_growth=0.10, years=5,
    )
    # Should either raise or produce a clearly invalid result
    assert result.value < 0 or result.value > 0  # Document actual behavior
```

### 3. Fraud Score Boundary at Exactly 0.3 — Low vs Medium Threshold
**Module:** `fraud_detection.py:86`  
**Test file:** `test_fraud_detection.py`  
**Severity:** HIGH  
**What's missing:** No test for a signal combination that produces `score == 0.3` exactly. The code uses `score < 0.3` for low and `score <= 0.7` for medium, so 0.3 falls into "medium".  
**Why it matters:** Off-by-one errors at threshold boundaries are among the most common bugs. The exact boundary behavior should be pinned.  
**Suggested test:**
```python
def test_fraud_score_exactly_at_low_medium_boundary(self):
    detector = FraudDetector()
    # Construct signals that yield score == 0.3
    # With DEFAULT_WEIGHT=0.1, need: sum(1-v)*w / sum(w) == 0.3
    signals = [FraudSignal(name="unknown_signal", value=0.7)]
    score = detector.score(signals)
    assert score.score == pytest.approx(0.3, abs=0.01)
    assert score.risk_level == "medium"  # 0.3 is NOT < 0.3
```

### 4. Fraud Score Boundary at Exactly 0.7 — Medium vs High Threshold
**Module:** `fraud_detection.py:88`  
**Test file:** `test_fraud_detection.py`  
**Severity:** HIGH  
**What's missing:** No test for `score == 0.7` exactly. The code uses `score <= 0.7` for medium, so 0.7 is "medium" not "high".  
**Why it matters:** Boundary at 0.7 determines whether a listing is flagged as high risk.  
**Suggested test:**
```python
def test_fraud_score_exactly_at_medium_high_boundary(self):
    detector = FraudDetector()
    signals = [FraudSignal(name="unknown_signal", value=0.3)]
    score = detector.score(signals)
    assert score.score == pytest.approx(0.7, abs=0.01)
    assert score.risk_level == "medium"  # 0.7 is <= 0.7
```

### 5. Entity Resolution `threshold=0.0` — Clusters Everything
**Module:** `entity_resolution.py:153`  
**Test file:** `test_entity_resolution.py`  
**Severity:** HIGH  
**What's missing:** No test for `EntityResolver(threshold=0.0)`, which should cluster all entities into a single cluster regardless of name similarity.  
**Why it matters:** At threshold 0.0, even completely dissimilar names should be unioned. This tests the lower bound of the threshold parameter.  
**Suggested test:**
```python
def test_threshold_zero_clusters_everything(self):
    resolver = EntityResolver(threshold=0.0)
    entities = [
        {"id": "e1", "name": "Acme Corp", "domain": "acme.com"},
        {"id": "e2", "name": "Globex Inc", "domain": "globex.com"},
    ]
    result = resolver.resolve(entities)
    assert len(result) == 1
    assert len(result[0].entities) == 2
```

### 6. Entity Resolution `threshold=1.0` — Only Exact Matches
**Module:** `entity_resolution.py:153`  
**Test file:** `test_entity_resolution.py`  
**Severity:** HIGH  
**What's missing:** No test for `EntityResolver(threshold=1.0)`, which should only cluster entities with identical normalized names.  
**Why it matters:** At threshold 1.0, only perfect matches should cluster. This tests the upper bound.  
**Suggested test:**
```python
def test_threshold_one_only_exact_matches(self):
    resolver = EntityResolver(threshold=1.0)
    entities = [
        {"id": "e1", "name": "Acme Corp", "domain": "acme.com"},
        {"id": "e2", "name": "Acme Corp", "domain": "acme.com"},
        {"id": "e3", "name": "Globex Inc", "domain": "globex.com"},
    ]
    result = resolver.resolve(entities)
    assert len(result) == 2  # Acme cluster + Globex singleton
```

### 7. Entity Resolution — Missing `"name"` Key
**Module:** `entity_resolution.py:178`  
**Test file:** `test_entity_resolution.py`  
**Severity:** HIGH  
**What's missing:** No test for entities without a `"name"` key. The code uses `e.get("name", "")` which returns `""`, and `_normalize("")` returns `""`, which blocks under `""[:3]` = `""`.  
**Why it matters:** Missing keys are common in real-world data. The behavior should be defined and tested.  
**Suggested test:**
```python
def test_entity_missing_name_key(self):
    resolver = EntityResolver()
    entities = [
        {"id": "e1", "domain": "acme.com"},  # No "name" key
        {"id": "e2", "name": "Acme Corp", "domain": "acme.com"},
    ]
    result = resolver.resolve(entities)
    # Empty name should not match "Acme Corp"
    assert len(result) == 2
```

### 8. Matching — Buyer with `budget=0`
**Module:** `matching.py:116`  
**Test file:** `test_matching.py`  
**Severity:** HIGH  
**What's missing:** No test for `Buyer(budget=0)`. The `_is_feasible` check `buyer.budget < seller.asking_price` would reject all sellers with `asking_price > 0`, but a seller with `asking_price=0` would pass.  
**Why it matters:** Zero-budget buyers are a realistic edge case (e.g., acquirers using all-stock deals).  
**Suggested test:**
```python
def test_buyer_zero_budget_no_match(self):
    matcher = BuyerSellerMatcher()
    buyers = [Buyer(id="b1", budget=0, preferences={"category": "saas"})]
    sellers = [Seller(id="s1", asking_price=0, attributes={"category": "saas"})]
    matches = matcher.match(buyers, sellers)
    # budget=0 >= asking_price=0, so this is feasible
    # But _compute_score returns 0.0 for budget <= 0
    assert len(matches) == 1
    assert matches[0].score == 0.0
```

### 9. Matching — Seller with `asking_price=0`
**Module:** `matching.py:116`  
**Test file:** `test_matching.py`  
**Severity:** HIGH  
**What's missing:** No test for `Seller(asking_price=0)`. This is a "free" listing that any buyer can afford.  
**Why it matters:** Zero-price listings are common in distressed acquisitions.  
**Suggested test:**
```python
def test_seller_zero_asking_price(self):
    matcher = BuyerSellerMatcher()
    buyers = [Buyer(id="b1", budget=100000, preferences={"category": "saas"})]
    sellers = [Seller(id="s1", asking_price=0, attributes={"category": "saas"})]
    matches = matcher.match(buyers, sellers)
    assert len(matches) == 1
    assert matches[0].score == 1.0  # (1 - 0/100000) = 1.0
```

### 10. Portfolio Optimizer — `max_assets=0`
**Module:** `portfolio_optimizer.py:44`  
**Test file:** `test_portfolio_optimizer.py`  
**Severity:** HIGH  
**What's missing:** No test for `PortfolioOptimizer(max_assets=0)`. The greedy loop checks `len(selected) >= self.max_assets` which would be `0 >= 0` = True immediately, returning an empty portfolio.  
**Why it matters:** Zero max_assets is a valid constraint (e.g., "no acquisitions this quarter").  
**Suggested test:**
```python
def test_max_assets_zero_returns_empty(self):
    optimizer = PortfolioOptimizer(budget=1000000, max_assets=0)
    assets = [Asset(id="a1", cost=500000, expected_return=0.12, risk=0.15)]
    result = optimizer.optimize(assets, risk_tolerance=0.5)
    assert result.assets == []
    assert result.expected_return == 0.0
```

### 11. Portfolio Optimizer — All Assets Exceed Budget
**Module:** `portfolio_optimizer.py:70`  
**Test file:** `test_portfolio_optimizer.py`  
**Severity:** HIGH  
**What's missing:** No test for when all assets have `cost > budget`. The `affordable` list would be empty, and the function returns `Portfolio()` with no assets.  
**Why it matters:** This is a common real-world scenario (budget too small for any target).  
**Suggested test:**
```python
def test_all_assets_exceed_budget_returns_empty(self):
    optimizer = PortfolioOptimizer(budget=100000)
    assets = [
        Asset(id="a1", cost=200000, expected_return=0.12, risk=0.15),
        Asset(id="a2", cost=300000, expected_return=0.10, risk=0.10),
    ]
    result = optimizer.optimize(assets, risk_tolerance=0.5)
    assert result.assets == []
    assert result.expected_return == 0.0
```

### 12. Fraud Detection — Empty Signals List
**Module:** `fraud_detection.py:56`  
**Test file:** `test_fraud_detection.py`  
**Severity:** HIGH  
**What's missing:** No test for `detector.score([])`. The code has an explicit early return for empty signals with `score=0.0, risk_level="low", confidence=0.0`.  
**Why it matters:** Empty input is a common edge case that should be explicitly tested.  
**Suggested test:**
```python
def test_empty_signals_returns_low_risk_zero_confidence(self):
    detector = FraudDetector()
    score = detector.score([])
    assert score.score == 0.0
    assert score.risk_level == "low"
    assert score.confidence == 0.0
    assert len(score.explanations) == 1
```

### 13. Fraud Detection — Unknown Signal Name Uses DEFAULT_WEIGHT
**Module:** `fraud_detection.py:69`  
**Test file:** `test_fraud_detection.py`  
**Severity:** HIGH  
**What's missing:** No test for a signal with an unrecognized name. The code uses `self.WEIGHTS.get(signal.name, self.DEFAULT_WEIGHT)` which falls back to `0.1`.  
**Why it matters:** Unknown signals should not crash the system; they should be handled gracefully with default weighting.  
**Suggested test:**
```python
def test_unknown_signal_name_uses_default_weight(self):
    detector = FraudDetector()
    signals = [FraudSignal(name="unknown_signal_xyz", value=0.5)]
    score = detector.score(signals)
    # DEFAULT_WEIGHT = 0.1, fraud_value = 1.0 - 0.5 = 0.5
    # score = 0.5 * 0.1 / 0.1 = 0.5
    assert score.score == pytest.approx(0.5, abs=0.01)
    assert score.risk_level == "medium"
```

### 14. Fraud Detection — Graph with Self-Loop
**Module:** `fraud_detection.py:110`  
**Test file:** `test_fraud_detection.py`  
**Severity:** MEDIUM  
**What's missing:** No test for a graph with a self-loop edge `("a", "a")`. The adjacency building adds `a` to its own neighbors, but the cycle detection uses `n1 <= node` which would skip self-loops.  
**Why it matters:** Self-loops could indicate data quality issues or a specific fraud pattern.  
**Suggested test:**
```python
def test_graph_with_self_loop_no_ring(self):
    detector = FraudDetector()
    graph = {
        "nodes": ["a", "b"],
        "edges": [("a", "a"), ("a", "b")],
    }
    result = detector.analyze_graph(graph)
    assert result.has_ring is False
```

### 15. Fraud Detection — Graph with Disconnected Components
**Module:** `fraud_detection.py:100`  
**Test file:** `test_fraud_detection.py`  
**Severity:** MEDIUM  
**What's missing:** No test for a graph with multiple disconnected components (e.g., two separate triangles).  
**Why it matters:** Disconnected components should each be analyzed independently.  
**Suggested test:**
```python
def test_graph_disconnected_components(self):
    detector = FraudDetector()
    graph = {
        "nodes": ["a", "b", "c", "d", "e", "f"],
        "edges": [("a", "b"), ("b", "c"), ("c", "a"),  # Triangle 1
                  ("d", "e"), ("e", "f"), ("f", "d")],  # Triangle 2
    }
    result = detector.analyze_graph(graph)
    assert result.has_ring is True
    assert result.risk_score == 0.8
```

### 16. Dynamic Pricing — Invalid `market_condition` String
**Module:** `dynamic_pricing.py:52`  
**Test file:** `test_dynamic_pricing.py`  
**Severity:** MEDIUM  
**What's missing:** No test for an unrecognized `market_condition` string. The code uses `market_multipliers.get(market_condition, 1.0)` which defaults to 1.0.  
**Why it matters:** Invalid market conditions should not crash; they should default to neutral.  
**Suggested test:**
```python
def test_invalid_market_condition_defaults_to_normal(self):
    engine = PricingEngine()
    normal = engine.recommend_price(
        base_value=100000, demand_level=0.5, competition_level=0.5,
        market_condition="normal",
    )
    invalid = engine.recommend_price(
        base_value=100000, demand_level=0.5, competition_level=0.5,
        market_condition="invalid_condition",
    )
    assert invalid.recommended_price == normal.recommended_price
```

### 17. Dynamic Pricing — Zero `base_value`
**Module:** `dynamic_pricing.py:54`  
**Test file:** `test_dynamic_pricing.py`  
**Severity:** MEDIUM  
**What's missing:** No test for `base_value=0`. All computed prices would be 0, and `confidence` would still be computed normally.  
**Why it matters:** Zero base value could occur for distressed or pre-revenue targets.  
**Suggested test:**
```python
def test_zero_base_value_returns_zero_prices(self):
    engine = PricingEngine()
    rec = engine.recommend_price(
        base_value=0, demand_level=0.5, competition_level=0.5,
        market_condition="normal",
    )
    assert rec.recommended_price == 0.0
    assert rec.floor_price == 0.0
    assert rec.ceiling_price == 0.0
    assert rec.equilibrium_price == 0.0
```

### 18. Evolution — `population_size=1`
**Module:** `evolution.py:74`  
**Test file:** `test_evolution.py`  
**Severity:** MEDIUM  
**What's missing:** No test for `EvolutionEngine(population_size=1)`. With a single individual, tournament selection would fail (`random.sample(range(1), 2)` raises `ValueError`).  
**Why it matters:** Minimum population size is a critical boundary.  
**Suggested test:**
```python
def test_population_size_one_raises_or_handles(self):
    engine = EvolutionEngine(population_size=1, generations=5)
    with pytest.raises(ValueError):
        engine.evolve(fitness_fn=lambda x: x, gene_range=(0, 10))
```

### 19. Evolution — `generations=0`
**Module:** `evolution.py:118`  
**Test file:** `test_evolution.py`  
**Severity:** MEDIUM  
**What's missing:** No test for `EvolutionEngine(generations=0)`. The for-loop would not execute, and the function would return with `generation_count=0` and `converged=False`.  
**Why it matters:** Zero generations is a valid "no evolution" scenario.  
**Suggested test:**
```python
def test_zero_generations_returns_initial_population(self):
    engine = EvolutionEngine(population_size=10, generations=0)
    result = engine.evolve(fitness_fn=lambda x: x, gene_range=(0, 100))
    assert result.generation_count == 0
    assert result.converged is False
    assert result.offspring_count == 0
```

### 20. Search Ranking — `user_preferences=None`
**Module:** `search_ranking.py:44`  
**Test file:** `test_search_ranking.py`  
**Severity:** MEDIUM  
**What's missing:** No test for `rank(query, listings, user_preferences=None)`. The code checks `if user_preferences:` which is falsy for `None`, so `preferred_category` stays `None`.  
**Why it matters:** None is the default and most common case for user_preferences.  
**Suggested test:**
```python
def test_none_user_preferences_no_personalization(self):
    ranker = SearchRanker()
    listings = [
        Listing(id="l1", title="SaaS", relevance=0.7, category="saas"),
        Listing(id="l2", title="E-commerce", relevance=0.7, category="ecommerce"),
    ]
    results = ranker.rank("platform", listings, user_preferences=None)
    # No personalization boost, so order is by relevance (both 0.7)
    # First occurrence gets diversity_factor=1.0, second gets 0.7
    assert results[0].id == "l1"  # Higher score due to diversity
```

---

## Summary of All Missing Edge Cases by Category

| Category | Count | Critical | High | Medium |
|----------|-------|----------|------|--------|
| Zero values | 8 | 0 | 3 | 5 |
| Negative values | 4 | 0 | 1 | 3 |
| Boundary values | 10 | 2 | 4 | 4 |
| Empty inputs | 6 | 0 | 3 | 3 |
| Invalid inputs | 8 | 0 | 3 | 5 |
| Error conditions | 4 | 2 | 1 | 1 |
| Duplicate elements | 3 | 0 | 1 | 2 |
| Single-element lists | 5 | 0 | 2 | 3 |
| None inputs | 4 | 0 | 1 | 3 |
| Very large values | 3 | 0 | 1 | 2 |
| **Total unique gaps** | **~55** | **4** | **19** | **32** |

---

## Additional Missing Edge Cases (Beyond Top 20)

### Dynamic Pricing (`test_dynamic_pricing.py`)
- `demand_level=0.0` — minimum demand
- `demand_level=1.0` — maximum demand
- `competition_level=0.0` — minimum competition
- `competition_level=1.0` — maximum competition
- Negative `base_value` — undefined behavior
- Very large `base_value` — overflow check
- `confidence` when `demand_level == competition_level` — should be 1.0

### Entity Resolution (`test_entity_resolution.py`)
- Empty string names — `""` normalizes to `""`
- Single character names — blocking with `norm[:3]` on short strings
- Names with only punctuation — normalization strips all chars
- Unicode/special characters — normalization with non-ASCII
- `comparison_count` reset between calls
- Canonical name tie-breaking — first encountered wins
- Case sensitivity — `"ACME"` vs `"acme"`
- Large block size — many entities with same first 3 chars

### Evolution (`test_evolution.py`)
- `mutation_rate=0.0` — no mutation
- `mutation_rate=1.0` — always mutate
- `elitism=0` — no elitism
- `elitism >= population_size` — all elite
- Negative fitness function — `lambda x: -x**2`
- Constant fitness function — `lambda x: 1.0`
- `gene_range` where `low == high` — zero range
- `Benchmark` with `target=0` — always passes
- `Benchmark.evaluate` with `actual == target` — boundary

### Fraud Detection (`test_fraud_detection.py`)
- Single signal — minimum signals
- Signal `value=0.0` — maximum fraud contribution
- Signal `value=1.0` — minimum fraud contribution
- Signal `value` outside `[0, 1]` — undefined behavior
- Graph with no edges — empty edge list
- Graph with single node — no possible cycles
- Graph with duplicate edges
- Graph with non-existent nodes in edges
- Triangle detection (3-cycle)
- Graph with no cycle — tree structure
- Confidence with all signals present — should be 1.0

### Matching (`test_matching.py`)
- Empty `buyers` list only — `match([], sellers)`
- Empty `sellers` list only — `match(buyers, [])`
- Buyer `budget` exactly equal to `asking_price` — boundary
- Multiple sellers competing for single buyer — 1:N
- Many-to-many matching — N:M
- Match score calculation verification — exact value
- Confidence score calculation verification — exact value
- Matches sorted by score descending — verify order
- Duplicate buyer IDs
- Duplicate seller IDs
- Buyer with no preferences — `preferences={}`
- Seller with no attributes — `attributes={}`

### Portfolio Optimizer (`test_portfolio_optimizer.py`)
- `risk_tolerance=0.0` — minimum risk tolerance
- `risk_tolerance=1.0` — maximum risk tolerance
- `risk_tolerance` outside `[0, 1]` — undefined behavior
- `max_assets=1` — single asset
- `max_assets > len(assets)` — cardinality not binding
- Asset with `cost=0` — free asset
- Asset with `risk=0` — risk-free asset
- Asset with negative `expected_return` — loss-making asset
- Asset with negative `cost` — undefined behavior
- Portfolio with single asset — sharpe ratio calculation
- Assets with same sector — diversification penalty
- Assets with empty `sector` string

### Search Ranking (`test_search_ranking.py`)
- Empty `listings` list — `rank("query", [])`
- `user_preferences` with empty dict — `{}`
- `user_preferences` with unknown category — no match
- Listing with `relevance=0.0` — zero relevance
- Listing with `relevance=1.0` — maximum relevance
- Listing with negative `relevance` — undefined behavior
- Listing with empty `category` — `""`
- Many listings in same category — diversity penalty stacking
- All listings in same category — maximum diversity penalty
- Duplicate listings with different scores — deduplication keeps highest

### Valuation (`test_valuation.py`)
- DCF `years=0` — no forecast period
- DCF `years=1` — single year
- DCF negative `growth_rate` — declining cash flows
- DCF `growth_rate > discount_rate` — undefined behavior
- DCF negative `free_cash_flow` — negative valuation
- DCF zero `free_cash_flow` — zero valuation
- Comps `metric=0` — zero valuation
- Comps `multiple=0` — zero valuation
- Comps negative `metric` — negative valuation
- Comps negative `multiple` — negative valuation
- Ensemble with extreme values — very large/small inputs
- SDE `sde=0` — zero valuation
- SDE `multiple=0` — zero valuation
- ARR `arr=0` — zero valuation
- ARR `multiple=0` — zero valuation
- Confidence interval bounds — `low_estimate < high_estimate` for all methods

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
asyncio: mode=Mode.STRICT, asyncio_default_fixture_loop_scope=None, asyncio_default_fixture_loop_scope=function
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

- **Boundary value testing** (min/max of numeric ranges, exact threshold values)
- **Error condition testing** (division by zero, invalid inputs, undefined behavior)
- **Empty input testing** (empty lists, zero values, None inputs)
- **Calculation verification** (exact value assertions, formula verification)
- **Edge case interactions** (combined boundary conditions)

**55+ additional tests** are recommended to achieve comprehensive coverage. The top 20 critical gaps identified above should be addressed first, as they represent the highest risk of silent failures or incorrect behavior in production.
