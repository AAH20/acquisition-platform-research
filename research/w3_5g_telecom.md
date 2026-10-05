# Wave 3 Research: Dual-Use 5G & Telecommunications Acquisitions

**Date:** 2026-10-05  
**Agent:** Wave 1 Research Subagent  
**Focus:** Dual-use 5G and telecommunications technology acquisitions

---

## Market Overview

The dual-use 5G and telecommunications M&A landscape is shaped by three converging forces: national security imperatives, vendor consolidation, and cross-border regulatory shifts.

**Defense & Government Investment:** The U.S. DoD announced $600M in awards for 5G experimentation at five military installations (Hill AFB, JBLM, MCLB Albany, Naval Base San Diego, Nellis AFB), representing the largest full-scale dual-use 5G tests globally. Projects span AR/VR training, smart warehousing, distributed C2, and dynamic spectrum sharing. Industry partners include AT&T, Samsung (via GBL), Nokia, Ericsson, GE Research, and Booz Allen Hamilton. This signals sustained government demand for dual-use 5G capabilities and creates acquisition targets in the defense-telecom supply chain.

**Vendor Concentration & Open RAN Reality:** The RAN market remains highly concentrated — top five suppliers held 96% of the 1Q25–3Q25 market (up from 95% in 2024), with HHI above 2,500 in five of six tracked regions. Open RAN revenues are approaching $10B cumulatively but declined ~40% within two years of the initial Japan/US scaling wave before returning to growth in 2Q25. Dell'Oro projects multi-vendor RAN at only $2–3B by 2029. The AT&T/Ericsson ~$14B open RAN deal (Dec 2023) is the largest in history but remains near-single-vendor in practice. EchoStar's spectrum sales ($23B to AT&T, $17B to SpaceX) and conversion to a hybrid MNO represent a cautionary tale — balance sheet and distribution, not RAN architecture, decided outcomes.

**Cross-Border M&A Trends:** Cross-border M&A has declined from ~50% of global deal value at its 2007 peak to ~30% today. Intra-regional deals outperform: average two-year rTSR of +1.2% for intra-regional vs. -0.9% for domestic and +0.6% for inter-regional. The EU is actively encouraging cross-border telecom consolidation, with Internal Market Commissioner Thierry Breton pushing for a single European telecoms market. The European Commission has eased its insistence on four-player markets and launched a public consultation on connectivity infrastructure funding, including potential contributions from big tech for 5G/fiber deployment.

**Technology Transfer & Geopolitics:** In Latin America, Huawei has gained market share through price competition and direct government engagement, while Ericsson and Nokia maintain long-standing partnerships. The U.S. has lobbied Brazil and Chile to exclude Chinese providers without much success. DFARS 252.204-7018 prohibits acquisition of covered defense telecommunications equipment from Huawei, ZTE, and entities connected to China or Russia for covered missions (nuclear deterrence, homeland defense).

---

## Key Technologies

