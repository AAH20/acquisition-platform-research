# Wave 2: Scalability & Large-Scale Behavior Analysis

**Date:** 2026-10-04  
**Scope:** EntityResolver, BuyerSellerMatcher, PortfolioOptimizer, EvolutionEngine

---

## 1. EntityResolver — ⚠️ CRITICAL BOTTLENECK

### Test Results

| Input Size | Time | Comparisons | Notes |
|---|---|---|---|
| 1,000 entities (same prefix "Company N") | **4.05s** | 499,500 | All pairs compared — blocking failed |
| 1,000 entities (varied names) | **4.93s** | 499,500 | Still all pairs — blocking ineffective |
| 2,000 entities (same prefix) | **15.49s** | 1,999,000 | O(n²) confirmed |

### Root Cause

The blocking strategy uses `normalized[:3]` (first 3 characters of normalized name). For names like "Company 0", "Company 1", ..., all normalize to start with `"com"`, so **every entity lands in the same block**. The result is a full O(n²) pairwise comparison — 499,500 comparisons for 1,000 entities (exactly n*(n-1)/2).

The Jaro-Winkler computation itself is O(len1 × len2) per pair, making the total cost O(n² × L²) where L is average name length.

### Scaling Projection

| Entities | Estimated Time | Comparisons |
|---|---|---|
| 1,000 | 4s | 500K |
| 2,000 | 15s | 2M |
| 5,000 | ~95s | 12.5M |
| 10,000 | ~6.3 min | 50M |
| 50,000 | ~2.6 hours | 1.25B |

### Recommendations

1. **Improve blocking keys**: Use multiple blocking strategies (first 3 chars + Soundex/Metaphone + domain) and union the candidate pairs.
2. **Length-based filtering**: Skip pairs where name lengths differ by more than a threshold (Jaro-Winkler cannot exceed a certain score for very different lengths).
3. **Prefix-based early termination**: If the first 4+ characters differ, skip the full Jaro-Winkler computation.
4. **Use `rapidfuzz` or `jellyfish`**: C-optimized string similarity libraries are 10-100x faster than pure Python.
5. **Parallelize**: The pairwise comparisons are embarrassingly parallel.

---

## 2. BuyerSellerMatcher — ✅ SCALES WELL

### Test Results

| Buyers | Sellers | Time | Matches |
|---|---|---|---|
| 100 | 100 | 0.021s | 100 |
| 500 | 500 | 0.479s | 500 |

### Analysis

- Complexity: O(n*m*log(n*m)) for generating and sorting all feasible pairs.
- At 500×500 = 250,000 candidate pairs, completes in under 0.5s.
- The greedy assignment loop is O(n*m) after sorting.
- **No scalability concerns** for realistic marketplace sizes (thousands of buyers/sellers).

---

## 3. PortfolioOptimizer — ✅ SCALES EXCELLENTLY

### Test Results

| Assets | Time | Selected |
|---|---|---|
| 1,000 | 0.0007s | 5 |
| 10,000 | 0.0069s | 47 |

### Analysis

- Complexity: O(n log n) for sorting + O(n) for greedy selection.
- 10,000 assets processed in under 7ms.
- The diversification bonus uses a set lookup (O(1) per asset).
- **No scalability concerns** — can handle 100K+ assets easily.

---

## 4. EvolutionEngine — ✅ SCALES WELL

### Test Results

| Population | Generations | Time | Converged | Generations Run |
|---|---|---|---|---|
| 500 | 50 | 0.028s | Yes | 11 |
| 2,000 | 100 | 0.087s | Yes | 11 |

### Analysis

- Complexity: O(population_size × generations) for fitness evaluation.
- Converges quickly (11 generations) due to elitism + tournament selection.
- The convergence check (improvement < 0.001 for 5 consecutive generations) prevents wasted computation.
- **No scalability concerns** — even 10,000 population × 200 generations would complete in ~2s.

---

## 5. Summary: Scalability Ranking

| Module | Status | Bottleneck | Max Practical Input |
|---|---|---|---|
| **EntityResolver** | 🔴 CRITICAL | O(n²) blocking failure | ~2,000 entities |
| BuyerSellerMatcher | 🟢 Good | None | 10,000+ pairs |
| PortfolioOptimizer | 🟢 Excellent | None | 100,000+ assets |
| EvolutionEngine | 🟢 Good | None | 10,000+ population |

### Key Finding

**EntityResolver is the only module that does not scale.** Its blocking strategy fails catastrophically when entity names share a common prefix (e.g., "Company 0", "Company 1", ...), degrading to O(n²) pairwise comparisons. At 10,000 entities, it would take ~6 minutes and perform 50 million Jaro-Winkler computations. This is the top priority for optimization.

All other modules scale linearly or log-linearly and can handle large inputs without modification.
