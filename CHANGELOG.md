# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-10-22

### Added
- Alpha evolution engine (`evolution.py`): `AlphaEvolver` — NSGA-II with multi-gene genomes, constraint domination, adaptive mutation, bounded Pareto archive, and seeded determinism
- Evaluation library (`evaluation.py`): classification, ranking (AUC/AP/MAP/NDCG), regression, calibration, bootstrap CI, paired p-value, Cohen's d
- Alpha lab (`alpha_lab.py`): labelled matching benchmark, policy evolution, held-out evaluation, latent-weight recovery
- Benchmark suite (`benchmark_suite.py`): warmup/repeats, baseline persistence, regression gate
- `MatchingPolicy`: injectable, evolvable scoring policy whose defaults preserve legacy behaviour
- Alpha registry (`alpha_registry.py`): append-only hash-chained event log with shadow → canary → production stages, gate-checked promotion, rollback, and tamper detection
- Cross-validation (`AlphaLab.cross_validate`): k-fold re-run of the whole procedure with per-fold seeds
- Specification-shift curve (`AlphaLab.robustness_curve`): held-out performance as the latent fair-value point moves
- Search comparators: equal-budget random search and a multimodal (Rastrigin) benchmark that separates search strategies
- Benchmark regression gate gains a measurement-noise floor for sub-5 ms cases
- 128 new tests since the v0.1 baseline (1342 total); mutation-tested invariants

### Changed
- `BuyerSellerMatcher` accepts an optional `MatchingPolicy`
- Measured held-out NDCG@5: 0.7667 → 1.0000 (p < 0.0001, weight-recovery L1 0.0653, train/test gap 0.0000)
- 5-fold CV: +0.2358 ± 0.0254, win rate 100%
- Rastrigin 5-D: optimum reached in 497 evaluations vs random search −25.34 at 2,381

## [Unreleased]

### Added
- CLI (`__main__.py`) — argparse-based command-line interface for all solvers
- REST API (`api.py`) — FastAPI endpoints for all optimization engines
- Batch processing (`batch.py`) — chunked and parallel execution
- Caching layer (`caching.py`) — TTL cache with LRU eviction
- Notification system (`notifications.py`) — extensible notification framework
- Data I/O (`data_io.py`) — JSON, CSV, YAML import/export
- Security module (`security.py`) — rate limiting, input sanitization, audit logging
- Observability (`observability.py`) — logging, metrics, health checks
- Orchestrator (`orchestrator.py`) — unified pipeline chaining all modules
- Reporting (`reporting.py`) — consolidated JSON/CSV/Markdown reports
- Schemas (`schemas.py`) — shared data types and utilities
- Serialization (`serialization.py`) — generic to_dict/from_dict mixin
- Configuration (`config.py`) — centralized parameter management
- Exceptions (`exceptions.py`) — custom exception hierarchy
- Auction design (`auction_design.py`) — Vickrey, GSP, English, Dutch formats
- Due diligence (`due_diligence.py`) — constraint-based task scheduling
- Cross-border optimization (`cross_border.py`) — multi-jurisdiction deal optimization
- Recommendation engine (`recommendation.py`) — hybrid collaborative + content-based filtering
- 22 new test files covering all new modules
- 646 new tests (total: 708)
- 19 new source modules (total: 27)
- 72 new research documents (total: 122)

### Changed
- All core modules refactored to use shared schemas, serialization, and observability
- Type hints added throughout (strict mypy compatible)
- Pydantic models for API request/response validation
- Configuration externalized from hardcoded constants

## [0.1.0] - 2026-10-04

### Added
- Initial release of acquisition-platform
- Buyer-seller matching engine with greedy algorithm
- Valuation engine with comparable analysis
- Fraud detection with ensemble scoring
- Portfolio optimizer with risk-adjusted returns
- Dynamic pricing engine with elasticity modeling
- Entity resolution with fuzzy matching
- Search ranking with BM25 algorithm
- Evolution engine for strategy optimization
- Full test coverage for all modules
- Documentation and architecture diagrams
