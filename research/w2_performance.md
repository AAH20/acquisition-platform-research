# Wave 2: Performance Bottleneck Analysis

**Date:** 2026-10-04  
**Scope:** All 8 modules in `acquisition_platform`  
**Method:** Empirical benchmarking with `time.perf_counter()` + code review

---

## Executive Summary

| Module | Complexity | Bottleneck Severity | Key Issue |
|--------|-----------|-------------------|-----------|
| `entity_resolution.py` | O(n²) per block | **CRITICAL** | Single-block worst case: 22s for 2K entities |
| `matching.py` | O(n·m·log(n·m)) | **HIGH** | 78s for 5K×5K; generates all pairs before sorting |
| `portfolio_optimizer.py` | O(n log n) | **MEDIUM** | Diversification bonus is dead code (computed, never used) |
| `evolution.py` | O(pop·gen) | **LOW** | Converges in 11 gens; redundant final fitness evaluation |
| `fraud_detection.py` | O(n³) worst case | **MEDIUM** | Ring graphs (>4 cycle) not detected; algorithm is correct but limited |
| `search_ranking.py` | O(n log n) | **NONE** | Efficient; 0.13s for 100K listings |
| `valuation.py` | O(years) | **NONE** | Fast; 0.024s for 100-year DCF × 1000 iterations |
| `dynamic_pricing.py` | O(1) | **NONE** | Trivial; 0.12s for 100K calls |

---

## 1. Entity Resolution — CRITICAL O(n²) Bottleneck

### Benchmark Results

| n (entities) | Blocking | Time | Comparisons | Clusters |
|-------------|----------|------|-------------|----------|
| 100 | Single block | 0.055s | 4,950 | 1 |
| 500 | Single block | 1.629s | 124,750 | 1 |
| 1,000 | Single block | 5.485s | 499,500 | 1 |
| 2,000 | Single block | 22.18s | 1,999,000 | 1 |

**Scaling:** ~4× time doubling → confirmed O(n²).

### Root Cause

```python
# entity_resolution.py:184-199
for indices in blocks.values():
    for a in range(len(indices)):
        for b in range(a + 1, len(indices)):
            i, j = indices[a], indices[b]
            self.comparison_count += 1
            sim = _jaro_winkler(normalized[i], normalized[j])
```

When all entities share the same 3-character prefix (e.g., "Company 0 Inc", "Company 1 Inc", ...), they fall into a single block. The nested loop compares all O(n²) pairs.

### Jaro-Winkler Cost

Each `_jaro_winkler()` call is O(len(s1) × len(s2)) due to the match-window scan. For long names, this multiplies the O(n²) pair count.

### Recommendations

1. **Pre-filter by length:** Skip pairs where `abs(len(s1) - len(s2)) > threshold` — Jaro-Winkler cannot exceed the length ratio.
2. **Length-based sub-blocking:** Within each 3-char block, sub-block by name length (e.g., ±20% length window).
3. **Early termination in Jaro-Winkler:** If the maximum possible Jaro similarity (given length difference) is below threshold, return 0 immediately.
4. **Cache normalized names:** Already done (line 178), but `_jaro_winkler` could use `@lru_cache` for repeated comparisons.
5. **Use `rapidfuzz` library:** C++ implementation of Jaro-Winkler is 10-100× faster than pure Python.

---

## 2. Matching — HIGH O(n·m) Pair Generation

### Benchmark Results

| Buyers × Sellers | Time | Matches |
|-----------------|------|---------|
| 100 × 100 | 0.017s | 77 |
| 500 × 500 | 0.414s | 383 |
| 1,000 × 1,000 | 2.230s | 772 |
| 2,000 × 2,000 | 11.95s | 1,542 |
| 5,000 × 5,000 | 78.82s | 3,855 |

**Scaling:** ~5-6× time doubling → confirmed O(n·m) with significant constant factor.

### Root Cause

