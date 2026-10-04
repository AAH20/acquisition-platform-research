# Acquisition Platform Research & Optimization

Unified research and optimization engine for acquisition/auction platforms.

## Research Coverage

50 parallel research agents analyzed:
- **Acquisition.com** — Media-driven PE/advisory ($250M+ portfolio revenue)
- **Flippa** — Open marketplace (1.6M users, 400K weekly buyers)
- **Crunchbase** — SaaS + data licensing ($160M revenue, 85M+ profiles)
- **PitchBook** — Per-seat SaaS ($12K-40K/seat/yr, 6M+ companies)
- **Empire Flippers** — Curated marketplace ($604M+ volume, 91% rejection)
- **Quiet Light** — Boutique brokerage (100-150 deals/yr)
- **FE International** — M&A advisory (1,500+ deals, 94.1% success rate)
- **Acquire.com** — Direct marketplace ($500M+ volume, 500K+ users)

## NP-Hard Problems Identified

| Problem | Complexity | Module |
|---------|-----------|--------|
| Buyer-Seller Matching | GAP (NP-hard) | `matching.py` |
| Business Valuation | PPAD-hard | `valuation.py` |
| Fraud Detection | Dense Subgraph (NP-hard) | `fraud_detection.py` |
| Portfolio Optimization | MIQP (NP-hard) | `portfolio_optimizer.py` |
| Dynamic Pricing | Σ₂^p-complete | `dynamic_pricing.py` |
| Auction Design | #P-hard | `auction_design.py` |
| Entity Resolution | O(n²) pairwise | `entity_resolution.py` |
| Search Ranking | Submodular max (NP-hard) | `search_ranking.py` |
| Due Diligence Scheduling | Job Shop (NP-hard) | `due_diligence.py` |
| Cross-Border M&A | Multi-constraint | `cross_border.py` |

## Architecture

See `docs/ARCHITECTURE.md` for the unified architecture and `diagrams/` for mermaid diagrams.

## Quick Start

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## Module Structure

```
src/acquisition_platform/
├── __init__.py
├── matching.py           # Buyer-Seller Matching (GAP)
├── valuation.py          # Valuation Engine (PPAD-hard)
├── fraud_detection.py    # Fraud Detection (Dense Subgraph)
├── portfolio_optimizer.py # Portfolio Optimization (MIQP)
├── dynamic_pricing.py    # Dynamic Pricing (Stackelberg)
├── entity_resolution.py  # Entity Resolution (O(n²))
├── search_ranking.py     # Search Ranking (Submodular Max)
└── evolution.py          # Evolution & Evaluation Framework
```

## License

AGPL-3.0
