# Wave 3 Research: Dual-Use Autonomous Systems Acquisitions

**Date:** 2026-10-05  
**Focus:** Dual-use autonomous systems M&A, technology transfer, valuation, bottlenecks, and computational complexity

---

## Market Overview

The dual-use autonomous systems market is experiencing unprecedented M&A activity, driven by defense spending shifts, commercial technology crossover, and AI-enabled capabilities.

### Deal Activity & Volume

| Metric | Value | Source |
|--------|-------|--------|
| Drone/UAS deals in 2025 | 46 transactions | Mergermarket |
| Drone/UAS deals in 2024 | 29 transactions | Mergermarket |
| Drone/UAS deals in 2023 | 20 transactions | Mergermarket |
| Drone deal volume 2025 | $5.2B | Mergermarket |
| Drone deal volume 2024 | $6.2B | Mergermarket |
| Defense Tech M&A (24 months) | 33 deals | NewMarketPitch |
| Defense Tech M&A (recent 12 months) | 22 deals (doubled) | NewMarketPitch |

### Largest Disclosed Deals

| Target | Acquirer | Value | Category |
|--------|----------|-------|----------|
| BlueHalo | AeroVironment | >$1B | Counter-UAS, EW, space |
| Silvus | Motorola | Undisclosed | Secure MANET communications |
| D-Fend Solutions | Motorola | ~$1.5B | RF counter-drone takeover |
| Dzyne Technologies | Ondas Inc. | $876M | Surveillance/recon drones |
| Iveco Defence | Leonardo | Undisclosed | Land systems |
| Edge Autonomy | Redwire | Undisclosed | Autonomous systems |
| SciTec | Firefly | Undisclosed | Defense tech |
| Lanteris | Intuitive Machines | Undisclosed | Space defense |
| Loc Performance | Rheinmetall | Undisclosed | Defense manufacturing |
| Omnisys | Ondas | $196.6M | Battlefield C2 software |

### Market Catalysts

- **US defense budget expansion:** Trump administration proposed $1.5T defense budget (up from $1T)
- **Foreign hardware ban:** December 2025 ban on foreign-made UAS (notably DJI) opened market gap for domestic entrants
- **State/local counter-drone demand:** Federal law enacted December 2025 created framework for state, tribal, local governments to deploy counter-drone technology—potentially larger than federal market
- **Dual-use acquisition strategies:** FY2024 NDAA Section 267 supports commercial technology developers in DoD autonomous programs (Software Acquisition Pathways model)
- **Consolidation phase:** Buyers assembling platforms across drones, counter-drone, C2, secure comms, and mission software

---

## Key Technologies

### Autonomous Driving & Navigation
- **Kodiak Robotics:** Dual-use autonomous driving for trucking and defense; $50M DIU contract for Army RCV program; GPS-challenged environment navigation
- **Shield AI Hivemind:** Autonomy stack operating without GPS, datalink, or human pilot; V-BAT and Nova VTOL drones for contested environments
- **Anduril Lattice:** AI operating system for autonomous warfare; Fury autonomous fighter drone; Barracuda munition family

### Counter-Drone & Airspace Security
- **Dronebuster (Dzyne):** Portable RF-based counter-drone; backpack-carried, radio-wave attack
- **D-Fend Solutions:** RF-based counter-drone takeover (acquired by Motorola for ~$1.5B)
- **Sentrycs:** Cyber-over-RF counter-drone capability (acquired by Ondas)
- **Dedrone:** Counter-drone and airspace-security software (acquired by Axon)

### Robotics AI & Software
- **FieldAI:** Universal AI brain for humanoids, drones, industrial robots; $10B valuation; $135M revenue across 30+ customers
- **Physical Intelligence:** ~$11B valuation; robot software
- **Skild AI:** $14B valuation; robot software
- **Reliable Robotics:** $160M round (April 2026); first FAA-certifiable autonomous aircraft system; 200+ commitments

### Wearable Robotics / Exoskeletons
- **Ekso Bionics:** FDA-cleared EksoNR for stroke, spinal cord injury, brain injury, MS; 375+ rehabilitation centers; 200M+ powered steps
- **Wandercraft:** Atalante X (only self-balancing FDA-cleared exoskeleton); $75M Series D (mid-2025)
- **Wearable Robotics:** ALEx RS (medical) / LBE30 (industrial, 40kg loads); €5M Series A (April 2026)

