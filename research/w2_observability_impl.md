# Wave 2: Logging & Observability Implementation

## Summary

Added comprehensive logging and observability infrastructure to the acquisition platform.

## What Was Done

### 1. Created `src/acquisition_platform/observability.py`

- **`get_logger(name)`** — Factory that returns configured `logging.Logger` instances. Auto-configures root logger with standard format on first call.
- **`log_execution_time`** — Decorator that logs function execution time in milliseconds. Supports custom logger, log level, and threshold (only log if exceeded).
- **`log_module_call`** — Decorator that logs CALL/RETURN/RAISED events for functions.
- **`MetricsCollector`** — Thread-unsafe metrics collection with:
  - Counters (`increment`, `decrement`, `get_counter`)
  - Gauges (`gauge`, `get_gauge`)
  - Timers (`timer`, `get_timer_stats`, `timeit` context manager)
  - `reset()` and `snapshot()` for full state export
- **`HealthCheck`** — Health check registry with `register`, `unregister`, `check_all`, and `is_healthy`.

### 2. Added Logging to All Modules

Added module-level logger and `@log_execution_time(logger)` decorator to public methods across 14 modules:

| Module | Methods Decorated |
|--------|------------------|
| valuation.py | 5 |
| matching.py | 1 |
| fraud_detection.py | 2 |
| portfolio_optimizer.py | 1 |
| dynamic_pricing.py | 1 |
| entity_resolution.py | 5 |
| search_ranking.py | 1 |
| evolution.py | 2 |
| auction_design.py | 5 |
| cross_border.py | 5 |
| due_diligence.py | 4 |
| recommendation.py | 5 |
| orchestrator.py | 8 |
| reporting.py | 14 |

**Total: 59 public methods decorated with execution time logging.**

### 3. Created `tests/test_observability.py`

41 tests covering:
- Logger creation (5 tests)
- Execution time decorator (7 tests)
- Module call decorator (3 tests)
- Metrics collection (14 tests)
- Health checks (10 tests)
- Integration tests (3 tests)

## Test Results

```
tests/test_observability.py: 41 passed
Full suite: 637 passed, 18 failed (all pre-existing from sibling subagents)
```

## Files Created/Modified

- **Created:** `src/acquisition_platform/observability.py`
- **Created:** `tests/test_observability.py`
- **Modified:** 14 source modules (added logger import + decorators)
