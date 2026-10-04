# Wave 2: Type Safety & Mypy Compliance Report

**Date:** 2026-10-04  
**Scope:** `src/acquisition_platform/` (9 Python modules)  
**Mypy version:** Configured in `pyproject.toml` with `strict = true`, `warn_return_any = true`

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Total mypy errors | **9** |
| Files with errors | **3** of 9 |
| Functions/methods | 27 |
| Return annotation coverage | **100%** (27/27) |
| Parameter annotation coverage | **100%** (59/59) |
| Parameters using `Any` | 1 |
| Return statements leaking `Any` | 2 |

The codebase has excellent annotation coverage but fails mypy strict mode due to **unparameterized `dict` generics** and **`Any` leakage** from dict access patterns.

---

## 1. Mypy Error Breakdown

### 1.1 `type-arg` Errors (7 occurrences)

These occur when `dict` is used without type parameters (e.g., `dict` instead of `dict[str, Any]`).

| File | Line | Context |
|------|------|---------|
| `search_ranking.py` | 44 | `user_preferences: dict \| None = None` |
| `matching.py` | 31 | `preferences: dict` (dataclass field) |
| `matching.py` | 40 | `attributes: dict` (dataclass field) |
| `entity_resolution.py` | 33 | `entities: list[dict]` (dataclass field) |
| `entity_resolution.py` | 41 | `entities: list[dict]` (dataclass field) |
| `entity_resolution.py` | 157 | `def resolve(self, entities: list[dict]) -> ...` |
| `entity_resolution.py` | 218 | `def _canonical_name(entities: list[dict]) -> str` |

**Root cause:** Bare `dict` without `[key_type, value_type]` parameters. Under `strict = true`, mypy requires all generic types to be parameterized.

### 1.2 `no-any-return` Errors (2 occurrences)

| File | Line | Context |
|------|------|---------|
| `entity_resolution.py` | 225 | `return name` where `name` comes from `e.get("name", "")` |
| `entity_resolution.py` | 226 | `return names[0]` where `names` is a list of `Any` |

**Root cause:** `dict.get()` returns `Any` when the dict itself is unparameterized. The `names` list is `list[Any]`, so indexing it produces `Any`, which mypy flags as leaking from a function declared to return `str`.

---

## 2. Type Annotation Coverage Analysis

### 2.1 Coverage Summary

| Category | Count | Percentage |
|----------|-------|------------|
| Functions/methods with return annotation | 27/27 | 100% |
| Parameters with type annotation | 59/59 | 100% |
| Functions with `Any` in return type | 0/27 | 0% |
| Parameters typed as `Any` | 1/59 | 1.7% |

### 2.2 The Single `Any` Parameter

**File:** `fraud_detection.py`, line 100  
**Signature:** `def analyze_graph(self, graph: dict[str, Any]) -> GraphAnalysis:`

This is the only parameter using `Any`. While `dict[str, Any]` is parameterized, the value type is `Any`, which defeats much of the type safety benefit. The graph structure has a known schema:
- `nodes`: `list[str]`
- `edges`: `list[tuple[str, str]]`

**Recommendation:** Define a `TypedDict` or dataclass for the graph structure.

---

## 3. Detailed Findings by File

### 3.1 `entity_resolution.py` — 5 errors (highest severity)

**Issues:**
- Lines 33, 41: `list[dict]` in dataclass fields — should be `list[dict[str, Any]]` or better, a typed structure
- Line 157: `list[dict]` in method parameter
- Line 218: `list[dict]` in static method parameter
- Lines 225-226: `Any` leakage from `dict.get()` calls

**Impact:** The `EntityResolver.resolve()` method accepts `list[dict]` where each dict should have at least `name: str` and optionally `domain: str`. The lack of typing means:
- No IDE autocomplete for entity dict keys
- No static detection of misspelled keys
- `Any` propagates through `_canonical_name()` return

**Fix approach:**
```python
# Define a typed structure
class EntityDict(TypedDict, total=False):
    name: str
    domain: str

# Or use a dataclass
@dataclass
class Entity:
    name: str
    domain: str = ""
```

### 3.2 `matching.py` — 2 errors

**Issues:**
- Line 31: `Buyer.preferences: dict` — should be `dict[str, Any]` or more specific
- Line 40: `Seller.attributes: dict` — should be `dict[str, Any]` or more specific

**Impact:** The `preferences` dict is accessed via `.get("category")` and `attributes` via `.get("category")`. Without typing, there's no guarantee these keys exist or have the expected types.

**Fix approach:**
```python
@dataclass
class Buyer:
    id: str
    budget: float
    preferences: dict[str, Any]  # or a TypedDict with known keys

@dataclass  
class Seller:
    id: str
    asking_price: float
    attributes: dict[str, Any]  # or a TypedDict
```