```python
# matching.py:76-83
candidates: list[tuple[float, float, Buyer, Seller]] = []
for buyer in buyers:
    for seller in sellers:
        if not self._is_feasible(buyer, seller):
            continue
        score = self._compute_score(buyer, seller)
        confidence = self._compute_confidence(buyer, seller, score)
        candidates.append((score, confidence, buyer, seller))
```

All n×m pairs are generated, scored, and stored before sorting. For 5K×5K, that's 25M tuples in memory.

### Recommendations

1. **Category-based pre-partitioning:** Group buyers and sellers by category first, then only compare within matching categories. This reduces n×m to Σ(n_c × m_c).
2. **Budget-based pruning:** For each buyer, only consider sellers with `asking_price <= buyer.budget`. Sort sellers by price and use binary search.
3. **Use a heap for top-K:** Instead of sorting all candidates, use `heapq.nlargest` to find top-K matches without full sort.
4. **Lazy confidence computation:** `_compute_confidence` is called for every pair but only used for the final match. Compute it only for matched pairs.

---

## 3. Portfolio Optimizer — MEDIUM: Dead Code (Diversification Bug)

### Benchmark Results

| Assets | Time | Selected | Return |
|--------|------|----------|--------|
| 100 | 0.0001s | 9 | 38,643 |
| 1,000 | 0.0004s | 6 | 46,676 |
| 10,000 | 0.0088s | 6 | 48,457 |

Performance is fine, but there is a **correctness bug**:

### Bug: Diversification Bonus Never Applied

```python
# portfolio_optimizer.py:96-101
diversification_bonus = 1.5 if asset.sector not in selected_sectors else 1.0
effective_score = score * diversification_bonus  # ← Computed but NEVER USED

selected.append(asset)  # ← Selection uses original sort order, not effective_score
selected_sectors.add(asset.sector)
remaining_budget -= asset.cost
```

The `effective_score` is computed but never used for selection. The greedy loop iterates over `scored` (sorted by base score only), so diversification has no effect on which assets are chosen.

**Proof:** In a test with 5 SaaS assets (returns 50K-46K) and 5 e-commerce assets (returns 45K-41K), all 5 selected assets were from SaaS — the diversification bonus had zero effect.

### Recommendations

1. **Fix the bug:** Re-sort or use a priority queue that accounts for `effective_score` at each step.
2. **True greedy diversification:** At each step, select the asset with the highest `effective_score` given the current `selected_sectors`, not a pre-sorted list.
3. **Consider risk parity:** The current risk adjustment (`base_score * (1 + risk_tolerance)`) is a linear scaling that doesn't differentiate assets.

---

## 4. Evolution — LOW: Convergence Speed & Redundancy

### Benchmark Results

| Population | Generations | Time | Best Fitness | Converged | Actual Gens |
|-----------|-------------|------|-------------|-----------|-------------|
| 20 | 20 | 0.0008s | 10.0000 | Yes | 11 |
| 50 | 50 | 0.0017s | 10.0000 | Yes | 11 |
| 100 | 100 | 0.0035s | 10.0000 | Yes | 11 |
| 200 | 100 | 0.0071s | 10.0000 | Yes | 11 |

### Findings

1. **Fast convergence:** All configurations converge in 11 generations for a simple quadratic fitness function. The convergence check (5 stagnant generations after gen 10) works correctly.
2. **Redundant final evaluation:** After the loop, `fitness_fn` is called again for the entire population (line 176), but the fitness scores from the last generation's evaluation (line 120) are already available. This doubles the fitness evaluations for the final generation.
3. **Tournament selection is weak:** Using `random.sample(range(len(population)), 2)` picks 2 random individuals and takes the better. This is a very weak selection pressure (effectively random for large populations).

### Recommendations

1. **Reuse last generation's fitness scores:** Store `fitness_scores` from the last iteration and reuse them for the final result.
2. **Increase tournament size:** Use 3-4 individuals per tournament for better selection pressure.
3. **Adaptive mutation:** Reduce mutation rate as convergence approaches to fine-tune solutions.
4. **Early termination for flat fitness:** If all fitness values are identical, terminate immediately.

---

## 5. Fraud Detection — MEDIUM: Graph Cycle Detection Limitations

