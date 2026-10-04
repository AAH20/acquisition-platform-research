# Wave 2: Caching & Memoization Opportunities

## Summary

Analyzed all 9 Python modules in `src/acquisition_platform/` for caching and memoization opportunities. Identified **high-value** opportunities in entity resolution, valuation, and fraud detection; **moderate-value** opportunities in matching, search ranking, and dynamic pricing; and **low-value** opportunities in portfolio optimization and evolution.

---

## 1. `entity_resolution.py` — Similarity Score Caching

### Opportunity: HIGH

**Current behavior:**
- `_jaro_winkler(s1, s2)` is called for every pair within a block (line 190).
- `_normalize(name)` is called for every entity name (line 178).
- The same normalized name may appear in multiple pairs, especially in dense blocks.

**Caching targets:**

| Function | Cache key | Benefit |
|----------|-----------|---------|
| `_normalize(name)` | `name: str` | Avoids redundant regex substitution for duplicate names |
| `_jaro_winkler(s1, s2)` | `(s1, s2)` tuple | Avoids O(len1×len2) computation for repeated pairs |

**Why it matters:**
- Jaro-Winkler is the most expensive operation in the module: O(len1 × len 2) for the matching window scan.
- In dense blocks (many entities sharing the same 3-char prefix), the same string pairs are compared repeatedly.
- Normalization uses `re.sub()` which is relatively expensive for repeated calls.

**Recommended approach:**
```python
from functools import lru_cache

@lru_cache(maxsize=1024)
def _normalize(name: str) -> str:
    return re.sub(r"[^\w\s]", "", name.lower()).strip()

@lru_cache(maxsize=4096)
def _jaro_winkler(s1: str, s2: str) -> float:
    # ... existing implementation ...
```

**Caveat:** `lru_cache` requires hashable arguments. Strings are hashable, so this works directly. The cache should be bounded (maxsize) to avoid unbounded memory growth in long-running processes.

---

## 2. `matching.py` — Feasibility & Score Caching

### Opportunity: MODERATE

**Current behavior:**
- `_is_feasible(buyer, seller)` is called for every (buyer, seller) pair: O(n×m) calls.
- `_compute_score(buyer, seller)` is called for every feasible pair.
- `_compute_confidence(buyer, seller, score)` is called for every feasible pair.

**Caching targets:**

| Function | Cache key | Benefit |
|----------|-----------|---------|
| `_is_feasible` | `(buyer.id, seller.id)` | Avoids repeated dict lookups + comparisons |
| `_compute_score` | `(buyer.id, seller.id)` | Avoids repeated float division |
| `_compute_confidence` | `(buyer.id, seller.id, score)` | Avoids repeated float arithmetic |

**Why it matters:**
- For n buyers and m sellers, there are n×m feasibility checks. With 100 buyers and 100 sellers, that's 10,000 calls.
- The individual operations are cheap (dict lookups, float division), so the benefit is only realized when `match()` is called repeatedly with overlapping buyer/seller sets.
- In a batch matching scenario (e.g., matching against a large seller pool repeatedly), caching would help.

**Recommended approach:**
```python
from functools import lru_cache

class BuyerSellerMatcher:
    def __init__(self, threshold: float = 0.85) -> None:
        self.threshold = threshold
        self._feasibility_cache: dict[tuple[str, str], bool] = {}
        self._score_cache: dict[tuple[str, str], float] = {}

    def _is_feasible(self, buyer: Buyer, seller: Seller) -> bool:
        key = (buyer.id, seller.id)
        if key not in self._feasibility_cache:
            # ... compute and store ...
        return self._feasibility_cache[key]
```

**Caveat:** Buyer and Seller are dataclasses. If they are mutable, caching by ID is safer than caching the objects themselves. The cache should be cleared when the underlying data changes.

---

## 3. `valuation.py` — DCF Calculation Caching

### Opportunity: HIGH

**Current behavior:**
- `dcf_valuation` computes `(1 + growth_rate) ** t` and `(1 + discount_rate) ** t` for t = 1..years (lines 64-65).
- These exponentiations are recomputed from scratch on every call.
- `ensemble_valuation` calls `dcf_valuation` internally (line 129), so the same DCF computation may be repeated.

**Caching targets:**

| Function | Cache key | Benefit |
|----------|-----------|---------|
| `dcf_valuation` | `(fcf, growth_rate, discount_rate, terminal_growth, years)` | Avoids entire DCF recomputation |
| Power computations | `(base, exponent)` | Avoids repeated `**` operations |

**Why it matters:**
- DCF is called repeatedly in ensemble valuation and potentially in batch valuation scenarios.
- The loop over `years` with exponentiation is the bottleneck: O(years) exponentiations.
- If the same parameters are used across multiple calls (e.g., sensitivity analysis with slight parameter changes), caching the full result helps.