| Technology | Description | Acquisition Relevance |
|------------|-------------|----------------------|
| **Open RAN (O-RAN)** | Disaggregated RAN with open fronthaul interfaces (7.2x split), RIC (RAN Intelligent Controller), rApps/xApps/dApps | Nokia pivoting to Nvidia GPU-based AI-RAN; Ericsson/Samsung resistant to xApps; dApps emerging via E3 interface |
| **5G Standalone (SA)** | Full 5G Core (5GC) with service-based architecture, network slicing, VoNR, edge computing | 5G SA median download 269.51 Mbps vs. 177.37 Mbps for NSA (52% premium); 63.6% of global core network software spending |
| **Network Slicing** | Virtual network embedding (VNE) — mapping virtual requests to physical infrastructure | NP-hard optimization problem; meta-heuristic solutions required |
| **Massive MIMO & Beamforming** | Multi-antenna systems for spatial multiplexing and interference management | Core 5G infrastructure; Nokia/Ericsson/Samsung differentiation |
| **mmWave & Mid-Band Spectrum** | High-frequency (24–40 GHz) for ultra-high speed; mid-band (1–6 GHz) for coverage/capacity balance | Spectrum assets are primary M&A valuation drivers |
| **Integrated Sensing & Communication (ISAC)** | Dual-use cellular infrastructure for environmental sensing without dedicated LiDAR/radar | Samsung/LG Uplus field testing Q3-Q4 2026; ITU-R designated as 6G scenario |
| **Dynamic Spectrum Sharing (DSS)** | Coexistence between 5G and radar/other systems in shared bands (e.g., 3.1–3.45 GHz) | DoD testbeds at Hill AFB; Key Bridge Wireless, Shared Spectrum Company |
| **AI-RAN** | GPU-based RAN processing (Nvidia Aerial/CUDA platform) | Nokia's strategic bet; 19 initial deployment signups; portability concerns |
| **Edge Computing & UPF Placement** | User plane function topology optimization for latency reduction | Critical for enterprise/private 5G networks |
| **5G Advanced (3GPP Rel 18/19)** | AI-native radio resource management, Sub-band Full Duplex, Uplink Multi-TRP, Dynamic Tx Switching | Optimization phase of 5G; new service delivery models |

---

## Valuation

### Multiples & Benchmarks

| Metric | Value | Source |
|--------|-------|--------|
| 5G Networks Ltd (ASX:5GN) Market Cap | $16.37M AUD | SmallCaps.com.au |
| 5GN Price/Sales (ttm) | 0.40 | Yahoo Finance |
| 5GN Price/Book (mrq) | 0.79 | Yahoo Finance |
| 5GN Enterprise Value/Revenue | 0.32 | Yahoo Finance |
| 5GN 52-week return | -56.9% | SmallCaps.com.au |
| Open RAN cumulative revenue | ~$10B | Dell'Oro |
| Open RAN revenue decline | ~40% within 2 years of peak | Dell'Oro |
| Multi-vendor RAN projection (2029) | $2–3B | Dell'Oro |
| AT&T/Ericsson open RAN deal | ~$14B (5-year estimate) | Ericsson/AT&T |
| EchoStar spectrum sale to AT&T | ~$23B | SEC 8-K |
| EchoStar spectrum sale to SpaceX | ~$17B | SEC 8-K |
| TPG Telecom/Vocus fibre deal | $6.3B | iTnews |
| RAN market spending | $35B (2025, down from $45B in 2022) | Omdia |
| 5G core software spending growth | 63.6% of global core network function software | Ookla/Omdia |

### Valuation Considerations for 5G Acquisitions

- **Spectrum assets** are the primary value driver — EchoStar's $40B spectrum sales demonstrate the premium for licensed spectrum
- **Vendor concentration** creates scarcity value for independent RAN software/app developers
- **Open RAN option value** — openness delivers procurement leverage and credible swap threats, not necessarily multi-supplier patchwork
- **Balance sheet strength** differentiates greenfield survivors (Rakuten) from those that fold (EchoStar)
- **Cross-border premium** — intra-regional deals outperform domestic by ~2.1 percentage points in 2-year rTSR
- **Technology transfer risk** — geopolitical considerations (DFARS, EU single market) can restrict eligible buyers

---

## Bottlenecks

### Technical Bottlenecks

1. **NSA Dual-Connectivity Drain:** Non-standalone 5G requires simultaneous 4G/5G connections, increasing battery drain 25–40% and causing throughput lower than 4G in some conditions. SA 5G can deliver up to 3 hours more battery endurance.

2. **mmWave Propagation Loss:** High-frequency signals (24–40 GHz) cannot penetrate walls, windows, or heavy rain. Signal strength drops from -85 dBm outdoors to -115 dBm indoors. Range limited to <1,000 feet vs. 4G's 10-mile range.

