# Wave 3 Research: Dual-Use Air & Aircraft Technology Acquisitions

**Date:** 2026-10-05  
**Scope:** Dual-use aircraft technology M&A, valuation, bottlenecks, NP-hard problems, due diligence, cross-border transactions, portfolio optimization, and technology transfer.

---

## Market Overview

The aerospace & defense (A&D) sector is experiencing a structural M&A upcycle driven by record backlogs, defense budget expansion, European rearmament, and production bottlenecks. Key dynamics:

- **Backlog & Demand:** The top five A&D primes ended FY2025 with **$1.36 trillion** in combined backlog, up 23.7% YoY. European rearmament and US defense funding through 2029 provide multi-year visibility.
- **Deal Activity:** H1 2026 A&D deal activity is tracking toward an approximately **$32 billion** full-year pace. Q1 2026 saw a 37% YoY increase in M&A volume totaling $47.1B in disclosed EV.
- **Valuation Multiples:** 2025 ADGS M&A averaged **3.0x EV/Revenue** and **11.4x EV/EBITDA**. Q1 2026 EBITDA multiples contracted to 9.5x while revenue multiples expanded to 4.8x, signaling demand for subscription-based and early-stage technology assets.
- **Portfolio Clarity:** Legacy complexity is being penalized; software-first, dual-use, space, autonomy, counter-UAS, missile defense, and MRO assets attract premium multiples. Carve-outs by RTX, L3Harris, and Boeing are accelerating.
- **Cross-Border Catalyst:** European rearmament is creating durable cross-border M&A opportunities. US buyers target Europe's fragmented supplier base; European primes access US capabilities. Export controls (ITAR), FOCI, and national security reviews are central diligence issues.
- **Dual-Use as Center of Gravity:** JetZero, Joby Aviation, and Mach Industries argue the future of US air dominance runs through dual-use aviation. DiamondStream Partners applies four filters for deep-tech aviation: demand, tech difficulty, access to experience, and capital availability.

---

## Key Technologies

| Technology | Dual-Use Application | Acquisition Relevance |
|---|---|---|
| **eVTOL / Autonomous VTOL** | Commercial air taxi + defense logistics, attack | Joby Aviation acquired Resonant Sciences ($500M) for RF/sensor tech; Anduril + Archer unveiled Thunder autonomous VTOL platform |
| **Hybrid-Electric Propulsion** | Commercial efficiency + military range/endurance | Joby's turbine-hybrid VTOL with L3Harris; liquid-hydrogen fuel cell variant (500+ mile range) |
| **RF Sensing / Electronic Warfare** | Commercial sensor fusion + contested/denied environments | Resonant Sciences RF suite; Honeywell acquired CAES Systems ($1.9B) for RF/EW |
| **Unmanned Aerial Systems (UAS)** | Commercial inspection/logistics + defense ISR | AeroVironment acquired BlueHalo ($4.1B); Mobix Labs acquired Vision Aerial |
| **Counter-UAS** | Critical infrastructure protection + military base defense | Premium multiples; active M&A interest |
| **Software-Defined Defense / Autonomy** | Commercial autonomy stack + military autonomous collaborative platforms | DoD Replicator initiative driving demand |
| **Advanced Materials (CFRP, etc.)** | Commercial weight reduction + military performance | Airbus A350 uses ~53% carbon-fiber-reinforced polymer |
| **MRO / Sustainment** | Commercial fleet sustainment + military readiness | Active PE-backed roll-ups; capacity scarcity drives valuations |

---

## Valuation

- **A&D Multiples (2025):** 3.0x EV/Revenue, 11.4x EV/EBITDA (Capstone Partners ADGS report).
- **Q1 2026 Shift:** EBITDA multiples contracted ~2 turns to 9.5x; revenue multiples expanded to 4.8x — reflecting demand for early-stage technology and subscription models.
- **Aircraft Asset Values:** Widebody lease rates and market values increased >5% in 2026, supported by persistent shortages. Narrowbody lease rates eased from peak but values remain stable. Supply constraints dominate valuations.
- **Engine Scarcity:** Installed engines on new-generation narrowbody aircraft may generate greater economic returns than the aircraft themselves through engine leasing.
- **SpaceX IPO Effect:** Accelerating repricing of A&D around software-enabled, dual-use, and space-based capability; driving dual-track (IPO + M&A) activity.
- **Premium Valuations:** Driven by credible synergy underwriting, clear standalone operating models, and portfolio clarity. Carve-outs require supply chain separation planning and early identification of regulatory/ITAR/national security requirements.

---

## Bottlenecks

| Bottleneck | Description | M&A Implication |
|---|---|---|
| **Engine Production** | Pratt & Whitney bottleneck affecting Airbus A320neo deliveries; limited ability to scale advanced propulsion capacity | Vertical integration and capacity acquisitions are practical fixes |
| **Aircraft Deliveries** | Persistent delays across narrowbody and widebody programs | Supply chain capacity becomes deal thesis |
| **MRO Capacity** | Maintenance, repair, and overhaul backlogs limit fleet availability | PE-backed roll-ups of Tier 2/3 suppliers; distressed acquisitions of qualified facilities |
| **Tier 2/3 Supplier Fragmentation** | Qualified capacity remains scarce across specialized manufacturing | Roll-ups and technology deals to improve throughput |
| **Export Controls / ITAR** | International Traffic in Arms Regulations restrict cross-border technology transfer | Central to diligence and integration planning; FOCI mitigation required |
| **Certification "Slow Zone"** | Long, capital-intensive march from prototype to certified product | Defense revenue as bridge financing; dual-use platforms built modular from the start |
| **Capital Controls** | Sovereign nations can freeze large FX outflows (e.g., Turkish lira case) | Escrow structuring, purchase agreement language addressing sovereign financial regulation delays |
| **Title & Lien Complexity** | Cross-border aircraft have multi-jurisdictional registration, financing, and operation | FAA Registry search necessary but not sufficient; International Registry + jurisdiction-specific searches required |

