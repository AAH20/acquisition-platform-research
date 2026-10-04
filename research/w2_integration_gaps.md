# Wave 2: Integration Gap Analysis

**Date:** 2026-10-04  
**Scope:** Cross-module integration audit of `acquisition_platform` package

---

## 1. Does `matching.py` use `valuation.py`?

**Status: NO — Integration Gap**

`matching.py` has zero imports from `valuation.py`. The matching engine scores pairs using a simple price-ratio formula:

```python
score = (1.0 - price_ratio) * category_bonus  # price_ratio = asking_price / budget
```

This is a purely relative score (how much budget headroom exists), not an absolute fair-value assessment. The `ValuationEngine` (DCF, comps, ensemble, SDE, ARR) is never consulted to determine whether the asking price is fair relative to intrinsic business value.

**Impact:** The matcher cannot distinguish between a fairly-priced seller and an overpriced one — it only knows if the buyer can afford it. A seller asking 10x DCF value would score identically to one asking 1.0x DCF value (assuming both fit the budget).

**Recommendation:** `BuyerSellerMatcher` should accept an optional `ValuationEngine` and incorporate valuation confidence or `(intrinsic_value - asking_price) / intrinsic_value` into the scoring formula.

---

## 2. Does `portfolio_optimizer.py` use `valuation.py`?

**Status: NO — Integration Gap**

`portfolio_optimizer.py` has zero imports from `valuation.py`. The `Asset` dataclass stores `expected_return` and `risk` as raw floats, and the optimizer uses them directly:

```python
base_score = asset.expected_return / (asset.risk + 0.01)
```

There is no mechanism to derive `expected_return` from financial data (FCF, revenue, SDE, ARR) via the `ValuationEngine`. The caller must pre-compute expected returns externally with no guidance or integration.

**Impact:** The optimizer operates in a vacuum — it can't evaluate new candidate assets that only have financial statements. The valuation module's ensemble confidence scores could also serve as a risk signal.

**Recommendation:** `PortfolioOptimizer.optimize()` should accept assets with raw financial data and use `ValuationEngine` to compute expected returns internally, or at minimum accept a `ValuationEngine` instance for on-the-fly valuation.

---

## 3. Does `fraud_detection.py` integrate with `matching.py`?

**Status: NO — Integration Gap**

`fraud_detection.py` has zero imports from `matching.py` (and vice versa). The `FraudDetector` operates on `FraudSignal` lists and relationship graphs, producing `FraudScore` / `GraphAnalysis` results. The `BuyerSellerMatcher` has no awareness of fraud scores.

**Impact:** Fraudulent sellers can enter the matching pool unchecked. A seller with a high fraud score (e.g., fake financials, identity fraud) would still be matched to buyers. The matcher's confidence score does not factor in fraud risk.

**Recommendation:** The matcher should accept an optional fraud score lookup (dict mapping seller_id → FraudScore) and either filter out high-fraud-risk sellers or penalize their match scores. Alternatively, a pipeline orchestrator should run fraud detection before matching.

---

## 4. Is there a top-level orchestrator that combines all modules?

**Status: NO — Critical Gap**

There is **no orchestrator, pipeline, or workflow file** in the project. The `__init__.py` only re-exports classes for convenience. There is no `main.py`, `pipeline.py`, `orchestrator.py`, `workflow.py`, or `cli.py` that chains modules together.

The README shows individual usage examples per module, but no end-to-end workflow combining them. The `docs/wiki/getting-started.md` also shows only isolated module usage.

**Impact:** Users must manually wire modules together. There is no canonical "acquisition pipeline" that:
1. Resolves entities (deduplication)
2. Screens for fraud
3. Values targets
4. Matches buyers to sellers
5. Optimizes portfolio
6. Recommends pricing
7. Ranks search results
8. Evolves hyperparameters

**Recommendation:** Create an `AcquisitionPipeline` or `Orchestrator` class that chains modules in a sensible order, passing outputs from one stage as inputs to the next.

---

## 5. Can `evolution.py` optimize parameters for all modules?

**Status: PARTIAL — Standalone Tool, Not Wired**

`evolution.py` is a generic genetic algorithm (`EvolutionEngine`) that can optimize any `fitness_fn: Callable[[float], float]`. It is fully decoupled from all other modules. The `Benchmark` class can evaluate metrics against targets, but there is no code that:

- Uses `EvolutionEngine` to tune `BuyerSellerMatcher` scoring weights
- Uses `EvolutionEngine` to tune `PortfolioOptimizer` risk tolerance
- Uses `EvolutionEngine` to tune `FraudDetector` signal weights
- Uses `EvolutionEngine` to tune `PricingEngine` multipliers
- Uses `EvolutionEngine` to tune `EntityResolver` threshold
- Uses `EvolutionEngine` to tune `SearchRanker` diversity/personalization factors

**Impact:** The evolution engine is a powerful tool sitting unused. Each module has hard-coded parameters that could be optimized against historical data or simulation benchmarks.

