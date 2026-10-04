# Wave 2: Data Model & Schema Gap Analysis

**Date:** 2026-10-04  
**Scope:** `src/acquisition_platform/` — all 8 modules + tests  
**Method:** Full source review of all `.py` files under `src/` and `tests/`

---

## 1. Are There Shared Data Models/Schemas?

**Finding: NO — zero shared data models exist.**

Each module defines its own dataclasses independently. There is no `models.py`, `schemas.py`, `types.py`, or any shared type definitions module. The `__init__.py` re-exports all dataclasses but does not define any shared base classes or protocols.

| Module | Dataclasses Defined | Shared? |
|--------|-------------------|---------|
| `search_ranking.py` | `Listing`, `RankedListing` | No |
| `matching.py` | `Buyer`, `Seller`, `Match` | No |
| `fraud_detection.py` | `FraudSignal`, `FraudScore`, `GraphAnalysis` | No |
| `dynamic_pricing.py` | `PriceRecommendation` | No |
| `valuation.py` | `ValuationResult` | No |
| `entity_resolution.py` | `ResolvedEntity`, `EntityCluster` | No |
| `portfolio_optimizer.py` | `Asset`, `Portfolio` | No |
| `evolution.py` | `EvaluationResult`, `Benchmark`, `EvolutionResult` | No |

**Impact:** Modules cannot safely exchange data. A `Listing` from search_ranking cannot be passed to the matching engine without manual field mapping. A `Seller` from matching cannot be evaluated by the valuation engine without transformation.

---

## 2. Is There a Common Listing/Business/Deal Data Structure?

**Finding: NO — the same real-world concept is represented 4+ different ways.**

The core domain entity — a business/listing/deal for sale — is represented differently in each module:

| Module | Class | Fields | Concept |
|--------|-------|--------|---------|
| `search_ranking.py` | `Listing` | `id, title, relevance, category` | A searchable listing |
| `matching.py` | `Seller` | `id, asking_price, attributes` | A seller's business |
| `portfolio_optimizer.py` | `Asset` | `id, cost, expected_return, risk, sector` | An acquisition target |
| `entity_resolution.py` | raw `dict` | `name, domain` (plus arbitrary keys) | An entity to resolve |
| `fraud_detection.py` | `FraudSignal` | `name, value` | A fraud signal (not a listing) |

**Key inconsistencies:**
- `Listing` has `title` but `Seller` has no title field
- `Seller` has `asking_price` but `Listing` has no price field
- `Asset` has `cost` and `expected_return` but `Seller` has only `asking_price`
- `Listing` has `category` but `Asset` has `sector` (same concept, different name)
- `entity_resolution.py` uses raw `dict` instead of a dataclass — no type safety at all
- `fraud_detection.py` operates on `FraudSignal` objects, not on listings — there is no way to associate a fraud score with a specific listing

**Impact:** To run a full pipeline (search → match → value → price → fraud-check), a developer must write custom transformation code between every pair of modules. There is no canonical "Listing" or "Deal" type that flows through the system.

---

## 3. Do Modules Use Inconsistent Data Formats?

**Finding: YES — significant format inconsistencies exist.**

### 3.1 Entity representation: dataclass vs. raw dict

| Module | Entity Format | Example |
|--------|--------------|---------|
| `search_ranking.py` | `@dataclass` | `Listing(id="l1", title="SaaS", relevance=0.9)` |
| `matching.py` | `@dataclass` | `Seller(id="s1", asking_price=80000, attributes={})` |
| `portfolio_optimizer.py` | `@dataclass` | `Asset(id="a1", cost=500000, expected_return=0.12)` |
| `entity_resolution.py` | **raw `dict`** | `{"id": "e1", "name": "Acme Corp", "domain": "acme.com"}` |
| `fraud_detection.py` | **raw `dict`** for graph | `{"nodes": ["a","b"], "edges": [("a","b")]}` |

### 3.2 Category/sector field naming

| Module | Field Name | Values |
|--------|-----------|--------|
| `search_ranking.py` | `category` | `"saas"`, `"ecommerce"` |
| `matching.py` | `category` (inside `preferences`/`attributes` dicts) | `"saas"`, `"ecommerce"` |
| `portfolio_optimizer.py` | `sector` | `"saas"`, `"ecommerce"` |

Same concept, two different field names (`category` vs `sector`).

### 3.3 Price/value field naming

