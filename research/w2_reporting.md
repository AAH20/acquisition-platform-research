# Wave 2: Output Formatting & Reporting Gaps Analysis

**Project:** acquisition-platform-research  
**Package:** `src/acquisition_platform/`  
**Modules analyzed:** All 9 Python files (8 algorithm modules + `__init__.py`)  
**Date:** 2026-10-04  

---

## 1. Module-by-Module Output Type Analysis

### 1.1 `matching.py` — Buyer-Seller Matching

**Output type:** `list[Match]` where `Match` is a dataclass:
```python
@dataclass
class Match:
    buyer_id: str
    seller_id: str
    score: float
    confidence: float
```

**User-friendliness:** ❌ **Poor**
- Raw float scores (0.0–1.0) with no interpretation layer
- No human-readable match quality label (e.g., "Strong Match", "Weak Match")
- No formatted currency or percentage output
- No explanation of WHY a match was made
- No summary statistics (e.g., "3 of 5 buyers matched, avg confidence 0.72")
- `score` and `confidence` are opaque floats — a score of 0.2 means nothing to a business user

**Missing:**
- `__str__` / `__repr__` with business context
- Match quality tier (strong/moderate/weak)
- Formatted summary report
- Match explanation/reasoning

---

### 1.2 `valuation.py` — Valuation Engine

**Output type:** `ValuationResult` dataclass:
```python
@dataclass
class ValuationResult:
    value: float
    method: str
    confidence: float
    low_estimate: float
    high_estimate: float
```

**User-friendliness:** ❌ **Poor**
- Raw float `value` with no currency formatting (e.g., `$1,234,567`)
- `confidence` is a bare float (0.0–1.0) — no label like "High Confidence" or "Low Confidence"
- `low_estimate` / `high_estimate` are raw floats — no formatted range string
- No comparison to asking price or market benchmarks
- No risk-adjusted context
- `method` is a string ("DCF", "Comps", "Ensemble", "SDE", "ARR") but no description of what each method means
- No valuation report with assumptions, sensitivity analysis, or scenario breakdown

**Missing:**
- Currency formatting (`$1.2M`, `$1,234,567`)
- Confidence label (High/Medium/Low)
- Formatted valuation range (`$1.0M – $1.4M`)
- Method description/explanation
- Valuation report with assumptions and sensitivity
- Comparison vs. asking price (premium/discount %)

---

### 1.3 `fraud_detection.py` — Fraud Detection

**Output types:** `FraudScore` and `GraphAnalysis` dataclasses:
```python
@dataclass
class FraudScore:
    score: float
    risk_level: str
    confidence: float
    explanations: list[str]

@dataclass
class GraphAnalysis(FraudScore):
    has_ring: bool
    risk_score: float
```

**User-friendliness:** ⚠️ **Partial**
- ✅ `risk_level` is a string ("low"/"medium"/"high") — this IS user-friendly
- ✅ `explanations` provides human-readable strings
- ❌ `score` is a raw float (0.0–1.0) — no percentage or label
- ❌ `confidence` is a raw float — no label
- ❌ `GraphAnalysis` has both `score` and `risk_score` which is confusing (redundant fields)
- ❌ No fraud report summarizing all signals
- ❌ No recommended action (e.g., "Block listing", "Request verification", "Approve with caution")
- ❌ No fraud risk dashboard data

**Missing:**
- Percentage formatting for scores
- Confidence label
- Recommended action based on risk level
- Consolidated fraud report
- Signal breakdown visualization data

---

### 1.4 `portfolio_optimizer.py` — Portfolio Optimization

**Output type:** `Portfolio` dataclass:
```python
@dataclass
class Portfolio:
    assets: list[Asset]
    expected_return: float
    sharpe_ratio: float
```

**User-friendliness:** ❌ **Poor**
- `expected_return` is a raw float (0.12) — no percentage format ("12%")
- `sharpe_ratio` is a raw float — no interpretation ("Good", "Excellent")
- No total portfolio value/cost
- No sector allocation breakdown
- No risk assessment summary
- No diversification metrics
- No comparison to benchmark

**Missing:**
- Percentage formatting for returns
- Sharpe ratio interpretation label
- Total portfolio cost
- Sector allocation breakdown
- Risk-adjusted performance summary
- Portfolio report with allocation pie chart data

---

### 1.5 `dynamic_pricing.py` — Dynamic Pricing

