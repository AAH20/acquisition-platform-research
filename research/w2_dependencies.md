# Wave 2: Dependency & Import Analysis

**Project:** acquisition-platform-research  
**Package:** `src/acquisition_platform/`  
**Modules analyzed:** matching, valuation, fraud_detection, portfolio_optimizer, dynamic_pricing, entity_resolution, search_ranking, evolution  
**Date:** 2026-10-04

---

## 1. Full Import Map

### matching.py
| Import | Type |
|--------|------|
| `from __future__ import annotations` | stdlib |
| `from dataclasses import dataclass` | stdlib |

### valuation.py
| Import | Type |
|--------|------|
| `from dataclasses import dataclass` | stdlib |

### fraud_detection.py
| Import | Type |
|--------|------|
| `from __future__ import annotations` | stdlib |
| `from dataclasses import dataclass, field` | stdlib |
| `from typing import Any` | stdlib |

### portfolio_optimizer.py
| Import | Type |
|--------|------|
| `from __future__ import annotations` | stdlib |
| `from dataclasses import dataclass, field` | stdlib |

### dynamic_pricing.py
| Import | Type |
|--------|------|
| `from dataclasses import dataclass` | stdlib |

### entity_resolution.py
| Import | Type |
|--------|------|
| `from __future__ import annotations` | stdlib |
| `import re` | stdlib |
| `from collections import Counter, defaultdict` | stdlib |
| `from dataclasses import dataclass` | stdlib |

### search_ranking.py
| Import | Type |
|--------|------|
| `from dataclasses import dataclass` | stdlib |

### evolution.py
| Import | Type |
|--------|------|
| `from __future__ import annotations` | stdlib |
| `import random` | stdlib |
| `import statistics` | stdlib |
| `from dataclasses import dataclass` | stdlib |
| `from typing import Callable, Tuple` | stdlib |

### Key Observations
- **All imports are stdlib only** — zero third-party dependencies.
- **Zero cross-module imports** — no module imports from any sibling module in the package.
- The package is fully self-contained with no internal coupling.

---

## 2. Circular Import Detection

**Result: No circular imports detected.**

The dependency graph is a flat set of 8 isolated nodes with no edges between them. Each module is completely independent.

---

## 3. Unused Imports

| Module | Unused Import | Line | Notes |
|--------|--------------|------|-------|
| matching.py | `from __future__ import annotations` | 20 | Not needed — no forward references used |
| fraud_detection.py | `from __future__ import annotations` | 7 | Not needed — no forward references used |
| portfolio_optimizer.py | `from __future__ import annotations` | 9 | Not needed — no forward references used |
| entity_resolution.py | `from __future__ import annotations` | 22 | Not needed — no forward references used |
| evolution.py | `from __future__ import annotations` | 12 | Not needed — no forward references used |

**Summary:** 5 of 8 modules have an unused `from __future__ import annotations` import. This is a minor code hygiene issue — the import is harmless but unnecessary since none of these modules use forward reference annotations (string annotations for types not yet defined).

**No other unused imports found.** All other imports (dataclass, field, Any, re, Counter, defaultdict, random, statistics, Callable, Tuple) are actively used.

---

## 4. `__init__.py` Exports vs Actual Module Contents

### Exports that match module contents: 6 of 8 modules ✓
- matching.py, valuation.py, portfolio_optimizer.py, dynamic_pricing.py, search_ranking.py, evolution.py

### Discrepancies found:

#### fraud_detection.py
| Name | Status |
|------|--------|
| `GraphAnalysis` | Defined in module (line 32) but **NOT exported** in `__init__.py` |

**Impact:** `GraphAnalysis` is a public class (no `_` prefix) that is not re-exported. External consumers must use `from acquisition_platform.fraud_detection import GraphAnalysis` instead of the shorter `from acquisition_platform import GraphAnalysis`. This is an inconsistency — all other public classes are exported.

#### entity_resolution.py
| Name | Status |
|------|--------|
| `_normalize` | Private function (line 45), 2 references — correctly NOT exported |
| `_jaro_winkler` | Private function (line 50), 2 references — correctly NOT exported |
| `_UnionFind` | Private class (line 117), 2 references — correctly NOT exported |

**Impact:** None — these are private (underscore-prefixed) and correctly omitted from `__init__.py`.

---

## 5. Non-Existent Module Imports

**Result: No imports from non-existent modules.**

All imports resolve to either:
- Python standard library modules (`__future__`, `dataclasses`, `typing`, `re`, `collections`, `random`, `statistics`)
- The package's own submodules (via `__init__.py` re-exports)

No broken or dangling imports detected.

---

## 6. Cross-Module Import Graph

```
matching          → (no sibling imports)
valuation         → (no sibling imports)
fraud_detection   → (no sibling imports)
portfolio_optimizer → (no sibling imports)
dynamic_pricing   → (no sibling imports)
entity_resolution  → (no sibling imports)
search_ranking    → (no sibling imports)
evolution         → (no sibling imports)
```

**The package has zero internal coupling.** Every module is fully independent.

---

## 7. External Importers

The package is imported by 8 test files:

| Test File | Imports From |
|-----------|-------------|
| tests/test_matching.py | acquisition_platform.matching |
| tests/test_valuation.py | acquisition_platform.valuation |
| tests/test_fraud_detection.py | acquisition_platform.fraud_detection |
| tests/test_portfolio_optimizer.py | acquisition_platform.portfolio_optimizer |
| tests/test_dynamic_pricing.py | acquisition_platform.dynamic_pricing |
| tests/test_entity_resolution.py | acquisition_platform.entity_resolution |
| tests/test_search_ranking.py | acquisition_platform.search_ranking |
| tests/test_evolution.py | acquisition_platform.evolution |

All test files import directly from submodules (not from the package `__init__`), so the `__init__.py` export gap for `GraphAnalysis` does not affect tests.

---

## 8. Summary & Recommendations

### Health Score: ✅ Good

| Metric | Status |
|--------|--------|
| Circular imports | ✅ None |
| Non-existent imports | ✅ None |
| Cross-module coupling | ✅ Zero (fully decoupled) |
| Third-party dependencies | ✅ Zero (stdlib only) |
| `__init__.py` export completeness | ⚠️ 1 missing (`GraphAnalysis`) |
| Unused imports | ⚠️ 5 (`__future__` in 5 modules) |

### Recommended Actions

1. **Export `GraphAnalysis` from `__init__.py`** — Add it to the import list and `__all__` in `__init__.py` for consistency with other public classes.

2. **Remove unused `from __future__ import annotations`** — Clean up the 5 unnecessary imports in matching, fraud_detection, portfolio_optimizer, entity_resolution, and evolution. These modules don't use forward references.

3. **No architectural changes needed** — The flat, zero-coupling design is clean and intentional. Each module is a self-contained algorithm implementation.
