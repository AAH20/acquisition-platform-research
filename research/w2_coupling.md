# Wave 2: Module Coupling & Cohesion Analysis

**Package:** `src/acquisition_platform/`  
**Modules analyzed:** 9 files (8 functional + 1 `__init__.py`)  
**Total LOC:** ~1,140 lines of Python

---

## 1. Module Inventory

| Module | Lines | Primary Responsibility | Key Classes/Functions |
|--------|-------|----------------------|----------------------|
| `__init__.py` | 50 | Package facade; re-exports all public symbols | — |
| `dynamic_pricing.py` | 70 | Stackelberg game-theory pricing | `PricingEngine`, `PriceRecommendation` |
| `entity_resolution.py` | 226 | Entity deduplication via blocking + Jaro-Winkler + union-find | `EntityResolver`, `EntityCluster`, `_jaro_winkler`, `_UnionFind` |
| `evolution.py` | 194 | Genetic algorithm hyperparameter optimization | `EvolutionEngine`, `Benchmark`, `EvolutionResult` |
| `fraud_detection.py` | 172 | Fraud signal scoring + graph ring detection | `FraudDetector`, `FraudScore`, `GraphAnalysis` |
| `matching.py` | 156 | Buyer-seller matching (GAP approximation) | `BuyerSellerMatcher`, `Buyer`, `Seller`, `Match` |
| `portfolio_optimizer.py` | 119 | MIQP portfolio optimization | `PortfolioOptimizer`, `Asset`, `Portfolio` |
| `search_ranking.py` | 103 | Submodular search ranking | `SearchRanker`, `Listing`, `RankedListing` |
| `valuation.py` | 200 | Multi-method valuation (DCF, Comps, SDE, ARR, Ensemble) | `ValuationEngine`, `ValuationResult` |

---

## 2. Coupling Analysis

### 2.1 Import Coupling

**Finding: ZERO inter-module imports.**

No module in `acquisition_platform/` imports from any other module in the same package. The dependency graph is a **star topology** with `__init__.py` at the center:

```
                    __init__.py
                   /  |  |  |  |  |  |  \
                  /   |  |  |  |  |  |   \
                 /    |  |  |  |  |  |    \
           matching valuation fraud portfolio dynamic entity evolution search
           pricing  detection optimizer pricing resolution  ranking
```

Each module imports only from Python's standard library:
- `dataclasses` (all modules)
- `re`, `collections` (entity_resolution)
- `random`, `statistics` (evolution)
- `typing` (fraud_detection, evolution)

**Verdict:** Excellent. No tight coupling between modules.

### 2.2 Data Coupling

**Finding: NO shared data structures.**

Each module defines its own dataclasses with no cross-module type references. For example:
- `matching.py` defines `Buyer`, `Seller`, `Match` — used only within that module
- `valuation.py` defines `ValuationResult` — used only within that module
- `fraud_detection.py` defines `FraudSignal`, `FraudScore`, `GraphAnalysis` — used only within that module

**Verdict:** Excellent. Modules are fully decoupled at the data level.

### 2.3 External Coupling

**Finding: ZERO external dependencies.**

All modules use only Python standard library. No third-party imports (no numpy, scipy, networkx, etc.). This makes the package extremely portable.

**Verdict:** Excellent. No external coupling risks.

### 2.4 Common/Content Coupling

**Finding: NONE.**

- No shared global state or module-level mutable variables
- No module accesses another module's internals
- No monkey-patching or dynamic modification

**Verdict:** Excellent. No hidden coupling paths.

### 2.5 Coupling Summary Matrix

| Coupling Type | Rating | Notes |
|---------------|--------|-------|
| Import coupling | ★☆☆☆☆ (None) | No inter-module imports |
| Data coupling | ★☆☆☆☆ (None) | No shared data structures |
| External coupling | ★☆☆☆☆ (None) | Stdlib only |
| Common coupling | ★☆☆☆☆ (None) | No shared global state |
| Content coupling | ★☆☆☆☆ (None) | No internal access |
| **Overall** | **★☆☆☆☆ (Minimal)** | **Star topology, fully decoupled** |

---

## 3. Cohesion Analysis

### 3.1 Cohesion Ratings