**Output type:** `PriceRecommendation` dataclass:
```python
@dataclass
class PriceRecommendation:
    recommended_price: float
    confidence: float
    floor_price: float
    ceiling_price: float
    equilibrium_price: float
```

**User-friendliness:** ❌ **Poor**
- All prices are raw floats — no currency formatting
- `confidence` is a raw float — no label
- No explanation of pricing strategy
- No comparison to market comparables
- No negotiation guidance (e.g., "Start at $X, walk away above $Y")
- No price sensitivity analysis

**Missing:**
- Currency formatting
- Confidence label
- Pricing strategy explanation
- Negotiation guidance
- Price range visualization data
- Market comparison context

---

### 1.6 `entity_resolution.py` — Entity Resolution

**Output type:** `list[EntityCluster]` where:
```python
@dataclass
class EntityCluster:
    entities: list[dict]
    canonical_name: str
```

**User-friendliness:** ❌ **Poor**
- `entities` is a list of raw dicts — no structured format
- No match quality indicator for each pair
- No duplicate confidence score
- No merge recommendation (e.g., "Merge these 3 records")
- No entity resolution report
- No statistics (e.g., "Resolved 50 entities into 12 clusters, 8 duplicates found")

**Missing:**
- Match quality per pair
- Merge recommendation
- Resolution statistics
- Duplicate report
- Cluster visualization data

---

### 1.7 `search_ranking.py` — Search Ranking

**Output type:** `list[RankedListing]` where:
```python
@dataclass
class RankedListing:
    id: str
    title: str
    score: float
    category: str
```

**User-friendliness:** ❌ **Poor**
- `score` is a raw float — no relevance percentage or label
- No explanation of ranking factors
- No diversity/personalization breakdown
- No search result summary
- No pagination support

**Missing:**
- Relevance percentage
- Ranking factor explanation
- Search summary
- Pagination support
- Result quality metrics

---

### 1.8 `evolution.py` — Evolution Framework

**Output types:** `EvolutionResult` and `EvaluationResult` dataclasses:
```python
@dataclass
class EvolutionResult:
    best_fitness: float
    generation_count: int
    population_size: int
    diversity: float
    offspring_count: int
    converged: bool
    worst_fitness: float

@dataclass
class EvaluationResult:
    passed: bool
    gap: float
    suggestion: str
```

**User-friendliness:** ⚠️ **Partial**
- ✅ `EvaluationResult.suggestion` is a human-readable string
- ✅ `EvaluationResult.passed` is a boolean — clear pass/fail
- ❌ `EvolutionResult` metrics are all raw floats — no interpretation
- ❌ No convergence visualization data
- ❌ No fitness progression data
- ❌ No evolution report summarizing the optimization run
- ❌ `diversity` is a raw float — no label

**Missing:**
- Fitness progression data (for charts)
- Convergence visualization
- Evolution summary report
- Diversity interpretation
- Optimization recommendations

---

## 2. Report Generation Module

### Status: ❌ **DOES NOT EXIST**

**Findings:**
- No `report.py`, `reporting.py`, or `generate_report()` function anywhere in the codebase
- No report templates (Jinja2, HTML, Markdown)
- No report generation logic
- No scheduled report generation
- No report storage or archival

**Impact:** Users of the platform have no way to generate consolidated reports combining outputs from multiple modules (e.g., a due diligence report that includes valuation, fraud score, and matching results).

---

## 3. Results Export Feature (CSV, JSON, PDF)

### Status: ❌ **DOES NOT EXIST**

**Findings:**
- No `export.py` or `serialization.py` module
- No `to_dict()`, `to_json()`, or `to_csv()` methods on any dataclass
- No CSV export functionality
- No JSON export functionality
- No PDF export functionality
- No Excel export functionality
- No API endpoint for data export

**Impact:** Results from any module cannot be exported to standard formats. Users must manually write serialization code to save or share results. This is a critical gap for a platform that produces valuation reports, fraud analyses, and portfolio recommendations.

---

## 4. Notification System

### Status: ❌ **DOES NOT EXIST**

**Findings:**
- No `notification.py` or `alert.py` module
- No email notification support
- No webhook integration
- No SMS/push notification support
- No alert thresholds or rules
- No notification preferences system
- No real-time alerting for critical events (e.g., high fraud risk detected)

**Impact:** Users cannot be automatically notified of important events:
- High fraud risk detected on a listing
- Valuation complete
- Match found for a buyer
- Portfolio optimization complete
- Price recommendation ready

