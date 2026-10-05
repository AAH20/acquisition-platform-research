# Wave 3 Research: Dual-Use Software & Cloud Technology Acquisitions

## Market Overview

The dual-use software and cloud technology acquisition market is experiencing unprecedented acceleration driven by geopolitical tensions, digital sovereignty imperatives, and the boundary between commercial and defense technology dissolving. Defense tech M&A has accelerated since 2022, with rising defense spending across the US, UK, and EU, the post-Ukraine reset in NATO procurement, and a wave of strategic interest from the primes widening the buyer set materially [1]. US defense sector deal volume rose 20% year-on-year to 18 transactions in 2025, while value nearly tripled to US$4.6 billion from US$1.7 billion. Venture capital investment in defense tech reached a record US$49.9 billion in 2025, up 83% on the prior year [3].

The federal government's push to modernize IT has spurred M&A activity in cloud services, with more than 60 transactions executed at a combined enterprise value of over $34 billion and an average EV/EBITDA multiple of 11.6x [2]. Key strategic acquirers include Lockheed Martin, RTX, Northrop Grumman, General Dynamics, BAE Systems, Leonardo, and L3Harris, with Anduril and Palantir active as acquirers in autonomy and software-defined warfare [1].

Europe has surpassed the US in total defense deal volume in 2025, with transactions rising 85% year-on-year to 24, while value more than doubled to US$1.3 billion [3]. The Pentagon's fiscal year 2027 budget proposal includes US$54.6 billion for the Defense Autonomous Warfare Group alone—a more than 24,000% increase on the prior year's allocation [3].

## Key Technologies

**Dual-Use Software & Algorithms**: Dual-use technology refers to hardware, software, materials, scientific research, or algorithmic models developed primarily for civilian and commercial markets that inherently possess direct, highly lethal, or strategic military and intelligence applications [4]. Key operational mechanisms include Commercial Off-The-Shelf (COTS) Acquisition, Technological Symbiosis (Spin-On), and Venture Capital Integration (e.g., In-Q-Tel) [4].

**Cloud Infrastructure & Classified Cloud**: The Joint Warfighting Cloud Capability (JWCC) was awarded in December 2022 to four hyperscale cloud service providers: AWS, Google, Microsoft, and Oracle, with a contract ceiling of $9 billion over 10 years [5]. JWCC provides cloud computing, storage, and related services at three classification levels: Unclassified, Secret, and Top Secret (IL2–IL6) [5]. The JWCC Unified Cloud Marketplace (UCM) is being restructured into three tiers: Tier 1 (hyperscale core), Tier 2 (XaaS), and Tier 3 (commercial innovators) [6].

**AI & Autonomous Systems**: AI-powered systems for border, airspace, and infrastructure security, autonomous platforms, radar integrations, and counter-drone interceptors are key acquisition targets [1]. The Software Protection Index extends existing notions of potency and resilience by evaluating protection effectiveness against attack paths using software metrics [7].

**Zero-Trust Architecture**: NATO's Protected Business Network contract (€200M over 7 years) with Accenture and Leonardo implements zero-trust architecture using AI-driven cyber defense platforms [8].

**Edge Computing & DDIL**: Cloud frameworks emphasize operations in denied, degraded, intermittent, and limited-bandwidth (DDIL) environments, along with edge computing capabilities such as man-portable and vehicle-mounted systems [6].

## Valuation

**Defense Tech Multiples**: Recent defense tech acquisitions have shown varied multiples: Ultra Maritime acquired by Lockheed Martin at $3.5B (4.4x), Arka Group by CACI at $2.6B (4.0x), D-Fend Solutions by Motorola at $1.5B (15x), and DZYNE Technologies by Ondas at $876M (4.6x) [1]. The $33B acquisition of AES by BlackRock was the largest DefenseTech M&A transaction completed in the last year [1].

**SaaS & Software Multiples**: US-headquartered SaaS businesses traded at a mean 2.4x ARR premium over comparable European targets with matched growth, retention, and margins in 2025-2026. For UK targets, the premium relative to Europe was 0.7-1.1x ARR [9]. Median revenue multiples in European software M&A tracked at 4.1x trailing-12-month revenue [10].