### 3.3 `search_ranking.py` — 1 error

**Issue:**
- Line 44: `user_preferences: dict | None = None` — should be `dict[str, Any] | None`

**Impact:** Minor — the dict is only accessed via `.get("category")`, but the unparameterized dict still triggers mypy.

**Fix:**
```python
def rank(
    self,
    query: str,
    listings: list[Listing],
    user_preferences: dict[str, Any] | None = None,
) -> list[RankedListing]:
```

### 3.4 `fraud_detection.py` — 0 mypy errors, but 1 `Any` usage

**Observation:** This file passes mypy because `dict[str, Any]` is properly parameterized. However, the `Any` value type means the graph structure is not type-safe.

**Recommendation:** Replace with a typed structure:
```python
class GraphDict(TypedDict):
    nodes: list[str]
    edges: list[tuple[str, str]]
```

### 3.5 Clean files (0 errors, no `Any`)

- `dynamic_pricing.py` — fully typed, no issues
- `evolution.py` — fully typed, no issues
- `valuation.py` — fully typed, no issues
- `portfolio_optimizer.py` — fully typed, no issues
- `__init__.py` — re-exports only

---

## 4. Type Safety Issues Beyond Mypy

### 4.1 Runtime Type Assumptions Not Enforced

Several methods assume dict keys exist without validation:

| File | Line | Assumption |
|------|------|------------|
| `entity_resolution.py` | 178 | `e.get("name", "")` — assumes "name" key exists |
| `entity_resolution.py` | 193-194 | `entities[i].get("domain", "")` — assumes "domain" key exists |
| `matching.py` | 118-119 | `buyer.preferences.get("category")` — assumes "category" key exists |
| `search_ranking.py` | 62 | `user_preferences.get("category")` — assumes "category" key exists |

While `.get()` with defaults prevents `KeyError`, the defaults may mask data quality issues. Consider:
- Using `TypedDict` with `total=False` for optional keys
- adding runtime validation for critical fields
- using `assert` or explicit checks for required fields

### 4.2 `dict[str, Any]` as a Type Safety Anti-Pattern

The `fraud_detection.py` graph parameter uses `dict[str, Any]`, which:
- Passes mypy (it's parameterized)
- Provides zero type safety for the value type
- Is equivalent to saying "I don't know what's in here"

This is a common pattern that gives a false sense of type safety. A `TypedDict` or dataclass would be strictly better.

### 4.3 Missing `__all__` in Submodules

Only `__init__.py` defines `__all__`. Submodules don't, which means:
- `from acquisition_platform.entity_resolution import *` would export everything
- No explicit control over the public API surface

---

## 5. Recommendations (Prioritized)

### Priority 1: Fix Mypy Errors (9 errors → 0)

1. **Replace bare `dict` with `dict[str, Any]`** in:
   - `search_ranking.py:44`
   - `matching.py:31,40`
   - `entity_resolution.py:33,41,157,218`

2. **Fix `Any` leakage in `entity_resolution.py:225-226`**:
   - Option A: Cast the return value: `return str(name)`
   - Option B: Use a typed structure instead of `dict`
   - Option C: Add `assert isinstance(name, str)` before returning

### Priority 2: Eliminate `Any` Usage

1. **Replace `dict[str, Any]` in `fraud_detection.py:100`** with a `TypedDict`:
   ```python
   class GraphDict(TypedDict):
       nodes: list[str]
       edges: list[tuple[str, str]]
   ```

2. **Consider `TypedDict` for entity dicts** in `entity_resolution.py`:
   ```python
   class EntityDict(TypedDict, total=False):
       name: str
       domain: str
   ```

### Priority 3: Add Type Safety Infrastructure

1. **Add `py.typed` marker** to the package for PEP 561 compliance:
   ```
   src/acquisition_platform/py.typed
   ```

2. **Add mypy to CI** (if not already present) to prevent regressions

3. **Consider using `beartype` or `typeguard`** for runtime type validation of external inputs

---

## 6. Conclusion

The codebase has **excellent annotation coverage** (100% for both parameters and returns) but falls short of mypy strict compliance due to:

- **7 unparameterized `dict` generics** — mechanical fix, low effort
- **2 `Any` leakage points** — requires either casting or better typing
- **1 `dict[str, Any]` parameter** — passes mypy but provides no real type safety

All issues are straightforward to fix. The most impactful change would be introducing `TypedDict` or dataclass structures for the entity dicts and graph structures, which would eliminate both the mypy errors and the `Any` usage while improving IDE support and documentation.