### Sim-to-Real & Training
- **DARPA Transfer from Imprecise and Abstract Models:** Low-fidelity simulation approach for rapid autonomy transfer; same-day vs. weeks/months; two 18-month phases
- **Aechelon Technology:** High-fidelity simulation for autonomous systems training (acquired by Shield AI)

### AI-Enabled Cybersecurity for AVs
- Generative AI (GANs, VAEs, Diffusion Models) for adversarial attack emulation, anomaly detection, synthetic data generation
- 216 peer-reviewed studies synthesized (2020–2026); critical gaps in scalability, real-time deployment, explainability

---

## Valuation

### Public & Private Company Valuations

| Company | Valuation | Round/Event | Focus |
|---------|-----------|-------------|-------|
| Anduril Industries | ~$61B | Series H ($5B) | Autonomous warfare, Lattice AI |
| Skild AI | $14B | — | Robot software |
| Shield AI | $12.7B | Series G ($1.5B) | Hivemind autonomy stack |
| Physical Intelligence | ~$11B | — | Robot software |
| FieldAI | $10B | Term sheet ($700M) | Universal robot AI brain |
| Ondas Inc. | $4.2B (market cap) | Nasdaq: ONDS | Autonomous drones, counter-drone |

### Valuation Trends

- **Software > Hardware:** Three robot software companies (FieldAI, Physical Intelligence, Skild AI) carry ~$35B combined valuation; software valuations dwarf hardware in American robotics market
- **Fivefold jumps:** FieldAI went from $2B to $10B in just over a year
- **Dual-use discount/premium:** Dual-use platforms (Reliable Robotics, Scout AI, Saildrone, Kelluu) have lower valuations than pure defense tech but more diversified risk profiles; no single customer >30% of revenue provides downside protection
- **Exoskeleton market projections:** $1.79B by 2033 (Grand View Research) to $30B by 2032 (Fortune Business Insights)—disagreement reflects industrial adoption velocity uncertainty

### Acquisition Multiples & Deal Structures

- Strategic-scale transactions now common: buyers acquiring capability, not just teams
- Many strategically central deals have undisclosed values (Anduril/ExoAnalytic, Shield AI/Aechelon, Forterra/goTenna, York/Orbion)
- Ondas building platform via serial acquisition: Dzyne ($876M), Omnisys ($196.6M), plus 6+ undisclosed deals
- Motorola pairing Silvus (comms) + D-Fend (counter-drone) = layered defense platform

---

## Bottlenecks

### Computational Bottlenecks in Autonomous Systems

| Bottleneck | Impact | Source |
|------------|--------|--------|
| Object detection (DET) | Dominates computation; exceeds latency requirements alone | Clemson/Architectural Implications paper |
| Object tracking (TRA) | Second-largest computational burden; DNN-based | Same |
| Localization (LOC) | Third bottleneck; combined with DET+TRA = >94% of computation | Same |
| Multicore CPUs | Not viable for DET and TRA under design constraints | Same |
| FPGA DSPs | Limited number prevents meeting performance constraints | Same |
| Tail latency | Critical for safety-critical autonomous systems | Same |

### Sim-to-Real Gap
- Training models in high-fidelity environments takes **months to years** for DoD platforms
- Autonomy becomes vulnerable in unknown real-world situations
- Military systems face more unknown variables than commercial (adversary behavior, lighting, flight dynamics)
- DARPA theorizes low-fidelity simulations with shared semantics (rules of engagement) can enable same-day transfer

### AI & Cross-Border Bottlenecks

| Bottleneck | Detail |
|------------|--------|
| Data privacy fragmentation | Only 12% of companies feel completely prepared for global data privacy patchwork |
| Model portability | Closed models: restrictive licensing, vendor dependency; Open models: IP exposure, support gaps |
| Workforce readiness | Local teams may lack experience managing model outputs, edge cases, AI governance |
| Regulatory variance | AI agent may be restricted in markets requiring human oversight or explainability |
| Regional architecture fragmentation | Centrally trained models may not be allowed to learn across borders |

### Technology Transfer Bottlenecks
- Data quality and accuracy: AI systems only as good as training data
- System integration complexity
- Need for ongoing human oversight in complex decision-making
- Bureaucratic processes slowing traditional tech transfer
- Limited human experts to review all discoveries

