# Module: `dynamic_pricing.py`

## Purpose

Dynamic pricing engine based on Stackelberg game theory with demand, competition, and market condition multipliers.

## Responsibilities

- Compute price recommendations given market conditions
- Provide floor/ceiling bounds and equilibrium price
- Calculate confidence based on demand-competition alignment

## Key Files

- [`src/acquisition_platform/dynamic_pricing.py`](../../../src/acquisition_platform/dynamic_pricing.py) — 70 lines

## Public API

### `PriceRecommendation`

```python
@dataclass
class PriceRecommendation:
    recommended_price: float
    confidence: float
    floor_price: float
    ceiling_price: float
    equilibrium_price: float
```

### `PricingEngine`

```python
class PricingEngine:
    def recommend_price(self, base_value: float, demand_level: float,
                        competition_level: float,
                        market_condition: str) -> PriceRecommendation
```

## Multipliers

| Factor | Formula | Range |
|--------|---------|-------|
| Demand | `0.8 + demand_level * 0.4` | 0.8 — 1.2 |
| Competition | `1.2 - competition_level * 0.4` | 0.8 — 1.2 |
| Market (bull) | 1.15 | — |
| Market (bear) | 0.85 | — |
| Market (normal) | 1.0 | — |

**Recommended price:** `base_value × demand × competition × market`
**Equilibrium price:** `base_value × (demand + competition) / 2`
**Confidence:** `1 - |demand_level - competition_level|`

## Dependencies

- **Used by:** Evolution framework
- **Uses:** Valuation engine (for base value)

## Tests

7 tests in [`tests/test_dynamic_pricing.py`](../../../tests/test_dynamic_pricing.py):
- Basic recommendation, demand/competition effects, bull/bear market, bounds, equilibrium