### Benchmark Results

| Graph Type | Nodes | Time | Has Ring |
|-----------|-------|------|----------|
| Ring | 50 | 0.0005s | **False** (bug) |
| Ring | 100 | 0.0001s | **False** (bug) |
| Ring | 500 | 0.0006s | **False** (bug) |
| Dense | 50 | 0.0001s | True |
| Dense | 100 | 0.0002s | True |
| Dense | 200 | 0.0004s | True |

### Bug: Ring Graphs Not Detected

The `_has_cycle_of_length_3_or_4` method only detects 3-cycles and 4-cycles. A ring of 5+ nodes (e.g., N0→N1→N2→N3→N4→N0) is **not detected** as a fraud ring, even though it represents a coordinated fraud ring.

**Test results:**
- Triangle (3-cycle): ✅ Detected
- Square (4-cycle): ✅ Detected
- Pentagon (5-cycle): ❌ Not detected
- 10-cycle ring: ❌ Not detected

### Recommendations

1. **Generalize cycle detection:** Use DFS-based cycle detection that finds cycles of any length, or at least up to length 6-8.
2. **Strongly connected components:** For directed graphs, use Tarjan's SCC algorithm — any SCC with >1 node indicates a ring.
3. **Performance is acceptable:** Even for 500-node graphs, detection is <1ms. The issue is correctness, not speed.

---

## 6. Search Ranking — No Issues

### Benchmark Results

| Listings | Time | Results |
|----------|------|---------|
| 100 | 0.0001s | 100 |
| 1,000 | 0.0009s | 1,000 |
| 10,000 | 0.0129s | 10,000 |
| 100,000 | 0.1340s | 100,000 |

**Scaling:** Linear O(n) — excellent. No bottlenecks.

---

## 7. Valuation — No Issues

### Benchmark Results

| DCF Years | Time (×1000) |
|-----------|-------------|
| 5 | 0.0021s |
| 10 | 0.0039s |
| 20 | 0.0053s |
| 50 | 0.0117s |
| 100 | 0.0240s |

**Scaling:** Linear O(years) — excellent. No bottlenecks.

---

## 8. Dynamic Pricing — No Issues

### Benchmark Results

| Calls | Time |
|-------|------|
| 100,000 | 0.1214s |

**Scaling:** O(1) per call — excellent. No bottlenecks.

---

## Caching & Memoization Opportunities

### High-Value Targets

| Module | Function | Cache Key | Expected Speedup |
|--------|----------|-----------|-----------------|
| `entity_resolution` | `_jaro_winkler(s1, s2)` | `(s1, s2)` | 10-100× for repeated comparisons |
| `matching` | `_compute_score(buyer, seller)` | `(buyer.id, seller.id)` | 2-5× for repeated market runs |
| `matching` | `_compute_confidence(buyer, seller, score)` | `(buyer.id, seller.id, score)` | 2-5× |
| `fraud_detection` | `_has_cycle_of_length_3_or_4(adj, nodes)` | `frozenset(edges)` | Avoids recomputation for same graph |

### Implementation Notes

- Use `functools.lru_cache(maxsize=1024)` for pure functions.
- For `_jaro_winkler`, normalize the key: `tuple(sorted([s1, s2]))` since Jaro-Winkler is symmetric.
- For matching, cache at the `BuyerSellerMatcher` instance level (not global) since scores depend on buyer/seller objects.

---

## Summary of Recommendations (Priority Order)

1. **CRITICAL — Entity Resolution:** Add length-based pre-filtering and sub-blocking to avoid O(n²) worst case.
2. **HIGH — Matching:** Add category-based pre-partitioning and budget-based pruning to reduce pair count.
3. **MEDIUM — Portfolio Optimizer:** Fix diversification bonus dead code bug.
4. **MEDIUM — Fraud Detection:** Generalize cycle detection beyond length 3-4.
5. **LOW — Evolution:** Reuse last generation's fitness scores; increase tournament size.
6. **LOW — All modules:** Add `@lru_cache` to expensive pure functions.