| Module | Cohesion Level | Rating | Notes |
|--------|---------------|--------|-------|
| `dynamic_pricing.py` | Functional | ★★★★★ | Single purpose: pricing |
| `entity_resolution.py` | Functional | ★★★★☆ | One domain, but contains 3 distinct sub-algorithms |
| `evolution.py` | Functional | ★★★★☆ | GA engine + benchmark evaluation (related but separable) |
| `fraud_detection.py` | Functional | ★★★★☆ | Signal scoring + graph analysis (two sub-domains) |
| `matching.py` | Functional | ★★★★★ | Single purpose: matching |
| `portfolio_optimizer.py` | Functional | ★★★★★ | Single purpose: portfolio optimization |
| `search_ranking.py` | Functional | ★★★★★ | Single purpose: ranking |
| `valuation.py` | Functional | ★★★★★ | Multiple methods, all valuation-related |

### 3.2 Detailed Cohesion Review

#### `entity_resolution.py` — ★★★★☆ (High, but largest module)

Contains 4 distinct components:
1. **String normalization** (`_normalize`) — 3 lines
2. **Jaro-Winkler similarity** (`_jaro_winkler`) — 65 lines (substantial algorithm)
3. **Union-Find data structure** (`_UnionFind`) — 25 lines (reusable data structure)
4. **Entity resolution orchestration** (`EntityResolver`) — 80 lines

All components serve the single goal of entity resolution, so cohesion is high. However, the Jaro-Winkler algorithm and Union-Find are **reusable utilities** that could benefit from extraction.

#### `fraud_detection.py` — ★★★★☆ (High, but two sub-domains)

Contains 2 distinct sub-domains:
1. **Signal-based scoring** (`score()` method) — weighted average of fraud signals
2. **Graph-based ring detection** (`analyze_graph()` method) — cycle detection in relationship graphs

Both serve fraud detection, but the graph analysis is a substantially different algorithm (graph traversal vs. weighted scoring). The `GraphAnalysis` dataclass inherits from `FraudScore`, creating a minor structural coupling within the module.

#### `evolution.py` — ★★★★☆ (High, but mixed concerns)

Contains 2 distinct components:
1. **Benchmark evaluation** (`Benchmark` class) — target comparison
2. **Genetic algorithm** (`EvolutionEngine` class) — population evolution

The `Benchmark` class is a standalone evaluation tool that doesn't depend on `EvolutionEngine`. It could be extracted without affecting the GA engine.

---

## 4. Circular Dependency Check

**Finding: NO circular dependencies.**

The dependency graph is a DAG (Directed Acyclic Graph) with `__init__.py` as the sole hub. No module imports from another module, so circular dependencies are impossible.

```
Dependency direction: __init__.py → all modules (one-way only)
```

**Verdict:** Clean. No risk of circular import issues.

---

## 5. Module Split Recommendations

### 5.1 `entity_resolution.py` → Split into 3 modules

**Current:** 226 lines, 4 distinct components

**Proposed split:**

| New Module | Contents | Lines | Rationale |
|------------|----------|-------|-----------|
| `string_similarity.py` | `_normalize()`, `_jaro_winkler()` | ~68 | Reusable string similarity algorithm |
| `union_find.py` | `_UnionFind` class | ~25 | Reusable data structure |
| `entity_resolution.py` | `EntityResolver`, `EntityCluster`, `ResolvedEntity` | ~130 | Core resolution logic |

**Benefit:** Jaro-Winkler and Union-Find become reusable across the package (e.g., Jaro-Winkler could be used in `matching.py` for fuzzy buyer-seller name matching).

**Priority:** Medium. The module works correctly as-is; extraction is for reusability, not bug fixes.

### 5.2 `fraud_detection.py` → Split into 2 modules

**Current:** 172 lines, 2 sub-domains

**Proposed split:**

| New Module | Contents | Lines | Rationale |
|------------|----------|-------|-----------|
| `fraud_detection.py` | `FraudDetector.score()`, `FraudSignal`, `FraudScore` | ~100 | Signal-based scoring |
| `fraud_graph.py` | `FraudDetector.analyze_graph()`, `GraphAnalysis` | ~70 | Graph-based ring detection |

**Benefit:** Graph analysis is a distinct algorithm that could be reused for other graph-based detection (e.g., collusion detection in bidding).

