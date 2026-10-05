# W3 — National Security Screening Module Implementation

**Status:** Complete — 10/10 module tests passing, module mypy-clean and ruff-clean.

## Deliverables

| File | Purpose |
|------|---------|
| `src/acquisition_platform/national_security.py` | National security screener implementation |
| `tests/test_national_security.py` | 10 TDD tests |

## What was built

### Dataclasses
- **`ScreeningItem`** — `technology_id`, `name`, `tid`, `foreign_investor`,
  `government_investor`, `clearance_required`.
- **`ScreeningResult`** — `items`, `cfius_risk`, `fdi_risk`,
  `clearance_required`, `filing_required`, `mitigation_plan`.

### `NationalSecurityScreener` methods
- `screen(...)` — build a `ScreeningItem`.
- `cfius_risk(items)` — mean per-item exposure (TID 0.4, foreign 0.3,
  government 0.2, clearance 0.1), normalized to [0, 1]; empty → 0.0.
- `fdi_risk(items, countries)` — foreign/government exposure × mean country
  political risk; domestic-only → 0.0.
- `is_tid_business(items)` — any TID flag.
- `clearance_requirements(items)` — sorted unique non-`none` levels.
- `mandatory_filing_required(items)` — true if TID + foreign investor, or any
  government investor.
- `generate_mitigation_plan(items)` — ordered mitigation steps (proxy board,
  national security agreement, passive-ownership limits, FCL program, CFIUS
  Form 1595 filing, ongoing monitoring); empty portfolio → `[]`.
- `political_risk(country, region)` — country base score + region modifier,
  clamped to [0, 1].
- `generate_screening_report(items)` — assembles a full `ScreeningResult`.

## Test results

**Module tests** (`tests/test_national_security.py`):
```
10 passed in 0.16s
```
Covers: CFIUS scoring, FDI assessment, TID detection, clearance requirements,
empty defaults, multi-country cross-border screening, mandatory filing,
mitigation plan, report generation, political risk.

**Full suite** (`python -m pytest tests/ -q --tb=no`):
```
1 failed, 1002 passed, 15 errors
```
- The **15 errors** are all a pre-existing collection failure in
  `tests/test_benchmarks.py` (bad import of `Jurisdiction` from
  `cross_border`) — reproduced on clean `git stash` at HEAD, unrelated to this
  module.
- The **1 failure** is `tests/test_type_safety.py::test_mypy_passes_on_source`,
  caused by pre-existing type errors in other wave-2 modules
  (`portfolio_optimization.py`, `tech_transfer.py`, `recommendation.py`).
  `national_security.py` itself passes `mypy` with no issues.
- All 1002 passing tests include the 10 new national-security tests.

## Quality gates
- `ruff check` on both new files: **All checks passed**.
- `mypy src/acquisition_platform/national_security.py`: **Success, no issues**.

## Notes / follow-ups
- `generate_screening_report` calls `fdi_risk(items, [])` — report-level FDI
  uses the default country risk because the method signature carries no
  country list. Callers wanting jurisdiction-aware FDI should call
  `fdi_risk` directly.
- Pre-existing `test_benchmarks.py` collection error and the three
  mypy-failing modules are outside this task's scope; flagging for the
  integration wave.
