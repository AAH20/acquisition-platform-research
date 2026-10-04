# Code Wiki — Acquisition Platform Research & Optimization

> Auto-generated reference documentation for the acquisition-platform-research codebase.

## Overview

This project is a unified optimization engine for acquisition and auction platforms. It solves 8 NP-hard problems using modular, test-driven Python modules. The codebase is organized into 8 solver modules, 8 test files (62 tests), 50 research documents, and 4 architecture diagrams.

## Module Map

| Module | Purpose | NP-Hard Problem | Tests |
|--------|---------|-----------------|-------|
| [`matching.py`](modules/matching.md) | Buyer-seller matching | GAP (Generalized Assignment Problem) | 8/8 |
| [`valuation.py`](modules/valuation.md) | Business valuation | PPAD-hard (fair price) | 8/8 |
| [`fraud_detection.py`](modules/fraud_detection.md) | Fraud detection | Dense subgraph detection | 7/7 |
| [`portfolio_optimizer.py`](modules/portfolio_optimizer.md) | Portfolio optimization | MIQP (Mixed Integer Quadratic) | 7/7 |
| [`dynamic_pricing.py`](modules/dynamic_pricing.md) | Dynamic pricing | Σ₂^p-complete (Stackelberg) | 7/7 |
| [`entity_resolution.py`](modules/entity_resolution.md) | Entity resolution | O(n²) pairwise comparison | 8/8 |
| [`search_ranking.py`](modules/search_ranking.md) | Search ranking | Submodular maximization | 7/7 |
| [`evolution.py`](modules/evolution.md) | Evolution framework | Genetic algorithm | 10/10 |

## Documentation

- [Architecture](architecture.md) — System design, data flow, module interactions
- [Getting Started](getting-started.md) — Installation, quick start, common workflows
- [Class Diagram](diagrams/class-diagram.md) — Core type relationships
- [Sequence Diagrams](diagrams/sequences.md) — Key workflow traces

## Source

- **Repository:** https://github.com/AAH20/acquisition-platform-research
- **Language:** Python 3.10+
- **License:** AGPL-3.0
- **Test framework:** pytest
