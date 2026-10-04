# Crunchbase Data Quality & Coverage — Wave 1 Research

**Date:** 2026-10-04  
**Agent:** Wave 1 Research Agent  
**Focus:** Crunchbase data quality, coverage gaps, entity resolution, freshness, validation, bottlenecks

---

## Executive Summary

Crunchbase is the de facto database for startup and private-company data, tracking ~4.7M+ private companies, 600,000+ funding rounds, and an investor graph used as ground truth by VCs, founders, and analysts. However, its data quality is structurally uneven: broad and deep for venture-backed technology companies, but thin for non-tech industries, pre-seed/seed stages, and non-US geographies. The platform relies on a hybrid model of community contributions, AI/ML validation, and a dedicated data team, but user reviews consistently flag stale records, missing fields, and duplicate entries. Entity resolution remains a significant challenge — exact name matching achieves only ~58% join rates against CRM data, requiring fuzzy matching (WRatio ≥ 90) to reach 100%. Freshness is a known weakness: CSV exports go stale immediately, and the platform's refresh cadence lags behind real-time funding events. The enterprise API (starting ~$2,000–$49,000/year) creates a data-access bottleneck that pushes teams toward scraping (legally risky) or bulk datasets from resellers.

---

## 1. Data Quality Metrics

| Metric | Value / Finding | Source |
|--------|----------------|--------|
| Companies tracked | ~4.7M+ private companies | PitchBook comparison; Bright Data dataset |
| Funding rounds | 600,000+ | AgentHustler dev.to article |
| Data updates per year | 30M+ (vendor claim) | Market Intelligence Tools review |
| Founder coverage | 59% (self-reported) | "More than Crunchbase" PDF |
| Funding prediction precision | 95% (internal backtesting) | GlobeNewswire press release, Feb 2025 |
| Funding prediction recall | 99% (internal backtesting) | GlobeNewswire press release, Feb 2025 |
| Growth prediction accuracy | 81% of growing companies | Crunchbase blog (PitchBook vs Crunchbase) |
| Acquisition prediction | 70% recall, 90% precision | Crunchbase blog |
| IPO prediction | 60% recall, 74% precision | Crunchbase blog |
| Quarterly data refresh rate | 25.3% QoQ | Crunchbase blog |
| Early-stage coverage advantage | 16% more than PitchBook (US), 31% more (Asia) | Crunchbase blog |
| User-reported accuracy complaints | "Considerable amount of errors" (Capterra, G2) | Market Intelligence Tools review |
| Exact name join rate (Crunchbase → CRM) | 58.3% (56/96) | Entity resolution guide (differ.blog) |
| Fuzzy join rate (WRatio ≥ 90) | 100% (96/96) | Entity resolution guide |

**Key Insight:** Crunchbase's internal metrics (95% precision, 99% recall on funding predictions) are vendor-reported and not independently verified. User reviews on G2 and Capterra consistently report data accuracy issues, with one UK commercial director rating the platform 3.0/5 and noting "the data is only as good as the last time it was updated."

---

## 2. Coverage Gaps

### 2.1 Industry Coverage
- **Strong:** Venture-backed technology companies, SaaS, FinTech, AI, robotics, cybersecurity
- **Weak:** Music and entertainment, non-tech industries, traditional sectors
- **Quote:** "Abundant for tech startups but lacking for other industries especially music and entertainment" — G2 reviewer (Verified User, Entertainment, Mid-Market, March 2026)

### 2.2 Geographic Coverage
- **Strong:** United States (headquarters concentration)
- **Moderate:** Europe (11% more early-stage than PitchBook)
- **Growing:** Asia (31% more early-stage than PitchBook)
- **Weak:** Emerging markets, non-English-speaking regions

### 2.3 Stage Coverage
- **Strong:** Series A through growth stage
- **Weak:** Pre-seed, seed, angel stage (though Crunchbase claims 16% more early-stage coverage than PitchBook)
- **Missing:** Bootstrapped companies, companies that never raised venture funding

### 2.4 Data Type Coverage
| Data Type | Coverage Level | Notes |
|-----------|---------------|-------|
| Funding rounds | Strong | Amount, investors, valuation where reported |
| Acquisitions/M&A | Moderate | Tied to company profiles |
| Leadership changes | Moderate | Executive and founder moves logged |
| LP/fund data | Weak | Not available; PitchBook dominates |
| Fund performance | Weak | Not available; PitchBook has 164k funds |
| Public company financials | Weak | Limited coverage; PitchBook integrates Morningstar |
| Contact data (email/phone) | Weak | "I would love to have access to people's email or phone like ZoomInfo" — G2 review |
| Competitor data | Moderate | Listed on profiles but shallow |
| Private company financials | Weak | Only disclosed funding rounds; no revenue/EBITDA |