---

## NP-Hard Problems

Aircraft operations and logistics involve several computationally intractable problems relevant to acquisition due diligence and operational optimization:

| Problem | Complexity | Source |
|---|---|---|
| **Aircraft Routing Problem (ARP)** | NP-hard (reduction from 3-dimensional matching); NP-complete for finite-horizon with fixed γ ≥ 4 | arXiv:2508.05532; IEEE (2006) |
| **Aircraft Landing Problem (ALP)** | NP-hard | Prakash et al. (2018) |
| **Aircraft Take-off Problem (ATP)** | NP-hard | Prakash et al. (2018) |
| **Aircraft Scheduling Problem (ASP)** | NP-hard | Prakash et al. (2018) |
| **Runway Scheduling Problem (RSP)** | NP-hard; exact methods do not scale with number of aircraft | ScienceDirect survey |
| **Fleet Planning Under Stochastic Demand** | NP-hard combinatorial optimization; portfolio-based approaches yield robust fleet composition | RePEc/Elsevier (2020) |

**Implication for Acquirers:** Target companies with proprietary optimization algorithms, heuristic solvers, or LP-relaxation approaches for these problems represent valuable IP assets. Due diligence should assess computational capabilities in fleet management, scheduling, and routing.

---

## Due Diligence Considerations

### Regulatory & Compliance
- **ITAR / Export Controls:** Technologies with defense applications subject to specific requirements even where primary market is civilian. Early consideration of regulatory exposure essential.
- **FOCI (Foreign Ownership, Control, or Influence):** National security reviews central to cross-border deals.
- **Sanctions:** Enhanced diligence on beneficial ownership history; verify no connections to sanctioned entities. Flight tracking data may reveal operational history.
- **Wassenaar Arrangement:** Multilateral export control framework; consensus-based, making rapid control action difficult.

### Technical Records
- **Aircraft Technical Records Audit:** Three levels — Level 1 (sampling), Level 2 (comprehensive review of available data), Level 3 (verification of all hard copy and electronic records).
- **Key Records:** CofA, CofR, W&B, owner/operator history, power-by-the-hour status, maintenance projections, major modification status, damage history, MRO work reports.

### Cross-Border Specific
- **Title Chain:** Full FAA registry title chain examination going back to manufacture; International Registry search by airframe and engine serial numbers; jurisdiction-specific supplemental searches.
- **Capital Controls:** Diligence on buyer must extend to the financial system they operate within.
- **Escrow & Title Sequencing:** IATS (Insured Aircraft Title Service) escrow; bill of sale sequencing critical.

### IP & Technology
- **IP Ownership:** Clear identification of IP including trade secrets; contractual arrangements for modifications/improvements.
- **Technology Transfer History:** Assess prior technology transfer agreements, offset arrangements, and licensing dependencies.

---

## Citations

1. Aerospace America / AIAA — "Future of U.S. Airpower Rests on Dual-Use Innovation" (AIAA AVIATION Forum 2026)
2. CRM Today — "Joby Aviation builds out defense business with $500M acquisition" (Resonant Sciences)
3. Voxel Matters — "Anduril and Archer unveil autonomous VTOL platform built for defense and commercial use" (Farnborough 2026)
4. PwC — "Aerospace and defense: US Deals 2026 midyear outlook"
5. Cresa — "M&A Activity in the Aerospace & Defense Industry" (July 2025)
6. Capstone Partners — "Aerospace & Defense M&A Update" (ADGS Industry Report)
7. IBA — "Future Technology Aircraft and Engines – Valuation Considerations"
8. ISTAT — "What's Driving Aircraft Values Today?" (Farnborough Airshow 2026)
9. GAO — "Unmanned Aerial Vehicles: DOD's Acquisition Efforts" (T-NSIAD-97-138)
10. CRS — "The U.S. Army's Small Uncrewed Aircraft Systems" (IF12668)
11. CNAS — "Dual-Use Technology and U.S. Export Controls"
12. Defence Finance Monitor — "Engine Bottlenecks and European Propulsion Sovereignty"
13. Gowling WLG — "What dual-use technologies mean for the aviation, aerospace and defence sector"
14. arXiv:2508.05532 — "Aircraft routing: periodicity and complexity"
15. IEEE — "Solving the aircraft routing problem using network flow algorithms"
16. ScienceDirect — "The aircraft runway scheduling problem: A survey"
17. NBAA — "Ukraine Crisis Places Renewed Emphasis on Due Diligence in Aircraft Transactions"
18. W5 Aviation — "Aircraft Technical Records Audit"
19. MyVIP Aviation — "International Aircraft Transactions: Capital Controls, Escrow, and the Bill of Sale Sequence"
20. Guibert Law — "Aircraft Title and Lien Searches in Cross-Border Transactions"
21. ICAO — "Cross Border Transfers (XBT) of Aircraft"
22. Aerlytix — "Aircraft Portfolio Management Software"
23. RePEc/Elsevier — "Portfolio-based airline fleet planning under stochastic demand"
24. Acumen Aero — "Fleet Management and Aircraft Acquisition"
25. ScienceDirect — "Developing countries and the aircraft industry: match or mismatch?" (technology transfer)