**Recommendation:** Create an `AutoTuner` or `HyperparameterOptimizer` that wraps `EvolutionEngine` and exposes per-module tuning interfaces. Each module should expose its tunable parameters and a fitness function that the evolution engine can optimize.

---

## 6. Modules That Should Import From Another But Don't

| Module | Should Import From | Reason |
|---|---|---|
| `dynamic_pricing.py` | `valuation.py` | `PricingEngine.recommend_price()` takes `base_value` as a raw float. It should accept financial data and use `ValuationEngine` to compute the base value internally, or at least accept a `ValuationEngine` instance. |
| `search_ranking.py` | `fraud_detection.py` | The ranker should filter out or penalize listings with high fraud scores before ranking. Currently, a fraudulent listing with high relevance would rank first. |
| `search_ranking.py` | `entity_resolution.py` | The ranker deduplicates by `id` only. It should use `EntityResolver` to cluster listings that refer to the same entity (same business listed multiple times). |
| `matching.py` | `entity_resolution.py` | The matcher should deduplicate buyers and sellers before matching. Currently, the same entity listed twice could be matched to two different buyers. |
| `matching.py` | `fraud_detection.py` | As noted in §3 — fraud screening should gate matching. |
| `portfolio_optimizer.py` | `fraud_detection.py` | The optimizer should filter out or penalize assets with high fraud scores. A fraudulent asset with high expected return would be selected. |
| `portfolio_optimizer.py` | `entity_resolution.py` | The optimizer should deduplicate assets. The same acquisition target listed twice could consume twice the budget. |
| `evolution.py` | All modules | As noted in §5 — the evolution engine should be wired to optimize parameters for every module. |

---

## Summary of Gaps

| # | Gap | Severity |
|---|---|---|
| 1 | `matching.py` ↔ `valuation.py` | Medium — matcher lacks fair-value awareness |
| 2 | `portfolio_optimizer.py` ↔ `valuation.py` | Medium — optimizer can't evaluate raw financials |
| 3 | `fraud_detection.py` ↔ `matching.py` | High — fraud sellers enter matching pool |
| 4 | No top-level orchestrator | Critical — no end-to-end pipeline exists |
| 5 | `evolution.py` not wired to modules | Medium — optimization engine is unused |
| 6 | `dynamic_pricing.py` ↔ `valuation.py` | Medium — pricing engine doesn't compute base value |
| 7 | `search_ranking.py` ↔ `fraud_detection.py` | High — fraudulent listings rank first |
| 8 | `search_ranking.py` ↔ `entity_resolution.py` | Medium — duplicate listings not deduplicated |
| 9 | `matching.py` ↔ `entity_resolution.py` | Medium — duplicate entities not deduplicated |
| 10 | `portfolio_optimizer.py` ↔ `fraud_detection.py` | High — fraudulent assets enter portfolio |
| 11 | `portfolio_optimizer.py` ↔ `entity_resolution.py` | Medium — duplicate assets not deduplicated |

---

## Recommended Integration Architecture

```
┌─────────────────────────────────────────────────────┐
│                  AcquisitionPipeline                 │
│                  (Orchestrator)                      │
├─────────────────────────────────────────────────────┤
│                                                     │
│  1. EntityResolver.resolve(entities)                │
│     → deduplicate buyers & sellers                 │
│                                                     │
│  2. FraudDetector.score(signals)                    │
│     → filter out high-risk entities                 │
│                                                     │
│  3. ValuationEngine.ensemble_valuation(financials)   │
│     → compute fair value for each target            │
│                                                     │
│  4. BuyerSellerMatcher.match(buyers, sellers)       │
│     → use valuation-adjusted scoring                │
│                                                     │
│  5. PortfolioOptimizer.optimize(assets)             │
│     → use valuation-derived expected returns        │
│                                                     │
│  6. PricingEngine.recommend_price(valuation, ...)   │
│     → use valuation as base_value                   │
│                                                     │
│  7. SearchRanker.rank(query, listings)              │
│     → filter fraud, deduplicate entities            │
│                                                     │
│  8. EvolutionEngine.evolve(fitness_fn, range)       │
│     → tune all module parameters                   │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## Files Analyzed

- `src/acquisition_platform/__init__.py` — package exports only, no orchestration
- `src/acquisition_platform/matching.py` — no cross-module imports
- `src/acquisition_platform/valuation.py` — no cross-module imports
- `src/acquisition_platform/portfolio_optimizer.py` — no cross-module imports
- `src/acquisition_platform/fraud_detection.py` — no cross-module imports
- `src/acquisition_platform/evolution.py` — no cross-module imports
- `src/acquisition_platform/dynamic_pricing.py` — no cross-module imports
- `src/acquisition_platform/entity_resolution.py` — no cross-module imports
- `src/acquisition_platform/search_ranking.py` — no cross-module imports
- `README.md` — individual usage examples only
- `docs/wiki/getting-started.md` — individual usage examples only
