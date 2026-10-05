# Wave 3: Dual-Use Data & Analytics — Acquisition Research

> **Focus:** Dual-use data and analytics technology acquisitions
> **Date:** 2026-10-05
> **Method:** 10 web searches, top 3 results each, synthesized

---

## 1. Market Overview

The dual-use data and analytics M&A landscape is experiencing unprecedented growth, driven by defense modernization, AI proliferation, and the strategic value of proprietary datasets.

### Defense Tech M&A Surge
- **VC investment in defense tech** reached a record **$49.9B in 2025**, up 83% YoY (PitchBook).
- **Defense sector M&A** in the US: deal volume rose 20% YoY to **18 transactions in 2025**; value nearly tripled to **$1.7B**.
- In 2026 (through May 22): **14 deals worth $1.2B** — both figures well ahead of prior year.
- The **three largest defense deals globally** in 2025–Q1 2026 were all US transactions, all driven by technology or technology-adjacent capabilities.

### Notable Transactions
| Acquirer | Target | Value | Strategic Rationale |
|----------|--------|-------|---------------------|
| CACI International | ARKA Group (from Blackstone) | $2.6B | Space-based optical/sensor tech + agentic AI for geospatial intelligence |
| Firefly Aerospace | SciTec | $855M | Satellite-based missile warning and tracking |
| Consumer Edge | Earnest Analytics | Undisclosed | Consumer + healthcare transaction data consolidation |
| Greystones Group | Dual-use data analytics IP (US Treasury) | Undisclosed | AI/ML/NLP analytics platform for federal agencies |
| Teradata | RainStor, Revelytix, Hadapt, Think Big Analytics | Multiple | Big data archiving, Hadoop, analytics consulting |
| Syncsort | Circle Computer Group | Undisclosed | Mainframe-to-Hadoop data integration |

### Market Structure
- **Late-stage private defense tech** is a hybrid of venture, industrial policy, and regulated markets investing.
- Capital structure: late-stage rounds fund **factories, not runway** ($3.6B+ raised across four rounds in 19 months by Anduril, Saronic, Hadrian, Helsing).
- Revenue arrives as a **step function** — milestone deliveries on government timelines.
- GAO 2024 assessment: average Major Defense Acquisition Program takes **11 years** to deliver initial capability.

---

## 2. Key Technologies

### AI/ML/NLP Analytics Platforms
- **Greystones Analytics Platform**: COTS-based, open architecture, microservices; supports AI/ML/NLP analytics within federal security/compliance standards. Deployed at US Treasury (6,000+ analysts), identified $1B+ in tax fraud. SBIR Phase 3 awarded.
- **Agentic AI for geospatial intelligence**: CACI/ARKA deal highlights autonomous AI agents for spatial analysis.
- **Predictive analytics**: Earnest Analytics' Dash platform surfaces predictions on earnings, sales growth, and market share.

### Data Infrastructure & Analytics Engines
- **Hybrid analytics / Dual Execution**: MotherDuck's query planner treats laptop and cloud as two nodes in a single distributed system, minimizing data movement.
- **Columnar databases + vectorized execution**: DuckDB processes data in large batches, orders of magnitude faster than row-stores for OLAP.
- **Data compression**: RainStor offers 10x–40x compression, immutable storage, SQL accessibility.
- **Mainframe data integration**: Circle Computer Group's DL/2 enables transparent migration from IMS to DB2 without application changes.

### Space & Sensor Technologies
- Space-based optical and sensor technology (ARKA Group)
- Satellite-based missile warning and tracking (SciTec)

### Data Marketplace & Exchange
- **Data marketplaces** generate market evidence for data value through licensing, M&A, data-sharing agreements, and collateral structures.
- **GenAI price signals**: visible prices for rights-cleared content and expert-labeled training data, though contract-specific.

---

## 3. Valuation

### Data as a Strategic Asset
- Proprietary data is driving **deal premiums** and IP strategies across sectors.
- Buyers have paid premiums largely attributed to target's data assets, **even when revenue was minimal**.
- **Twitter acquisition** serves as a cautionary tale: transaction overlooked immense value in user-generated behavioral/engagement data.

