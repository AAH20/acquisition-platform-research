# Wave 2 Research: Cross-Border Module Gap Analysis

**Date:** 2026-10-04
**Agent:** Wave 1 Research Agent
**Focus:** Cross-border M&A module gap — `cross_border.py` missing

---

## Executive Summary

The `cross_border.py` module is referenced in the project's README and architecture diagrams but **does not exist** in the codebase. Cross-Border M&A is identified as bottleneck #5 (High severity, NP-hard, multi-constraint) affecting all platforms (85% cross-border), yet no solution module has been implemented. This document identifies the gap, the classes/functions the module should export, and the NP-hard problems it should solve.

---

## 1. Gap Identification

### 1.1 Module Does Not Exist

```bash
$ grep -r 'cross_border' src/
# No matches found

$ find . -name "cross_border*"
# No files found
```

The `src/acquisition_platform/` directory contains 9 Python files:
- `__init__.py`
- `matching.py`
- `valuation.py`
- `fraud_detection.py`
- `portfolio_optimizer.py`
- `dynamic_pricing.py`
- `entity_resolution.py`
- `search_ranking.py`
- `evolution.py`

**No `cross_border.py` exists.**

### 1.2 README References

The README references Cross-Border M&A in multiple places but never assigns it a solution module:

| Location | Reference | Solution Module |
|----------|-----------|-----------------|
| Line 65 (Bottlenecks table) | `5 | Cross-Border Complexity | High | All (85%) | Yes (multi-constraint) | —` | **None assigned** |
| Line 114 (Architecture diagram) | `XB["Cross-Border M&A<br/>Multi-Constraint"]` | Diagram node only |
| Line 249 (Module interactions) | `XB[Cross-Border M&A]` | Diagram node only |

The Solution Module column for bottleneck #5 is `—` (em dash), indicating no module has been built.

### 1.3 Architecture Diagrams

Both `system_architecture.mmd` and `module_interactions.mmd` include Cross-Border M&A as a node:

- **system_architecture.mmd:** `XB[Cross-Border M&A<br/>Multi-Constraint]` in the Core Optimization Engine subgraph
- **module_interactions.mmd:** `XB[Cross-Border M&A]` in the Optimization Layer subgraph, with `XB --> EVO` (feeds into Evolution Engine)

### 1.4 `__init__.py` Does Not Export It

The package `__init__.py` exports 24 symbols from 8 modules. No `cross_border` imports or exports exist.

### 1.5 No Other Module Imports From It

```bash
$ grep -rn 'from.*cross_border\|import.*cross_border' .
# No matches found
```

No module depends on `cross_border.py` — it is a leaf node in the architecture.

### 1.6 README Module Reference Missing

The README "Module Reference" section documents 8 modules (`matching.py`, `valuation.py`, `fraud_detection.py`, `portfolio_optimizer.py`, `dynamic_pricing.py`, `entity_resolution.py`, `search_ranking.py`, `evolution.py`). **No `cross_border.py` section exists.**

### 1.7 NP-Hard Problems Table Missing

The README "NP-Hard Problems" table lists 8 problems. Cross-Border M&A is **not listed** despite being classified as NP-hard in the bottlenecks table and architecture docs.

---

## 2. What `cross_border.py` Should Export

Based on the architecture diagrams, the w1_cross_border_ma.md research, and the patterns established by existing modules, the module should export the following classes and functions:

### 2.1 Data Classes (following existing module patterns)

| Class | Purpose | Fields |
|-------|---------|--------|
| `Jurisdiction` | Represents a regulatory jurisdiction | `name`, `country_code`, `regulatory_body`, `filing_threshold`, `review_timeline_days`, `penalty` |
| `RegulatoryFiling` | Represents a required regulatory filing | `jurisdiction`, `filing_type`, `trigger_threshold`, `mandatory`, `dependencies`, `estimated_days` |
| `CrossBorderDeal` | Represents a cross-border transaction | `acquirer_country`, `target_country`, `deal_value`, `industry`, `filings_required` |
| `FilingSequence` | Represents an optimized filing sequence | `sequence`, `total_days`, `parallel_groups`, `critical_path` |
| `TaxStructure` | Represents a tax-optimized holding structure | `jurisdictions`, `withholding_rates`, `treaty_benefits`, `effective_tax_rate` |
| `HedgingStrategy` | Represents an FX hedging approach | `instrument`, `coverage_ratio`, `contingency`, `expected_cost` |
| `IntegrationPlan` | Represents a cultural integration plan | `phases`, `timeline_months`, `synergy_targets`, `retention_risk` |

### 2.2 Engine/Optimizer Classes

| Class | Purpose | Key Methods |
|-------|---------|-------------|
| `RegulatoryCoordinator` | Optimizes multi-jurisdictional filing sequence | `optimize_sequence(filings) -> FilingSequence`, `identify_dependencies(filings)`, `compute_critical_path(sequence)` |
| `TaxOptimizer` | Optimizes tax structure across jurisdictions | `optimize_structure(deal, jurisdictions) -> TaxStructure`, `compute_withholding_taxes(structure)`, `apply_treaty_benefits(structure)` |
| `HedgingOptimizer` | Optimizes FX hedging with deal contingency | `optimize_hedge(deal, fx_exposure) -> HedgingStrategy`, `compute_expected_cost(strategy)`, `evaluate_contingency(strategy, deal_probability)` |
| `IntegrationPlanner` | Plans cultural integration sequence | `plan_integration(acquirer_culture, target_culture) -> IntegrationPlan`, `estimate_synergy_realization(plan)`, `assess_retention_risk(plan)` |
| `CrossBorderOptimizer` | Main entry point — multi-objective optimization | `optimize(deal) -> CrossBorderResult`, `evaluate_tradeoffs(deal)`, `generate_recommendations(deal)` |

