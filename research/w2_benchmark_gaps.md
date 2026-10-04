# Wave 2: Benchmark & Evaluation Gap Analysis

**Date:** 2026-10-04  
**Scope:** Audit of benchmark infrastructure, evaluation metrics, and test coverage across all 8 modules  
**Files Analyzed:** 9 source files (1,290 LOC), 8 test files, 1 evolution/benchmark module

---

## 1. Benchmark Class Analysis (`evolution.py`)

### 1.1 Current State

The `Benchmark` class (lines 30–51) is a minimal threshold-checking utility:

```python
@dataclass
class Benchmark:
    name: str
    target: float

    def evaluate(self, actual: float) -> EvaluationResult:
        passed = actual >= self.target
        gap = round(self.target - actual, 10)
        ...
```

### 1.2 What It Has
| Feature | Status |
|---------|--------|
| Single scalar target comparison | ✅ |
| Pass/fail determination | ✅ |
| Gap calculation | ✅ |
| Improvement suggestion | ✅ |

### 1.3 What It's Missing (Critical Gaps)

| Missing Metric | Impact | Needed By |
|----------------|--------|-----------|
| **Precision** | Cannot measure false positive rate | Fraud detection, entity resolution, matching |
| **Recall** | Cannot measure false negative rate | Fraud detection, entity resolution, matching |
| **F1 Score** | No harmonic mean of precision/recall | All classification modules |
| **AUC-ROC** | No threshold-independent evaluation | Fraud detection, matching |
| **NDCG** | No ranking quality measurement | Search ranking, recommendation |
| **MAP** | No mean average precision | Search ranking, entity resolution |
| **Accuracy** | No overall correctness measure | All modules |
| **Confusion Matrix** | No TP/FP/TN/FN breakdown | Fraud detection, entity resolution |
| **Log Loss** | No probabilistic evaluation | Fraud detection, dynamic pricing |
| **MAE/RMSE** | No regression error measurement | Valuation, dynamic pricing |
| **Calibration** | No probability calibration check | Fraud detection, pricing |
| **Multi-metric evaluation** | Only supports single scalar | All modules |
| **Statistical significance** | No confidence intervals | All modules |
| **Baseline comparison** | No comparison to naive baselines | All modules |

### 1.4 `EvaluationResult` Limitations

```python
@dataclass
class EvaluationResult:
    passed: bool
    gap: float
    suggestion: str
```

