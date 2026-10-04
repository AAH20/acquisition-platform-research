# Wave 2: Due Diligence Module Implementation

## Summary

Implemented `due_diligence.py` with TDD — 12 tests written first, then implementation.

## Files Created/Modified

- **Created**: `src/acquisition_platform/due_diligence.py` — full module
- **Created**: `tests/test_due_diligence.py` — 12 tests
- **Modified**: `src/acquisition_platform/__init__.py` — made cross-wave imports resilient via `importlib`

## Module Structure

### Dataclasses
- `DueDiligenceTask`: id, name, duration, expertise, dependencies
- `Reviewer`: id, name, expertise, availability
- `DueDiligenceSchedule`: assignments, makespan, reviewer_utilization

### DueDiligenceScheduler
- `schedule(tasks, reviewers)` — greedy list-scheduling with topological sort
- `add_task(task)` — adds task and invalidates cached schedule
- `reschedule()` — recomputes from current state
- `get_critical_path()` — longest dependency chain by duration

## Algorithm

1. Topological sort (Kahn's) for dependency ordering
2. For each task, find earliest-starting qualified reviewer
3. Track reviewer timelines and availability
4. Compute makespan and utilization

## Test Results

- `tests/test_due_diligence.py`: **12/12 passed**
- Full suite (excluding other waves' missing modules): **413/413 passed**
- mypy compliance: **passed**

## Issues Encountered

- `__init__.py` referenced modules from other waves (`auction_design`, `cross_border`, `recommendation`, `orchestrator`) that don't exist yet — fixed with `importlib`-based resilient imports
- 2 collection errors in `test_auction_design.py` and `test_cross_border.py` are pre-existing (other waves' work)