---

## NP-Hard Problems in Autonomous Systems

### Multi-Agent Pathfinding (MAPF)
- **Definition:** Finding collision-free paths for a team of agents on a map
- **Complexity:** NP-hard for makespan or sum-of-cost optimization (Yu and LaValle, 2013); remains NP-hard even for planar graphs and grid-based problems
- **Practical hardness gap:** Real-world MAPF instances often solved quickly by optimal algorithms despite theoretical hardness—discrepancy between theory and practice
- **Research challenges:**
  1. Algorithm selection: determining best-performing algorithm per instance
  2. Instance features: structural properties (phase transition, backbone/backdoor) affecting hardness
  3. Hard instance generation: creating diverse benchmark datasets

### NP-Hard Graph Problems for LLM Training
- **Graph-R1 framework:** NP-hard graph problems as synthetic training corpus for LLM reasoning
- **Properties:** Exponential worst-case complexity forces deep reasoning; absence of polynomial-time solutions fosters extensive exploration
- **Two-stage post-training:** (1) Long CoT SFT on rejection-sampled NPH instances; (2) RL with fine-grained reward design
- **Results:** Graph-R1-7B surpasses QwQ-32B on NPH graph problems in accuracy and reasoning efficiency

### Canonical NP-Hard Problems in Autonomous Systems
- **Traveling Salesman Problem (TSP):** Route optimization for autonomous vehicles and drones
- **SAT/Satisfiability:** Decision-making under constraints
- **Halting Problem:** NP-hard but not computable—relevant to autonomous system verification
- **Busy Beaver, Post's Correspondence Problem:** NP-hard, undecidable

### Implications for Acquisition Targets
- Companies solving NP-hard problems efficiently (approximation algorithms, heuristics) have defensible IP moats
- Algorithm selection as a service: ML-based prediction of best algorithm per instance
- Benchmark generation for autonomous system validation

---

## Due Diligence

### Autonomous Due Diligence Platforms

| Platform | Approach | Pricing | Turnaround |
|----------|----------|---------|------------|
| DueVestor | AI pipeline + 125+ verified sources; sanctions, PEP, adverse media | $79–$990/report | Minutes |
| audt.ai | Autonomous research agents analyzing public/private data | Enterprise | On-demand |
| Reuben AI | AI-native diligence workflow; document parsing, risk surfacing, IC memo generation | Enterprise | Days (vs. weeks) |

### Key Due Diligence Features
- **Source-tier every claim:** Self-reported vs. verified vs. triangulated data
- **Parallel analysis:** Financial, legal, operational, market, team dimensions simultaneously
- **Audit trail:** Provenance captured automatically for LP/regulator inquiries
- **Confidence scoring:** Every finding carries source, timestamp, confidence grade
- **Risk surfacing:** Red flags with severity scoring; critical risks to deal lead within hours

### Agentic AI in M&A (Accenture)
- 650 senior dealmakers surveyed across 12 industries, 24 countries
- 72% expected growth in agentic AI maturity for post-deal integration
- PE firms ahead: designing agentic AI into deal assumptions and post-close value delivery
- 47% say clear human-in-the-lead controls would significantly increase adoption willingness
- PE firms report 1.4x preparedness for human-agent collaboration vs. corporate development teams
- 75% of PE respondents engage external partners for AI capabilities during M&A

---

## Cross-Border M&A

### AI-Enabled Cross-Border Deal Success
- AI applications strengthen internal capabilities and external reputation → market signals → transparency → stakeholder trust → deal completion
- Higher regional marketization levels and CEO duality strengthen AI's positive effect
- Executives with financial backgrounds weaken AI's positive effect (CFOs temper cross-border deals)

### Cross-Border AI Risks (West Monroe)
- **Agent-readiness framework:** Technical portability + Regulatory viability + Workforce readiness
- **Pre-LOI:** Rapid regulatory scan and agent-readiness screen
- **LOI:** Conditions tied to model access and regulatory fit
- **Diligence:** Deep dive on model provenance and workforce readiness
- **Integration:** Explicit migration and adoption plan
- **Deal structure:** Price AI risk, protect against it, or require it to be fixed

### Model Licensing & Portability
| Model Type | Advantages | Risks |
|------------|------------|-------|
| Closed | Speed, performance, IP indemnification | Restrictive licensing, vendor dependency, limited transferability |
| Open/Open-derived | Portable, flexible | Support, liability, performance consistency, IP exposure |

