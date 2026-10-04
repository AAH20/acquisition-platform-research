# Module: `matching.py`

## Purpose

Matches buyers to sellers in an acquisition marketplace using a greedy approximation to the GAP (Generalized Assignment Problem).

## Responsibilities

- Generate feasible buyer-seller pairs (budget + category constraints)
- Score pairs using price-ratio formula
- Greedily assign one-to-one matches
- Return matches sorted by score descending

## Key Files

- [`src/acquisition_platform/matching.py`](../../../src/acquisition_platform/matching.py) — 156 lines

## Public API

### `Buyer`

```python
@dataclass
class Buyer:
    id: str
    budget: float
    preferences: dict
```

### `Seller`

```python
@dataclass
class Seller:
    id: str
    asking_price: float
    attributes: dict
```

### `Match`

```python
@dataclass
class Match:
    buyer_id: str
    seller_id: str
    score: float
    confidence: float
```

### `BuyerSellerMatcher`

```python
class BuyerSellerMatcher:
    def match(self, buyers: list[Buyer], sellers: list[Seller]) -> list[Match]
```

## Algorithm

1. **Feasibility check** — Budget ≥ asking price AND category match
2. **Scoring** — `score = (1 - asking_price / budget) * 1.0`, clamped to [0, 1]
3. **Confidence** — `confidence = score * (1 - |asking_price - budget/2| / budget)`
4. **Greedy assignment** — Sort by score descending, assign each buyer/seller at most once

**Complexity:** O(n·m·log(n·m)) where n = buyers, m = sellers.

## Dependencies

- **Used by:** Portfolio optimizer, auction designer, recommendation system
- **Uses:** Nothing (standalone module)

## Tests

8 tests in [`tests/test_matching.py`](../../../tests/test_matching.py):
- Empty inputs, single match, budget constraint, competition, score bounds, category mismatch, confidence score
