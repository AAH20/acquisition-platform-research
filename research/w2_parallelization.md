# Wave 2: Parallelization Opportunities Analysis

**Date:** 2026-10-04  
**Scope:** `src/acquisition_platform/*.py` — all 8 modules  
**Method:** Static analysis of loops, data dependencies, and thread-safety

---

## 1. Summary of Findings

| Module | Parallelizable? | Approach | Speedup Potential | Thread-Safe? |
|--------|----------------|----------|-------------------|--------------|
| `entity_resolution.py` | **Yes** | Block-level parallelism | High (O(n²) → O(n²/p)) | Needs care |
| `matching.py` | **Yes** | Pair-level parallelism | High (O(n·m) → O(n·m/p)) | Yes (read-only) |
| `evolution.py` | **Yes** | Population-level parallelism | High (O(pop·gen) → O(pop·gen/p)) | Needs care |
| `valuation.py` | **Partial** | Method-level parallelism | Low-Medium | Yes (stateless) |
| `portfolio_optimizer.py` | **No** | Greedy sequential | None | N/A |
| `fraud_detection.py` | **Partial** | Signal-level parallelism | Low | Yes (stateless) |
| `dynamic_pricing.py` | **No** | Single computation | None | N/A |
| `search_ranking.py` | **Partial** | Listing-level parallelism | Medium | Needs care |

---

## 2. Detailed Analysis by Module

### 2.1 `entity_resolution.py` — **HIGH PRIORITY**

**Location:** `EntityResolver.resolve()` (lines 157–215)

**Current bottleneck:**
```python
# Lines 184-199: Nested loop over blocks and pairs
for indices in blocks.values():
    for a in range(len(indices)):
        for b in range(a + 1, len(indices)):
            i, j = indices[a], indices[b]
            self.comparison_count += 1
            sim = _jaro_winkler(normalized[i], normalized[j])
            # ... domain bonus ...
            if sim >= self.threshold:
                uf.union(i, j)
```

**Parallelization strategy:**
- **Block-level parallelism:** Each block's pair comparisons are independent. Use `concurrent.futures.ProcessPoolExecutor` or `ThreadPoolExecutor` to process blocks in parallel.
- **Pair-level parallelism within blocks:** For large blocks, parallelize the O(k²) pair comparisons using `concurrent.futures`.

**Key constraint — Union-Find is sequential:**
The `_UnionFind.union()` operation mutates shared state (`parent`, `rank`). This is the main thread-safety concern.

**Recommended approach:**
1. **Phase 1 (parallel):** Compute all similarity scores in parallel, producing a list of `(i, j, sim)` tuples that pass the threshold.
2. **Phase 2 (sequential):** Apply union operations in order (or use a concurrent union-find with locking).

```python
# Phase 1: Parallel similarity computation
def compute_block_similarities(block_indices, normalized, entities, threshold):
    results = []
    for a in range(len(block_indices)):
        for b in range(a + 1, len(block_indices)):
            i, j = block_indices[a], block_indices[b]
            sim = _jaro_winkler(normalized[i], normalized[j])
            # ... domain bonus ...
            if sim >= threshold:
                results.append((i, j))
    return results

# Phase 2: Sequential union (fast, O(n α(n)))
for i, j in all_passing_pairs:
    uf.union(i, j)
```

**Speedup:** For n entities with b blocks, ideal speedup is O(b) for the similarity phase. The union phase is nearly linear and fast.

**Thread-safety concerns:**
- `self.comparison_count` is mutated in the loop — use `threading.Lock` or compute counts per-block and sum.
- `_UnionFind` is not thread-safe — keep union operations in a single thread.
- `normalized` list is read-only after construction — safe to share.

---

### 2.2 `matching.py` — **HIGH PRIORITY**

**Location:** `BuyerSellerMatcher.match()` (lines 61–107)

**Current bottleneck:**
```python
# Lines 76-83: Nested loop over all buyer-seller pairs
candidates: list[tuple[float, float, Buyer, Seller]] = []
for buyer in buyers:
    for seller in sellers:
        if not self._is_feasible(buyer, seller):
            continue
        score = self._compute_score(buyer, seller)
        confidence = self._compute_confidence(buyer, seller, score)
        candidates.append((score, confidence, buyer, seller))
```