### 2.5 Structural Coverage Limitations
- **SEC filing dependency:** "The only requirement for disclosure of funds raised is to state either the range of revenues, or range of value of assets… This results in the vast majority of information collected by Crunchbase end up either being collected by the few people that put actual info into Form D or self reporting." — Reddit r/Entrepreneur commenter
- **Survivorship bias:** Only companies that closed rounds are visible; failed companies and those that never raised are underrepresented
- **Self-reporting bias:** 3,500+ investment firms submit updates, but they have "a clear incentive to provide the kind of information they want to have publicized"

---

## 3. Entity Resolution

### 3.1 The Core Problem
Entity resolution — matching records that describe the same real-world entity across different systems — is a significant challenge with Crunchbase data. The same company appears under different names across Crunchbase, CRMs, and other databases.

### 3.2 Join Rate Analysis
| Matching Method | Join Rate | Source |
|----------------|-----------|--------|
| Exact (normalized string) | 58.3% (56/96) | differ.blog entity resolution guide |
| Fuzzy (WRatio ≥ 90) | 100% (96/96) | differ.blog entity resolution guide |
| CRM → Crunchbase exact | 34.8% (48/138) | differ.blog |
| CRM → Crunchbase fuzzy | 100% (138/138) | differ.blog |

### 3.3 Common Name Variants
| Crunchbase Name | CRM Variant | Drift Type |
|-----------------|-------------|------------|
| Necker FinTech | Necker FinTech Holdings Inc. | Legal suffix + spacing |
| PANTA | PANTA Group | Type descriptor appended |
| Physical Intelligence | Physical Intelligence (Pi), Inc. | Parenthetical + legal suffix |
| PointsKash | Points Kash | Token spacing |
| qBotica | q Botica | Token spacing |
| Investing.com | Fusion Media Limited | Brand vs. legal name (WRatio 30.0) |

### 3.4 Resolution Strategies
1. **Fuzzy matching (RapidFuzz WRatio):** Primary method for stylistic drift; threshold 90 recommended
2. **Lookup tables / enrichment APIs:** For brand vs. legal name (e.g., GLEIF, Clearbit, domain)
3. **ML record linkage (Dedupe, Splink):** For large-scale probabilistic linkage with many fields
4. **Domain-based matching:** Join on domain, never on company name alone
5. **Canonical ID assignment:** Collapse variants to a single canonical cluster with aliases

### 3.5 Crunchbase's Internal Approach
Crunchbase uses "400+ algorithms validating, deduping, and scoring data daily" across five sourcing types, including 5.2 billion derived intelligence signals, 1.9 billion behavioral data points, and 1.1 billion third-party records. The platform's `cb_expert_resolve_entity` tool disambiguates entity names against the Crunchbase catalog, with domain lookup taking precedence over name matching.

---

## 4. Freshness

### 4.1 Refresh Cadence
| Data Type | Refresh Frequency | Source |
|-----------|-------------------|--------|
| Company profiles | Weekly to monthly | Web scraping guides |
| Funding rounds | Post-announcement (0 weeks lead time) | GitDealflow comparison |
| CSV exports | Frozen at download time | CUFinder blog |
| Legacy CSV export | Daily (morning) | Crunchbase developer docs |
| Quarterly data refresh | 25.3% QoQ | Crunchbase blog |
| PitchBook comparison | 12.4% QoQ | Crunchbase blog |

### 4.2 Freshness Complaints
- **G2 review (Nov 2024):** "The data is only as good as the last time it was updated and you can never be quite sure when that was. So many details might be missing."
- **Capterra review (Apr 2022):** "There are considerable amount of errors in the details that is populated as a result likelihood of time getting wasted going behind wrong details is inevitable."
- **CSV staleness:** "A funding round that closed last month is one of the strongest buying signals in B2B. A six-month-old CSV hides it." — CUFinder blog
- **Dataset refresh:** Pre-collected datasets refresh monthly, quarterly, or biannually; a dataset bought on the 3rd can be weeks behind on a round announced on the 1st

### 4.3 Lead Time Comparison
- **Crunchbase:** 0 weeks (post-announcement) — records events after they happen
- **PitchBook:** Post-announcement
- **Both are lagging indicators:** Neither provides leading signals; investors wanting to catch companies before they raise should pair with a leading-signal tool

### 4.4 Crunchbase's Freshness Advantage
Crunchbase claims to surface 4.9x more companies globally within three months of their raise (11.6x over six months) compared to PitchBook, and refreshes data 25.3% quarter-over-quarter — more than double PitchBook's 12.4% growth rate.

---

## 5. Validation

### 5.1 Crunchbase's Validation Pipeline
Crunchbase employs a multi-layered validation approach:

1. **AI/ML Validation:** Machine learning algorithms continuously validate data accuracy, scan for anomalies, flag potential conflicts, and alert the data science team
2. **Manual Data Curation:** A dedicated data team manually validates, curates, and analyzes information from various sources
3. **Community Contribution Verification:** Multi-step verification process for user-submitted data, involving automated checks and manual review
4. **Investor Network Validation:** 3,700+ global investment firms submit monthly portfolio updates, providing firsthand access to current information
5. **User Feedback Loop:** Users can flag incorrect data and submit updates for review

### 5.2 Validation Gaps
- **Self-reported data bias:** Much of the data is volunteered by users or acquired through publicly available sources, "which may be carefully curated to tell a certain story"
- **Inconsistent quality:** "Data quality varies by company" — PitchBook comparison
- **Outdated entries:** "Outdated entries are a known issue" — PitchBook comparison
- **Missing fields:** "A missing field is not permission to invent one" — CrunchbaseUS.com editorial standard
- **No independent audit:** Validation is primarily internal; no third-party data quality certification

### 5.3 Validation Tools
- **Crunchbase Scout AI Assistant:** Available on Pro (limited) and Business (full) tiers
- **Predictions & Insights:** Business tier only; includes funding, growth, acquisition, IPO, remain private, layoffs, and closures predictions
- **Heat Score:** Built from activity across an 80M-person network
- **400+ algorithms:** Validating, deduping, and scoring data daily

---

## 6. Bottlenecks

### 6.1 Data Access Bottlenecks
| Access Method | Cost | Limitations |
|---------------|------|-------------|
| Free tier | $0 | Search only, no export |
| Pro | $99/mo ($49/mo annual) | 2,000 export rows/month, limited AI |
| Business | $199/mo+ | 5,000 export rows/month |
| Enterprise API | ~$2,000–$49,000/year | Annual contract, custom quote |
| Data Enrichment API | Custom quote | Sold through sales team |
| Data Licensing | Custom quote | Sold through sales team |

### 6.2 Technical Bottlenecks
- **Login wall:** Most interesting data (funding round details, investor lists, key employees, acquisition history, competitor data) requires an authenticated session
- **Heavy JavaScript frontend:** Single-page React-style application with asynchronous data loading; eliminates 90% of naive scraping approaches
- **Anti-bot stack:** Cloudflare bot management, behavioral fingerprinting, request rate analysis, aggressive IP reputation scoring
- **No developer tier:** The free API that existed from 2012–2022 is gone; legacy API keys have been rotated out
- **Rate limits:** ~10 requests/min per IP before Turnstile challenges; datacenter IPs blocked almost every request

### 6.3 Data Quality Bottlenecks
- **Community contribution model:** Fast and broad at the funding-announcement layer, but data quality varies by company
- **Self-reporting bias:** Investment firms have incentives to control their public narrative
- **SEC filing dependency:** Most data comes from Form D filings or self-reporting, creating structural gaps
- **Non-tech coverage:** Thin coverage outside venture-backed technology
- **Contact data thinness:** No email/phone data; requires separate enrichment step

### 6.4 Export Bottlenecks
- **CSV export caps:** 2,000 rows/month (Pro), 5,000 rows/month (Business)
- **Legacy CSV export:** Marked "Legacy as of July 2024"; requires Enterprise or Applications Access
- **No live connection:** CSV exports are frozen at download time; no updates, no ping when a company raises
- **Redistribution restrictions:** Data cannot be redistributed to third parties

---

## 7. NP-Hard Problems

### 7.1 Entity Resolution as NP-Hard
Entity resolution (record linkage) is a well-known NP-hard problem in computer science. The core challenge — determining whether two records refer to the same real-world entity — has no known polynomial-time solution for the general case.

**Why it's NP-Hard:**
- **Combinatorial explosion:** Comparing N records against M records requires O(N×M) comparisons
- **Fuzzy matching complexity:** String similarity metrics (edit distance, token-based, phonetic) add computational overhead
- **No single correct answer:** Threshold selection (e.g., WRatio ≥ 90) involves trade-offs between precision and recall
- **Context dependence:** The "correct" match depends on context, use case, and risk tolerance

**Practical Implications:**
- Exact matching is fast but achieves only ~58% join rates
- Fuzzy matching improves to 100% but requires careful threshold tuning
- ML-based record linkage (Dedupe, Splink) scales better but requires training data
- Domain-based matching is most reliable but not always available

### 7.2 Data Deduplication at Scale
Deduplicating Crunchbase's 4.7M+ company records against external datasets (CRMs, other databases) is computationally expensive:
- **Pairwise comparison:** O(n²) complexity for naive approaches
- **Blocking strategies:** Required to reduce comparison space (e.g., blocking on domain, location, industry)
- **Canonical entity selection:** Choosing the "best" representative from a cluster of duplicates involves subjective judgment

