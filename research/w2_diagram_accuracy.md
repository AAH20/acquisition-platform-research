# Wave 2: Mermaid Diagram Accuracy Report

**Date:** 2026-10-04  
**Scope:** Verify all 6 mermaid diagrams against actual codebase structure  
**Codebase:** `src/acquisition_platform/` (9 Python modules, ~1,500 LOC)

---

## Executive Summary

| Diagram | Accuracy | Missing Nodes | Incorrect Edges | Verdict |
|---------|----------|---------------|----------------|---------|
| system_architecture.mmd | Low | 15+ | All edges conceptual | Major revisions needed |
| data_flow.mmd | Low | 10+ | Linear flow misleading | Major revisions needed |
| module_interactions.mmd | Medium | 3 | All edges conceptual | Needs correction |
| evolution_framework.mmd | Medium | 4 | Some edges inaccurate | Needs correction |
| class-diagram.md | Medium | 10+ | Missing relationships | Incomplete |
| sequences.md | High | 0 | Minor omissions | Mostly accurate |

---

## Actual Code Structure

### Modules (9 files)

| Module | Classes | Key Methods |
|--------|---------|-------------|
| `matching.py` | Buyer, Seller, Match, BuyerSellerMatcher | `match()`, `_is_feasible()`, `_compute_score()`, `_compute_confidence()` |
| `valuation.py` | ValuationResult, ValuationEngine | `dcf_valuation()`, `comparable_valuation()`, `ensemble_valuation()`, `sde_valuation()`, `arr_valuation()` |
| `fraud_detection.py` | FraudSignal, FraudScore, GraphAnalysis, FraudDetector | `score()`, `analyze_graph()`, `_has_cycle_of_length_3_or_4()` |
| `portfolio_optimizer.py` | Asset, Portfolio, PortfolioOptimizer | `optimize()` |
| `dynamic_pricing.py` | PriceRecommendation, PricingEngine | `recommend_price()` |
| `entity_resolution.py` | ResolvedEntity, EntityCluster, EntityResolver | `resolve()`, `_jaro_winkler()`, `_canonical_name()` |
| `search_ranking.py` | Listing, RankedListing, SearchRanker | `rank()` |
| `evolution.py` | EvaluationResult, Benchmark, EvolutionResult, EvolutionEngine | `evaluate()`, `evolve()` |

### Key Observations

1. **No inter-module imports**: All 8 engine modules are completely independent. No module imports from another.
2. **No external integrations**: No database, API, cache, or storage layer exists.
3. **No ML/NLP components**: No GNN, XGBoost, LLM, or learning-to-rank implementations.
4. **No API/UI layer**: No REST, MCP, WebSocket, or dashboard code.
5. **No due diligence module**: Referenced in diagrams but does not exist.
6. **No cross-border M&A module**: Referenced in diagrams but does not exist.
7. **No auction designer module**: Referenced in diagrams but does not exist.

---

## Diagram 1: system_architecture.mmd

### Missing Nodes (15+)

**Entire layers that don't exist in code:**
- External Data Sources (Crunchbase, PitchBook, Flippa, Acquire.com, Empire Flippers, Quiet Light, FE International)
- Ingestion Layer (Web Crawlers, API Client, Data Normalizer, Data Validator)
- Storage Layer (Neo4j, Snowflake, Redis, VDR)
- ML/NLP Layer (GNN Matcher, Learning to Rank, NLP Entity Extraction, Ensemble Valuator, XGBoost Fraud Detector, LLM Advisor)
- API Layer (REST API, MCP Server, WebSocket)
- UI Layer (Dashboard, Search Interface, Deal Room, Analytics)

**Core modules that don't exist:**
- Due Diligence (DD)
- Cross-Border M&A (XB)
- Auction Designer (AUCTION)

### Incorrect Edges

All edges are conceptual, not actual code dependencies:
- `External --> Ingestion` — No ingestion code exists
- `Ingestion --> Storage` — No storage code exists
- `Storage --> Core` — No storage layer exists
- `Core --> ML` — No ML layer exists
- `ML --> Evolution` — No ML layer exists
- `Evolution --> Core` — No actual dependency
- `Core --> API` — No API layer exists
- `API --> UI` — No UI layer exists

### Verdict

**Major revisions needed.** The diagram depicts a full production system with data pipelines, storage, ML infrastructure, and API/UI layers. The actual codebase is a pure optimization library with 8 independent algorithmic modules. The diagram should either:
1. Be rewritten to show only the actual optimization modules, or
2. Clearly label the missing layers as "planned" or "not implemented"

---

## Diagram 2: data_flow.mmd

### Missing Nodes (10+)

