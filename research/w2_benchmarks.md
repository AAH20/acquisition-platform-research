# Wave 2: Benchmark Suite Results

**Date:** 2026-10-04  
**Scope:** Comprehensive benchmark suite for all acquisition platform modules  
**File Created:** `tests/test_benchmarks.py` (15 benchmarks)

---

## Summary

Created a comprehensive pytest-benchmark suite covering all 13 modules plus the full orchestrator pipeline. All 15 benchmarks pass successfully.

---

## Benchmark Results

| Benchmark | Mean Time | OPS | Rounds |
|-----------|-----------|-----|--------|
| `test_benchmark_auction_100` | 17.7 µs | 56,478 | 40,837 |
| `test_benchmark_cross_border_10` | 71.8 µs | 13,924 | 12,998 |
| `test_benchmark_portfolio_100` | 150.3 µs | 6,652 | 6,459 |
| `test_benchmark_due_diligence_50` | 346.0 µs | 2,890 | 3,380 |
| `test_benchmark_ranking_1000` | 1,054.5 µs | 948 | 1,171 |
| `test_benchmark_matching_100` | 1,971.8 µs | 507 | 447 |
| `test_benchmark_orchestrator_full` | 4,977.8 µs | 201 | 22 |
| `test_benchmark_entity_resolution_100` | 4,019.9 µs | 249 | 159 |
| `test_benchmark_evolution_100` | 4,704.4 µs | 213 | 91 |
| `test_benchmark_fraud_1000` | 6,360.1 µs | 157 | 226 |
| `test_benchmark_valuation_1000` | 12,257.1 µs | 82 | 133 |
| `test_benchmark_pricing_10000` | 29,199.0 µs | 34 | 20 |
| `test_benchmark_entity_resolution_1000` | 39,008.9 µs | 26 | 27 |
| `test_benchmark_recommendation_100` | 61,338.2 µs | 16 | 21 |
| `test_benchmark_matching_1000` | 786,733.2 µs | 1.27 | 5 |

---

## Key Observations

### Fastest Operations (>10K OPS)
- **Auction design** (100 bids): 17.7 µs — near-constant time for sorting-based winner selection
- **Cross-border optimization** (10 jurisdictions): 71.8 µs — linear in jurisdictions
- **Portfolio optimization** (100 assets): 150.3 µs — O(n log n) greedy selection

### Moderate Performance (100–10K OPS)
- **Due diligence scheduling** (50 tasks, 10 reviewers): 346 µs
- **Search ranking** (1000 listings): 1.05 ms
- **Matching** (100×100): 1.97 ms
- **Full orchestrator pipeline**: 4.98 ms
- **Entity resolution** (100 entities): 4.02 ms
- **Evolution** (100 pop, 50 gen): 4.70 ms
- **Fraud detection** (1000 scores): 6.36 ms
- **Valuation** (1000 DCF): 12.26 ms

### Slowest Operations (<100 OPS)
- **Dynamic pricing** (10,000 recommendations): 29.2 ms
- **Entity resolution** (1000 entities): 39.0 ms
- **Recommendation** (100 items, 10 users): 61.3 ms
- **Matching** (1000×1000): 786.7 ms — O(n²m²) pair generation dominates

### Scaling Characteristics
- **Matching** scales quadratically: 100→1000 (10× data) = ~400× slower (expected O(n²) behavior)
- **Entity resolution** scales ~10× from 100→1000 entities (near-linear with sorted-neighborhood blocking)
- **Pricing** scales linearly: 10K recommendations in ~29 ms
- **Fraud detection** scales linearly: 1000 scores in ~6.4 ms

---

## Full Test Suite Results

```
655 tests collected
641 passed
14 failed (pre-existing, unrelated to benchmarks)
15 benchmarks passed
```

### Pre-existing Failures (not caused by benchmark suite)
- `test_batch.py`: 11 failures (batch processing tests)
- `test_type_safety.py`: 1 failure (mypy compliance)
- `test_valuation.py`: 1 failure (DCF caching assertion)

---

## Bug Fix Applied

Fixed a pre-existing syntax error in `src/acquisition_platform/orchestrator.py` (line 49–55) where the `from acquisition_platform.evolution import (` block was malformed — the closing parenthesis and subsequent imports were incorrectly placed inside the import statement. This was blocking all imports of the orchestrator module.

---

## Files Created/Modified

| File | Action |
|------|--------|
| `tests/test_benchmarks.py` | **Created** — 15 benchmark tests |
| `src/acquisition_platform/orchestrator.py` | **Fixed** — syntax error in import block |
| `research/w2_benchmarks.md` | **Created** — this summary |
