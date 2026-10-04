# W2 Implementation: Orchestrator Module

## What Was Done

Implemented `src/acquisition_platform/orchestrator.py` — the unified pipeline that chains all 8 existing modules into a single configurable workflow.

## Files Created/Modified

| File | Action |
|------|--------|
| `src/acquisition_platform/orchestrator.py` | **Created** — PipelineConfig, PipelineResult, AcquisitionPipeline |
| `tests/test_orchestrator.py` | **Created** — 22 tests covering all pipeline stages |
| `src/acquisition_platform/__init__.py` | Already had orchestrator imports (added by sibling agent) |

## Architecture

### PipelineConfig dataclass
7 boolean flags controlling which stages run: `enable_matching`, `enable_valuation`, `enable_fraud`, `enable_portfolio`, `enable_pricing`, `enable_ranking`, `enable_evolution`. All default to `True`.

### PipelineResult dataclass
7 output fields: `matches`, `valuations`, `fraud_scores`, `portfolio`, `prices`, `rankings`, `evolution_result`. Lists default to empty; object fields default to `None`.

### AcquisitionPipeline class
- **`run(entities, config)`** — Main entry point. Classifies entity dicts into Buyer/Seller objects, then runs each enabled stage in order: Fraud → Valuation → Matching → Portfolio → Pricing → Ranking → Evolution.
- **`run_matching(buyers, sellers)`** — Delegates to `BuyerSellerMatcher.match()`
- **`run_valuation(entities)`** — Uses `ValuationEngine.comparable_valuation()` with 1.5x multiple on asking_price
- **`run_fraud_detection(entities)`** — Extracts signals from entity attributes, delegates to `FraudDetector.score()`
- **`run_portfolio_optimization(assets, budget)`** — Uses `PortfolioOptimizer` with risk_tolerance=0.5
- **`run_pricing(valuations)`** — Uses `PricingEngine.recommend_price()` with neutral market conditions
- **`run_ranking(query, items)`** — Delegates to `SearchRanker.rank()`
- **`run_evolution(fitness_fn, gene_range)`** — Delegates to `EvolutionEngine.evolve()`

### Entity Classification
Entities with `budget` → Buyer; entities with `asking_price` → Seller. This allows a single input list to feed both sides of the matching engine.

## Test Results

```
tests/test_orchestrator.py — 22/22 PASSED
Full suite (excluding pre-existing auction_design import error) — 423/423 PASSED
```

### Test Coverage
- `TestPipelineConfig` — default and custom config
- `TestPipelineResult` — default values and populated result
- `TestFullPipeline` — end-to-end with all stages enabled
- `TestPipelineWithFraudFiltering` — fraud detection runs on all entities
- `TestPipelineWithValuation` — valuation results have correct types
- `TestPipelineWithPortfolioOptimization` — portfolio object returned
- `TestPipelineWithPricing` — price recommendations within bounds
- `TestPipelineWithRanking` — ranked results sorted by score
- `TestPipelineWithEvolution` — evolution result has fitness metrics
- `TestEmptyPipeline` — empty input returns empty result
- `TestPartialPipeline` — disabled stages produce no output
- `TestPipelineResultStructure` — all fields exist with correct types
- `TestIndividualRunnerMethods` — each runner method works independently
- `TestPipelineEvolutionIntegration` — evolution metrics populated

## Issues Encountered

1. **Type mismatch** — `run_valuation` and `_sellers_to_assets` expected `list[dict]` but received `list[Seller]`. Fixed by passing seller dicts (not Seller objects) to these methods.
2. **Pre-existing collection error** — `tests/test_auction_design.py` fails to import `acquisition_platform.auction_design` (module from another wave, not yet implemented). Unrelated to orchestrator work.
