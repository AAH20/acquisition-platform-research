# Wave 3: IP/Patent Valuation Module — Implementation Summary

## What was done

Implemented the IP/patent valuation module with strict TDD (RED → GREEN).

## Files created/modified

| File | Action |
|------|--------|
| `tests/test_ip_valuation.py` | **Created** — 17 tests covering all required behaviors |
| `src/acquisition_platform/ip_valuation.py` | **Created** — full module implementation |
| `research/w3_ip_valuation_impl.md` | **Created** — this summary |

## Module structure

### Dataclasses
- **`Patent`** — `patent_id: str`, `title: str`, `status: str`, `citations: int`, `filed_date: str`, `granted_date: str`
- **`PatentPortfolio`** — `patents: list[Patent]`, `total_value: float`, `fto_score: float`, `thicket_detected: bool`

### IPValuator methods
| Method | Formula / Logic |
|--------|-----------------|
| `value_patent(patent)` | Relief-from-Royalty: `base_value(100k) × citation_impact × status_multiplier` |
| `value_portfolio(patents)` | Sums individual patent values; computes FTO score and thicket flag |
| `citation_impact(citations)` | `1.0 + min(citations, 100)/100` → range [1.0, 2.0] |
| `granted_vs_pending(status)` | granted=1.0, pending=0.5, expired=0.1 |
| `fto_score(patents, competitor_patents)` | Fraction of our patents with no title-similarity overlap with competitor patents |
| `thicket_detected(patents)` | True if any two patents share significant title keywords |
| `income_approach(revenue, margin, discount_rate)` | `(revenue × margin) / discount_rate` |
| `market_approach(comps_multiple, revenue)` | `comps_multiple × revenue` |

### Validation
- `ValidationError` on negative citations/revenue, unknown patent status
- `InvalidRangeError` on margin outside [0, 1]
- `DivisionByZeroError` on zero discount rate

## Test results

```
tests/test_ip_valuation.py  →  17 passed
Full suite (excl. pre-existing broken test_talent.py)  →  916 passed
mypy strict on src/  →  no issues
```

## Design decisions

- **Title similarity** for FTO and thicket detection uses stopword-filtered token overlap — simple, deterministic, no external dependencies.
- **Citation cap** at 100 prevents outlier patents from dominating portfolio value.
- Both dataclasses inherit `SerializableMixin` for `to_dict`/`from_dict` support, consistent with existing codebase patterns.
- Uses the project's custom exception hierarchy (`ValidationError`, `InvalidRangeError`, `DivisionByZeroError`) matching existing module conventions.

## Issues

- `tests/test_talent.py` has a pre-existing import error (`acquisition_platform.talent` module does not exist) — unrelated to this work.
- First full-suite run showed a flaky failure in `test_type_safety.py::test_mypy_passes_on_source` (likely resource contention under parallel benchmark load); second run confirmed the suite is fully green.