- Only 3 fields — insufficient for serious evaluation
- No support for storing multiple metrics
- No support for per-class metrics
- No support for metric history tracking
- No serialization support (can't save/load results)

---

## 2. Benchmark Runner Script

### 2.1 Status: **DOES NOT EXIST**

```
$ find . -type f \( -name "*.sh" -o -name "benchmark*" -o -name "run*" -o -name "eval*" \) ! -path "*/.venv-test/*"
(no results)
```

**No benchmark runner script exists anywhere in the project.** There is:
- No `benchmarks/` directory
- No `scripts/` directory
- No `run_benchmarks.py` or similar
- No `Makefile` or `justfile` with benchmark targets
- No CI workflow that runs benchmarks
- No `pytest-benchmark` integration

### 2.2 What's Needed

A benchmark runner should:
1. Load test datasets (gold-standard labeled data)
2. Run each module against the dataset
3. Compute standard metrics (precision, recall, F1, AUC, NDCG, MAP)
4. Compare against the `Benchmark` targets
5. Aggregate results across modules
6. Generate a report (JSON/Markdown)
7. Track performance over time (regression detection)

---

## 3. Results Aggregation System

### 3.1 Status: **DOES NOT EXIST**

There is no:
- Results database or storage
- Aggregation module
- Report generator
- Performance tracking over time
- Regression detection system
- Comparison across runs

The `Benchmark.evaluate()` method returns a result that is immediately discarded — there is no mechanism to collect, store, or compare results across multiple evaluations.

### 3.2 What's Needed

- A `BenchmarkSuite` class that runs multiple benchmarks and aggregates results
- A `ResultsStore` for persisting benchmark results (JSON/SQLite)
- A `ReportGenerator` for human-readable output
- A `RegressionDetector` that compares current vs. previous results
- Integration with `pytest` for automated benchmark testing

---

## 4. Module-by-Module Benchmark Requirements

### 4.1 Fraud Detection (`fraud_detection.py`)

| Metric | Needed | Current Test Coverage |
|--------|--------|----------------------|
| Precision | ✅ Critical | ❌ None |
| Recall | ✅ Critical | ❌ None |
| F1 Score | ✅ Critical | ❌ None |
| AUC-ROC | ✅ High | ❌ None |
| False Positive Rate | ✅ High | ❌ None |
| False Negative Rate | ✅ High | ❌ None |
| Confusion Matrix | ✅ High | ❌ None |
| Latency (p50/p99) | ✅ Medium | ✅ Basic (<500ms test exists) |

**Current tests only check:** risk level classification, score ranges, explanation presence, graph ring detection. No labeled dataset evaluation.

### 4.2 Entity Resolution (`entity_resolution.py`)

| Metric | Needed | Current Test Coverage |
|--------|--------|----------------------|
| Pairwise Precision | ✅ Critical | ❌ None |
| Pairwise Recall | ✅ Critical | ❌ None |
| Pairwise F1 | ✅ Critical | ❌ None |
| Cluster Precision/Recall | ✅ High | ❌ None |
| B-cubed F1 | ✅ Medium | ❌ None |
| Comparison Efficiency | ✅ Medium | ✅ Basic (comparison_count < 10000) |

**Current tests only check:** clustering behavior, canonical name selection, blocking efficiency. No labeled dataset evaluation.

### 4.3 Matching (`matching.py`)

| Metric | Needed | Current Test Coverage |
|--------|--------|----------------------|
| Match Accuracy | ✅ Critical | ❌ None |
| Match Precision | ✅ Critical | ❌ None |
| Match Recall | ✅ Critical | ❌ None |
| Budget Utilization | ✅ High | ❌ None |
| Category Match Rate | ✅ Medium | ❌ None |
| Optimality Gap | ✅ Medium | ❌ None |

**Current tests only check:** basic matching logic, budget constraints, score ranges. No labeled dataset evaluation.

### 4.4 Valuation (`valuation.py`)

| Metric | Needed | Current Test Coverage |
|--------|--------|----------------------|
| MAE (Mean Absolute Error) | ✅ Critical | ❌ None |
| RMSE | ✅ Critical | ❌ None |
| MAPE | ✅ High | ❌ None |
| R² | ✅ High | ❌ None |
| Valuation Bias | ✅ Medium | ❌ None |
| Confidence Calibration | ✅ Medium | ❌ None |

**Current tests only check:** basic calculation correctness, monotonicity properties. No comparison to actual market prices.

### 4.5 Portfolio Optimizer (`portfolio_optimizer.py`)

| Metric | Needed | Current Test Coverage |
|--------|--------|----------------------|
| Return vs. Benchmark | ✅ Critical | ❌ None |
| Sharpe Ratio | ✅ High | ✅ Basic (exists but not evaluated) |
| Max Drawdown | ✅ High | ❌ None |
| Diversification Score | ✅ Medium | ❌ None |
| Optimality Gap | ✅ Medium | ❌ None |
| Risk-Adjusted Return | ✅ High | ❌ None |

**Current tests only check:** budget constraints, cardinality limits, diversification behavior. No quantitative portfolio performance evaluation.

### 4.6 Search Ranking (`search_ranking.py`)

| Metric | Needed | Current Test Coverage |
|--------|--------|----------------------|
| NDCG@K | ✅ Critical | ❌ None |
| MAP | ✅ Critical | ❌ None |
| MRR | ✅ High | ❌ None |
| Precision@K | ✅ High | ❌ None |
| Recall@K | ✅ High | ❌ None |
| Diversity Score | ✅ Medium | ❌ None |
| Coverage | ✅ Medium | ❌ None |

**Current tests only check:** ranking order, deduplication, diversity penalty behavior. No labeled relevance dataset evaluation.

### 4.7 Dynamic Pricing (`dynamic_pricing.py`)

| Metric | Needed | Current Test Coverage |
|--------|--------|----------------------|
| Revenue Optimization | ✅ Critical | ❌ None |
| Price Elasticity Accuracy | ✅ High | ❌ None |
| Market Share Impact | ✅ Medium | ❌ None |
| Equilibrium Convergence | ✅ Medium | ❌ None |
| Profit Margin | ✅ High | ❌ None |

**Current tests only check:** basic price calculation, monotonicity, bounds. No market simulation evaluation.

### 4.8 Evolution Engine (`evolution.py`)

| Metric | Needed | Current Test Coverage |
|--------|--------|----------------------|
| Convergence Speed | ✅ High | ✅ Basic |
| Solution Quality | ✅ High | ✅ Basic |
| Diversity Maintenance | ✅ Medium | ✅ Basic |
| Fitness Improvement | ✅ High | ✅ Basic |

**Current tests are the most complete** — they check convergence, diversity, offspring production, elitism. But still no quantitative fitness targets.

---

## 5. Missing Evaluation Metrics in Test Files

### 5.1 Summary

| Test File | Tests | Quantitative Metrics | Labeled Data | Benchmark Targets |
|-----------|-------|---------------------|--------------|-------------------|
| `test_fraud_detection.py` | 7 | ❌ None | ❌ None | ❌ None |
| `test_entity_resolution.py` | 8 | ❌ None | ❌ None | ❌ None |
| `test_matching.py` | 8 | ❌ None | ❌ None | ❌ None |
| `test_valuation.py` | 8 | ❌ None | ❌ None | ❌ None |
| `test_portfolio_optimizer.py` | 7 | ❌ None | ❌ None | ❌ None |
| `test_search_ranking.py` | 7 | ❌ None | ❌ None | ❌ None |
| `test_dynamic_pricing.py` | 7 | ❌ None | ❌ None | ❌ None |
| `test_evolution.py` | 9 | ⚠️ Minimal | ❌ None | ⚠️ Basic |

### 5.2 Test Quality Issues

1. **No labeled datasets** — Tests use synthetic inputs with no ground truth
2. **No quantitative assertions** — Tests check properties ("> 0", "< 1") not accuracy
3. **No edge case coverage** — No tests for adversarial inputs, boundary conditions
4. **No regression tests** — No tests that verify performance doesn't degrade
5. **No cross-module tests** — No integration tests combining modules
6. **No performance benchmarks** — Only fraud detection has a latency test
7. **No statistical tests** — No tests for distribution properties, variance

### 5.3 Specific Missing Test Patterns

```python
# MISSING: Precision/Recall evaluation
def test_fraud_detection_precision():
    detector = FraudDetector()
    # Load labeled dataset
    # y_true, y_pred = ...
    # assert precision_score(y_true, y_pred) >= 0.90

# MISSING: NDCG evaluation
def test_search_ranking_ndcg():
    ranker = SearchRanker()
    # Load labeled relevance judgments
    # ndcg = compute_ndcg(ranked_results, relevance_judgments)
    # assert ndcg >= 0.85

# MISSING: Valuation accuracy
def test_valuation_mae():
    engine = ValuationEngine()
    # Load actual transaction prices
    # mae = mean_absolute_error(predicted, actual)
    # assert mae < 0.15 * mean(actual)
```

---

## 6. Gap Severity Summary

| Gap | Severity | Impact |
|-----|----------|--------|
| No standard ML metrics (precision, recall, F1, AUC, NDCG, MAP) | **Critical** | Cannot evaluate model quality |
| No benchmark runner script | **Critical** | Cannot run systematic evaluations |
| No results aggregation system | **High** | Cannot track performance over time |
| No labeled datasets | **Critical** | Cannot compute ground-truth metrics |
| No quantitative test assertions | **High** | Tests verify structure, not quality |
| No regression detection | **High** | Performance degradation goes unnoticed |
| No cross-module evaluation | **Medium** | Integration quality unmeasured |
| No statistical significance testing | **Medium** | Cannot distinguish signal from noise |
| No baseline comparisons | **Medium** | Cannot measure improvement over naive approaches |

---

## 7. Recommendations

### 7.1 Immediate (P0)

1. **Extend `Benchmark` class** to support multi-metric evaluation:
   ```python
   @dataclass
   class Benchmark:
       name: str
       targets: dict[str, float]  # metric_name -> target_value
       weights: dict[str, float]  # metric_name -> weight
   ```

2. **Create `metrics.py`** with standard metric implementations:
   - `precision_score(y_true, y_pred)`
   - `recall_score(y_true, y_pred)`
   - `f1_score(y_true, y_pred)`
   - `auc_roc(y_true, y_scores)`
   - `ndcg_at_k(ranked_results, relevance, k)`
   - `average_precision(y_true, y_scores)`
   - `mean_absolute_error(y_true, y_pred)`
   - `root_mean_squared_error(y_true, y_pred)`

3. **Create `benchmarks/run_benchmarks.py`** — a benchmark runner that:
   - Discovers all modules
   - Runs each against labeled data
   - Computes metrics
   - Compares to targets
   - Outputs JSON/Markdown report

### 7.2 Short-term (P1)

4. **Create labeled datasets** for each module (even small synthetic ones with known ground truth)
5. **Add quantitative assertions** to existing tests
6. **Create `BenchmarkSuite`** for aggregating results across modules
7. **Add `pytest-benchmark`** for performance regression testing

### 7.3 Medium-term (P2)

8. **Create `ResultsStore`** (SQLite/JSON) for tracking benchmark history
9. **Create `ReportGenerator`** for human-readable benchmark reports
10. **Add CI integration** to run benchmarks on every PR
11. **Create baseline implementations** (naive classifiers, random rankers) for comparison
12. **Add statistical significance testing** (paired t-test, bootstrap confidence intervals)

---

## 8. Conclusion

The project has a **minimal benchmark infrastructure** that supports only single-scalar threshold checking. The `Benchmark` class and `EvaluationResult` are insufficient for serious model evaluation. There are **no standard ML metrics**, **no benchmark runner**, **no results aggregation**, and **no labeled datasets**. Tests verify structural properties (return types, basic constraints) but not quantitative quality (accuracy, ranking quality, valuation error).

The evolution engine is the only module with any benchmark testing, and even that is minimal. All other modules have zero evaluation metric coverage. This is the **single largest gap** in the project's quality infrastructure.
