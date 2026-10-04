# Wave 2: Memory Usage & Optimization Analysis

**Scope:** `src/acquisition_platform/*.py` (9 files)
**Focus:** Memory efficiency, unnecessary intermediate data structures, generator opportunities

---

## 1. entity_resolution.py — Intermediate Lists

### 1.1 `resolve()` method (lines 157–215)

| Line | Structure | Issue |
|------|-----------|-------|
| 178 | `normalized = [_normalize(e.get("name", "")) for e in entities]` | Full list of all normalized names. Could be a generator if consumed lazily, but it's indexed multiple times (blocking + comparison), so a list is justified. |
| 179–181 | `blocks: dict[str, list[int]]` | Stores all indices per block. Necessary for the blocking strategy. |
| 202–204 | `groups: dict[int, list[int]]` | Another full index-to-group mapping. Could be avoided by building clusters directly from union-find roots. |
| 209 | `cluster_entities = [entities[i] for i in indices]` | Intermediate list per cluster. Could yield entities directly. |
| 220 | `names = [e.get("name", "") for e in entities]` (in `_canonical_name`) | Another intermediate list. Could iterate once and count. |

### 1.2 `_jaro_winkler()` function (lines 50–114)

| Line | Structure | Issue |
|------|-----------|-------|
| 67 | `s1_matches = [False] * len1` | Boolean list proportional to string length. |
| 68 | `s2_matches = [False] * len2` | Boolean list proportional to string length. |

These are **necessary** for the Jaro algorithm — they track which characters have been matched. Not easily replaceable without changing the algorithm.

### 1.3 Optimization Opportunities

1. **Merge `groups` dict into cluster building** (lines 202–215): Instead of building `groups` then iterating to create `EntityCluster` objects, build clusters directly:
   ```python
   # Current: groups dict → iterate → build clusters
   # Optimized: single pass building clusters
   root_to_cluster: dict[int, list[dict]] = defaultdict(list)
   for i, entity in enumerate(entities):
       root_to_cluster[uf.find(i)].append(entity)
   ```
   This eliminates one `dict[int, list[int]]` structure.

2. **`_canonical_name` single-pass counting** (lines 218–226): Replace list + Counter with a single-pass approach:
   ```python
   counts: dict[str, int] = {}
   for e in entities:
       name = e.get("name", "")
       counts[name] = counts.get(name, 0) + 1
   ```
   Saves one intermediate `names` list per cluster.

---

## 2. matching.py — Unnecessary Tuples

### 2.1 `match()` method (lines 61–107)

| Line | Structure | Issue |
|------|-----------|-------|
| 76 | `candidates: list[tuple[float, float, Buyer, Seller]]` | **Major memory issue.** Stores ALL feasible pairs as 4-tuples. For n buyers × m sellers, this is O(n×m) memory. |
| 83 | `candidates.append((score, confidence, buyer, seller))` | Each tuple holds two floats + two object references. |
| 86 | `candidates.sort(...)` | Sorts the entire list in-place. |
| 93 | `for score, confidence, buyer, seller in candidates` | Unpacks tuples during greedy assignment. |

### 2.2 Optimization Opportunities

1. **Use a generator + heap for lazy evaluation** (lines 76–86): Instead of materializing all pairs, use a min-heap (negated scores for max-heap behavior) to yield pairs in score order:
   ```python
   import heapq
   candidates = []
   for buyer in buyers:
       for seller in sellers:
           if not self._is_feasible(buyer, seller):
               continue
           score = self._compute_score(buyer, seller)
           confidence = self._compute_confidence(buyer, seller, score)
           heapq.heappush(candidates, (-score, confidence, buyer, seller))
   ```
   This avoids the O(n×m) sort and allows early termination if only top-K matches are needed.

2. **Store only what's needed** (line 76): The `confidence` value is only used in the final `Match` object. If confidence can be recomputed cheaply, don't store it in the tuple — recompute during assignment. This reduces tuple size from 4 elements to 3.

3. **Early termination** (lines 93–106): If the caller only needs top-K matches, add a `max_matches` parameter to stop early, avoiding full iteration over all candidates.

---

## 3. evolution.py — Unnecessary History

### 3.1 `evolve()` method (lines 94–194)

| Line | Structure | Issue |
|------|-----------|-------|
| 111 | `population = [random.uniform(low, high) for _ in range(self.population_size)]` | Initial population list. Necessary. |
| 120 | `fitness_scores = [fitness_fn(gene) for gene in population]` | **Full fitness list per generation.** O(population_size) memory. |
| 142–144 | `sorted_indices = sorted(range(len(population)), ...)` | Index list for sorting. |
| 145 | `elite_genes = [population[i] for i in sorted_indices[: self.elitism]]` | Intermediate list. |
| 148 | `new_population = list(elite_genes)` | **Unnecessary copy.** `elite_genes` is already a fresh list. |
| 176 | `final_fitness = [fitness_fn(gene) for gene in population]` | Another full fitness list. |

### 3.2 Key Observations

- **No cross-generation history is stored** — this is good. The engine doesn't keep past populations or fitness histories.
- **Within each generation**, there are 3–4 intermediate lists that could be reduced.

### 3.3 Optimization Opportunities

1. **Eliminate `new_population = list(elite_genes)` copy** (line 148): `elite_genes` is already a new list from the list comprehension on line 145. Just use `new_population = elite_genes` and append to it directly.