- All 7 data sources (no integration code)
- All 4 ingestion methods (no ingestion code)
- Normalization, Validation, Enrichment (no processing code)
- All 4 storage systems (no storage code)
- All 4 output types (no output code)
- Search Ranking (exists but not shown)
- Entity Resolution (exists but placed in Processing, not as standalone)
- Evolution framework (exists but not shown)

### Incorrect Edges

- `Sources --> Ingestion` — No code
- `Ingestion --> Processing` — No code
- `Processing --> Storage` — No code
- `Storage --> Analytics` — No code; analytics modules are independent
- `Analytics --> Output` — No code

### Structural Issues

1. **Linear pipeline is misleading**: The actual modules are independent optimization engines, not stages in a data pipeline.
2. **Missing modules**: Search Ranking and Entity Resolution are core modules but not shown in the flow.
3. **No feedback loops**: The evolution framework provides feedback to optimization but isn't shown.

### Verdict

**Major revisions needed.** The diagram implies a linear ETL pipeline that doesn't exist. Should be rewritten to show the actual modular structure with independent optimization engines.

---

## Diagram 3: module_interactions.mmd

### Missing Nodes (3)

- Recommendation System (REC) — doesn't exist
- Auction Design (AUC) — doesn't exist
- Due Diligence (DD) — doesn't exist
- Cross-Border M&A (XB) — doesn't exist

### Incorrect Edges

All edges are conceptual, not actual code dependencies:
- `ER --> MATCH` — No actual dependency; modules are independent
- `ER --> RANK` — No actual dependency
- `VAL --> MATCH` — No actual dependency
- `VAL --> PORT` — No actual dependency
- `VAL --> PRICE` — No actual dependency
- `FRAUD --> MATCH` — No actual dependency
- `FRAUD --> REC` — REC doesn't exist
- `MATCH --> PORT` — No actual dependency
- `MATCH --> AUC` — AUC doesn't exist
- `RANK --> REC` — REC doesn't exist
- `PORT --> EVO` — No actual dependency
- `PRICE --> EVO` — No actual dependency
- `AUC --> EVO` — AUC doesn't exist
- `DD --> EVO` — DD doesn't exist
- `XB --> EVO` — XB doesn't exist
- `EVO --> BENCH` — No actual dependency
- `EVAL --> EVO` — No actual dependency

### Verdict

**Needs correction.** The diagram shows a layered architecture with data flow between layers, but the actual codebase has completely independent modules with no inter-module dependencies. Should be rewritten to show the actual modular structure.

---

## Diagram 4: evolution_framework.mmd

### Missing Nodes (4)

- Metrics Calculator — doesn't exist as separate component
- Comparison — doesn't exist as separate component
- Result Ranking — doesn't exist as separate component
- Visualization — doesn't exist

### Incorrect Edges

- `Input --> Evolution` — Oversimplified; evolution takes fitness function and gene range, not "research data"
- `Evolution --> Evaluation` — No separate evaluation framework exists
- `Evaluation --> Output` — No separate output layer exists
- `METRICS --> COMPARISON` — These components don't exist
- `COMPARISON --> RANKING` — These components don't exist
- `RANKING --> VISUAL` — These components don't exist

### What's Correct

- The genetic algorithm flow (Initialize → Evaluate → Select → Crossover → Mutate → Replace) is accurate
- The evolution loop structure is correct

### Verdict

**Needs correction.** The diagram shows a more complex evaluation and output framework than what exists. The actual code has a simple `EvolutionEngine.evolve()` method that returns an `EvolutionResult`. Should be simplified to match the actual implementation.

---

## Diagram 5: class-diagram.md

### Missing Classes (10+)

**Engine/Optimizer classes not shown:**
- BuyerSellerMatcher
- ValuationEngine
- FraudDetector
- PortfolioOptimizer
- PricingEngine
- EntityResolver
- SearchRanker
- EvolutionEngine

**Data classes not shown:**
- ResolvedEntity
- GraphAnalysis
- EvaluationResult

### Missing Relationships

- No relationships shown between engine classes and their result classes
- No composition relationships (e.g., PortfolioOptimizer creates Portfolio)
- No inheritance relationships shown (GraphAnalysis extends FraudScore)

### Missing Methods

- Only `Benchmark.evaluate()` is shown
- No methods for any other class
- Key methods like `match()`, `optimize()`, `evolve()`, `score()`, `rank()`, `resolve()` are missing

### What's Correct

- Data class fields are mostly accurate
- `GraphAnalysis` as subclass of `FraudScore` is correct
- `EvaluationResult` returned by `Benchmark.evaluate()` is correct
- `EvolutionResult` returned by `EvolutionEngine.evolve()` is correct

### Verdict

**Incomplete.** The diagram only shows data classes and omits all engine/optimizer classes that contain the actual business logic. Should be expanded to include the full class hierarchy.