---

## Portfolio Optimization

### Agentic AI Portfolio Construction
- **44 specialized agents** produce capital market assumptions, construct portfolios using **21 competing methods**, critique and vote on outputs
- **Methods range:** Equal-weight, inverse-volatility, mean-variance optimization, risk parity, hierarchical risk parity, Total Portfolio Approach
- **CIO agent** scores, combines, selects from surviving proposals
- **Investment Policy Statement** governs autonomous agents (same document guiding human PMs)

### LLM Portfolio Performance
| Strategy | Sharpe Ratio | Notes |
|----------|-------------|-------|
| LLM-generated (best) | 0.741 | Outperformed naive diversification |
| AI-optimized benchmark | 1.361 | LLMs lag behind explicit optimization |
| Low-turnover LLM | Competitive post-costs | Surpasses cap-weighted benchmarks after transaction costs |

### Multi-Agent Crypto Portfolios
- Crew AI framework with modular agents: data splitter, portfolio metrics, optimizer, rolling optimizer, benchmark comparison, file checker
- Static equal-weight vs. 30-day rolling Sharpe-maximization
- Dynamic optimization achieves significantly better risk-adjusted returns in volatile markets

---

## Technology Transfer

### Autonomous Technology Transfer (Kwintely)
- AI-powered move of scientific discoveries from labs to market without constant human oversight
- **Three key components:**
  1. Intelligent patent and literature mining (NLP analysis of millions of documents)
  2. Automated competitive intelligence and market analysis
  3. AI-powered contract and agreement management
- **Benefits:** Faster identification, comprehensive competitive analysis, streamlined IP/licensing management
- **Challenges:** Data quality, system integration, need for human oversight in complex decisions

### Defense Technology Transfer
- **DRDO ToT Policy (India):** Revised policy for seamless transfer of indigenous defense technologies to industry; automation of internal processes; reduced timelines; supports "Make in India" and "Make for the World"
- **DARPA Sim-to-Real:** Transfer from imprecise and abstract models; low-fidelity simulations for rapid autonomy transfer; same-day vs. weeks/months; two 18-month phases

---

## Citations