| Module | Field Name | Type |
|--------|-----------|------|
| `matching.py` | `asking_price` | `float` |
| `portfolio_optimizer.py` | `cost` | `float` |
| `valuation.py` | `value` | `float` |
| `dynamic_pricing.py` | `recommended_price` | `float` |

Four different names for the same concept (price of a business).

### 3.4 ID field type

All modules use `str` for IDs — this is consistent. Good.

### 3.5 Preferences/attributes as untyped dicts

- `Buyer.preferences: dict` — no type parameter, no validation
- `Seller.attributes: dict` — no type parameter, no validation
- `user_preferences: dict | None` in `SearchRanker.rank()` — no type parameter

These dicts are accessed with `.get("category")` but there is no guarantee the key exists or the value is the expected type.

---

## 4. Is a Pydantic/Dataclass Schema Layer Needed?

**Finding: YES — strongly recommended.**

### Current state
- All dataclasses are plain `@dataclass` with zero validation
- No `__post_init__` validation anywhere
- No type constraints beyond Python type hints (which are not enforced at runtime)
- `entity_resolution.py` and `fraud_detection.py` use raw `dict` with no structure

### Specific validation gaps

| Class | Field | Missing Validation |
|-------|-------|--------------------|
| `Buyer` | `budget` | No check for negative values |
| `Seller` | `asking_price` | No check for negative values |
| `Listing` | `relevance` | No check for [0, 1] range |
| `Asset` | `risk` | No check for negative values |
| `Asset` | `expected_return` | No check for valid range |
| `FraudSignal` | `value` | No check for [0, 1] range |
| `FraudScore` | `score` | No check for [0, 1] range |
| `FraudScore` | `confidence` | No check for [0, 1] range |
| `ValuationResult` | `confidence` | No check for [0, 1] range |
| `PriceRecommendation` | `confidence` | No check for [0, 1] range |
| All classes | `id` | No check for non-empty string |

### Recommendation
Introduce a `schemas.py` module with Pydantic `BaseModel` classes (or enhanced dataclasses with `__post_init__` validation) that define:
1. A canonical `Listing` / `Business` / `Deal` type
2. Shared types for `Money`, `Confidence`, `RiskLevel`, `Category`
3. Validation at the boundary (input to each engine)

---

## 5. Is There Validation Logic That Should Be Centralized?

**Finding: YES — several validation/transformation patterns are duplicated across modules.**

### 5.1 Score clamping to [0, 1]

The expression `max(0.0, min(1.0, value))` appears in:

| Module | Location | Code |
|--------|----------|------|
| `matching.py` | `_compute_score()` | `return max(0.0, min(1.0, score))` |
| `matching.py` | `_compute_confidence()` | `return max(0.0, min(1.0, confidence))` |
| `fraud_detection.py` | `score()` | `score = max(0.0, min(1.0, score))` |
| `valuation.py` | `ensemble_valuation()` | `confidence = max(0.0, min(1.0, confidence))` |

**Recommendation:** Extract to a shared utility: `clamp(value: float, low: float = 0.0, high: float = 1.0) -> float`

### 5.2 Risk level classification

`fraud_detection.py` has:
```python
if score < 0.3:
    risk_level = "low"
elif score <= 0.7:
    risk_level = "medium"
else:
    risk_level = "high"
```

This pattern (threshold-based classification) could be needed in other modules (e.g., classifying valuation confidence, match quality). Currently it is hardcoded in one place.

### 5.3 Confidence calculation

Multiple modules compute confidence differently:
- `fraud_detection.py`: `confidence = 1.0 - (missing / TOTAL_EXPECTED_SIGNALS)`
- `matching.py`: `confidence = score * (1.0 - price_deviation)`
- `valuation.py`: `confidence = 1 - (high_estimate - low_estimate) / (2 * value)`
- `dynamic_pricing.py`: `confidence = 1 - abs(demand_level - competition_level)`

These are domain-specific, but the pattern of "confidence decreases with uncertainty" is shared. A shared `Confidence` value object with validation would help.

### 5.4 Empty input handling

Every module has its own pattern:
- `if not listings: return []`
- `if not buyers or not sellers: return []`
- `if not assets: return Portfolio()`
- `if not entities: return []`
- `if not signals: return FraudScore(...)`

This is fine as-is, but a shared `Result` type with an explicit "empty" state could standardize the API.

---

## 6. Is There Duplicate Data Transformation Code Across Modules?

**Finding: YES — significant duplication exists.**

### 6.1 The "business for sale" concept is transformed 4 times