### Valuation Frameworks
| Approach | Description | Best For |
|----------|-------------|----------|
| **Cost Approach** | Cost to recreate dataset (time, infrastructure, collection, compliance) | Floor valuation |
| **Income Approach** | Incremental cash flows attributable to data (predictive analytics improving churn/underwriting) | Commercialized datasets |
| **Market Approach** | Benchmarking against recent transactions involving similar datasets | Rare; comparables often confidential |
| **Real Options** | Data as building blocks that unlock choices — value is not intrinsic | Early-stage, strategic flexibility |
| **Shapley-based** | Allocating collaborative contribution among data sources | Data sharing/partnerships |

### Accounting & Recognition
- **ASC 805** governs recognition and measurement of intangible assets in business combinations.
- Data is often absorbed into customer relationships, databases, developed technology, or goodwill rather than reported as a standalone data asset.
- **Three-layer valuation architecture** (Fraunhofer ISST):
  1. Accounting and disclosure (conservative recognition)
  2. Internal management valuation (data asset registers, product P&Ls)
  3. Transaction-based market pricing (AI licensing, data marketplaces, M&A)

### Key Valuation Principles
- Data value is **not intrinsic** — produced by interaction of data, rights, quality, models, workflows, governance, and complementary capabilities.
- **High retention, recurring revenue, embedded workflow usage, and hard-to-replicate data sourcing** are stronger indicators of data value than raw data volume.
- **Data Shapley** may allocate collaborative contribution.
- By 2035, data valuation likely operates across three layers: accounting/disclosure, internal management valuation, and transaction-based market pricing.

---

## 4. Bottlenecks

### Technical Bottlenecks
| Bottleneck | Description | Mitigation |
|------------|-------------|------------|
| **Data gravity** | Slow/expensive to move large datasets across networks | Dual execution engines, query pushdown |
| **Row-store limitations** | OLTP databases inefficient for OLAP; reads all columns | Columnar architecture, vectorized execution |
| **Query folding** | Broken folding forces massive data movement | Careful DAX/M code, source tuning |
| **Filter propagation** | Cross-storage queries kill performance | Dual mode for dimensions, explicit table roles |
| **Data quality** | Poor provenance, completeness, accuracy, bias | Data governance, quality metrics, lineage tracking |
| **Data staleness** | Silent staleness in Import mode | Freshness indicators, DirectQuery for real-time |

### Regulatory & Legal Bottlenecks
| Bottleneck | Description |
|------------|-------------|
| **Export controls (ITAR/EAR)** | Technical data on USML requires State/DDTC license; EAR "600-series" requires BIS authorization; deemed export rules |
| **CFIUS review** | Mandatory filing for TID US businesses (critical tech, critical infrastructure, sensitive personal data); post-FIRRMA "export-based" test |
| **FOCI mitigation** | Foreign ownership requires DCSA review; Board Resolution, SCA, SSA, Proxy or Voting Trust |
| **Cross-border data transfer** | GDPR, privacy laws, purpose limitation, data-subject rights |
| **Personal data as dual-use** | 2024 laws (TikTok ban, Protecting Americans Data from Foreign Adversaries Act), DOJ Bulk Data Regulation |
| **Facility Clearance** | Classified contracts require clearance; foreign ownership introduces FOCI |

### Due Diligence Bottlenecks
- **Disclosure perimeter**: No customer-by-program revenue waterfall, no forward-pipeline composition, executive resumes with gaps.
- **Data room limitations**: Standard late-stage framework reshaped around disclosure assumptions.
- **Data diligence gap**: IT diligence focuses on "T" while ignoring "I" — data assets regularly overlooked.
- **Integration feasibility**: Isolating economic contribution of data from surrounding system is the central valuation problem.

---

## 5. NP-Hard Problems

### Computational Complexity in Data Analytics
- **P vs. NP** remains one of the most important open mathematical problems (Clay Institute Millennium Problem, $1M bounty).
- **NP-complete problems**: Traveling Salesman, Clique, Sudoku, Conjunctive Query Containment (CQC).
- **Implications for ML/AI**: Under the plausible assumption that NP ≠ coNP, **polynomial-time dataset generators cannot be used to train models to solve NP-hard problems**. Any efficient procedure generates biased, unrepresentative datasets of solved instances.