---

## Diagram 6: sequences.md

### Buyer-Seller Matching Sequence

**Accuracy: High**

What's correct:
- `match(buyers, sellers)` method signature
- Feasibility check (budget >= asking_price, category match)
- Score computation
- Greedy assignment

Minor omissions:
- Doesn't show the sorting step explicitly
- Doesn't show confidence computation

### Valuation Ensemble Sequence

**Accuracy: High**

What's correct:
- `ensemble_valuation()` calls `dcf_valuation()` and `comparable_valuation()`
- Averaging of values
- Confidence computation from agreement

Minor omissions:
- Doesn't show `sde_valuation()` and `arr_valuation()` methods that also exist

### Fraud Detection Sequence

**Accuracy: High**

What's correct:
- `score(signals)` method
- Weighted average of inverted signals
- Risk level determination
- `analyze_graph(graph)` method
- Adjacency list construction
- 3-cycle and 4-cycle detection
- Returns `GraphAnalysis` with `has_ring` and `risk_score`

### Evolution Optimization Sequence

**Accuracy: High**

What's correct:
- `evolve(fitness_fn, gene_range)` method signature
- Population initialization
- Fitness evaluation loop
- Convergence check
- Elitism (select elites)
- Tournament selection
- Crossover + Mutation
- Returns `EvolutionResult`

Minor omissions:
- Doesn't show the `for...else` construct for generation loop
- Doesn't show diversity calculation

### Verdict

**Mostly accurate.** The sequence diagrams correctly reflect the actual method calls and control flow. Minor omissions exist but don't affect understanding.

---

## Summary of Findings

### Critical Issues

1. **Phantom modules**: 3+ modules referenced in diagrams don't exist (Due Diligence, Cross-Border M&A, Auction Designer)
2. **Phantom layers**: Entire architectural layers don't exist (Ingestion, Storage, ML/NLP, API, UI)
3. **Phantom components**: Multiple components don't exist (GNN, XGBoost, LLM, Recommendation System, etc.)
4. **Misleading dependencies**: All inter-module edges are conceptual, not actual code dependencies
5. **Missing classes**: Class diagram omits all engine/optimizer classes

### Minor Issues

1. **Incomplete method lists**: Class diagrams only show fields, not methods
2. **Missing data classes**: ResolvedEntity, GraphAnalysis, EvaluationResult not shown
3. **Oversimplified sequences**: Some steps omitted but core flow is correct

### Recommendations

1. **system_architecture.mmd**: Rewrite to show only actual optimization modules, or clearly label unimplemented layers
2. **data_flow.mmd**: Replace linear pipeline with modular architecture diagram
3. **module_interactions.mmd**: Remove phantom modules, show actual independence of modules
4. **evolution_framework.mmd**: Simplify to match actual EvolutionEngine implementation
5. **class-diagram.md**: Add all engine/optimizer classes and their relationships
6. **sequences.md**: Minor updates to show missing methods (sde_valuation, arr_valuation)

---

## Appendix: Actual Module Dependency Graph

```
┌─────────────────────────────────────────────────────────────┐
│                    acquisition_platform                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   matching   │  │   valuation  │  │    fraud     │       │
│  │              │  │              │  │   detection  │       │
│  │ Buyer        │  │ Valuation    │  │ FraudSignal  │       │
│  │ Seller       │  │ Result       │  │ FraudScore   │       │
│  │ Match        │  │ Valuation    │  │ GraphAnalysis│       │
│  │ BuyerSeller  │  │ Engine       │  │ FraudDetector│       │
│  │ Matcher      │  │              │  │              │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  portfolio   │  │   dynamic    │  │    entity    │       │
│  │  optimizer   │  │   pricing    │  │  resolution  │       │
│  │              │  │              │  │              │       │
│  │ Asset        │  │ Price        │  │ Resolved     │       │
│  │ Portfolio    │  │ Recommendation│ │ Entity       │       │
│  │ Portfolio    │  │ Pricing      │  │ EntityCluster│       │
│  │ Optimizer    │  │ Engine       │  │ EntityResolver│      │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐                         │
│  │   search     │  │   evolution  │                         │
│  │   ranking    │  │              │                         │
│  │              │  │ Evaluation   │                         │
│  │ Listing      │  │ Result       │                         │
│  │ RankedListing │  │ Benchmark    │                         │
│  │ SearchRanker │  │ Evolution    │                         │
│  │              │  │ Result       │                         │
│  │              │  │ Evolution     │                         │
│  │              │  │ Engine       │                         │
│  └──────────────┘  └──────────────┘                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘

NO INTER-MODULE DEPENDENCIES
All modules are independent and self-contained.
```