To go from a search result to a portfolio asset, a developer must:

1. `Listing` (search_ranking) → manually extract fields → `Seller` (matching)
2. `Seller` (matching) → manually extract fields → `Asset` (portfolio_optimizer)
3. `Seller` (matching) → manually extract fields → `ValuationResult` (valuation)
4. `ValuationResult` (valuation) → manually extract fields → `PriceRecommendation` (dynamic_pricing)

Each transformation is ad-hoc, untested, and lives in application code (not in the library).

### 6.2 Score/confidence clamping duplication

As noted in §5.1, the clamp pattern appears 4 times. This is a pure function that should be defined once.

### 6.3 Category matching logic

- `matching.py` `_is_feasible()`: `buyer.preferences.get("category") != seller.attributes.get("category")`
- `search_ranking.py` `rank()`: `cat == preferred_category` (string comparison)
- `portfolio_optimizer.py` `optimize()`: `asset.sector not in selected_sectors` (set membership)

Three different ways to compare categories, none shared.

### 6.4 Graph analysis operates on raw dicts

`fraud_detection.py` `analyze_graph()` takes `dict[str, Any]` and manually extracts `nodes` and `edges`. There is no `Graph` dataclass. This means:
- No validation that `nodes` is a list of strings
- No validation that `edges` is a list of 2-tuples
- No reuse — if another module needs graph analysis, it must duplicate the adjacency-building code

### 6.5 Entity resolution uses raw dicts

`entity_resolution.py` operates on `list[dict]` with `.get("name", "")` and `.get("domain", "")`. There is no `Entity` dataclass. This means:
- No validation that required fields exist
- No type safety
- The `ResolvedEntity` and `EntityCluster` dataclasses wrap raw dicts, providing no real structure

---

## Summary of Gaps

| # | Gap | Severity | Effort to Fix |
|---|-----|----------|---------------|
| 1 | No shared data models/schemas module | **High** | Medium |
| 2 | No canonical Listing/Business/Deal type | **High** | Medium |
| 3 | Inconsistent field naming (category/sector, asking_price/cost/value) | **Medium** | Low |
| 4 | `entity_resolution.py` and `fraud_detection.py` use raw dicts | **Medium** | Low |
| 5 | No validation on any dataclass fields | **High** | Medium |
| 6 | Score clamping duplicated 4x | **Low** | Low |
| 7 | Risk level classification hardcoded | **Low** | Low |
| 8 | No shared Category/Sector enum | **Medium** | Low |
| 9 | No shared Money/Price value object | **Medium** | Low |
| 10 | No shared Confidence value object | **Medium** | Low |
| 11 | Ad-hoc transformations between module data types | **High** | High |
| 12 | No Graph dataclass for fraud detection | **Low** | Low |

---

## Recommended Schema Layer

```python
# src/acquisition_platform/schemas.py

from pydantic import BaseModel, Field, field_validator
from enum import Enum
from typing import Optional

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class Category(str, Enum):
    SAAS = "saas"
    ECOMMERCE = "ecommerce"
    # ... etc

class Money(BaseModel):
    amount: float = Field(..., gt=0)
    currency: str = "USD"

class Confidence(BaseModel):
    value: float = Field(..., ge=0.0, le=1.0)

class Listing(BaseModel):
    """Canonical listing/business/deal type used across all modules."""
    id: str = Field(..., min_length=1)
    title: str
    category: Category
    asking_price: Money
    revenue: Optional[float] = None
    risk: Optional[float] = Field(None, ge=0.0)
    # ... etc

class FraudAssessment(BaseModel):
    listing_id: str
    risk_level: RiskLevel
    score: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    explanations: list[str] = []

# Shared utilities
def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))

def classify_risk(score: float) -> RiskLevel:
    if score < 0.3:
        return RiskLevel.LOW
    elif score <= 0.7:
        return RiskLevel.MEDIUM
    return RiskLevel.HIGH
```

---

## Conclusion

The codebase has **no shared data model layer**. Each module operates in isolation with its own dataclasses, field names, and data formats. This is the single largest architectural gap in the project. Introducing a `schemas.py` module with Pydantic models would:

1. Eliminate the need for ad-hoc transformations between modules
2. Provide runtime validation at module boundaries
3. Make the domain model explicit and documented
4. Enable type-safe composition of engines into pipelines
5. Reduce duplication of clamping, classification, and confidence logic

**Priority: HIGH** — this gap blocks any attempt to compose modules into a unified pipeline.