**Recommended approach:**
```python
from functools import lru_cache

class ValuationEngine:
    @lru_cache(maxsize=256)
    def dcf_valuation(
        self,
        free_cash_flow: float,
        growth_rate: float,
        discount_rate: float,
        terminal_growth: float,
        years: int,
    ) -> ValuationResult:
        # ... existing implementation ...
```

**Alternative (incremental computation):**
```python
def dcf_valuation(self, ...):
    pv = 0.0
    growth_factor = 1.0 + growth_rate
    discount_factor = 1.0 + discount_rate
    g_pow = 1.0  # (1 + growth_rate) ** t
    d_pow = 1.0  # (1 + discount_rate) ** t
    for t in range(1, years + 1):
        g_pow *= growth_factor
        d_pow *= discount_factor
        pv += free_cash_flow * g_pow / d_pow
    # ...
```
This avoids the `**` operator entirely, replacing it with multiplication.

**Caveat:** `lru_cache` on instance methods holds a reference to `self`, which can prevent garbage collection. Consider using a module-level cache or clearing the cache when appropriate.

---

## 4. `fraud_detection.py` — Graph Analysis Caching

### Opportunity: HIGH

**Current behavior:**
- `_has_cycle_of_length_3_or_4` is O(n³) for triangle detection and O(n⁴) for 4-cycle detection.
- The adjacency list is rebuilt from the edge list on every call to `analyze_graph`.
- If the same graph is analyzed multiple times (e.g., in a batch screening scenario), the entire computation is repeated.

**Caching targets:**

| Function | Cache key | Benefit |
|----------|-----------|---------|
| `analyze_graph` | Hash of (nodes, edges) | Avoids O(n³) cycle detection |
| `_has_cycle_of_length_3_or_4` | Hash of adjacency structure | Avoids repeated cycle detection |

**Why it matters:**
- Cycle detection is the most expensive operation in the module.
- In a batch fraud screening scenario, the same graph may be analyzed multiple times (e.g., re-screening after minor updates).
- The adjacency list construction is O(n + e) and is repeated unnecessarily.

**Recommended approach:**
```python
class FraudDetector:
    def __init__(self):
        self._graph_cache: dict[tuple, GraphAnalysis] = {}

    def analyze_graph(self, graph: dict[str, Any]) -> GraphAnalysis:
        # Create a hashable key from the graph structure
        nodes = tuple(sorted(graph.get("nodes", [])))
        edges = tuple(sorted(tuple(sorted(e)) for e in graph.get("edges", [])))
        key = (nodes, edges)
        
        if key not in self._graph_cache:
            self._graph_cache[key] = self._analyze_graph_uncached(graph)
        return self._graph_cache[key]
```

**Caveat:** The cache key must capture the full graph structure. Using sorted tuples of nodes and edges ensures that structurally identical graphs produce the same key regardless of input ordering.

---

## 5. `search_ranking.py` — Ranking Result Caching

### Opportunity: MODERATE

**Current behavior:**
- `rank()` is a pure function of (query, listings, user_preferences).
- The same query + listings + preferences combination produces the same result.
- In a search scenario, the same query may be issued repeatedly (e.g., pagination, auto-refresh).

**Caching targets:**

| Function | Cache key | Benefit |
|----------|-----------|---------|
| `rank` | `(query, tuple(listings), tuple(preferences.items()))` | Avoids O(n log n) sorting |

**Why it matters:**
- Ranking involves sorting: O(n log n).
- For repeated queries on the same listing set, caching avoids redundant computation.
- The deduplication step (lines 95-98) is also repeated.

**Recommended approach:**
```python
class SearchRanker:
    def __init__(self):
        self._rank_cache: dict[tuple, list[RankedListing]] = {}

    def rank(self, query, listings, user_preferences=None):
        key = (
            query,
            tuple((l.id, l.title, l.relevance, l.category) for l in listings),
            tuple(sorted((user_preferences or {}).items()))
        )
        if key not in self._rank_cache:
            self._rank_cache[key] = self._rank_uncached(query, listings, user_preferences)
        return self._rank_cache[key]
```

**Caveat:** The cache key must include all listing attributes that affect the score. If listings are mutable, the cache may return stale results.

---

## 6. `dynamic_pricing.py` — Price Recommendation Caching

### Opportunity: MODERATE

**Current behavior:**
- `recommend_price` is a pure function of (base_value, demand_level, competition_level, market_condition).
- The computation is cheap (a few multiplications), but in a high-throughput pricing scenario, caching could reduce CPU usage.

**Caching targets:**

| Function | Cache key | Benefit |
|----------|-----------|---------|
| `recommend_price` | `(base_value, demand_level, competition_level, market_condition)` | Avoids repeated float arithmetic |

**Why it matters:**
- The computation is very cheap, so the benefit is only realized at high call volumes.
- In a batch pricing scenario (e.g., pricing 10,000 targets), caching could help.
- The `market_multipliers` dict lookup (line 52) is repeated unnecessarily.