**Parallelization strategy:**
- **Pair-level parallelism:** Each (buyer, seller) pair's feasibility check, score, and confidence computation is completely independent. This is embarrassingly parallel.
- Use `concurrent.futures.ProcessPoolExecutor` for CPU-bound work or `ThreadPoolExecutor` for I/O-bound scenarios.

```python
def evaluate_pair(buyer, sellers):
    results = []
    for seller in sellers:
        if not self._is_feasible(buyer, seller):
            continue
        score = self._compute_score(buyer, seller)
        confidence = self._compute_confidence(buyer, seller, score)
        results.append((score, confidence, buyer, seller))
    return results

# Parallelize over buyers
with concurrent.futures.ThreadPoolExecutor() as executor:
    futures = [executor.submit(evaluate_pair, buyer, sellers) for buyer in buyers]
    candidates = [item for f in concurrent.futures.as_completed(futures) for item in f.result()]
```

**Speedup:** O(n·m) → O(n·m/p) where p = number of workers. For large buyer/seller lists, this is a near-linear speedup.

**Thread-safety concerns:**
- `Buyer` and `Seller` dataclasses are read-only during matching — safe to share.
- `candidates` list is built from independent results — safe to collect after all futures complete.
- No shared mutable state — fully thread-safe.

---

### 2.3 `evolution.py` — **HIGH PRIORITY**

**Location:** `EvolutionEngine.evolve()` (lines 94–194)

**Current bottleneck:**
```python
# Line 120: Fitness evaluation for entire population
fitness_scores = [fitness_fn(gene) for gene in population]

# Line 176: Final fitness evaluation
final_fitness = [fitness_fn(gene) for gene in population]
```

**Parallelization strategy:**
- **Population-level parallelism:** Each individual's fitness evaluation is independent. This is the classic parallel fitness evaluation pattern in genetic algorithms.
- Use `concurrent.futures.ProcessPoolExecutor` if `fitness_fn` is CPU-bound (likely for model evaluation).
- Use `concurrent.futures.ThreadPoolExecutor` if `fitness_fn` involves I/O (e.g., database queries, API calls).

```python
# Parallel fitness evaluation
with concurrent.futures.ProcessPoolExecutor() as executor:
    fitness_scores = list(executor.map(fitness_fn, population))
```

**Speedup:** O(population_size) → O(population_size/p) per generation. Over G generations, total speedup is significant.

**Thread-safety concerns:**
- `fitness_fn` must be thread-safe or process-safe. If it uses shared state (e.g., a model), it needs to be either:
  - Stateless (pure function of gene value)
  - Protected by locks
  - Copied to each process (ProcessPoolExecutor handles this via fork/spawn)
- `random` module is used in tournament selection — `random.sample()` and `random.random()` are not thread-safe. The selection phase should remain sequential or use thread-local random state.
- `population` list is read-only during fitness evaluation — safe to share.

**Additional consideration:**
The tournament selection and crossover/mutation phases (lines 142–171) are inherently sequential (each generation depends on the previous). Only the fitness evaluation phase parallelizes cleanly.

---

### 2.4 `valuation.py` — **LOW-MEDIUM PRIORITY**

**Location:** `ValuationEngine.ensemble_valuation()` (lines 102–156)

**Current bottleneck:**
```python
# Lines 129-139: Sequential method calls
dcf_result = self.dcf_valuation(...)
comps_result = self.comparable_valuation(...)
```

**Parallelization strategy:**
- **Method-level parallelism:** DCF and Comps valuations are independent. Could run in parallel.
- However, both methods are fast (simple arithmetic), so overhead may dominate.

**Speedup:** Minimal — the methods are O(years) and O(1) respectively. Not worth parallelizing unless `years` is very large.

**Thread-safety concerns:**
- `ValuationEngine` is stateless — fully thread-safe.
- `ValuationResult` is a dataclass — immutable after creation.

**Verdict:** Not recommended for parallelization. The methods are too fast to benefit.