1. Mergermarket/ION Analytics. "Drone deals soar as opportunities emerge beyond defense." 2026. https://ionanalytics.com/insights/mergermarket/drone-deals-soar-as-opportunities-emerge-beyond-defense-dealspeak-north-america
2. Orange County Business Journal. "Drone Maker Dzyne Sells for $876M." 2026. https://ocbj.com/defense-2/drone-maker-dzyne-sells-for-876m
3. NewMarketPitch. "Defense Tech M&A: what is happening now?" 2026. https://newmarketpitch.com/blogs/news/defense-tech-ma-tracker
4. Kodiak Robotics/PR Newswire. "U.S. House Supports Dual-Use Acquisition Strategies for Army Autonomous Driving Programs in FY2024 NDAA." July 2023. https://www.prnewswire.com/news-releases/us-house-of-representatives-supports-dual-use-acquisition-strategies-for-army-autonomous-driving-programs-in-the-fy-2024-national-defense-authorization-act-ndaa-301878896.html
5. IDA. "Acquisition Challenges of Autonomous Systems." 2018. https://www.ida.org/research-and-publications/publications/all/a/ac/acquisition-challenges-of-autonomous-systems-conference-paper
6. Springer. "Mitigating cyberattacks on autonomous vehicles: Generative AI defense techniques." 2026. https://doi.org/10.1007/s10462-026-11636-0
7. Nexi Fund. "Defense Procurement Reform Is Reshaping the Robotics Market." 2026. https://nexi.fund/procurement-reform-robotics-dual-use-2026
8. Nexi Fund. "Exoskeletons Go Both Ways: The Dual-Use Wearable Robotics Market in 2026." 2026. https://nexi.fund/exoskeleton-dual-use-wearable-robotics-2026
9. The Outpost. "FieldAI Secures $700M at $10B Valuation as Robot Software Outpaces Hardware Investments." 2026. https://theoutpost.ai/news-story/fieldai-secures-700m-at-10b-valuation-as-robot-software-outpaces-hardware-investments-31668
10. IEEE. "Demystifying Power and Performance Bottlenecks in Autonomous Driving Systems." IISWC 2020. https://www.computer.org/csdl/proceedings-article/iiswc/2020/764500a205/1oSXQxxrhSg
11. Clemson University. "The Architectural Implications of Autonomous Driving." https://people.computing.clemson.edu/~jmarty/projects/lowLatencyNetworking/papers/EmergingApplicationSystems/AutonomousVehicles/AutonomousCarConstraints.pdf
12. arXiv. "Graph-R1: Unleashing LLM Reasoning with NP-Hard Graph Problems." 2025. https://arxiv.org/html/2508.20373v1
13. arXiv. "Empirical Hardness in Multi-Agent Pathfinding." 2025. https://arxiv.org/html/2512.10078v1
14. Preprints.org. "From P =? NP to Practice: Description Complexity and Certificate-First Automated Discovery." 2025. https://preprints.org/manuscript/202509.2038
15. DueVestor. "The autonomous due diligence platform." 2026. https://duevestor.com/en
16. audt.ai. "Intelligence and due diligence as a service." 2026. https://www.audt.ai/private-sector
17. Reuben AI. "Due Diligence Automation for Private Capital." 2026. https://www.goreuben.com/due-diligence-automation
18. Accenture. "The Dawn of the Agentic Deal Report." 2026. https://www.accenture.com/content/dam/accenture/final/accenture-com/document-fy26/q3/Accenture-The-dawn-of-the-agentic-deal.pdf
19. West Monroe. "When AI Doesn't Travel: The Hidden Risks in Cross-Border M&A." 2026. https://www.westmonroe.com/insights/the-hidden-risks-in-cross-border-m-and-a
20. RePEc. "Financial expertise vs. AI momentum: Why CFOs temper cross-border deals." 2025. https://ideas.repec.org/a/eee/finlet/v86y2025ipbs1544612325016915.html
21. arXiv. "Self_Driving_Portfolio: Agentic AI for strategic asset allocation." 2026. https://arxiv.org/pdf/2604.02279
22. MDPI. "Few-Shot Portfolio Optimization: Can LLMs Outperform Quantitative Portfolio Optimization?" 2025. https://mdpi.com/1911-8074/19/5/320
23. arXiv. "Building crypto portfolios with agentic AI." 2025. https://arxiv.org/pdf/2507.20468v1
24. Kwintely. "What is Autonomous Technology Transfer?" 2026. https://kwintely.com/articles/what-is-autonomous-technology-transfer
25. DRDO. "DRDO Policy for Transfer of Technology." 2025. https://www.drdo.gov.in/drdo/sites/default/files/inline-files/DRDOToTPolicy04022025.pdf
26. DARPA. "Transfer from Imprecise and Abstract Models to Autonomous Technologies." 2026. https://www.darpa.mil/research/programs/transfer-from-imprecise

---

## Summary Table

| Dimension | Key Finding | Implication for Acquisition Strategy |
|-----------|-------------|--------------------------------------|
| Market | 46 drone deals in 2025; $5.2B volume; 33 defense tech deals in 24 months | Market in consolidation phase; platform strategies emerging |
| Technology | Counter-drone hottest category; software > hardware valuations; sim-to-real gap persists | Acquire software/IP layers, not just hardware |
| Valuation | Anduril $61B; robot software ~$35B combined; fivefold jumps possible | Software targets command premium; dual-use discount exists |
| Bottlenecks | DET+TRA+LOC = 94% computation; sim-to-real gap; cross-border AI regulation | Targets solving bottlenecks have defensible moats |
| NP-Hard | MAPF NP-hard; NP-hard graph problems for LLM training; algorithm selection | Efficient solvers = valuable IP; benchmark generation opportunity |
| Due Diligence | Autonomous DD platforms deliver 30–100x cost reduction; minutes vs. weeks | AI-native diligence is competitive advantage |
| Cross-Border | Only 12% prepared for data privacy patchwork; agent-readiness framework | Structure deals around AI portability and regulatory risk |
| Portfolio | 44-agent pipeline; 21 methods; LLM Sharpe 0.741 vs AI-optimized 1.361 | Agentic AI augments but doesn't replace optimization |
| Tech Transfer | AI-powered lab-to-market; DRDO ToT; DARPA sim-to-real | Autonomous tech transfer accelerates commercialization |