**Recommended approach:**
```python
from functools import lru_cache

class PricingEngine:
    _MARKET_MULTIPLIERS = {
        "bull": 1.15,
        "bear": 0.85,
        "normal": 1.0,
    }

    @lru_cache(maxsize=1024)
    def recommend_price(
        self,
        base_value: float,
        demand_level: float,
        competition_level: float,
        market_condition: str,
    ) -> PriceRecommendation:
        # ... existing implementation ...
```

**Caveat:** The benefit is marginal due to the simplicity of the computation. Only recommended if profiling shows this is a bottleneck.

---

## 7. `portfolio_optimizer.py` — Optimization Result Caching

### Opportunity: LOW

**Current behavior:**
- `optimize` is deterministic given (assets, risk_tolerance).
- The computation is O(n log n) due to sorting.
- In practice, the asset set changes frequently (new targets added/removed), reducing cache hit rate.

**Caching targets:**

| Function | Cache key | Benefit |
|----------|-----------|---------|
| `optimize` | `(tuple(assets), risk_tolerance)` | Avoids O(n log n) sorting |

**Why it matters:**
- The benefit is limited because asset sets change frequently.
- The computation is already efficient (O(n log n)).
- Caching is only beneficial if the same asset set is optimized repeatedly with different risk tolerances.

**Recommended approach:** Not recommended unless profiling shows repeated calls with the same asset set.

---

## 8. `evolution.py` — Fitness Evaluation Caching

### Opportunity: LOW-MODERATE

**Current behavior:**
- `fitness_fn(gene)` is called for each gene in each generation (line 120).
- Due to elitism and crossover, the same gene values may recur across generations.
- If `fitness_fn` is expensive (e.g., involves model training), caching could help.

**Caching targets:**

| Function | Cache key | Benefit |
|----------|-----------|---------|
| `fitness_fn(gene)` | `gene: float` | Avoids redundant fitness evaluation |

**Why it matters:**
- In a typical GA run with population_size=50 and generations=20, there are 1,000 fitness evaluations.
- Due to elitism (top 2 preserved) and crossover (averaging parents), some gene values recur.
- If `fitness_fn` is expensive, caching could significantly reduce total computation.

**Recommended approach:**
```python
class EvolutionEngine:
    def evolve(self, fitness_fn, gene_range):
        fitness_cache: dict[float, float] = {}
        
        def cached_fitness(gene):
            if gene not in fitness_cache:
                fitness_cache[gene] = fitness_fn(gene)
            return fitness_cache[gene]
        
        # Use cached_fitness instead of fitness_fn
        fitness_scores = [cached_fitness(gene) for gene in population]
        # ...
```

**Caveat:** The benefit depends on the expense of `fitness_fn` and the recurrence rate of gene values. For simple fitness functions, the overhead of caching may exceed the benefit.

---

## 9. `__init__.py` — No Opportunities

The `__init__.py` file only contains imports and re-exports. No caching opportunities.

---

## Summary Table

| Module | Opportunity | Priority | Estimated Benefit |
|--------|-------------|----------|-------------------|
| `entity_resolution.py` | Cache `_jaro_winkler` and `_normalize` | HIGH | Avoids O(n²) string comparisons |
| `valuation.py` | Cache `dcf_valuation` or use incremental powers | HIGH | Avoids O(years) exponentiations |
| `fraud_detection.py` | Cache graph analysis results | HIGH | Avoids O(n³) cycle detection |
| `matching.py` | Cache feasibility and score computations | MODERATE | Avoids O(n×m) repeated checks |
| `search_ranking.py` | Cache ranking results | MODERATE | Avoids O(n log n) sorting |
| `dynamic_pricing.py` | Cache price recommendations | MODERATE | Avoids repeated float arithmetic |
| `evolution.py` | Cache fitness evaluations | LOW-MODERATE | Avoids redundant fitness calls |
| `portfolio_optimizer.py` | Cache optimization results | LOW | Limited by changing asset sets |

---

## General Recommendations

1. **Use `functools.lru_cache` for pure functions** — `_jaro_winkler`, `_normalize`, `dcf_valuation`, `recommend_price` are all pure functions that benefit from `lru_cache`.

2. **Use instance-level caches for methods** — For methods that depend on instance state (e.g., `analyze_graph`), use a dict cache on the instance.

3. **Bound all caches** — Use `maxsize` to prevent unbounded memory growth in long-running processes.

4. **Consider cache invalidation** — For mutable data structures (e.g., listings, assets), ensure the cache is cleared when the underlying data changes.

5. **Profile before optimizing** — The actual benefit of caching depends on the call patterns. Profile the application to identify which functions are called most frequently with the same arguments.

6. **Incremental computation** — For DCF, consider computing powers incrementally (multiplication instead of exponentiation) as a complementary optimization to caching.
