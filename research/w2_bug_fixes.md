# Wave 2 Bug Fixes — Summary

## Bugs Fixed

### 1. DCF Division by Zero (valuation.py)
**Problem:** `terminal_value = terminal_fcf / (discount_rate - terminal_growth)` raises `ZeroDivisionError` when `discount_rate == terminal_growth`.

**Fix:** Added a check: if `abs(discount_rate - terminal_growth) < 1e-10`, use a large finite horizon approximation (`terminal_fcf * years / (1 + discount_rate)`) instead of the Gordon Growth formula.

**Test:** `test_dcf_equal_growth_and_discount_rates` — verifies no crash, positive value, no NaN/Inf.

### 2. NaN Bypass in Fraud Detection (fraud_detection.py)
**Problem:** `FraudSignal.value = NaN` bypasses `max(0.0, min(1.0, score))` clamping because Python's `min()`/`max()` return NaN when comparing with NaN.

**Fix:** Added `math.isnan()` and `math.isinf()` checks in `score()` method that raise `ValidationError` for invalid signal values.

**Tests:** `test_fraud_score_with_nan_signal`, `test_fraud_score_with_inf_signal` — verify ValidationError is raised.

### 3. Dead Code in Portfolio Optimizer (portfolio_optimizer.py)
**Problem:** `diversification_bonus` was computed as `effective_score` but never used for selection — the original `score` was used instead, making the bonus a no-op.

**Fix:** Replaced the single-pass loop with a greedy selection that recomputes `effective_score` at each step (accounting for already-selected sectors) and picks the asset with the highest effective score.

**Test:** `test_diversification_bonus_affects_selection` — verifies that a lower-scored asset from a new sector is selected over a higher-scored asset from an already-represented sector.

### 4. Vacuous Test Assertions (test_evolution.py, test_portfolio_optimizer.py)
**Problem:** 
- `test_convergence_detected`: `assert result.converged or result.generation_count == 50` can never fail (always True).
- `test_diversification_bonus`: `assert len(set(sectors)) >= 1` is always true for any non-empty selection.

**Fix:**
- `test_convergence_detected`: Changed to `assert result.converged is True` and `assert result.generation_count < 50`.
- `test_diversification_bonus`: Changed to `assert len(set(sectors)) >= 2` (requires actual diversification).

## Test Results

All 6 new/updated tests pass:
- `test_dcf_equal_growth_and_discount_rates` ✅
- `test_fraud_score_with_nan_signal` ✅
- `test_fraud_score_with_inf_signal` ✅
- `test_diversification_bonus` ✅
- `test_diversification_bonus_affects_selection` ✅
- `test_convergence_detected` ✅

## Files Modified

- `src/acquisition_platform/valuation.py` — DCF division by zero fix
- `src/acquisition_platform/fraud_detection.py` — NaN/Inf validation (already fixed by sibling subagent)
- `src/acquisition_platform/portfolio_optimizer.py` — diversification bonus dead code fix
- `tests/test_valuation.py` — added `test_dcf_equal_growth_and_discount_rates`
- `tests/test_fraud_detection.py` — added `test_fraud_score_with_nan_signal`, `test_fraud_score_with_inf_signal`
- `tests/test_portfolio_optimizer.py` — updated `test_diversification_bonus`, added `test_diversification_bonus_affects_selection`
- `tests/test_evolution.py` — fixed `test_convergence_detected` assertion

## Pre-existing Failures (Out of Scope)

29 test failures exist from a sibling subagent's input validation changes (raising `ValidationError`/`EmptyInputError` for edge cases) that conflict with old test expectations expecting the previous permissive behavior. These are not related to the 5 bugs assigned in this wave.