**Priority:** Low. Both sub-domains are fraud-related and the module is manageable at 172 lines.

### 5.3 `evolution.py` → Split into 2 modules

**Current:** 194 lines, 2 components

**Proposed split:**

| New Module | Contents | Lines | Rationale |
|------------|----------|-------|-----------|
| `benchmark.py` | `Benchmark`, `EvaluationResult` | ~30 | Standalone evaluation tool |
| `evolution.py` | `EvolutionEngine`, `EvolutionResult` | ~160 | GA engine |

**Benefit:** `Benchmark` is a generic evaluation tool not specific to genetic algorithms.

**Priority:** Low. The coupling between Benchmark and EvolutionEngine is minimal.

---

## 6. Module Merge Recommendations

**Finding: NO modules should be merged.**

All modules are well-separated by domain:
- Pricing ≠ Valuation (different algorithms, different inputs)
- Matching ≠ Portfolio Optimization (different optimization problems)
- Fraud Detection ≠ Search Ranking (completely unrelated domains)
- Entity Resolution ≠ Evolution (different problem spaces)

Merging any modules would reduce cohesion and increase coupling. The current separation is correct.

---

## 7. `__init__.py` Analysis

### 7.1 Current Behavior

`__init__.py` eagerly imports and re-exports all 24 public symbols from all 8 modules. This means:

```python
from acquisition_platform import Buyer  # Loads ALL 8 modules
```

### 7.2 Potential Issue

**Eager loading** — importing any single symbol loads all modules. For a package this size (~1,140 LOC), the performance impact is negligible. However, as the package grows, this could become a concern.

### 7.3 Recommendation

**Lazy imports via `__getattr__`** (PEP 562):

```python
# __init__.py
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from acquisition_platform.matching import Buyer, Seller, Match, BuyerSellerMatcher
    # ... all other imports

__all__ = [...]  # same as current

def __getattr__(name: str):
    if name in ("Buyer", "Seller", "Match", "BuyerSellerMatcher"):
        from acquisition_platform import matching
        return getattr(matching, name)
    # ... etc for each module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
```

**Priority:** Low. Current approach is fine for the package's size. Revisit if the package grows beyond ~2,000 LOC.

---

## 8. Summary & Action Items

### Overall Assessment

| Metric | Rating | Notes |
|--------|--------|-------|
| **Coupling** | ★★★★★ (Minimal) | Zero inter-module imports; star topology |
| **Cohesion** | ★★★★☆ (High) | All modules are functionally cohesive |
| **Circular deps** | ★★★★★ (None) | Clean DAG |
| **Module count** | ★★★★★ (Appropriate) | 8 modules for 8 distinct domains |
| **Module size** | ★★★★☆ (Good) | Largest is 226 lines; acceptable |

### Action Items (Priority Order)

| # | Action | Priority | Effort | Impact |
|---|--------|----------|--------|--------|
| 1 | Extract `_jaro_winkler` and `_normalize` into `string_similarity.py` | Medium | Low | Enables reuse in matching |
| 2 | Extract `_UnionFind` into `union_find.py` | Medium | Low | Reusable data structure |
| 3 | Split `fraud_detection.py` into signal + graph modules | Low | Low | Better separation of concerns |
| 4 | Extract `Benchmark` from `evolution.py` | Low | Low | Generic evaluation tool |
| 5 | Add lazy imports to `__init__.py` | Low | Medium | Future-proofing |

### Non-Actions (Things NOT to Do)

- **Do NOT merge any modules** — current separation is correct
- **Do NOT add inter-module imports** — the decoupling is a strength
- **Do NOT add external dependencies** — stdlib-only is a feature
- **Do NOT over-engineer** — the package is clean and well-structured

---

## 9. Conclusion

The `acquisition_platform` package exhibits **excellent modular design**:

- **Coupling is minimal** — zero inter-module imports, no shared state, no external dependencies
- **Cohesion is high** — each module has a single, well-defined purpose
- **No circular dependencies** — clean star topology
- **Module sizes are appropriate** — 70-226 lines, all manageable

The only refactoring opportunities are **extractions for reusability** (Jaro-Winkler, Union-Find) and **separation of sub-domains** (fraud graph analysis, benchmark evaluation). These are low-priority improvements, not critical fixes.

**The package is well-architected and does not require significant refactoring.**