3. **Spectrum Fragmentation:** Carriers divided 5G into low-band (<1 GHz, barely faster than 4G), mid-band (1–6 GHz, limited deployment), and mmWave (24–40 GHz, tiny coverage). Constant handoffs between bands cause dropped calls and frozen connections.

4. **Flow Control in Split Bearers:** PDCP must divide traffic between two legs with unobservable capacity. Badly tuned flow control produces throughput noticeably lower than the better leg alone.

5. **Open RAN Integration Burden:** The integration cost is the line everyone underestimates and the reason incumbents keep winning on "speed." AT&T's first open RAN call with third-party radios happened ~20 months after signing the Ericsson deal.

6. **Vendor Lock-in via GPU RAN:** Nokia's Nvidia GPU-based strategy creates CUDA-native lock-in — apps cannot migrate to other hardware types. Ericsson and Samsung are not pursuing GPU RAN.

7. **xApp/dApp Immaturity:** rApps shipped commercially (AT&T, Rakuten), but xApps have no observable progress and dApps are "as complicated as brain surgery" per Cohere CEO.

### Market & Regulatory Bottlenecks

8. **EU Market Fragmentation:** Sub-optimised business models based on national markets and high spectrum licence costs hold back collective potential vs. US/Asian peers.

9. **Cross-Border Deal Decline:** Cross-border M&A at ~30% of global deal value vs. 50% peak in 2007. Intra-regional deals outperform but remain underutilized.

10. **Supply Chain Security:** DFARS 252.204-7018 prohibits covered defense telecommunications equipment from Huawei/ZTE/China/Russia-connected entities for covered missions, restricting the supplier base.

11. **Capital Intensity:** 5G deployment requires enormous investment in spectrum, cell sites, transmission, network core, and support systems. Carrier return on investment is dropping.

12. **Technology Transfer Restrictions:** Geopolitical tensions limit cross-border technology transfer, particularly between US-aligned and China-aligned markets.

---

## NP-Hard Problems in 5G

| Problem | Complexity | Description | Relevance to Acquisitions |
|---------|-----------|-------------|--------------------------|
| **NOMA Resource Allocation** | Strongly NP-Hard | Optimal joint subcarrier and power allocation in Non-Orthogonal Multiple Access for weighted generalized means (sum-rate, proportional fairness, harmonic mean, max-min fairness) | Affects spectral efficiency claims in vendor evaluation |
| **Virtual Network Embedding (VNE)** | NP-Hard | Mapping virtual network requests to physical infrastructure for network slicing | Core 5G slicing capability; meta-heuristic solutions required |
| **ILP/MILP Resource Allocation** | NP-Hard | Integer and mixed-integer programming for 5G/B5G resource allocation | Solver scalability limits (Gurobi/CPLEX); approximation algorithms needed |
| **Infill-Site Prioritization** | Submodular (greedy (1-1/e) guarantee) | Brownfield 5G expansion site selection under demand, coverage, and engineering constraints | ARGO-5G algorithm; portfolio optimization for network buildout |
| **User Plane Function Placement** | NP-Hard | Optimal UPF topology for latency minimization in SA networks | Differentiates operator performance; edge computing strategy |
| **Spectrum Sharing/Coexistence** | NP-Hard | Dynamic spectrum access between 5G and radar/other systems | DoD coexistence testbeds; Key Bridge Wireless, Shared Spectrum Company |
| **Beam Management Optimization** | NP-Hard | AI-driven beam prediction and management for energy efficiency | 5G Advanced feature; AI-native RAN differentiator |
| **Multi-Objective Network Optimization** | NP-Hard | Joint optimization of coverage, capacity, latency, energy, and cost | Network planning and acquisition target evaluation |