---

## 5. Dashboard Data API

### Status: ❌ **DOES NOT EXIST**

**Findings:**
- No REST API endpoints (no FastAPI/Flask routes)
- No WebSocket support for real-time updates
- No data feed for dashboard consumption
- No API for querying module results
- No authentication/authorization for API access
- The existing `docs/dashboard.html` is a **static HTML file** with no dynamic data binding — it cannot display live results from the optimization engine

**Impact:** There is no programmatic way to:
- Query valuation results
- Fetch fraud scores
- Retrieve match results
- Get portfolio optimization output
- Build a real-time dashboard
- Integrate with external BI tools

---

## 6. Summary of Gaps

| # | Gap | Severity | Modules Affected | Description |
|---|-----|----------|------------------|-------------|
| 1 | **No user-friendly output formatting** | 🔴 Critical | All 8 modules | Raw dataclass floats with no currency formatting, percentage labels, or human-readable interpretations |
| 2 | **No report generation** | 🔴 Critical | All modules | No way to generate consolidated reports combining multiple module outputs |
| 3 | **No results export** | 🔴 Critical | All modules | No CSV, JSON, PDF, or Excel export — results are trapped in Python objects |
| 4 | **No notification system** | 🟡 High | fraud_detection, matching, valuation | No alerts for critical events (high fraud risk, match found, valuation complete) |
| 5 | **No dashboard data API** | 🔴 Critical | All modules | No REST API or WebSocket for programmatic access to results |
| 6 | **No `__str__` methods on dataclasses** | 🟡 High | All modules | Default dataclass repr is developer-only, not business-user friendly |
| 7 | **No confidence/score labels** | 🟡 High | All modules | Raw floats (0.0–1.0) with no "High/Medium/Low" labels |
| 8 | **No summary statistics** | 🟡 Medium | All modules | No aggregate stats (counts, averages, distributions) |
| 9 | **No visualization data** | 🟡 Medium | All modules | No chart-ready data structures (time series, pie charts, bar charts) |
| 10 | **No batch processing reports** | 🟡 Medium | All modules | No way to run multiple items and get a consolidated report |
| 11 | **No audit trail** | 🟡 Medium | All modules | No logging of who ran what analysis when |
| 12 | **No comparison reports** | 🟡 Low | valuation, pricing | No side-by-side comparison of multiple valuations or pricing scenarios |

---

## 7. Recommended Reporting Features (Priority Order)

### P0 — Critical (Must Have)

1. **Results Export Module** (`export.py`)
   - `to_dict()` method on all result dataclasses
   - `to_json()` — JSON export with pretty printing
   - `to_csv()` — CSV export for tabular data (matches, listings, portfolio assets)
   - `to_markdown()` — Markdown export for reports
   - Batch export: `export_batch(results: list, format: str) -> str`

2. **Report Generation Module** (`report.py`)
   - `generate_valuation_report(ValuationResult) -> str` — formatted valuation report
   - `generate_fraud_report(FraudScore, GraphAnalysis) -> str` — fraud analysis report
   - `generate_match_report(list[Match]) -> str` — matching results report
   - `generate_portfolio_report(Portfolio) -> str` — portfolio summary report
   - `generate_pricing_report(PriceRecommendation) -> str` — pricing recommendation report
   - `generate_entity_report(list[EntityCluster]) -> str` — entity resolution report
   - `generate_ranking_report(list[RankedListing]) -> str` — search ranking report
   - `generate_evolution_report(EvolutionResult) -> str` — evolution summary report
   - `generate_consolidated_report(...) -> str` — combined due diligence report

3. **Dashboard Data API** (`api.py`)
   - REST endpoints: `/api/valuation`, `/api/fraud`, `/api/matching`, `/api/portfolio`, `/api/pricing`, `/api/entities`, `/api/ranking`, `/api/evolution`
   - JSON response format with consistent schema
   - Query parameters for filtering and pagination
   - Health check endpoint

### P1 — High (Should Have)

4. **Output Formatting Layer** (`formatting.py`)
   - `format_currency(value: float) -> str` — `$1,234,567` or `$1.2M`
   - `format_percentage(value: float) -> str` — `12.5%`
   - `format_confidence(value: float) -> str` — "High" / "Medium" / "Low"
   - `format_risk_level(level: str) -> str` — color-coded risk labels
   - `format_score(value: float) -> str` — `0.85 (Strong)`