**Cloud Services Valuation**: The federal IT services sector has seen an average EV/EBITDA multiple of 11.6x [2]. Cloud adoption could generate $3 trillion in EBITDA value by 2030 [11]. Key valuation drivers include capabilities, contract and customer access, position in the cloud ecosystem, business model, and percentage of revenue from the 8(a) Business Development Program [2].

**Cross-Border Considerations**: Foreign takeovers accounted for 86% of UK M&A by value in H1 2026, up from 75% the previous year. AI positioning is now the central valuation variable: 72% of SaaS transactions involved explicit AI positioning, and one in five strategic buyers walked away from a deal on AI obsolescence risk [10].

## Bottlenecks

**Regulatory & Export Control**: ITAR, EAR, FOCI, and CFIUS overlays shape which counterparts can actually close given the company's clearance, technology-control, and ownership profile [1]. Cross-border deals face three perimeters: regulatory (FDI national-security screening), data (data residency constraints), and mechanics (locked-box pricing, W&I insurance, works-council consultation) [12]. The UK's NSIA has 17 mandatory sectors at a 25% threshold with no deal-value floor; CFIUS has mandatory triggers; Australia screens from $0 [12].

**Integration Challenges**: Cross-border SaaS integration typically realises 55-75% of projected synergies within 24 months (compared with 70-90% for domestic). The gap is concentrated in product synergies constrained by data residency and regulatory compliance, and cost synergies constrained by national employment law [9].

**Technical Debt & Architecture**: Software due diligence must address technical debt, legacy or on-premise technology, and unresolved migration liability. High client concentration, key-person and founder dependency, and exposure to AI-led commoditisation of the core product are significant discount factors [10].

**Cloud Portfolio Complexity**: By 2026, the average organization uses over 200 SaaS apps, runs multiple public cloud accounts, and juggles complex hybrid setups. 20-30% of total cloud spend is "waste" (idle or overprovisioned resources) [13]. One in three cloud migrations fail due to inadequate planning [13].

**Supply Chain & Traceability**: Dual-use strategy requires defense-specific cybersecurity specifications, Controlled Goods program requirements, quality certifications, risk mitigation strategies, supply chain traceability, an intellectual property strategy, and a secure and stable delivery capacity [14].

## NP-Hard Problems

**Network Security Hardening**: Finding the optimal attack plan in an attack graph is an NP-hard problem [15]. The game-theoretic model of network hardening using honeypots presents a computational challenge where finding the best response of the attacker is NP-hard. Solution methods translate attack graphs into MDPs and solve them using policy search with pruning techniques [15].

**Software Protection Selection**: Automated selection of software protections to mitigate Machine-At-The-End risks involves a game-theoretic model where the defender strategically applies protections to code artifacts. The selection of the optimal defense maximizes resistance to attacks while ensuring the application remains usable—a problem solved through heuristic mini-max depth-first exploration with dynamic programming optimizations [7].

**Attack-Defense Tree Analysis**: Synthesizing optimal cost defense solutions using MaxSMT for attack-defense trees (ADTrees) is computationally intensive. The problem involves translating ADTrees into logical formulas and solving minimization queries to find defenses that mitigate all possible attacks with minimal cost [16].

**Cloud Resource Allocation**: Cloud portfolio optimization involves allocating applications to instances across time slots while minimizing costs—a problem approached with greedy algorithms (ERICH) and genetic algorithms (GEORG) [17]. The problem is characterized by binary assignment variables, preemptibility constraints, resource demand, and QoS parameters.

**Workload Placement Optimization**: Cloud 2.0 optimization requires workload-first placement matrices using workload economics, technical requirements, security constraints, and risk profiles to identify where each application belongs—a multi-objective optimization problem across cloud native, cloud hosted, and modern on-premise alternatives [13].

## Citations

[1] Flow Partners. "M&A advisory for DefenseTech companies." https://flowpartners.io/ma-advisory/defense-tech

[2] William Blair. "Federal Government's Push to Modernize IT Will Spur M&A Activity in Cloud Services." https://www.williamblair.com/-/media/Downloads/Insights/IB-Market-Assets/2020/Government-Services-June-2020.pdf