**Implications for Acquisitions:**
- Companies with proprietary optimization algorithms (e.g., Cohere's USM for spectral efficiency) have defensible IP
- NP-hard problems create barriers to entry and justify premium valuations for optimization software
- Meta-heuristic and AI/ML-based solution approaches are active R&D areas with acquisition potential
- Portfolio optimization for network buildout (site selection, spectrum allocation) is a distinct software opportunity

---

## Citations

1. **DoD 5G Experimentation:** "DOD Announces $600 Million for 5G Experimentation and Testing at Five Installations." defense.gov, 2023. https://defense.gov/News/Releases/Release/article/2376743/

2. **Samsung-LG ISAC Partnership:** "Telecom Networks Cross Into Sensing as Samsung-LG Validate ISAC." The Meridiem, May 2026. https://themeridiem.com/trends/2026/5/29/telecom-networks-cross-into-sensing-as-samsung-lg-validate-isac

3. **Nokia Open RAN / AI-RAN Strategy:** "Nokia puts new open RAN tech in 5G revival bid as Ericsson demurs." Light Reading, September 2026. https://lightreading.com/open-ran/nokia-puts-new-open-ran-tech-in-5g-revival-bid-as-ericsson-demurs

4. **Open RAN Market Reality:** "Open RAN in Practice: The 2026 Deployment, Market, and TCO Reality Check." 5G/6G Academy, July 2026. https://5g6gacademy.com/learn/open-ran-in-practice

5. **EU Cross-Border Telecom M&A:** "EU actively encourages cross-border telecoms M&A." Telecoms.com, 2026. https://www.telecoms.com/5g-6g/eu-actively-encourages-cross-border-telecoms-m-a

6. **Cross-Border M&A Performance:** "Capturing the Value of Cross-Border Deals." BCG, 2025. https://www.bcg.com/publications/2025/capturing-the-value-of-cross-border-deals

7. **NOMA NP-Hardness Proof:** "Optimal Joint Subcarrier and Power Allocation in NOMA is Strongly NP-Hard." arXiv:1910.01331, 2019. https://arxiv.org/pdf/1910.01331

8. **5G Resource Allocation Survey:** "A Comprehensive Survey of Linear, Integer, and Mixed-Integer Programming Approaches for Optimizing Resource Allocation in 5G and Beyond Networks." arXiv:2502.15585, 2025. https://arxiv.org/html/2502.15585v1

9. **Network Slicing VNE Meta-Heuristics:** "Application of Meta-Heuristics in 5G Network Slicing." PMC/NIH, 2022. https://pmc.ncbi.nlm.nih.gov/articles/PMC9505386

10. **5G Infill-Site Portfolio Optimization:** "Leakage-Aware 5G Infill-Site Prioritization via Robust Submodular Portfolio Optimization." Research Square, 2025. https://researchsquare.com/article/rs-10814441/v1.pdf

11. **5G SA & Advanced Report:** "5G SA and 5G Advanced 2026 Report." Ookla/Omdia, February 2026. https://ookla.com/s/media/2026/02/ookla_omdia-5GSA_2026_a.pdf

12. **5G Technology Evolution Review:** "The Evolution of Mobile Communications: A Review about 5G Technologies and Future Directions." JOCM, 2025. https://jocm.us/2025/JCM-V20N2-199.pdf

13. **Dual Connectivity Technical Analysis:** "Dual Connectivity: EN-DC, Bearer Types, and Talking to Two Nodes at Once." 5G/6G Lab, 2026. https://5g6glab.com/articles/dual-connectivity-explained

14. **5G Real-World Performance Issues:** "Why Does 5G Suck? The Truth Behind the Hype." Of Zen and Computing, August 2026. https://ofzenandcomputing.com/why-does-5g-suck-the-truth-behind-the-hype

15. **TPG Telecom/Vocus Due Diligence:** "TPG Telecom extends due diligence period with Vocus." iTnews, 2026. https://www.itnews.com.au/news/tpg-telecom-extends-due-diligence-period-with-vocus-599954

16. **Telecom M&A Due Diligence Guide:** "Telecom M&A Transactions." Holland & Knight, August 2025. https://www.hklaw.com/-/media/files/insights/publications/2025/08/balestrieri_practicalguidance_telecommna.pdf

17. **DFARS Telecom Equipment Prohibition:** "48 CFR § 252.204-7018 - Prohibition on the Acquisition of Covered Defense Telecommunications Equipment or Services." Cornell LII, 2023. https://www.law.cornell.edu/cfr/text/48/252.204-7018

18. **5G Networks Ltd Valuation Data:** "5G Networks Limited (5GN.AX) Stock Price, News, Quote & History." Yahoo Finance, 2026. https://finance.yahoo.com/quote/5GN.AX

19. **5G Architecture SA vs NSA:** "5G Now." TechYorker, 2026. https://techyorker.com/5g-now

20. **Technology Transfer in Latin America:** "Technology Transfer to Latin American Countries; Drifting Away from the United States and China?" OAPEN Library, 2024. https://library.oapen.org/bitstream/handle/20.500.12657/99202/9781003489450_10.4324_9781003489450-11.pdf

21. **EU 5G Cross-Border Corridors:** "Deploying European 5G cross-border corridors." European Commission Digital Strategy, 2026. https://digital-strategy.ec.europa.eu/en/policies/cross-border-corridors

22. **5G NSA Battery Drain (India):** "Your Phone Shows 5G But Feels Slower Than 4G." TamilTech, 2026. https://tamiltech.in/article/5g-slowing-phone-battery-jio-airtel-india-fix-4g-lte-better-2026

23. **Navy/DoW/CISA 5G Implementation:** "Inside the Navy, DoW and CISA's Approaches to Implementing 5G for Mission-Critical Operation." Government Technology Insider, 2026. https://governmenttechnologyinsider.com/inside-the-navy-dow-and-cisas-approaches-to-implementing-5g-for-mission-critical-operation

24. **Open RAN LFN Integration:** "Open RAN Unites: LFN Integration Completes the Open Source 5G Stack." Brief Glance, April 2026. https://briefglance.com/articles/open-ran-unites-lfn-integration-completes-the-open-source-5g-stack

25. **Telecom Advisory Due Diligence Services:** "Investment due Diligence." Telecom Advisory Services, 2021. https://www.teleadvs.com/investment-due-diligence

---

## Summary Table

| Dimension | Key Finding | Acquisition Implication |
|-----------|-------------|------------------------|
| **Market Size** | RAN market $35B (2025); Open RAN ~$10B cumulative; 5G core software 63.6% of core spend | Large addressable market but declining RAN spend; software growing |
| **Vendor Concentration** | Top 5 hold 96% RAN share; HHI >2,500 in 5/6 regions | Scarcity value for independent vendors; antitrust risk for consolidation |
| **Cross-Border** | ~30% of global deal value; intra-regional +1.2% rTSR | EU pushing cross-border consolidation; regulatory tailwind |
| **Valuation** | Spectrum assets command premiums ($23B-$17B EchoStar sales); P/S ~0.4x for small caps | Spectrum-rich targets command strategic premiums |
| **NP-Hard Problems** | NOMA, VNE, ILP/MILP, UPF placement, beam management | Optimization software is defensible IP and acquisition target |
| **Bottlenecks** | NSA battery drain, mmWave propagation, integration burden, vendor lock-in | Technical due diligence must assess SA roadmap and integration costs |
| **Geopolitics** | DFARS prohibits China/Russia telecom for defense; EU single market push | Cross-border deals face national security screening; eligible buyer pools restricted |
| **Technology Transfer** | Huawei price competition in Latin America; US lobbying without success | Emerging market acquisitions face geopolitical complexity |
| **Open RAN Reality** | Interfaces universal but multi-vendor mixing rare; $2-3B by 2029 | Open RAN software/app layer is the real opportunity, not hardware |
| **ISAC/Sensing** | Samsung/LG field testing Q3-Q4 2026; ITU-R 6G scenario | Dual-use sensing creates new market category; early-stage acquisition timing |