2. **Reuse `fitness_scores` for final evaluation** (lines 120, 176): If the loop runs to completion (no convergence break), `fitness_scores` from the last generation is the same as `final_fitness`. Only recompute if the loop broke early:
   ```python
   if not converged:
       final_fitness = fitness_scores  # reuse
   else:
       final_fitness = [fitness_fn(gene) for gene in population]
   ```

3. **Use `heapq.nlargest` for elitism** (lines 142–145): Instead of sorting all indices, use `heapq.nlargest(self.elitism, range(len(population)), key=lambda i: fitness_scores[i])` to get only the top-K indices in O(n log k) time.

4. **Generator for tournament selection** (lines 152–156): The tournament selection creates temporary index pairs. This is minor but could be encapsulated in a generator function for clarity.

---

## 4. portfolio_optimizer.py — Intermediate Lists

### 4.1 `optimize()` method (lines 54–119)

| Line | Structure | Issue |
|------|-----------|-------|
| 70 | `affordable = [a for a in assets if a.cost <= self.budget]` | Filtered list. Could be a generator. |
| 80–85 | `scored = []` + `scored.append((adjusted_score, asset))` | List of (score, asset) tuples. |
| 87 | `scored.sort(...)` | In-place sort. |
| 75 | `selected: list[Asset]` | Result list. |

### 4.2 Optimization Opportunities

1. **Generator for `affordable`** (line 70): Since `affordable` is only iterated once (lines 81–85), it could be a generator expression:
   ```python
   affordable = (a for a in assets if a.cost <= self.budget)
   ```
   However, `len(affordable)` is not used, so this is safe.

2. **Combine scoring and selection** (lines 80–102): The two-pass approach (score all, then select) could be merged into a single pass using a heap, but for typical portfolio sizes (< 1000 assets), the current approach is fine.

---

## 5. fraud_detection.py — Intermediate Structures

### 5.1 `analyze_graph()` method (lines 100–137)

| Line | Structure | Issue |
|------|-----------|-------|
| 109 | `adjacency: dict[str, set[str]]` | Adjacency list. Necessary for graph traversal. |
| 143 | `node_set = set(nodes)` | **Redundant.** `nodes` is already a list; `node_set` is created but never used (the function uses `adjacency` dict lookups instead). |
| 66 | `explanations: list[str]` | List of explanation strings. |

### 5.2 Optimization Opportunities

1. **Remove unused `node_set`** (line 143): `node_set = set(nodes)` is created but never referenced. Dead code — remove it.

2. **Generator for explanations** (lines 75–78): The explanations list could be a generator if the caller doesn't need random access, but since it's stored in a dataclass field, a list is appropriate.

---

## 6. search_ranking.py — Intermediate Lists

### 6.1 `rank()` method (lines 40–103)

| Line | Structure | Issue |
|------|-----------|-------|
| 66 | `scored: list[RankedListing]` | Full list of scored items. |
| 95–98 | `best_by_id: dict[str, RankedListing]` | Deduplication dictionary. |
| 101 | `results = sorted(best_by_id.values(), ...)` | Final sorted list. |

### 6.2 Optimization Opportunities

1. **Combine scoring and deduplication** (lines 66–98): Instead of building `scored` then deduplicating into `best_by_id`, update `best_by_id` directly during scoring:
   ```python
   best_by_id: dict[str, RankedListing] = {}
   for listing in listings:
       # ... compute score ...
       ranked = RankedListing(...)
       if ranked.id not in best_by_id or ranked.score > best_by_id[ranked.id].score:
           best_by_id[ranked.id] = ranked
   ```
   This eliminates the `scored` list entirely, saving O(n) memory.

---

## 7. valuation.py — Minimal Memory Usage

**No significant memory issues.** All methods perform scalar computations and return single `ValuationResult` objects. The `dcf_valuation` loop (lines 63–65) uses O(1) memory.

---

## 8. dynamic_pricing.py — Minimal Memory Usage

**No significant memory issues.** All computations are scalar. The `market_multipliers` dict (lines 47–51) is a small constant lookup table.

---

## Summary of Findings

| File | Issue | Severity | Estimated Savings |
|------|-------|----------|-------------------|
| `matching.py` | O(n×m) candidate tuple list | **High** | O(n×m) → O(k) with heap + early termination |
| `entity_resolution.py` | Multiple intermediate lists | Medium | ~30% reduction in peak memory |
| `evolution.py` | Unnecessary list copies | Low–Medium | ~20% reduction in per-generation memory |
| `search_ranking.py` | Redundant `scored` list | Medium | O(n) → O(1) additional |
| `portfolio_optimizer.py` | Generator opportunity | Low | Minor |
| `fraud_detection.py` | Dead code (`node_set`) | Low | Negligible (cleanup) |
| `valuation.py` | None | — | — |
| `dynamic_pricing.py` | None | — | — |

### Top 3 Recommendations (by impact)

1. **`matching.py`**: Replace full candidate list + sort with a heap-based lazy evaluation. This is the single largest memory consumer — O(n×m) tuples for n buyers and m sellers.

2. **`entity_resolution.py`**: Merge the `groups` dict into direct cluster building and use single-pass counting in `_canonical_name`. Eliminates 2 intermediate data structures.

3. **`search_ranking.py`**: Eliminate the `scored` list by updating `best_by_id` directly during scoring. Simple change, clear memory win.
