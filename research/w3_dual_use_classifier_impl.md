# Wave 3 — Dual-Use Technology Classifier Implementation

**Module:** `src/acquisition_platform/dual_use_classifier.py`
**Tests:** `tests/test_dual_use_classifier.py`
**Method:** TDD (RED → GREEN → REFACTOR)

## Deliverables

### Data classes
- `TechnologyProfile` — `name`, `category`, `military_apps: list[str]`,
  `commercial_apps: list[str]`, `trl: int`, `export_control: str`.
  All fields default so empty profiles are safe.
- `ClassificationResult` — `profile`, `dual_use_score: float`,
  `classification: str`, `regulatory_flags: list[str]`.

### `DualUseClassifier` methods
| Method | Behavior |
|---|---|
| `classify(profile)` | Returns `ClassificationResult` with score, label, flags. |
| `military_application_score(profile)` | 0.0 if no military apps; else `min(1, n/3)`, +0.2 for `defense` category, +0.2 for ITAR, capped at 1.0. |
| `commercial_application_score(profile)` | 0.0 if no commercial apps; else `min(1, n/3)`, +0.2 for `commercial` category, capped at 1.0. |
| `dual_use_score(profile)` | Geometric mean of military & commercial scores × TRL maturity factor. 0.0 if either domain is absent. |
| `classify_category(profile)` | `dual_use` / `military_only` / `commercial_only` / `neither`. |
| `regulatory_flags(profile)` | `ITAR_CONTROLLED`, `EAR_CONTROLLED`, `DUAL_USE_REVIEW_REQUIRED`, `ENHANCED_DUE_DILIGENCE`, `MILITARY_END_USE_SCREENING`. |
| `generate_classification_report(results)` | Dict: `total`, `average_dual_use_score`, `by_classification`, `dual_use_count`, `regulatory_flag_count`. Handles empty input. |

### Design notes
- **Geometric mean** for dual-use scoring: a technology must be strong in *both*
  domains to score highly; single-domain strength yields 0.0. This makes
  `dual_use` genuinely distinct from `military_only`/`commercial_only`.
- **TRL maturity factor** `0.5 + 0.5·(trl−1)/8` ∈ [0.5, 1.0]; out-of-range TRL clamped.
- **High/low threshold** at 0.5: `high_dual_use` if score ≥ 0.5, else `low_dual_use`.
- Integrated with `observability.get_logger` / `log_execution_time`, matching
  the conventions of `export_control.py` and `trl.py`.

## Verification

```
$ python -m pytest tests/test_dual_use_classifier.py -v
10 passed in 0.16s
```

All 10 required tests pass:
`test_classify_technology`, `test_military_application`,
`test_commercial_application`, `test_dual_use_score`, `test_empty_technology`,
`test_high_dual_use`, `test_low_dual_use`, `test_category_classification`,
`test_regulatory_flag`, `test_classification_report`.

```
$ python -m pytest tests/ -q --tb=no
1 failed, 1002 passed, 1 warning, 15 errors in 3.86s
```

- `mypy --strict` on the new module: **clean** (0 errors).
- `ruff check` on new module + test: **All checks passed**.

### Pre-existing failures (NOT caused by this change)
- `test_type_safety.py::test_mypy_passes_on_source` — 8 mypy errors in
  `portfolio_optimization.py`, `tech_transfer.py`, `recommendation.py`.
  The new module adds zero errors to the project-wide mypy run.
- 15 `test_benchmarks.py` errors — `fixture 'benchmark' not found`;
  `pytest-benchmark` plugin is not installed in `.venv-test`.
