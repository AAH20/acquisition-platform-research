# Wave 2 Fix: test_validation.py

## Summary

All 64 tests in `tests/test_validation.py` now pass (previously 52 failed, 12 passed).

## Changes Made

Added input validation to 8 source modules to match the test expectations:

### 1. `src/acquisition_platform/valuation.py`
- Added imports for `DivisionByZeroError`, `EmptyInputError`, `InvalidRangeError`
- `dcf_valuation`: Added checks for negative `discount_rate` and `terminal_growth`
- `comparable_valuation`: Added checks for negative `metric` and `multiple`
- `ensemble_valuation`: Added check for negative `revenue`
- `sde_valuation`: Added check for negative `sde`
- `arr_valuation`: Added check for negative `arr`

### 2. `src/acquisition_platform/matching.py`
- `match()`: Changed from returning `[]` for empty inputs to raising `EmptyInputError`
- Added validation for buyer budgets (must be > 0) and seller asking prices (must be > 0)

### 3. `src/acquisition_platform/fraud_detection.py`
- Added `InvalidRangeError` import
- `score()`: Added range check for signal values (must be in [0, 1])

### 4. `src/acquisition_platform/portfolio_optimizer.py`
- Added imports for `EmptyInputError`, `InvalidRangeError`
- `optimize()`: Changed from returning empty `Portfolio()` for empty assets to raising `EmptyInputError`
- Added range check for `risk_tolerance` (must be in [0, 1])
- Added validation for negative asset `cost` and `risk`

### 5. `src/acquisition_platform/dynamic_pricing.py`
- Added `InvalidRangeError` import
- `recommend_price()`: Added checks for negative `base_value`, `demand_level` out of [0,1], `competition_level` out of [0,1], and invalid `market_condition`

### 6. `src/acquisition_platform/entity_resolution.py`
- Added imports for `EmptyInputError`, `InvalidRangeError`
- `__init__()`: Added range check for `threshold` (must be in [0, 1])
- `resolve()`: Changed from returning `[]` for empty entities to raising `EmptyInputError`

### 7. `src/acquisition_platform/search_ranking.py`
- Added imports for `EmptyInputError`, `InvalidRangeError`
- `rank()`: Changed from returning `[]` for empty listings to raising `EmptyInputError`
- Added range check for listing `relevance` (must be in [0, 1])

### 8. `src/acquisition_platform/evolution.py`
- Added `InvalidRangeError` import
- `__init__()`: Added range check for `mutation_rate` (must be in [0, 1])

## Test Results

- `tests/test_validation.py`: **64 passed, 0 failed** (was 52 failed, 12 passed)
- Full suite: 767 passed, 57 failed (failures are in other test files, outside scope)