### Practical NP-Hard Problems in Data Domains
| Problem | Domain | Complexity |
|---------|--------|------------|
| Conjunctive Query Containment | Database query optimization | NP-complete |
| Traveling Salesman | Logistics, route optimization | NP-complete |
| Clique detection | Social network analysis, fraud | NP-complete |
| Sudoku (n×n) | Constraint satisfaction | NP-complete |
| Feature selection | Machine learning | NP-hard |
| Optimal data integration | Data merging | NP-hard |

### Implications for Acquisition Targets
- Targets claiming AI/ML solutions to NP-hard problems should be scrutinized for **biased training data** that leads to overestimated model accuracy.
- **Data augmentation techniques** may generate datasets that solve an easier sub-problem, not the true NP-hard problem.
- Due diligence should assess whether the target's computational claims are **theoretically sound** or rely on heuristic approximations.

---

## 6. Citations

### Search 1: Dual Use Data Analytics Acquisition
1. Earnest Analytics Crosses from Credit Cards to Medical Claims — *Startuply VC* — https://startuply.vc/article/earnest-analytics-crosses-from-credit-cards-to-medical-claims-1wh3qn
2. Greystones Group Announces Acquisition of Dual Use Data Analytics Software for AI/ML/NLP — *Greystones Group* — https://greystonesgroup.com/greystones-group-announces-acquisition-of-dual-use-data-analytics-software-for-ai-ml-nlp
3. Global Dual Channel Digital Acquisition Market Research Report — *WiseGuyReports* — https://wiseguyreports.com/reports/dual-channel-digital-acquisition-market

### Search 2: Defense Data M&A
1. Boots off the ground: Defense tech M&A skyrockets in US and Europe — *JD Supra* — https://www.jdsupra.com/legalnews/boots-off-the-ground-defense-tech-m-a-8359102/
2. What the data room can't tell you — *Augment Whitepaper* — https://augment.market/what-the-data-room-cant-tell-you
3. Cross-Border Aerospace & Defense M&A: Navigating U.S. Regulatory Hurdles — *MQR Associati* — https://www.mqrassociati.com/en/14-cross-border-aerospace-defense-ma-navigating-u-s-regulatory-hurdles/

### Search 3: Data Analytics Valuation Defense
1. Valuing Data: Its Impact on M&A and Financial Statements — *Withum* — https://www.withum.com/resources/valuing-data-its-impact-on-ma-and-financial-statements/
2. Data Valuation and Law — *SSRN* — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4549555
3. Quantifying the Intangible – A Practitioner Framework for Enterprise Data Valuation — *Fraunhofer ISST* — https://www.isst.fraunhofer.de/content/dam/isst/publikationen/whitepaper/FhGISST_A%20Practitioner%20Framework%20for%20Enterprise%20Data%20Valuation.pdf

### Search 4: Big Data Acquisition
1. Big Data — *Tracxn* — https://platform.tracxn.com/a/d/company/5cf67d2cb2e199156628a795/big%20data
2. Teradata Continues Big Data Acquisitions with Rainstor — *Database Trends and Applications* — https://www.dbta.com/Editorial/News-Flashes/Teradata-Continues-Big-Data-Acquisitions-with-Rainstor-101219.aspx
3. Syncsort hits the big data acquisition trail — *Precisely* — https://www.precisely.com/press-release/syncsort-hits-the-big-data-acquisition-trail

### Search 5: Data Dual Use Bottlenecks
1. Hybrid Analytics: Query Local & Cloud Data Instantly — *MotherDuck* — https://motherduck.com/learn-more/hybrid-analytics-guide
2. Choosing the Right Power BI Dataset Mode — *powerbi.app* — https://powerbi.app/power-bi-dataset-mode-guide
3. Personal data as a dual-use technology: Privacy professionals face new export controls — *IAPP / Cross Border Data Forum* — https://www.crossborderdataforum.org/iapp-personal-data-as-a-dual-use-technology-privacy-professionals-face-new-export-controls/