5. **Notification System** (`notification.py`)
   - `send_alert(event_type: str, severity: str, message: str) -> None`
   - Email notification support (SMTP)
   - Webhook notification support
   - Alert rules engine (e.g., "alert if fraud_score > 0.7")
   - Notification preferences (per-user, per-event-type)

6. **Summary Statistics** (`statistics.py`)
   - `summarize_matches(matches: list[Match]) -> dict` — count, avg score, avg confidence
   - `summarize_valuations(results: list[ValuationResult]) -> dict` — min, max, avg, median
   - `summarize_fraud_scores(scores: list[FraudScore]) -> dict` — risk distribution
   - `summarize_portfolio(portfolio: Portfolio) -> dict` — total cost, sector breakdown

### P2 — Medium (Nice to Have)

7. **Visualization Data** (`visualization.py`)
   - Chart-ready data structures (labels, values, colors)
   - Time series data for evolution fitness progression
   - Pie chart data for portfolio sector allocation
   - Bar chart data for fraud risk distribution
   - Heatmap data for match confidence matrix

8. **Batch Processing** (`batch.py`)
   - `run_batch_valuation(targets: list[dict]) -> list[ValuationResult]`
   - `run_batch_fraud_detection(listings: list[dict]) -> list[FraudScore]`
   - `run_batch_matching(buyers: list[Buyer], sellers: list[Seller]) -> list[Match]`
   - Batch report generation

9. **Audit Trail** (`audit.py`)
   - Log all analysis runs with timestamps
   - Track who ran what analysis
   - Store input parameters and output results
   - Compliance-ready audit logs

10. **Comparison Reports** (`comparison.py`)
    - Side-by-side valuation comparison (DCF vs Comps vs Ensemble)
    - Pricing scenario comparison (bull vs bear vs normal market)
    - Portfolio comparison (optimized vs benchmark)

---

## 8. Architecture Recommendation

```
src/acquisition_platform/
├── __init__.py              # Package exports (existing)
├── matching.py              # Existing algorithm modules (8 files)
├── valuation.py
├── fraud_detection.py
├── portfolio_optimizer.py
├── dynamic_pricing.py
├── entity_resolution.py
├── search_ranking.py
├── evolution.py
│
├── NEW: formatting.py       # Output formatting layer
│   ├── format_currency()
│   ├── format_percentage()
│   ├── format_confidence()
│   └── format_risk_level()
│
├── NEW: export.py           # Results export (CSV, JSON, Markdown)
│   ├── to_dict()
│   ├── to_json()
│   ├── to_csv()
│   └── to_markdown()
│
├── NEW: report.py           # Report generation
│   ├── generate_valuation_report()
│   ├── generate_fraud_report()
│   ├── generate_match_report()
│   ├── generate_portfolio_report()
│   ├── generate_pricing_report()
│   ├── generate_entity_report()
│   ├── generate_ranking_report()
│   ├── generate_evolution_report()
│   └── generate_consolidated_report()
│
├── NEW: api.py              # Dashboard data API
│   ├── /api/valuation
│   ├── /api/fraud
│   ├── /api/matching
│   ├── /api/portfolio
│   ├── /api/pricing
│   ├── /api/entities
│   ├── /api/ranking
│   └── /api/evolution
│
├── NEW: notification.py     # Notification system
│   ├── send_alert()
│   ├── send_email()
│   └── send_webhook()
│
├── NEW: statistics.py       # Summary statistics
│   ├── summarize_matches()
│   ├── summarize_valuations()
│   └── summarize_fraud_scores()
│
└── NEW: visualization.py    # Visualization data
    ├── chart_data()
    ├── time_series_data()
    └── pie_chart_data()
```

---

## 9. Conclusion

The `acquisition_platform` package has **strong algorithmic foundations** — 8 well-tested NP-hard problem solvers with clean APIs. However, it has **zero output formatting, reporting, export, notification, or dashboard capabilities**. The package is currently a **developer-only library** with no business-user-facing output layer.

The three most critical gaps are:
1. **No results export** — results are trapped in Python objects
2. **No report generation** — no consolidated reports possible
3. **No dashboard data API** — no programmatic access to results

These gaps must be addressed before the platform can be used in a real acquisition workflow where analysts, brokers, and investors need formatted reports, exportable data, and real-time dashboards.