---

### 2.5 `portfolio_optimizer.py` — **NOT PARALLELIZABLE**

**Location:** `PortfolioOptimizer.optimize()` (lines 54–119)

**Why not parallelizable:**
- The greedy selection loop (lines 90–102) is inherently sequential — each selection depends on the remaining budget and selected sectors.
- The scoring loop (lines 81–85) is O(n) and fast.
- The problem structure (greedy approximation) does not lend itself to parallelization.

**Thread-safety concerns:**
- N/A — no parallelization opportunity.

---

### 2.6 `fraud_detection.py` — **LOW PRIORITY**

**Location:** `FraudDetector.score()` (lines 50–98)

**Current bottleneck:**
```python
# Lines 68-78: Loop over signals
for signal in signals:
    weight = self.WEIGHTS.get(signal.name, self.DEFAULT_WEIGHT)
    fraud_value = 1.0 - signal.value
    contribution = fraud_value * weight
    weighted_sum += contribution
    total_weight += weight
    explanations.append(...)
```

**Parallelization strategy:**
- **Signal-level parallelism:** Each signal's contribution is independent.
- However, the loop is O(n) where n is typically small (3 signals expected). Overhead would dominate.

**Speedup:** Negligible — the loop is too short to benefit from parallelization.

**Thread-safety concerns:**
- `FraudDetector` is stateless (only class-level constants) — fully thread-safe.
- `FraudScore` and `FraudSignal` are dataclasses — immutable after creation.

**Verdict:** Not recommended for parallelization. The loop is too short.

---

### 2.7 `dynamic_pricing.py` — **NOT PARALLELIZABLE**

**Location:** `PricingEngine.recommend_price()` (lines 26–70)

**Why not parallelizable:**
- Single computation with no loops.
- All operations are simple arithmetic.

**Thread-safety concerns:**
- `PricingEngine` is stateless — fully thread-safe.

---

### 2.8 `search_ranking.py` — **MEDIUM PRIORITY**

**Location:** `SearchRanker.rank()` (lines 40–103)

**Current bottleneck:**
```python
# Lines 68-92: Loop over listings with sequential dependency
for listing in listings:
    cat = listing.category
    if cat in category_counts:
        diversity_factor = 0.7
    else:
        diversity_factor = 1.0
    category_counts[cat] = category_counts.get(cat, 0) + 1
    # ... personalization ...
    score = listing.relevance * diversity_factor * personalization_factor
    scored.append(...)
```

**Parallelization strategy:**
- **Listing-level parallelism with sequential diversity:** The diversity factor depends on category counts, which creates a sequential dependency. However:
  - **Option A:** Pre-compute category counts in a first pass (O(n)), then compute scores in parallel (O(n/p)).
  - **Option B:** Use a two-phase approach: (1) count categories sequentially, (2) compute scores in parallel.

```python
# Phase 1: Count categories (sequential, O(n))
category_counts = {}
for listing in listings:
    cat = listing.category
    category_counts[cat] = category_counts.get(cat, 0) + 1

# Phase 2: Compute scores in parallel (O(n/p))
def compute_score(listing, category_counts, preferred_category):
    cat = listing.category
    # ... compute diversity_factor based on category_counts ...
    # ... compute personalization_factor ...
    return RankedListing(...)

with concurrent.futures.ThreadPoolExecutor() as executor:
    scored = list(executor.map(lambda l: compute_score(l, category_counts, preferred_category), listings))
```

**Speedup:** O(n) → O(n/p) for the scoring phase. The counting phase remains O(n) but is fast.

**Thread-safety concerns:**
- `category_counts` is read-only after Phase 1 — safe to share.
- `scored` list is built from independent results — safe to collect.
- `SearchRanker` is stateless — fully thread-safe.

**Verdict:** Worth parallelizing for large listing sets (n > 1000).

---

## 3. Thread-Safety Summary

