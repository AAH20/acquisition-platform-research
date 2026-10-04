# Wave 2: cross_border Module Implementation

## Summary

Implemented `src/acquisition_platform/cross_border.py` with full TDD coverage.

## Files Created/Modified

- **Created:** `src/acquisition_platform/cross_border.py` — module implementation
- **Created:** `tests/test_cross_border.py` — 10 test cases

## Module Structure

### Dataclasses

| Class | Fields |
|-------|--------|
| `Jurisdiction` | `code`, `name`, `regulatory_body`, `tax_rate` |
| `RegulatoryFiling` | `jurisdiction`, `filing_type`, `deadline`, `dependencies` |
| `CrossBorderDeal` | `jurisdictions`, `deal_value`, `deal_type` |
| `CrossBorderResult` | `filings`, `total_tax`, `hedging_cost`, `integration_timeline`, `risk_score` |

### CrossBorderOptimizer Methods

| Method | Description |
|--------|-------------|
| `optimize(deal)` | Full optimization pipeline → `CrossBorderResult` |
| `coordinate_regulatory(deal)` | Generates ordered regulatory filings per jurisdiction |
| `optimize_tax(deal)` | Treaty-optimized tax (uses lowest jurisdiction rate) |
| `hedge_currency(deal)` | FX hedging cost scaling with jurisdiction pairs |
| `plan_integration(deal)` | Integration timeline in months |

## Test Results

```
tests/test_cross_border.py ..........  [100%]
10 passed
```

All 10 required tests pass:
- `test_regulatory_filing_sequence` — filings sorted by deadline, dependencies resolved
- `test_tax_optimization` — optimized tax < naive sum
- `test_currency_hedging` — cost scales with jurisdiction count
- `test_integration_planning` — timeline scales with jurisdiction count
- `test_multi_jurisdiction` — filings generated for all countries
- `test_fdi_screening` — FDI screening filings present
- `test_empty_jurisdictions` — empty plan for no jurisdictions
- `test_single_jurisdiction` — single country deal works
- `test_treaty_optimization` — tax ≤ max single rate
- `test_synergy_estimation` — risk score in [0, 1]

## Full Suite Status

- **422 passed**, 1 pre-existing failure (`test_mypy_passes_on_source` — missing `auction_design` module, unrelated)
- 1 pre-existing collection error (`test_auction_design.py` — same missing module)
- `cross_border.py` passes mypy cleanly

## Design Decisions

- **Tax optimization**: Uses lowest jurisdiction rate (treaty routing) — always ≤ max single rate, strictly < naive sum
- **Hedging cost**: Base per-jurisdiction fee + per-currency-pair fee (n*(n-1)/2 pairs)
- **Integration timeline**: 6 months base + 3 months per jurisdiction
- **Risk score**: Weighted combination of jurisdiction count (40%), avg tax rate (30%), deal value (30%), normalized to [0, 1]
- **Regulatory filings**: 5 filing types per jurisdiction with dependency chain: `tax_registration` / `fdi_screening` → `antitrust_notification` → `foreign_investment_review` → `securities_filing`