### 7.3 Data Freshness vs. Cost Trade-off
Maintaining real-time freshness across millions of records is an optimization problem:
- **Refresh frequency:** More frequent refreshes = higher costs but better accuracy
- **Selective refresh:** Prioritizing high-value records (recently active, high-traffic) requires predictive modeling
- **Event-driven updates:** Detecting and propagating changes in real-time is architecturally complex

### 7.4 Coverage vs. Depth Trade-off
Crunchbase faces a fundamental trade-off:
- **Broad coverage:** Track more companies with less depth per company
- **Deep coverage:** Track fewer companies with more comprehensive data
- **Current approach:** Deep for venture-backed tech, thin elsewhere — creating structural blind spots

---

## 8. Citations

### Primary Sources
1. **PitchBook vs Crunchbase 2026** — PitchBook official comparison page (pitchbook.com/compare/pitchbook-vs-crunchbase)
2. **PitchBook vs. Crunchbase: Which Is Right for You?** — Crunchbase blog (about.crunchbase.com/blog/pitchbook-vs-crunchbase)
3. **Crunchbase Declares Historical Data Dead** — GlobeNewswire press release, Feb 19, 2025
4. **Crunchbase Data Difference** — Crunchbase about page (web.archive.org)
5. **Crunchbase review** — Market Intelligence Tools (marketintelligencetools.com/reviews/crunchbase)
6. **Crunchbase Data in 2026: Why It's Hard to Get** — AgentHustler, dev.to
7. **How to Scrape Crunchbase in 2026** — Bright Data blog
8. **A Practical Guide To Entity Resolution in Python** — differ.blog / dev.to
9. **Crunchbase Export Leads: How to Clean the List** — DoWhatMatter.com
10. **Crunchbase Data Coverage | Evidence and Limits** — CrunchbaseUS.com
11. **More than Crunchbase V1** — PDF report (website-files.com)
12. **Crunchbase vs PitchBook (2026)** — GitDealflow.com
13. **Crunchbase CSV Export Alternative** — CUFinder.io blog
14. **How Does Crunchbase Get Its Data?** — Bardeen.ai
15. **Crunchbase Data Without the Enterprise API** — Web Data Labs
16. **Crunchbase Wikipedia** — de.wikipedia.org/wiki/Crunchbase
17. **Crunchbase Tool Reference** — data.crunchbase.com/docs/tool-reference
18. **Crunchbase Scraper in 2026** — webscraping.cc
19. **3 ways to scrape Crunchbase** — RoundProxies.com
20. **Cloudingo vs Crunchbase Pro** — Crozdesk.com

### User Review Sources
- G2 reviews (multiple, 2024–2026)
- Capterra reviews (2022)
- Reddit r/Entrepreneur discussions

---

## 9. Summary Table

| Dimension | Status | Key Finding |
|-----------|--------|-------------|
| **Data Quality** | ⚠️ Mixed | 95% precision (vendor-reported); user complaints of errors and staleness |
| **Coverage** | ⚠️ Uneven | Deep for venture-backed tech; thin for non-tech, non-US, pre-seed |
| **Entity Resolution** | ❌ Challenging | 58% exact match rate; requires fuzzy matching (WRatio ≥ 90) for 100% |
| **Freshness** | ⚠️ Lagging | Post-announcement recording; CSV exports stale immediately |
| **Validation** | ⚠️ Internal only | AI/ML + human team; no independent audit; self-reporting bias |
| **Bottlenecks** | ❌ Significant | Enterprise API pricing, anti-bot stack, export caps, login walls |
| **NP-Hard Problems** | 🔴 Present | Entity resolution, deduplication at scale, freshness optimization |
| **Overall Assessment** | ⚠️ Usable with caveats | Best-in-class for venture-backed tech; requires enrichment for contact data, non-tech coverage, and real-time signals |

---

## 10. Recommendations for Acquisition Platform

1. **Do not rely solely on Crunchbase** for company intelligence; supplement with PitchBook (for LP/fund data), ZoomInfo (for contact data), and industry-specific databases
2. **Implement fuzzy entity resolution** (WRatio ≥ 90) when joining Crunchbase data to internal CRMs; exact matching will miss ~42% of matches
3. **Budget for enterprise API access** (~$2,000–$49,000/year) if programmatic access is required; the free tier is insufficient for production use
4. **Plan for data decay:** Refresh Crunchbase-sourced data at least monthly; funding data has a half-life measured in days
5. **Validate critical fields independently** before making investment or outreach decisions; Crunchbase's self-reported data has known biases
6. **Consider bulk datasets from resellers** (Bright Data, Apify) for market-wide coverage at lower cost per record ($0.0025–$0.70/record)
7. **Address survivorship bias** by supplementing with data on bootstrapped and failed companies from other sources
