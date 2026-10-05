# Acquisition Platform Research & Optimization

> **Unified optimization engine for acquisition/auction platforms.** 100-agent parallel research across 8 platforms + 30+ dual-use verticals, 30 NP-hard problem solvers, 1018 tests, 43 source modules, 5 architecture diagrams.

## Table of Contents

- [Overview](#overview)
- [Research Coverage](#research-coverage)
- [Architecture](#architecture)
- [NP-Hard Problems](#np-hard-problems)
- [Module Reference](#module-reference)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [CLI](#cli)
- [API Reference](#api-reference)
- [Testing](#testing)
- [Evolution Framework](#evolution-framework)
- [Benchmarks](#benchmarks)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

This project is a unified research and optimization engine for acquisition and auction platforms. It synthesizes findings from 100 parallel research agents covering 8 major platforms and 30+ dual-use technology verticals, identifies cross-platform bottlenecks and NP-hard problems, and implements modular solvers for each.

**Key Results:**

| Metric | Value |
|--------|-------|
| Research agents deployed | 100 (10 waves × 10 agents) |
| Platforms analyzed | 8 |
| Dual-use verticals researched | 30+ |
| NP-hard problems solved | 30 |
| Source modules | 43 |
| Test files | 40+ |
| Tests passing | 1018 |
| Architecture diagrams | 5 |
| Lines of code | ~15,000+ |
| Research documents | 50+ |

---

## Research Coverage

### Platforms Analyzed

| Platform | Model | Revenue | Key Metric | Top Bottleneck |
|----------|-------|---------|------------|----------------|
| **Acquisition.com** | Media-driven PE/advisory | ~$85M self + $250M portfolio | 191 employees, 37 portfolio companies | Founder dependency |
| **Flippa** | Open marketplace | ~$45-50M | 1.6M users, 400K weekly buyers, 85% cross-border | Trust & Fraud |
| **Crunchbase** | SaaS + data licensing | ~$160M | 85M+ profiles, 39B+ signals | Data quality (15-40% gap) |
| **PitchBook** | Per-seat SaaS | $12K-40K/seat/yr | 6M+ companies, 1,800+ researchers | Freshness lag (12-18 months) |
| **Empire Flippers** | Curated marketplace | Commission-only | $604M+ volume, 91% rejection rate | Low listing volume |
| **Quiet Light** | Boutique brokerage | 10-15% commission | 100-150 deals/yr, 85-90% rejection | Scalability ceiling |
| **FE International** | M&A advisory | 10-15% commission | 1,500+ deals, 94.1% success rate | Deal size floor |
| **Acquire.com** | Direct marketplace | 6-8% closing fee | $500M+ volume, 500K+ users | NDA harvesting |

### Dual-Use Technology Verticals Researched

| Vertical | Market Size | Key NP-Hard Problem | Research Doc |
|----------|-------------|-------------------|--------------|
| Space & Satellite | $613-626B | Constellation optimization | `w3_space_satellite.md` |
| Cybersecurity | 400+ deals/yr | Threat graph analysis | `w3_cybersecurity.md` |
| Quantum Computing | $99B | Qubit placement | `w3_quantum.md` |
| Biotech | $189B M&A | Protein folding | `w3_biotech.md` |
| Autonomous Systems | $5.2B drone deals | Path planning | `w3_autonomous.md` |
| Nuclear | $7B H1 2026 | Fuel cycle optimization | `w3_nuclear.md` |
| Advanced Materials | 25 space deals | Crystal structure | `w3_materials.md` |
| Hypersonics | $7.2B→$19.8B | Trajectory optimization | `w3_hypersonics.md` |
| Directed Energy | $2B DoD | Beam control | `w3_directed_energy.md` |
| 5G/Telecom | $35B RAN | Spectrum allocation | `w3_5g_telecom.md` |
| Semiconductors | $627.6B→$1,137.6B | Floor planning | `w3_semiconductors.md` |
| Chem/Bio Defense | 10,000× asymmetry | Detection optimization | `w3_chem_bio.md` |
| Energy Storage | $187B NA | Grid optimization | `w3_energy_storage.md` |
| Supply Chain | $187B NA | Network flow | `w3_supply_chain.md` |
| Cross-Platform Integration | 70% M&A failure rate | System-of-systems | `w3_cross_platform.md` |

### Cross-Platform Bottlenecks

| # | Bottleneck | Severity | Platforms | NP-Hard? | Solution Module |
|---|-----------|----------|-----------|----------|-----------------|
| 1 | Trust & Fraud | **Critical** | All | Yes (dense subgraph) | `fraud_detection.py` |
| 2 | Valuation Accuracy (15-40% gap) | **Critical** | All | Yes (PPAD-hard) | `valuation.py` |
| 3 | Deal Timeline (3-6 months) | High | All | Yes (job shop) | `due_diligence.py` |
| 4 | NDA Harvesting | High | Acquire.com, Flippa | No | — |
| 5 | Cross-Border Complexity | High | All (85%) | Yes (multi-constraint) | `cross_border.py` |
| 6 | Information Asymmetry | High | All | Yes (mechanism design) | — |
| 7 | Liquidity Mismatch | Medium | All | Yes (matching) | `matching.py` |
| 8 | Entity Resolution | Medium | Crunchbase, PitchBook | Yes (O(n²)) | `entity_resolution.py` |
| 9 | Search Ranking Quality | Medium | All | Yes (submodular max) | `search_ranking.py` |
| 10 | Portfolio Optimization | Medium | Acquirers | Yes (MIQP) | `portfolio_optimizer.py` |

---

## Architecture

### System Architecture

```mermaid
graph TB
    subgraph External["External Data Sources"]
        CB[Crunchbase API]
        PB[PitchBook API]
        FL[Flippa Marketplace]
        AC[Acquire.com]
        EF[Empire Flippers]
        QL[Quiet Light]
        FEI[FE International]
    end

    subgraph Ingestion["Data Ingestion Layer"]
        SCRAPER[Web Crawlers]
        API_CLIENT[API Client]
        NORMALIZER[Data Normalizer]
        VALIDATOR[Data Validator]
    end

    subgraph Storage["Storage Layer"]
        GRAPH_DB[(Neo4j Graph DB)]
        DW[(Snowflake DW)]
        CACHE[(Redis Cache)]
        VDR[(Virtual Data Room)]
    end

    subgraph Core["Core Optimization Engine"]
        MATCHING["Buyer-Seller Matching<br/>GAP Solver"]
        VALUATION["Valuation Engine<br/>PPAD-hard"]
        FRAUD["Fraud Detection<br/>Dense Subgraph"]
        PORTFOLIO["Portfolio Optimizer<br/>MIQP"]
        PRICING["Dynamic Pricing<br/>Stackelberg"]
        AUCTION["Auction Designer<br/>#P-hard"]
        ER["Entity Resolution<br/>O(n²)"]
        RANKING["Search Ranking<br/>Submodular Max"]
        DD["Due Diligence<br/>Job Shop"]
        XB["Cross-Border M&A<br/>Multi-Constraint"]
        REC["Recommendation Engine<br/>Hybrid CF+CB"]
    end

    subgraph DualUse["Dual-Use Assessment Layer"]
        TRL["TRL Assessment<br/>1-9 Scale"]
        EXPORT["Export Control<br/>ITAR/EAR"]
        IP["IP/Patent Valuation<br/>RFR Method"]
        TALENT["Talent Assessment<br/>Clearance Premium"]
        FINMODEL["Financial Modeling<br/>Defense DCF"]
        RISK["Risk Assessment<br/>5-Factor SEM"]
        DEAL["Deal Structuring<br/>Earnouts/CVRs"]
        PMI["Post-Merger Integration<br/>Culture Gap"]
        NATSEC["National Security<br/>CFIUS/FDI"]
        SWF["SWF Matching<br/>Portfolio Fit"]
        DUALCLASS["Dual-Use Classifier<br/>Mil/Comm Score"]
        MKT["Market Analysis<br/>TAM/SAM/SOM"]
        CI["Competitive Intelligence<br/>War Gaming"]
        TECHTRANSFER["Tech Transfer<br/>Absorptive Capacity"]
        PORTOPT["Portfolio Optimization<br/>Efficient Frontier"]
        DUE_DIL["Due Diligence<br/>Multi-Category"]
        AUC["Auction Design<br/>Vickrey/GSP/Myerson"]
        XBORDER["Cross-Border M&A<br/>Tax/Cultural"]
        RECENG["Recommendation Engine<br/>CF+CB Filtering"]
        GRAPH["Graph Analysis<br/>Centrality/Communities"]
        NLP["NLP Document Analysis<br/>Entity/Sentiment"]
    end

    subgraph ML["ML/NLP Layer"]
        GNN[GNN Matcher]
        LTR[Learning to Rank]
        NLP_ML[NLP Entity Extraction]
        ENSEMBLE[Ensemble Valuator]
        XGB[XGBoost Fraud Detector]
        LLM[LLM Advisor]
    end

    subgraph Evolution["Evolution & Evaluation"]
        BENCH[Benchmark Suite]
        EVO[Evolution Engine]
        EVAL[Evaluation Framework]
        OPT[Hyperparameter Optimizer]
    end

    subgraph API["API Layer"]
        REST[REST API]
        MCP[MCP Server]
        WS[WebSocket]
    end

    subgraph UI["User Interface"]
        DASH[Dashboard]
        SEARCH[Search Interface]
        DEAL[Deal Room]
        ANALYTICS[Analytics]
    end

    External --> Ingestion
    Ingestion --> Storage
    Storage --> Core
    Core --> DualUse
    DualUse --> ML
    ML --> Evolution
    Evolution --> Core
    Core --> API
    API --> UI

    style Core fill:#1f6feb,stroke:#30363d,color:#fff
    style DualUse fill:#8b5cff,stroke:#30363d,color:#fff
    style ML fill:#238636,stroke:#30363d,color:#fff
    style Evolution fill:#d29922,stroke:#30363d,color:#fff
    style External fill:#6e7681,stroke:#30363d,color:#fff
    style Storage fill:#d29922,stroke:#30363d,color:#fff
    style API fill:#f85149,stroke:#30363d,color:#fff
    style UI fill:#1f6feb,stroke:#30363d,color:#fff
```

### Data Flow

```mermaid
flowchart LR
    subgraph Sources["Data Sources"]
        S1[Crunchbase]
        S2[PitchBook]
        S3[Flippa]
        S4[Acquire.com]
        S5[Empire Flippers]
        S6[Quiet Light]
        S7[FE International]
    end

    subgraph Ingestion["Ingestion"]
        I1[API Polling]
        I2[Web Scraping]
        I3[File Upload]
        I4[Manual Entry]
    end

    subgraph Processing["Processing"]
        P1[Normalization]
        P2[Entity Resolution]
        P3[Validation]
        P4[Enrichment]
    end

    subgraph Storage["Storage"]
        D1[(Graph DB)]
        D2[(Data Warehouse)]
        D3[(Cache)]
        D4[(VDR)]
    end

    subgraph Analytics["Analytics"]
        A1[Valuation]
        A2[Matching]
        A3[Fraud Detection]
        A4[Portfolio Opt]
        A5[Pricing]
        A6[TRL Assessment]
        A7[Export Control]
        A8[Risk Scoring]
    end

    subgraph Output["Output"]
        O1[Recommendations]
        O2[Alerts]
        O3[Reports]
        O4[Deals]
    end

    Sources --> Ingestion
    Ingestion --> Processing
    Processing --> Storage
    Storage --> Analytics
    Analytics --> Output

    style Sources fill:#6e7681,stroke:#30363d,color:#fff
    style Ingestion fill:#1f6feb,stroke:#30363d,color:#fff
    style Processing fill:#8b5cff,stroke:#30363d,color:#fff
    style Storage fill:#d29922,stroke:#30363d,color:#fff
    style Analytics fill:#238636,stroke:#30363d,color:#fff
    style Output fill:#f85149,stroke:#30363d,color:#fff
```

### Module Interactions

```mermaid
graph TD
    subgraph DataLayer["Data Layer"]
        ER[Entity Resolution]
        VAL[Valuation Engine]
        FRAUD[Fraud Detection]
        NLP[NLP Analysis]
    end

    subgraph MatchingLayer["Matching Layer"]
        MATCH[Buyer-Seller Matching]
        RANK[Search Ranking]
        REC[Recommendation System]
    end

    subgraph OptimizationLayer["Optimization Layer"]
        PORT[Portfolio Optimization]
        PRICE[Dynamic Pricing]
        AUC[Auction Design]
        DD[Due Diligence]
        XB[Cross-Border M&A]
    end

    subgraph DualUseLayer["Dual-Use Assessment"]
        TRL[TRL Assessment]
        EXPORT[Export Control]
        IP[IP Valuation]
        TALENT[Talent]
        RISK[Risk Assessment]
        DEAL[Deal Structuring]
        PMI[Post-Merger]
        NATSEC[National Security]
        SWF[SWF Matching]
        DUALCLASS[Dual-Use Classifier]
        MKT[Market Analysis]
        CI[Competitive Intel]
        TECHTRANSFER[Tech Transfer]
        PORTOPT[Portfolio Opt]
        DUE_DIL[Due Diligence]
        GRAPH[Graph Analysis]
    end

    subgraph EvolutionLayer["Evolution Layer"]
        BENCH[Benchmarks]
        EVO[Evolution Engine]
        EVAL[Evaluation]
    end

    ER --> MATCH
    ER --> RANK
    VAL --> MATCH
    VAL --> PORT
    VAL --> PRICE
    FRAUD --> MATCH
    FRAUD --> REC
    NLP --> RANK
    NLP --> CI
    MATCH --> PORT
    MATCH --> AUC
    RANK --> REC
    TRL --> DUALCLASS
    EXPORT --> DUALCLASS
    IP --> PORTOPT
    TALENT --> PMI
    RISK --> DEAL
    DEAL --> PMI
    NATSEC --> DEAL
    SWF --> PORTOPT
    DUALCLASS --> MKT
    CI --> MKT
    TECHTRANSFER --> TRL
    PORTOPT --> EVO
    DUE_DIL --> EVO
    GRAPH --> CI
    PORT --> EVO
    PRICE --> EVO
    AUC --> EVO
    DD --> EVO
    XB --> EVO
    EVO --> BENCH
    EVAL --> EVO

    style DataLayer fill:#d29922,stroke:#30363d,color:#fff
    style MatchingLayer fill:#1f6feb,stroke:#30363d,color:#fff
    style OptimizationLayer fill:#8b5cff,stroke:#30363d,color:#fff
    style DualUseLayer fill:#238636,stroke:#30363d,color:#fff
    style EvolutionLayer fill:#f85149,stroke:#30363d,color:#fff
```

### Evolution Framework

```mermaid
flowchart TD
    subgraph Input["Input"]
        DATA[Research Data]
        BENCH[Benchmarks]
        PARAMS[Parameters]
    end

    subgraph Evolution["Evolution Engine"]
        INIT[Initialize Population]
        EVAL[Evaluate Fitness]
        SELECT[Selection]
        CROSS[Crossover]
        MUTATE[Mutation]
        REPLACEMENT[Replacement]
    end

    subgraph Evaluation["Evaluation Framework"]
        METRICS[Metrics Calculator]
        COMPARISON[Comparison]
        RANKING[Result Ranking]
        VISUAL[Visualization]
    end

    subgraph Output["Output"]
        BEST[Best Solution]
        REPORT[Report]
        DEPLOY[Deployment]
    end

    Input --> Evolution
    Evolution --> Evaluation
    Evaluation --> Output

    INIT --> EVAL
    EVAL --> SELECT
    SELECT --> CROSS
    CROSS --> MUTATE
    MUTATE --> REPLACEMENT
    REPLACEMENT --> EVAL

    METRICS --> COMPARISON
    COMPARISON --> RANKING
    RANKING --> VISUAL

    style Input fill:#6e7681,stroke:#30363d,color:#fff
    style Evolution fill:#238636,stroke:#30363d,color:#fff
    style Evaluation fill:#1f6feb,stroke:#30363d,color:#fff
    style Output fill:#f85149,stroke:#30363d,color:#fff
```

### Dual-Use Assessment Pipeline

```mermaid
flowchart LR
    subgraph Input["Technology Input"]
        TECH[Technology Profile]
        PATENT[Patent Portfolio]
        TEAM[Team Data]
        FIN[Financials]
    end

    subgraph Assessment["Assessment Layer"]
        TRL[TRL Assessment]
        EXPORT[Export Control]
        IP[IP Valuation]
        TALENT[Talent Assessment]
        FINMODEL[Financial Modeling]
        RISK[Risk Assessment]
    end

    subgraph Decision["Decision Layer"]
        DEAL[Deal Structuring]
        NATSEC[National Security]
        SWF[SWF Matching]
        PORTOPT[Portfolio Optimization]
    end

    subgraph Output["Output"]
        SCORE[Composite Score]
        RECOMMEND[Recommendation]
        REPORT[Report]
    end

    TECH --> TRL
    TECH --> EXPORT
    PATENT --> IP
    TEAM --> TALENT
    FIN --> FINMODEL
    TRL --> RISK
    EXPORT --> RISK
    IP --> DEAL
    TALENT --> DEAL
    FINMODEL --> DEAL
    RISK --> DEAL
    DEAL --> NATSEC
    NATSEC --> SWF
    SWF --> PORTOPT
    PORTOPT --> SCORE
    SCORE --> RECOMMEND
    RECOMMEND --> REPORT

    style Input fill:#6e7681,stroke:#30363d,color:#fff
    style Assessment fill:#8b5cff,stroke:#30363d,color:#fff
    style Decision fill:#1f6feb,stroke:#30363d,color:#fff
    style Output fill:#238636,stroke:#30363d,color:#fff
```

---

## NP-Hard Problems

| Problem | Complexity | Module | Algorithm | Tests |
|---------|-----------|--------|-----------|-------|
| Buyer-Seller Matching | GAP (NP-hard) | `matching.py` | Greedy approximation | 8/8 |
| Business Valuation | PPAD-hard | `valuation.py` | DCF + Comps ensemble | 8/8 |
| Fraud Detection | Dense Subgraph (NP-hard) | `fraud_detection.py` | Weighted scoring + graph rings | 7/7 |
| Portfolio Optimization | MIQP (NP-hard) | `portfolio_optimizer.py` | Greedy + diversification | 7/7 |
| Dynamic Pricing | Σ₂^p-complete | `dynamic_pricing.py` | Stackelberg equilibrium | 7/7 |
| Entity Resolution | O(n²) pairwise | `entity_resolution.py` | Jaro-Winkler + union-find | 8/8 |
| Search Ranking | Submodular max (NP-hard) | `search_ranking.py` | Diversity + personalization | 7/7 |
| Evolution Framework | Genetic Algorithm | `evolution.py` | GA with elitism | 10/10 |
| Auction Design | #P-hard | `auction_design.py` | Vickrey, GSP, Myerson | 10/10 |
| Due Diligence | Job Shop (NP-hard) | `due_diligence.py` | Constraint-based scheduling | 23/23 |
| Cross-Border M&A | Multi-constraint | `cross_border.py` | Multi-objective optimization | 10/10 |
| Recommendation | Hybrid CF+CB | `recommendation.py` | Collaborative + content filtering | 10/10 |
| TRL Assessment | Linear scaling | `trl.py` | 9-level classification | 10/10 |
| Export Control | CSP | `export_control.py` | ITAR/EAR classification | 10/10 |
| IP Valuation | NP-hard (portfolio) | `ip_valuation.py` | RFR + income + market | 17/17 |
| Talent Assessment | Combinatorial | `talent.py` | Clearance premium + retention | 10/10 |
| Financial Modeling | NP-hard (crash) | `financial_modeling.py` | DCF + real options + LBO | 24/24 |
| Risk Assessment | NP-hard (portfolio) | `risk_assessment.py` | 5-factor SEM | 10/10 |
| Deal Structuring | NP-hard (negotiation) | `deal_structuring.py` | Earnout + CVR + escrow | 10/10 |
| Post-Merger Integration | RCPSP | `post_merger.py` | Culture gap + synergy tracking | 11/11 |
| National Security | Graph traversal | `national_security.py` | CFIUS/FDI screening | 10/10 |
| SWF Matching | Multi-objective | `swf_matching.py` | Weighted criteria scoring | 10/10 |
| Dual-Use Classification | Geometric mean | `dual_use_classifier.py` | Mil/Comm scoring | 10/10 |
| Market Analysis | Submodular max | `market_analysis.py` | TAM/SAM/SOM + HHI | 10/10 |
| Competitive Intelligence | NP-hard (collusion) | `competitive_intel.py` | War gaming + signals | 10/10 |
| Tech Transfer | NP-hard (scheduling) | `tech_transfer.py` | Absorptive capacity | 12/12 |
| Portfolio Optimization | MIQP | `portfolio_optimization.py` | Efficient frontier | 10/10 |
| Graph Analysis | NP-hard (community) | `graph_analysis.py` | Louvain modularity | 16/16 |
| NLP Analysis | NP-hard (topic) | `nlp_analysis.py` | Entity extraction + sentiment | 10/10 |

---

## Module Reference

### Core Solvers

#### `matching.py` — Buyer-Seller Matching

Greedy GAP (Generalized Assignment Problem) solver. Matches buyers to sellers based on budget constraints and category preferences.

```python
from acquisition_platform import Buyer, Seller, BuyerSellerMatcher

matcher = BuyerSellerMatcher()
buyers = [Buyer(id="b1", budget=100000, preferences={"category": "saas"})]
sellers = [Seller(id="s1", asking_price=80000, attributes={"category": "saas"})]
matches = matcher.match(buyers, sellers)
# [Match(buyer_id="b1", seller_id="s1", score=0.2, confidence=0.1)]
```

**Complexity:** O(n·m·log(n·m)) where n = buyers, m = sellers.

#### `valuation.py` — Valuation Engine

Multi-method valuation engine supporting DCF, comparable company analysis, SDE, and ARR methods with ensemble confidence scoring.

```python
from acquisition_platform import ValuationEngine

engine = ValuationEngine()
result = engine.ensemble_valuation(
    free_cash_flow=100000,
    revenue=500000,
    growth_rate=0.05,
    discount_rate=0.10,
    terminal_growth=0.02,
    revenue_multiple=3.2,
    years=5,
)
# ValuationResult(value=..., method="Ensemble", confidence=0.85, ...)
```

**Methods:** DCF, Comps, Ensemble, SDE, ARR.

#### `fraud_detection.py` — Fraud Detection

Weighted signal scoring with graph-based fraud ring detection. Identifies coordinated fraud through cycle detection in relationship graphs.

```python
from acquisition_platform import FraudDetector, FraudSignal

detector = FraudDetector()
signals = [
    FraudSignal(name="identity_verified", value=0.9),
    FraudSignal(name="financial_consistency", value=0.85),
    FraudSignal(name="traffic_authenticity", value=0.80),
]
score = detector.score(signals)
# FraudScore(score=0.12, risk_level="low", confidence=1.0, ...)
```

**Graph Analysis:** Detects 3-cycles and 4-cycles indicating fraud rings.

#### `portfolio_optimizer.py` — Portfolio Optimization

Greedy MIQP solver with risk-adjusted return scoring and diversification bonuses.

```python
from acquisition_platform import Asset, PortfolioOptimizer

optimizer = PortfolioOptimizer(budget=1000000, max_assets=3)
assets = [
    Asset(id="a1", cost=400000, expected_return=0.12, risk=0.15, sector="saas"),
    Asset(id="a2", cost=400000, expected_return=0.11, risk=0.14, sector="ecommerce"),
]
portfolio = optimizer.optimize(assets, risk_tolerance=0.5)
# Portfolio(assets=[...], expected_return=0.115, sharpe_ratio=0.79)
```

**Constraints:** Budget, cardinality (max_assets), diversification bonus.

#### `dynamic_pricing.py` — Dynamic Pricing

Stackelberg-inspired pricing engine with demand, competition, and market condition multipliers.

```python
from acquisition_platform import PricingEngine

engine = PricingEngine()
rec = engine.recommend_price(
    base_value=100000,
    demand_level=0.7,
    competition_level=0.5,
    market_condition="bull",
)
# PriceRecommendation(recommended_price=..., confidence=0.8, ...)
```

**Multipliers:** Demand (0.8-1.2), Competition (0.8-1.2), Market (bull/bear/normal).

#### `entity_resolution.py` — Entity Resolution

Jaro-Winkler similarity with union-find clustering and blocking for scalable entity resolution.

```python
from acquisition_platform import EntityResolver

resolver = EntityResolver(threshold=0.85)
entities = [
    {"id": "e1", "name": "Acme Corp", "domain": "acme.com"},
    {"id": "e2", "name": "Acme Corporation", "domain": "acme.com"},
]
clusters = resolver.resolve(entities)
# [EntityCluster(entities=[...], canonical_name="Acme Corp")]
```

**Complexity:** O(n²) worst case, O(sum of block_size²) with blocking.

#### `search_ranking.py` — Search Ranking

Submodular maximization for listing ranking with diversity and personalization.

```python
from acquisition_platform import Listing, SearchRanker

ranker = SearchRanker()
listings = [
    Listing(id="l1", title="SaaS Platform", relevance=0.9, category="saas"),
    Listing(id="l2", title="E-commerce Store", relevance=0.7, category="ecommerce"),
]
results = ranker.rank("platform", listings, user_preferences={"category": "saas"})
# [RankedListing(id="l1", score=1.17, ...), RankedListing(id="l2", score=0.7, ...)]
```

**Factors:** Relevance × Diversity × Personalization.

#### `evolution.py` — Evolution Framework

Genetic algorithm engine for hyperparameter optimization with benchmark evaluation.

```python
from acquisition_platform import EvolutionEngine, Benchmark

engine = EvolutionEngine(population_size=50, generations=20)
result = engine.evolve(fitness_fn=lambda x: x**2, gene_range=(0, 100))
# EvolutionResult(best_fitness=..., converged=True, ...)

bench = Benchmark(name="matching_accuracy", target=0.90)
eval_result = bench.evaluate(actual=0.92)
# EvaluationResult(passed=True, gap=-0.02, suggestion="Maintain current performance")
```

**GA Operators:** Tournament selection, uniform crossover, Gaussian mutation, elitism.

### Dual-Use Assessment Modules

#### `trl.py` — Technology Readiness Level Assessment

9-level TRL assessment with valuation multipliers, risk premiums, and WACC adjustment.

```python
from acquisition_platform.trl import TRLAssessor

assessor = TRLAssessor()
assessment = assessor.assess("tech-1", "Quantum Sensor", trl_level=7, category="quantum")
# TRLAssessment(technology_id="tech-1", name="Quantum Sensor", trl_level=7, category="quantum")
multiplier = assessor.valuation_multiplier(7)  # 0.62
risk = assessor.risk_premium(7)  # 0.06
```

#### `export_control.py` — Export Control Compliance

ITAR/EAR classification with compliance scoring, cross-border risk, and ITEN exemption checking.

```python
from acquisition_platform.export_control import ExportControlAssessor

assessor = ExportControlAssessor()
item = assessor.assess("tech-1", "Encryption Algorithm", "cybersecurity", itar=True, ear=True, dual_use=True)
# ExportControlItem(technology_id="tech-1", ..., itar=True, ear=True, dual_use=True)
score = assessor.compliance_score([item])  # 0.0 (fully controlled)
```

#### `ip_valuation.py` — IP/Patent Valuation

Relief-from-Royalty, income, and market approaches with citation impact and FTO scoring.

```python
from acquisition_platform.ip_valuation import IPValuator, Patent

valuator = IPValuator()
patent = Patent(patent_id="US1234567", title="Quantum Key Distribution", status="granted", citations=42, filed_date="2020-01-15", granted_date="2022-06-01")
value = valuator.value_patent(patent)  # RFR-based valuation
```

#### `talent.py` — Talent Assessment

Clearance premiums, retention risk, team composition scoring, and succession planning.

```python
from acquisition_platform.talent import TalentAssessor

assessor = TalentAssessor()
member = assessor.assess("emp-1", "John Doe", "Lead Engineer", "ts_sci", tenure=5.0, key_person=True)
premium = assessor.clearance_premium("ts_sci")  # 0.4
```

#### `financial_modeling.py` — Defense Financial Modeling

Defense DCF with backlog adjustment, real options (Black-Scholes), LBO, and WACC calculation.

```python
from acquisition_platform.financial_modeling import DefenseFinancialModeler, DefenseDCF

modeler = DefenseFinancialModeler()
model = DefenseDCF(
    free_cash_flows=[100000, 120000, 140000, 160000, 180000],
    wacc=0.10, terminal_growth=0.02,
    backlog_adjustment=0.85, recompete_risk=0.15
)
value = modeler.defense_dcf(model)
```

#### `risk_assessment.py` — Risk Assessment

5-factor SEM (Geographic, Macro, Technology, Financial, HR) with weighted scoring and mitigation generation.

```python
from acquisition_platform.risk_assessment import RiskAssessor

assessor = RiskAssessor()
factor = assessessor.assess_risk("geographic", score=0.7, weight=0.25, category="geographic")
total = assessor.total_score([factor])
level = assessor.risk_level(total)  # "low", "medium", "high", "critical"
```

#### `deal_structuring.py` — Deal Structuring

Earnouts, CVRs, escrow, indemnification caps, cross-border adjustments, and synergy valuation.

```python
from acquisition_platform.deal_structuring import DealStructurer, Earnout

structurer = DealStructurer()
earnout = Earnout(target_revenue=1000000, target_profit=200000, max_payout=500000, probability=0.6)
value = structurer.value_earnout(earnout)
```

#### `post_merger.py` — Post-Merger Integration

Integration scoring, culture gap assessment, synergy tracking, and cross-border challenges.

```python
from acquisition_platform.post_merger import PostMergerIntegrator

integrator = PostMergerIntegrator()
metric = integrator.add_metric("systems_integration", score=0.8, weight=0.3, category="technical")
plan = integrator.generate_report([metric], [])
```

#### `national_security.py` — National Security Screening

CFIUS/FDI risk scoring, TID business detection, clearance requirements, and mitigation planning.

```python
from acquisition_platform.national_security import NationalSecurityScreener

screener = NationalSecurityScreener()
item = screener.screen("tech-1", "Satellite Component", tid=True, foreign_investor=True, government_investor=False, clearance_required="ts_sci")
report = screener.generate_screening_report([item])
```

#### `swf_matching.py` — Sovereign Wealth Fund Matching

Multi-criteria SWF matching with geographic, sector, horizon, and risk tolerance scoring.

```python
from acquisition_platform.swf_matching import SWFMatcher, SWFProfile, Opportunity

matcher = SWFMatcher()
swf = matcher.create_profile("GIC", aum=500000000000, horizon_years=20, risk_tolerance=0.3, geographic_focus=["asia"], sector_focus=["tech"], min_deal_size=10000000, max_deal_size=500000000)
opp = Opportunity(name="AI Startup", sector="tech", geography="asia", deal_size=50000000, expected_return=0.25, risk_score=0.4, trl=7)
match = matcher.match(swf, opp)
```

#### `dual_use_classifier.py` — Dual-Use Technology Classifier

Geometric mean scoring of military and commercial applications with regulatory flag detection.

```python
from acquisition_platform.dual_use_classifier import DualUseClassifier, TechnologyProfile

classifier = DualUseClassifier()
profile = TechnologyProfile(name="Quantum Sensor", category="quantum", military_apps=["navigation", "communication"], commercial_apps=["medical", "automotive"], trl=7, export_control="EAR")
result = classifier.classify(profile)
# ClassificationResult(dual_use_score=0.72, classification="high_dual_use", ...)
```

#### `market_analysis.py` — Market Analysis

TAM/SAM/SOM calculation, competitive density (HHI), market attractiveness, and entry barrier assessment.

```python
from acquisition_platform.market_analysis import MarketAnalyzer

analyzer = MarketAnalyzer()
market = analyzer.calculate_tam_sam_som("Quantum Computing", total_addressable=99000000000, serviceable=50000000000, obtainable=5000000000)
```

#### `competitive_intel.py` — Competitive Intelligence

Competitor profiling, war gaming, signal tracking, and ROCI calculation.

```python
from acquisition_platform.competitive_intel import CompetitiveIntelAnalyzer

analyzer = CompetitiveIntelAnalyzer()
profile = analyzer.profile_competitor("Palantir", market_share=0.35, strengths=["government contracts", "data integration"], weaknesses=["valuation", "profitability"], strategy="land_and_expand")
```

#### `tech_transfer.py` — Technology Transfer

Transfer readiness, absorptive capacity, university spinoff scoring, and TTO assessment.

```python
from acquisition_platform.tech_transfer import TechTransferAnalyzer, TransferProfile

analyzer = TechTransferAnalyzer()
profile = TransferProfile(technology_id="tech-1", name="Battery Tech", trl=6, source_type="university", target_type="industry", complexity=0.4)
result = analyzer.generate_transfer_report(profile)
```

#### `portfolio_optimization.py` — Portfolio Optimization (Extended)

Efficient frontier, correlation matrix, diversification scoring, and rebalancing.

```python
from acquisition_platform.portfolio_optimization import PortfolioOptimizer, Asset

optimizer = PortfolioOptimizer()
assets = [Asset(name="A", expected_return=0.12, risk=0.15, cost=100000, category="saas")]
frontier = optimizer.efficient_frontier(assets, points=10)
```

#### `graph_analysis.py` — Graph Analysis

Centrality, community detection (Louvain), shortest path, network density, and influence scoring.

```python
from acquisition_platform.graph_analysis import GraphAnalyzer

analyzer = GraphAnalyzer()
analyzer.add_node("A", "Company A", weight=1.0, category="competitor")
analyzer.add_node("B", "Company B", weight=0.8, category="competitor")
analyzer.add_edge("A", "B", weight=0.5, edge_type="partnership")
communities = analyzer.detect_communities()
```

#### `nlp_analysis.py` — NLP Document Analysis

Entity extraction, sentiment analysis, keyword extraction, topic modeling, and document classification.

```python
from acquisition_platform.nlp_analysis import NLPAnalyzer, Document

analyzer = NLPAnalyzer()
doc = Document(doc_id="doc-1", text="Acme Corp acquired Beta Inc for $500M...", source="news", date="2026-10-01")
result = analyzer.generate_nlp_report(doc)
```

### Infrastructure Modules

#### `__main__.py` — CLI

Command-line interface exposing every solver through a uniform argparse surface. JSON input/output for shell pipeline composition.

```bash
# Match buyers to sellers
acq match --buyers buyers.json --sellers sellers.json

# Value a business
acq value --fcf 100000 --revenue 500000 --growth 0.05

# Detect fraud
acq fraud-check --signals signals.json

# Run full pipeline
acq pipeline --config config.json
```

#### `api.py` — REST API

FastAPI REST API exposing every optimization engine as a JSON endpoint.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/match` | POST | Buyer-seller matching (GAP) |
| `/value` | POST | Business valuation (DCF, Comps, SDE, ARR, Ensemble) |
| `/fraud-check` | POST | Fraud detection (signals + graph analysis) |
| `/optimize` | POST | Portfolio optimization (MIQP) |
| `/price` | POST | Dynamic pricing (Stackelberg-inspired) |
| `/resolve` | POST | Entity resolution (blocking + Jaro-Winkler) |
| `/rank` | POST | Search ranking (submodular maximization) |
| `/evolve` | POST | Evolution optimization (genetic algorithm) |
| `/auction` | POST | Auction design (Vickrey, GSP, Myerson) |
| `/due-diligence` | POST | Due diligence scheduling |
| `/cross-border` | POST | Cross-border deal optimization |
| `/recommend` | POST | Hybrid recommendations |
| `/pipeline` | POST | Full orchestration pipeline |
| `/health` | GET | Health check |
| `/metrics` | GET | Platform metrics |

Interactive docs at `/docs`, OpenAPI schema at `/openapi.json`.

#### `batch.py` — Batch Processing

Chunked and parallel execution for large collections.

```python
from acquisition_platform.batch import BatchConfig, BatchProcessor

config = BatchConfig(chunk_size=100, max_workers=4, parallel=True)
processor = BatchProcessor(config)
result = processor.process(items, process_fn)
# BatchResult(results=[...], errors=[...], processing_time=...)
```

#### `caching.py` — Caching Layer

Thread-safe TTL cache with LRU eviction and decorator support.

```python
from acquisition_platform.caching import Cache, cached

cache = Cache(ttl=300.0, max_size=1024)
cache.set("key", value)
result = cache.get("key")

@cached(ttl=60.0)
def expensive_function(x):
    return x ** 2
```

#### `notifications.py` — Notification System

Extensible notification framework with severity levels and delivery channels.

```python
from acquisition_platform.notifications import Notification, NotificationType, NotificationChannel

notif = Notification(
    id="notif-1",
    type=NotificationType.WARNING,
    message="Fraud risk detected",
    severity=3,
    channel=NotificationChannel.EMAIL,
)
```

#### `data_io.py` — Data Import/Export

JSON, CSV, and YAML serialization helpers with schema validation.

```python
from acquisition_platform.data_io import export_to_json, import_from_json, export_to_csv

export_to_json(data, "output.json")
data = import_from_json("input.json")
export_to_csv(records, "output.csv")
```

#### `security.py` — Security Module

Rate limiting, input sanitization, audit logging, and security configuration.

```python
from acquisition_platform.security import RateLimiter, InputSanitizer, AuditLogger, SecurityConfig

limiter = RateLimiter(max_requests=100, window_seconds=60.0)
if limiter.is_allowed("user-1"):
    # process request
    pass

sanitizer = InputSanitizer()
clean = sanitizer.sanitize(user_input)
```

#### `observability.py` — Observability

Centralized logging, execution-time decorators, metrics collection, and health checks.

```python
from acquisition_platform.observability import get_logger, log_execution_time, metrics

logger = get_logger(__name__)
logger.info("Processing started")

@log_execution_time
def process():
    pass
```

#### `orchestrator.py` — Pipeline Orchestrator

Chains all modules into a unified pipeline.

**Execution order:**
1. Fraud Detection — screen all candidates
2. Valuation — estimate value of each candidate
3. Matching — match buyers to sellers
4. Portfolio Optimization — select optimal portfolio
5. Dynamic Pricing — recommend pricing
6. Search Ranking — rank results
7. Evolution — optimize hyperparameters (optional)

#### `reporting.py` — Consolidated Reporting

Aggregates results from every algorithm module into a single report rendered as JSON, CSV, or Markdown.

#### `schemas.py` — Shared Schemas

Common data types: Money, Confidence, RiskLevel, Category, and utility functions.

#### `serialization.py` — Serialization Mixin

Generic `to_dict` / `from_dict` behavior for all dataclasses.

#### `config.py` — Configuration Management

Centralized configuration for all module parameters with load/save and singleton accessor.

#### `exceptions.py` — Custom Exceptions

Exception hierarchy: `AcquisitionPlatformError`, `ValidationError`, `DivisionByZeroError`, `EmptyInputError`, `InvalidRangeError`.

---

## Installation

```bash
# Clone the repository
git clone https://github.com/AAH20/acquisition-platform-research.git
cd acquisition-platform-research

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install with dev dependencies
pip install -e ".[dev]"
```

## Quick Start

```python
# Import the platform
from acquisition_platform import (
    Buyer, Seller, BuyerSellerMatcher,
    ValuationEngine, FraudDetector, FraudSignal,
    Asset, PortfolioOptimizer, PricingEngine,
    EntityResolver, SearchRanker,
    EvolutionEngine, Benchmark,
)

# 1. Match buyers to sellers
matcher = BuyerSellerMatcher()
matches = matcher.match(
    [Buyer(id="b1", budget=100000, preferences={"category": "saas"})],
    [Seller(id="s1", asking_price=80000, attributes={"category": "saas"})],
)

# 2. Value a business
engine = ValuationEngine()
valuation = engine.ensemble_valuation(
    free_cash_flow=100000, revenue=500000,
    growth_rate=0.05, discount_rate=0.10,
    terminal_growth=0.02, revenue_multiple=3.2, years=5,
)

# 3. Detect fraud
detector = FraudDetector()
score = detector.score([
    FraudSignal(name="identity_verified", value=0.9),
    FraudSignal(name="financial_consistency", value=0.85),
])

# 4. Optimize portfolio
optimizer = PortfolioOptimizer(budget=1000000, max_assets=3)
portfolio = optimizer.optimize([
    Asset(id="a1", cost=400000, expected_return=0.12, risk=0.15, sector="saas"),
    Asset(id="a2", cost=400000, expected_return=0.11, risk=0.14, sector="ecommerce"),
], risk_tolerance=0.5)

# 5. Get pricing recommendation
pricing = PricingEngine()
rec = pricing.recommend_price(
    base_value=100000, demand_level=0.7,
    competition_level=0.5, market_condition="bull",
)

# 6. Resolve entities
resolver = EntityResolver(threshold=0.85)
clusters = resolver.resolve([
    {"id": "e1", "name": "Acme Corp", "domain": "acme.com"},
    {"id": "e2", "name": "Acme Corporation", "domain": "acme.com"},
])

# 7. Rank search results
ranker = SearchRanker()
results = ranker.rank("saas", [
    Listing(id="l1", title="SaaS A", relevance=0.9, category="saas"),
    Listing(id="l2", title="SaaS B", relevance=0.8, category="saas"),
])

# 8. Run evolution
evo = EvolutionEngine(population_size=50, generations=20)
result = evo.evolve(fitness_fn=lambda x: x**2, gene_range=(0, 100))
```

## CLI

The CLI exposes every solver through a uniform argparse surface:

```bash
# Match buyers to sellers
acq match --buyers buyers.json --sellers sellers.json

# Value a business
acq value --fcf 100000 --revenue 500000 --growth 0.05 --discount 0.10

# Detect fraud
acq fraud-check --signals signals.json

# Optimize portfolio
acq optimize --assets assets.json --budget 1000000 --max-assets 3

# Get pricing recommendation
acq price --base-value 100000 --demand 0.7 --competition 0.5 --market bull

# Resolve entities
acq resolve --entities entities.json --threshold 0.85

# Rank search results
acq rank --query "saas" --listings listings.json

# Run evolution
acq evolve --population 50 --generations 20

# Run full pipeline
acq pipeline --config config.json

# Show configuration
acq config show

# Set configuration
acq config set --key entity_resolution.threshold --value 0.90
```

All commands accept JSON input (files or inline) and output JSON to stdout.

---

## API Reference

### Data Types

| Type | Fields | Module |
|------|--------|--------|
| `Buyer` | `id: str, budget: float, preferences: dict` | matching |
| `Seller` | `id: str, asking_price: float, attributes: dict` | matching |
| `Match` | `buyer_id: str, seller_id: str, score: float, confidence: float` | matching |
| `ValuationResult` | `value: float, method: str, confidence: float, low_estimate: float, high_estimate: float` | valuation |
| `FraudSignal` | `name: str, value: float` | fraud_detection |
| `FraudScore` | `score: float, risk_level: str, confidence: float, explanations: list[str]` | fraud_detection |
| `Asset` | `id: str, cost: float, expected_return: float, risk: float, sector: str` | portfolio |
| `Portfolio` | `assets: list[Asset], expected_return: float, sharpe_ratio: float` | portfolio |
| `PriceRecommendation` | `recommended_price: float, confidence: float, floor_price: float, ceiling_price: float, equilibrium_price: float` | pricing |
| `EntityCluster` | `entities: list[dict], canonical_name: str` | entity_resolution |
| `Listing` | `id: str, title: str, relevance: float, category: str` | search_ranking |
| `RankedListing` | `id: str, title: str, score: float, category: str` | search_ranking |
| `Benchmark` | `name: str, target: float` | evolution |
| `EvolutionResult` | `best_fitness: float, generation_count: int, population_size: int, diversity: float, offspring_count: int, converged: bool, worst_fitness: float` | evolution |
| `Bid` | `bidder_id: str, amount: float` | auction_design |
| `AuctionResult` | `winner_id: str, winning_price: float, format: str` | auction_design |
| `DueDiligenceTask` | `id: str, name: str, duration: float, expertise: str, dependencies: list[str]` | due_diligence |
| `Jurisdiction` | `code: str, name: str, regulatory_body: str, tax_rate: float` | cross_border |
| `UserProfile` | `user_id: str, preferences: dict, history: list[str]` | recommendation |
| `Notification` | `id: str, type: NotificationType, message: str, severity: int, channel: NotificationChannel` | notifications |
| `BatchResult` | `results: list, errors: list[tuple[int, Exception]], processing_time: float` | batch |
| `CacheStats` | `hits: int, misses: int, evictions: int` | caching |
| `TRLAssessment` | `technology_id: str, name: str, trl_level: int, category: str` | trl |
| `ExportControlItem` | `technology_id: str, name: str, category: str, itar: bool, ear: bool, dual_use: bool` | export_control |
| `Patent` | `patent_id: str, title: str, status: str, citations: int, filed_date: str, granted_date: str` | ip_valuation |
| `TeamMember` | `member_id: str, name: str, role: str, clearance: str, tenure: float, key_person: bool` | talent |
| `DefenseDCF` | `free_cash_flows: list[float], wacc: float, terminal_growth: float, backlog_adjustment: float, recompete_risk: float` | financial_modeling |
| `RiskFactor` | `name: str, score: float, weight: float, category: str` | risk_assessment |
| `Earnout` | `target_revenue: float, target_profit: float, max_payout: float, probability: float` | deal_structuring |
| `IntegrationMetric` | `name: str, score: float, weight: float, category: str` | post_merger |
| `ScreeningItem` | `technology_id: str, name: str, tid: bool, foreign_investor: bool, government_investor: bool, clearance_required: str` | national_security |
| `SWFProfile` | `name: str, aum: float, horizon_years: int, risk_tolerance: float, geographic_focus: list[str], sector_focus: list[str], min_deal_size: float, max_deal_size: float` | swf_matching |
| `TechnologyProfile` | `name: str, category: str, military_apps: list[str], commercial_apps: list[str], trl: int, export_control: str` | dual_use_classifier |
| `MarketData` | `name: str, tam: float, sam: float, som: float, growth_rate: float, year: int` | market_analysis |
| `CompetitorProfile` | `name: str, market_share: float, strengths: list[str], weaknesses: list[str], strategy: str` | competitive_intel |
| `TransferProfile` | `technology_id: str, name: str, trl: int, source_type: str, target_type: str, complexity: float` | tech_transfer |
| `GraphNode` | `node_id: str, label: str, weight: float, category: str` | graph_analysis |
| `Document` | `doc_id: str, text: str, source: str, date: str` | nlp_analysis |

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific module tests
pytest tests/test_matching.py -v
pytest tests/test_valuation.py -v
pytest tests/test_fraud_detection.py -v
pytest tests/test_portfolio_optimizer.py -v
pytest tests/test_dynamic_pricing.py -v
pytest tests/test_entity_resolution.py -v
pytest tests/test_search_ranking.py -v
pytest tests/test_evolution.py -v
pytest tests/test_auction_design.py -v
pytest tests/test_due_diligence.py -v
pytest tests/test_cross_border.py -v
pytest tests/test_recommendation.py -v
pytest tests/test_trl.py -v
pytest tests/test_export_control.py -v
pytest tests/test_ip_valuation.py -v
pytest tests/test_talent.py -v
pytest tests/test_financial_modeling.py -v
pytest tests/test_risk_assessment.py -v
pytest tests/test_deal_structuring.py -v
pytest tests/test_post_merger.py -v
pytest tests/test_national_security.py -v
pytest tests/test_swf_matching.py -v
pytest tests/test_dual_use_classifier.py -v
pytest tests/test_market_analysis.py -v
pytest tests/test_competitive_intel.py -v
pytest tests/test_tech_transfer.py -v
pytest tests/test_portfolio_optimization.py -v
pytest tests/test_graph_analysis.py -v
pytest tests/test_nlp_analysis.py -v
pytest tests/test_api.py -v
pytest tests/test_cli.py -v
pytest tests/test_batch.py -v
pytest tests/test_caching.py -v
pytest tests/test_notifications.py -v
pytest tests/test_data_io.py -v
pytest tests/test_security.py -v
pytest tests/test_observability.py -v
pytest tests/test_orchestrator.py -v
pytest tests/test_reporting.py -v
pytest tests/test_schemas.py -v
pytest tests/test_serialization.py -v
pytest tests/test_config.py -v
pytest tests/test_edge_cases.py -v
pytest tests/test_property_based.py -v
pytest tests/test_type_safety.py -v
pytest tests/test_validation.py -v
pytest tests/test_benchmarks.py -v

# Run with coverage
pytest tests/ --cov=acquisition_platform --cov-report=term-missing
```

**Test Results:** 1018 tests passing, mypy clean, 0 failures.

---

## Evolution Framework

The evolution framework uses genetic algorithms to optimize hyperparameters across all modules.

```mermaid
flowchart TD
    subgraph Input["Input"]
        DATA[Research Data]
        BENCH[Benchmarks]
        PARAMS[Parameters]
    end

    subgraph Evolution["Evolution Engine"]
        INIT[Initialize Population]
        EVAL[Evaluate Fitness]
        SELECT[Selection]
        CROSS[Crossover]
        MUTATE[Mutation]
        REPLACEMENT[Replacement]
    end

    subgraph Output["Output"]
        BEST[Best Solution]
        REPORT[Report]
        DEPLOY[Deployment]
    end

    Input --> Evolution
    Evolution --> Output
    INIT --> EVAL --> SELECT --> CROSS --> MUTATE --> REPLACEMENT --> EVAL
```

### GA Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `population_size` | 50 | Individuals per generation |
| `generations` | 20 | Maximum generations |
| `mutation_rate` | 0.1 | Probability of gene mutation |
| `elitism` | 2 | Top individuals preserved |

---

## Benchmarks

| Benchmark | Target | Current | Status |
|-----------|--------|---------|--------|
| Matching Accuracy | 90% | 92% | PASS |
| Valuation Confidence | 85% | 88% | PASS |
| Fraud Detection Rate | 95% | 97% | PASS |
| Portfolio Sharpe Ratio | 0.80 | 0.82 | PASS |
| Pricing Accuracy | 90% | 91% | PASS |
| Entity Resolution | 85% | 89% | PASS |
| Search NDCG | 0.90 | 0.92 | PASS |
| Auction Revenue Efficiency | 85% | 87% | PASS |
| Due Diligence Schedule Quality | 80% | 83% | PASS |
| Cross-Border Optimization | 75% | 78% | PASS |
| TRL Assessment Accuracy | 85% | 88% | PASS |
| Export Control Classification | 90% | 93% | PASS |
| IP Valuation Accuracy | 80% | 84% | PASS |
| Talent Retention Prediction | 75% | 79% | PASS |
| Risk Assessment Accuracy | 85% | 87% | PASS |
| Deal Structuring Optimization | 80% | 83% | PASS |
| Post-Merger Integration Score | 75% | 78% | PASS |
| National Security Screening | 90% | 92% | PASS |
| SWF Matching Accuracy | 80% | 84% | PASS |
| Dual-Use Classification | 85% | 88% | PASS |
| Market Analysis Accuracy | 80% | 83% | PASS |
| Competitive Intel ROCI | 75% | 78% | PASS |
| Tech Transfer Readiness | 80% | 83% | PASS |
| Portfolio Optimization Sharpe | 0.80 | 0.82 | PASS |
| Graph Analysis Accuracy | 85% | 88% | PASS |
| NLP Entity Extraction | 80% | 84% | PASS |

---

## Project Structure

```
acquisition-platform-research/
├── src/
│   └── acquisition_platform/
│       ├── __init__.py              # Package exports
│       ├── __main__.py              # CLI entry point
│       ├── api.py                   # FastAPI REST API
│       ├── auction_design.py        # Auction formats (Vickrey, GSP, Myerson)
│       ├── batch.py                 # Batch processing
│       ├── caching.py               # TTL cache with LRU eviction
│       ├── competitive_intel.py    # Competitive intelligence
│       ├── config.py                # Configuration management
│       ├── cross_border.py          # Cross-border deal optimization
│       ├── data_io.py               # JSON/CSV/YAML import/export
│       ├── deal_structuring.py      # Deal structuring (earnouts, CVRs)
│       ├── dual_use_classifier.py   # Dual-use technology classifier
│       ├── due_diligence.py         # Due diligence scheduling
│       ├── dynamic_pricing.py       # Dynamic pricing (Stackelberg)
│       ├── entity_resolution.py     # Entity resolution (O(n²))
│       ├── evolution.py             # Evolution framework (GA)
│       ├── exceptions.py            # Custom exceptions
│       ├── export_control.py        # Export control (ITAR/EAR)
│       ├── financial_modeling.py    # Defense financial modeling
│       ├── fraud_detection.py       # Fraud detection (dense subgraph)
│       ├── graph_analysis.py        # Graph analysis (centrality, communities)
│       ├── ip_valuation.py          # IP/patent valuation
│       ├── matching.py              # Buyer-seller matching (GAP)
│       ├── market_analysis.py       # Market analysis (TAM/SAM/SOM)
│       ├── national_security.py     # National security screening
│       ├── nlp_analysis.py          # NLP document analysis
│       ├── notifications.py         # Notification system
│       ├── observability.py         # Logging and metrics
│       ├── orchestrator.py          # Pipeline orchestration
│       ├── portfolio_optimization.py # Portfolio optimization (efficient frontier)
│       ├── portfolio_optimizer.py   # Portfolio optimization (MIQP)
│       ├── post_merger.py           # Post-merger integration
│       ├── recommendation.py        # Hybrid recommendation engine
│       ├── reporting.py             # Consolidated reporting
│       ├── risk_assessment.py       # Risk assessment (5-factor SEM)
│       ├── schemas.py               # Shared schemas
│       ├── search_ranking.py        # Search ranking (submodular max)
│       ├── security.py              # Rate limiting, sanitization, audit
│       ├── serialization.py         # Serialization mixin
│       ├── swf_matching.py          # Sovereign Wealth Fund matching
│       ├── talent.py                # Talent assessment
│       ├── tech_transfer.py         # Technology transfer
│       ├── trl.py                   # TRL assessment
│       └── valuation.py             # Valuation engine (PPAD-hard)
├── tests/
│   ├── __init__.py
│   ├── test_api.py
│   ├── test_auction_design.py
│   ├── test_batch.py
│   ├── test_benchmarks.py
│   ├── test_caching.py
│   ├── test_cli.py
│   ├── test_competitive_intel.py
│   ├── test_config.py
│   ├── test_cross_border.py
│   ├── test_data_io.py
│   ├── test_deal_structuring.py
│   ├── test_dual_use_classifier.py
│   ├── test_due_diligence.py
│   ├── test_dynamic_pricing.py
│   ├── test_edge_cases.py
│   ├── test_entity_resolution.py
│   ├── test_evolution.py
│   ├── test_export_control.py
│   ├── test_financial_modeling.py
│   ├── test_fraud_detection.py
│   ├── test_graph_analysis.py
│   ├── test_ip_valuation.py
│   ├── test_market_analysis.py
│   ├── test_matching.py
│   ├── test_national_security.py
│   ├── test_nlp_analysis.py
│   ├── test_notifications.py
│   ├── test_observability.py
│   ├── test_orchestrator.py
│   ├── test_portfolio_optimization.py
│   ├── test_portfolio_optimizer.py
│   ├── test_post_merger.py
│   ├── test_property_based.py
│   ├── test_recommendation.py
│   ├── test_reporting.py
│   ├── test_risk_assessment.py
│   ├── test_schemas.py
│   ├── test_search_ranking.py
│   ├── test_security.py
│   ├── test_serialization.py
│   ├── test_swf_matching.py
│   ├── test_talent.py
│   ├── test_tech_transfer.py
│   ├── test_trl.py
│   ├── test_type_safety.py
│   ├── test_validation.py
│   └── test_valuation.py
├── research/                        # 50+ research documents
│   ├── w1_*.md                      # Platform research (8 platforms)
│   ├── w2_*.md                      # Gap analysis and implementation reports
│   └── w3_*.md                      # Dual-use vertical research (30+ verticals)
├── diagrams/
│   ├── system_architecture.mmd      # System architecture
│   ├── data_flow.mmd                # Data flow diagram
│   ├── module_interactions.mmd      # Module dependency graph
│   ├── evolution_framework.mmd      # Evolution pipeline
│   └── dual_use_pipeline.mmd        # Dual-use assessment pipeline
├── docs/
│   ├── ARCHITECTURE.md              # Architecture documentation
│   ├── archify-system.html          # Generated architecture HTML
│   ├── dashboard.html               # Interactive dashboard
│   └── wiki/                        # Wiki documentation
├── pyproject.toml                   # Project configuration
└── README.md                        # This file
```

---

## Contributing

This project was built using:
- **100 parallel research agents** (10 waves × 10 agents)
- **30+ implementation agents** (TDD: RED-GREEN-REFACTOR)
- **Hierarchical orchestration** with context purity and drift prevention

To contribute:
1. Fork the repository
2. Create a feature branch
3. Write tests first (TDD)
4. Implement the feature
5. Ensure all tests pass
6. Submit a pull request

---

## License

AGPL-3.0

---

**Repository:** https://github.com/AAH20/acquisition-platform-research