### Search 6: Data NP-Hard Problems
1. Fifty Years of P vs. NP and the Possibility of the Impossible — *CACM* — https://cacm.acm.org/research/fifty-years-of-p-vs-np-and-the-possibility-of-the-impossible/
2. CS4104 Data and Algorithm Analysis — *Virginia Tech* — https://opendsa-server.cs.vt.edu/ODSA/Books/pubbook/senalgs/winter-2017/Public_Demonstration/html/NPComplete.html
3. It's Not What Machines Can Learn, It's What We Cannot Teach — *PMLR* — http://proceedings.mlr.press/v119/yehuda20a/yehuda20a.pdf

### Search 7: Data Due Diligence
1. Future of due diligence — *KPMG* — https://assets.kpmg.com/content/dam/kpmgsites/es/pdf/2023/09/future-of-due-diligence.pdf.coredownload.inline.pdf
2. Data & AI due diligence — *DataDiligence* — https://www.datadiligence.com/services/diligence
3. Data Diligence: The Missing Method In M&A Due Diligence — *Forbes* — https://www.forbes.com/sites/douglaslaney/2020/05/01/data-diligence-the-missing-method-in-ma-due-diligence

### Search 8: Data M&A Cross-Border
1. datacross — *Tracxn* — https://platform.tracxn.com/a/d/company/53194d3fe4b0f7e165f59e0e/datacross
2. Cross-border M&A risks and rewards — *Deloitte* — https://www.deloitte.com/us/en/what-we-do/capabilities/mergers/acquisitions/articles/cross-border-m-and-a-risks-rewards.html
3. Eight takeaways: Cross-border M&A investing in Europe — *Clifford Chance* — https://www.cliffordchance.com/insights/thought_leadership/eight-takeaways.html

### Search 9: Data Portfolio Optimization
1. Modern Portfolio Optimization in Practice — *Medium / AxionQuant* — https://medium.com/@axionquant/modern-portfolio-optimization-in-practice-from-theory-to-actionable-insights-891d3ceb1965
2. How to Use Fintech for Investment Portfolio — *ProTraderDaily* — https://protraderdaily.com/fintech/how-to-use-fintech-for-investment-portfolio
3. The Free Portfolio Optimizer That Uses J.P. Morgan Data — *Portfolio Lab* — https://portfoliolab.app/blog/free-portfolio-optimizer-jp-morgan-data

### Search 10: Data Technology Transfer
1. NIH OTT Open Data Initiative — *NIH Technology Transfer* — https://www.techtransfer.nih.gov/nih-ott-open-data-initiative
2. Technology Transfer — *DATAS Technology* — https://www.datas-tech.com/en/transfer-tehnologij
3. Rights in data-technology transfer — *Acquisition.gov (DOE)* — http://www.acquisition.gov/node/62880/printable/pdf

---

## Summary Table

| Dimension | Key Finding | Implication for Acquisition Platform |
|-----------|-------------|--------------------------------------|
| **Market** | Defense tech M&A at record highs ($1.7B in 2025); 3 largest deals all US tech-driven | High demand for data/analytics targets with defense applications |
| **Technology** | AI/ML/NLP platforms, hybrid analytics, space sensors, data marketplaces | Targets with proven COTS-based dual-use platforms command premium |
| **Valuation** | Data valued via cost/income/market/real options; ASC 805 recognition; value is not intrinsic | Must assess rights, quality, governance, and complementary capabilities |
| **Bottlenecks** | Data gravity, export controls (ITAR/EAR), CFIUS, FOCI, cross-border transfer | Regulatory diligence is critical; clean teams and TCPs required |
| **NP-Hard** | ML cannot solve NP-hard problems due to biased sampling (NP ≠ coNP) | Scrutinize AI claims; assess whether solutions are heuristic approximations |
| **Due Diligence** | Data assets regularly overlooked; two-phase readiness + evidence approach | Implement formal data diligence: rights, provenance, quality, integration feasibility |
| **Cross-Border** | US/EU corridor $3.9T + $3.4T; FDI filings, EU FSR, data privacy/AI regulations | Early merger control assessment; country sequencing plan essential |
| **Tech Transfer** | NIH OTT open data; DOE rights-in-data clauses; contractor copyright | Government-funded IP has specific rights and commercialization requirements |
