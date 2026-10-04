# Module: `valuation.py`

## Purpose

Multi-method business valuation engine supporting DCF, comparable company analysis, SDE, and ARR methods with ensemble confidence scoring.

## Responsibilities

- Compute DCF valuations with Gordon Growth terminal value
- Compute comparable company valuations
- Compute SDE (Seller's Discretionary Earnings) valuations
- Compute ARR (Annual Recurring Revenue) valuations
- Combine methods into ensemble with confidence scoring

## Key Files

- [`src/acquisition_platform/valuation.py`](../../../src/acquisition_platform/valuation.py) — 200 lines

## Public API

### `ValuationResult`

```python
@dataclass
class ValuationResult:
    value: float
    method: str
    confidence: float
    low_estimate: float
    high_estimate: float
```

### `ValuationEngine`

```python
class ValuationEngine:
    def dcf_valuation(self, free_cash_flow: float, growth_rate: float,
                      discount_rate: float, terminal_growth: float,
                      years: int) -> ValuationResult
    def comparable_valuation(self, metric: float, multiple: float) -> ValuationResult
    def ensemble_valuation(self, free_cash_flow: float, revenue: float,
                           growth_rate: float, discount_rate: float,
                           terminal_growth: float, revenue_multiple: float,
                           years: int) -> ValuationResult
    def sde_valuation(self, sde: float, multiple: float) -> ValuationResult
    def arr_valuation(self, arr: float, multiple: float) -> ValuationResult
```

## Methods

| Method | Formula | Confidence |
|--------|---------|------------|
| DCF | Σ FCF·(1+g)^t / (1+r)^t + TV / (1+r)^n | 0.70 |
| Comps | metric × multiple | 0.60 |
| Ensemble | average(DCF, Comps) | derived from agreement |
| SDE | sde × multiple | 0.60 |
| ARR | arr × multiple | 0.60 |

**Ensemble confidence:** `1 - (high - low) / (2 * value)`, clamped to [0, 1].

## Dependencies

- **Used by:** Portfolio optimizer, dynamic pricing, matching
- **Uses:** Nothing (standalone module)

## Tests

8 tests in [`tests/test_valuation.py`](../../../tests/test_valuation.py):
- DCF basic, growth/discount effects, comps, ensemble, confidence interval, SDE, ARR