[3] JD Supra. "Boots off the ground: Defense tech M&A skyrockets in US and Europe." https://www.jdsupra.com/legalnews/boots-off-the-ground-defense-tech-m-a-8359102/

[4] Intelligence Notes. "Dual-Use Technology." https://intelligencenotes.com/02-Concepts--and--Tactics/24-Technology--and--AI/Dual-Use-Technology

[5] LandOffset. "JWCC Unified Cloud Marketplace (UCM): Pentagon's Next-Generation Cloud Acquisition Framework." https://landoffset.com/t/jwcc-unified-cloud-marketplace-ucm-pentagons-next-generation-cloud-acquisition-framework/293

[6] CloudFront. "DISA Rebrands JWCC Next as Unified Cloud Marketplace." https://d3f5buclv39urb.cloudfront.net/articles/disa-rebrands-jwcc-next-as-unified-cloud-marketplace

[7] Computers and Security. "Automatic selection of protections to mitigate risks against software applications." https://dl.acm.org/doi/10.1016/j.cose.2026.104959

[8] Sentinel. "NATO Signs 200M-Euro Cloud Deal With Accenture." https://sentinel.ht/nato-accenture-protected-business-network-cloud

[9] Masynergy. "Cross-Border SaaS M&A: Europe-US-UK Deal Tactics 2026." https://masynergy.eu/blog/saas-cross-border-ma

[10] CapEQ. "UK & European ERP Software M&A Report 2026." https://capeq.com/market-intelligence/uk-european-erp-software-ma-report-2026

[11] McKinsey. "$3 trillion is up for grabs in the cloud." https://www.mckinsey.com/capabilities/tech-and-ai/our-insights/projecting-the-global-value-of-cloud-3-trillion-is-up-for-grabs-for-companies-that-go-beyond-adoption

[12] Peony. "Cross-Border M&A in 2026: A Field Guide for Your First Deal Abroad." https://peony.ink/blog/cross-border-ma-guide

[13] Kearney. "Cloud 2.0: from migration to optimization." https://kearney.com/service/digital-analytics/article/cloud-2.0-from-migration-to-optimization

[14] BDC. "What is dual use?" https://bdc.ca/en/articles-tools/entrepreneur-toolkit/templates-business-guides/glossary/dual-use

[15] Kiekintveld, C. et al. "Optimal Network Security Hardening Using Attack Graph Games." https://www.cs.utep.edu/kiekintveld/papers/2015/klbp_attack_graphs.pdf

[16] Springer. "Attack–defense tree-based analysis and optimal defense synthesis for system design." https://link.springer.com/article/10.1007/s11334-024-00556-3

[17] Moonlight. "A Cloud Resources Portfolio Optimization Business Model – From Theory to Practice." https://themoonlight.io/fr/review/a-cloud-resources-portfolio-optimization-business-model-from-theory-to-practice

[18] OECD. "Due diligence essentials for responsible software." https://www.oecd.org/content/dam/oecd/en/publications/reports/2025/07/responsible-business-conduct-spotlights_f7f722d0/due-diligence-essentials-for-responsible-software_ccf3dbbb/75b921f0-en.pdf

[19] Deloitte. "Software Due Diligence." https://www.deloitte.com/de/de/services/consulting-financial-services/software-due-diligence.html

[20] NASA NTRS. "Software engineering technology transfer: Understanding the process." https://ntrs.nasa.gov/citations/19940031995

[21] ACM. "Technology transfer macro-process: a practical guide for the effective introduction of technology." https://dl.acm.org/doi/10.1145/337180.337470

[22] IRISA. "Co-Evolutionary Service-Oriented Model of Technology Transfer in Software Engineering." https://www.irisa.fr/lande/lande/icse-proceedings/tt/p3.pdf

[23] ONES. "Cloud Portfolio Management: A Strategic Framework for 2026." https://ones.com/blog/cloud-portfolio-management-a-strategic-framework-for-2026

[24] Startup Fundraising. "Defense Software & Mission Autonomy Fundraising Guide (2026)." https://startupfundraising.com/defense-software-fundraising

[25] Morgan Stanley. "Valuing the Public Cloud - Taking a Workload View." https://cdn.geekwire.com/wp-content/uploads/2018/06/Weiss_Business_Final_V2.pdf
