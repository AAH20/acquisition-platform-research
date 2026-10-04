# Acquisition Platform Research & Optimization — Unified Architecture

## Executive Summary

Synthesized from 50 parallel research agents covering Acquisition.com, Flippa, Crunchbase, PitchBook, Empire Flippers, Quiet Light, FE International, Acquire.com, and cross-platform dynamics.

**Market Landscape:**
| Platform | Model | Revenue | Key Metric |
|----------|-------|---------|------------|
| Acquisition.com | Media-driven PE/advisory | ~$85M self + $250M portfolio | 191 employees, 37 portfolio companies |
| Flippa | Open marketplace | ~$45-50M | 1.6M users, 400K weekly buyers, 85% cross-border |
| Crunchbase | SaaS + data licensing | ~$160M | 85M+ profiles, 39B+ signals |
| PitchBook | Per-seat SaaS | $12K-40K/seat/yr | 6M+ companies, 1,800+ researchers |
| Empire Flippers | Curated marketplace | Commission-only | $604M+ volume, 91% rejection rate |
| Quiet Light | Boutique brokerage | 10-15% commission | 100-150 deals/yr, 85-90% rejection |
| FE International | M&A advisory | 10-15% commission | 1,500+ deals, 94.1% success rate |
| Acquire.com | Direct marketplace | 6-8% closing fee | $500M+ volume, 500K+ users |

## Top Bottlenecks (Cross-Platform)

| # | Bottleneck | Severity | Platforms Affected | NP-Hard? |
|---|-----------|----------|-------------------|----------|
| 1 | Trust & Fraud | Critical | All | Yes (dense subgraph) |
| 2 | Valuation Accuracy (15-40% gap) | Critical | All | Yes (PPAD-hard) |
| 3 | Deal Timeline (3-6 months) | High | All | Yes (job shop scheduling) |
| 4 | NDA Harvesting | High | Acquire.com, Flippa | No |
| 5 | Cross-Border Complexity | High | All (85% cross-border) | Yes (multi-constraint) |
| 6 | Information Asymmetry | High | All | Yes (mechanism design) |
| 7 | Liquidity Mismatch | Medium | All | Yes (matching) |
| 8 | Entity Resolution | Medium | Crunchbase, PitchBook | Yes (O(n²)) |
| 9 | Search Ranking Quality | Medium | All | Yes (submodular max) |
| 10 | Portfolio Optimization | Medium | Acquirers | Yes (MIQP) |

## NP-Hard Problem Classification

| Problem | Complexity | Current Solution | Our Approach |
|---------|-----------|------------------|--------------|
| Buyer-Seller Matching | GAP (NP-hard) | GNN heuristics | Approximation + ML hybrid |
| Business Valuation | PPAD-hard | Ensemble ML | Multi-method ensemble |
| Fraud Detection | Dense Subgraph (NP-hard) | XGBoost/GNN | Graph + ML cascade |
| Portfolio Optimization | MIQP (NP-hard) | Markowitz/Black-Litterman | GA + SA-TS hybrid |
| Dynamic Pricing | Σ₂^p-complete | Price corridors | Stackelberg equilibrium |
| Auction Design | #P-hard | VCG/GSP | Approximate mechanism |
| Entity Resolution | O(n²) pairwise | Fellegi-Sunter | Cascade + active learning |
| Search Ranking | Submodular max | LambdaMART | LTR + diversity |
| Due Diligence Scheduling | Job Shop (NP-hard) | Manual | Constraint programming |
| Cross-Border M&A | Multi-constraint | Advisors | Multi-objective optimization |

## Unified Platform Architecture

See `diagrams/` for full mermaid diagrams:
- `system_architecture.mmd` — Overall system design
- `data_flow.mmd` — Data pipeline and flow
- `module_interactions.mmd` — Module dependency graph
- `evolution_framework.mmd` — Evolution and evaluation pipeline