### 2.3 Result Classes

| Class | Purpose |
|-------|---------|
| `CrossBorderResult` | Aggregated optimization result |
| `RegulatoryResult` | Regulatory coordination result |
| `TaxOptimizationResult` | Tax optimization result |
| `HedgingResult` | Hedging optimization result |
| `IntegrationResult` | Integration planning result |

### 2.4 Expected `__init__.py` Exports

The following should be added to `__init__.py`:

```python
from acquisition_platform.cross_border import (
    CrossBorderDeal,
    CrossBorderOptimizer,
    CrossBorderResult,
    FilingSequence,
    HedgingOptimizer,
    HedgingStrategy,
    IntegrationPlan,
    IntegrationPlanner,
    Jurisdiction,
    RegulatoryCoordinator,
    RegulatoryFiling,
    TaxOptimizer,
    TaxStructure,
)
```

---

## 3. NP-Hard Problems It Should Solve

From `w1_cross_border_ma.md` Section 10, the module should address **6 NP-hard problems**:

### 3.1 Multi-Jurisdictional Regulatory Coordination

**Problem:** Given N jurisdictions, each with M regulatory requirements, determine the optimal filing sequence that minimizes total approval time while respecting dependencies.

**Complexity:** NP-hard — equivalent to job-shop scheduling with precedence constraints.

**Algorithm approach:** Heuristic scheduling (parallel filing where possible, early engagement). The `RegulatoryCoordinator` class should implement this.

### 3.2 Transfer Pricing Optimization

**Problem:** Given a multinational group with K entities across J jurisdictions, determine intercompany pricing for N transactions that minimizes global tax liability while satisfying arm's length constraints.

**Complexity:** NP-hard — multi-objective optimization with conflicting constraints.

**Algorithm approach:** Iterative optimization with BEPS documentation constraints. Part of `TaxOptimizer`.

### 3.3 Tax Treaty Network Optimization

**Problem:** Given a network of bilateral tax treaties between J countries, determine the optimal holding company structure that minimizes withholding taxes.

**Complexity:** NP-hard — equivalent to finding optimal paths in a directed graph with path-dependent edge weights.

**Algorithm approach:** Graph-based optimization with treaty benefit analysis. Part of `TaxOptimizer`.

### 3.4 Cultural Integration Planning

**Problem:** Given two organizations with different cultural attributes, determine the optimal integration sequence that maximizes synergy realization while minimizing talent loss.

**Complexity:** NP-hard — combinatorial optimization with interdependent, non-linear outcomes.

**Algorithm approach:** Heuristic planning with cultural due diligence inputs. The `IntegrationPlanner` class should implement this.

### 3.5 Currency Hedging with Deal Contingency

**Problem:** Given a cross-border deal with uncertain closing probability, determine the optimal hedging strategy that minimizes expected cost while protecting against FX risk.

**Complexity:** NP-hard — stochastic optimization with path-dependent payoffs.

**Algorithm approach:** Deal-contingent forward pricing with walk-away optionality. The `HedgingOptimizer` class should implement this.

### 3.6 Synergy Realization Optimization

**Problem:** Given a set of potential synergies with interdependencies, costs, and timing constraints, determine the optimal synergy capture plan that maximizes NPV.

**Complexity:** NP-hard — resource-constrained project scheduling with precedence constraints.

**Algorithm approach:** Milestone-based heuristics with dependency analysis. Part of `IntegrationPlanner`.

---

## 4. Module Position in Architecture

### 4.1 Layer

Cross-Border M&A belongs in the **Optimization Layer** (per `module_interactions.mmd`):

```
OptimizationLayer:
    PORT[Portfolio Optimization]
    PRICE[Dynamic Pricing]
    AUC[Auction Design]
    DD[Due Diligence]
    XB[Cross-Border M&A]        <-- MISSING
```

### 4.2 Dependencies

Per the architecture diagram, Cross-Border M&A feeds into the Evolution Engine:

```
XB --> EVO
```

It is a **leaf node** — no other module depends on it. It should consume outputs from:
- `ValuationEngine` (deal value for FX/tax calculations)
- `FraudDetector` (sanctions/compliance screening)
- `EntityResolver` (jurisdiction/entity mapping)

### 4.3 Evolution Framework Integration

The module should integrate with `evolution.py` for hyperparameter optimization:
- Population: different filing sequences, tax structures, hedging strategies
- Fitness: total approval time, tax efficiency, synergy realization
- Operators: crossover (combine structures), mutation (adjust parameters)

---

## 5. Gap Summary

| Aspect | Status | Details |
|--------|--------|---------|
| Module file | **Missing** | `cross_border.py` does not exist |
| `__init__.py` exports | **Missing** | No cross_border imports |
| README Module Reference | **Missing** | No documentation section |
| README NP-Hard table | **Missing** | Not listed despite being NP-hard |
| README Bottleneck #5 | **Unassigned** | Solution Module = `—` |
| Architecture diagrams | **Present** | Referenced as `XB` node |
| Other module imports | **None** | No dependencies on it |
| Tests | **Missing** | No `test_cross_border.py` |

---

## 6. Recommendation

Implement `cross_border.py` as a multi-objective optimization module addressing the 6 NP-hard problems identified in the w1 research. The module should:

1. Follow the existing module pattern (data classes + engine class + result class)
2. Export via `__init__.py` for package-level access
3. Integrate with `evolution.py` for hyperparameter tuning
4. Be documented in the README Module Reference and NP-Hard Problems tables
5. Have a corresponding `tests/test_cross_border.py` test file
6. Be assigned as the Solution Module for bottleneck #5 in the README

---

*End of Wave 2 Gap Analysis*