| Module | Shared Mutable State | Thread-Safe? | Mitigation |
|--------|---------------------|--------------|------------|
| `entity_resolution.py` | `_UnionFind.parent`, `_UnionFind.rank`, `self.comparison_count` | **No** | Keep union in single thread; use locks for counter |
| `matching.py` | None (read-only inputs) | **Yes** | None needed |
| `evolution.py` | `random` module, `population` list | **Partial** | Use thread-local random; keep selection sequential |
| `valuation.py` | None (stateless) | **Yes** | None needed |
| `portfolio_optimizer.py` | None (local variables only) | **Yes** | None needed |
| `fraud_detection.py` | None (stateless) | **Yes** | None needed |
| `dynamic_pricing.py` | None (stateless) | **Yes** | None needed |
| `search_ranking.py` | `category_counts` dict | **Partial** | Pre-compute counts before parallel scoring |

---

## 4. Recommended Implementation Priority

1. **`matching.py`** — Easiest win. Embarrassingly parallel, no shared state, large speedup potential.
2. **`evolution.py`** — High impact for GA workloads. Parallel fitness evaluation is standard practice.
3. **`entity_resolution.py`** — High impact for large datasets. Requires careful handling of union-find.
4. **`search_ranking.py`** — Moderate impact. Two-phase approach works well.
5. **`valuation.py`** — Low priority. Methods are too fast.
6. **`fraud_detection.py`** — Low priority. Loop is too short.
7. **`portfolio_optimizer.py`** — Not parallelizable.
8. **`dynamic_pricing.py`** — Not parallelizable.

---

## 5. General Recommendations

### 5.1 Use `concurrent.futures` over raw threads
The `concurrent.futures` module provides a high-level interface that handles thread/process pool management, task distribution, and result collection. It is the recommended approach for all parallelization in this codebase.

### 5.2 Prefer `ProcessPoolExecutor` for CPU-bound work
If the fitness function, similarity computation, or scoring involves heavy computation (e.g., model inference, complex math), use `ProcessPoolExecutor` to bypass the GIL.

### 5.3 Prefer `ThreadPoolExecutor` for I/O-bound work
If the fitness function involves database queries, API calls, or file I/O, use `ThreadPoolExecutor` to avoid the overhead of process creation.

### 5.4 Avoid parallelizing small workloads
For loops with fewer than ~100 iterations or operations that complete in <1ms, the overhead of thread/process creation and task distribution will dominate. Profile before parallelizing.

### 5.5 Consider `joblib` or `multiprocessing.Pool` for advanced use cases
For more complex parallelization patterns (e.g., nested parallelism, shared memory), consider `joblib` or `multiprocessing.Pool` with shared memory.

### 5.6 Thread-local storage for random number generation
The `random` module is not thread-safe. If parallelizing code that uses `random`, either:
- Use `threading.local()` to create thread-local random state
- Use `numpy.random` with explicit `Generator` instances per thread
- Keep random-dependent code sequential

---

## 6. Estimated Speedup Summary

| Module | Sequential Complexity | Parallel Complexity | Estimated Speedup (p=4) |
|--------|----------------------|---------------------|------------------------|
| `entity_resolution.py` | O(n²) | O(n²/p) + O(n α(n)) | ~3.5x |
| `matching.py` | O(n·m) | O(n·m/p) | ~3.8x |
| `evolution.py` | O(pop·gen) | O(pop·gen/p) | ~3.5x |
| `search_ranking.py` | O(n) | O(n) + O(n/p) | ~2.5x |
| `valuation.py` | O(years) | O(years) | ~1.0x |
| `fraud_detection.py` | O(n) | O(n) | ~1.0x |

*Note: Actual speedup depends on workload characteristics, data size, and hardware. These are theoretical upper bounds.*

---

## 7. Conclusion

The acquisition platform has **three high-priority parallelization opportunities** (`matching.py`, `evolution.py`, `entity_resolution.py`) that could yield **3-4x speedup** on multi-core systems. The key challenges are:

1. **Union-Find in entity resolution** — requires separating similarity computation (parallel) from union operations (sequential).
2. **Random state in evolution** — requires thread-local random or sequential selection phase.
3. **Shared counters** — require locks or per-thread accumulation with final reduction.

All other modules are either too fast to benefit from parallelization or have inherent sequential dependencies that prevent it.
