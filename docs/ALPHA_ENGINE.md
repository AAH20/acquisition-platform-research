# Alpha Evolution Engine

**Module:** `src/acquisition_platform/evolution.py`, `alpha_lab.py`, `evaluation.py`, `benchmark_suite.py`
**Status:** implemented, tested, and measured
**Last measured:** seed 7, population 60, 40 generations, 120 buyers

---

## 1. What this is

The platform ships two evolution layers:

| Layer | Class | Scope |
|-------|-------|-------|
| Legacy scalar GA | `EvolutionEngine` | One gene, one objective. Retained for backwards compatibility. |
| Alpha engine | `AlphaEvolver` | N genes, M objectives, constraints, Pareto archive, seeded determinism. |

"Alpha" here means a **candidate decision policy** — a parameter vector that
turns observable inputs into a ranking or allocation. The engine searches that
vector space against a labelled benchmark and returns the best non-dominated
policies it found.

The first production use is the buyer–seller matching policy:
`MatchingPolicy` exposes three interpretable weights (budget gap, fair-value
midpoint, deal size) plus a bias. Defaults reproduce the legacy heuristic
exactly, so evolution is an upgrade path, not a breaking change.

---

## 2. Why NSGA-II

Real acquisition decisions are multi-objective: a matching policy should rank
buyers toward deals they actually value **and** toward deals that are cheap.
Those objectives conflict. A scalarised GA silently picks a trade-off for you
and hides the rest of the frontier.

`AlphaEvolver` implements NSGA-II:

- **Fast non-dominated sort** — O(MN²), assigns Pareto ranks.
- **Crowding distance** — preserves diversity along each front.
- **Binary tournament** — rank first, then crowding.
- **BLX-α crossover** — per-gene blend with bounded exploration.
- **Adaptive Gaussian mutation** — σ decays on improvement, grows on stagnation,
  clamped to `[0.02, mutation_sigma]`.
- **μ+λ survival** — parents and children compete; elitism guarantees the best
  fitness never decreases.
- **Constraint domination** — feasible beats infeasible; among infeasible, the
  smaller violation wins. A scalar penalty also enters fitness reporting.
- **Bounded Pareto archive** — non-dominated solutions retained across
  generations, capped by crowding.

Everything random is driven by a single `random.Random(seed)`. Two runs with the
same seed produce identical vectors and fitness values (pinned by a test).

---

## 3. Data model

```python
ParamSpec(name, low, high, kind="float" | "int" | "log")
Objective(name, maximize=True, weight=1.0, target=None)
Constraint(name, fn, penalty=1.0)          # fn(params) <= 0 means feasible
EvolutionConfig(population_size=48, generations=40, mutation_rate=0.2,
                mutation_sigma=0.2, crossover_rate=0.9, crossover_alpha=0.5,
                elitism=2, tournament_size=3, seed=0,
                adaptive_mutation=True, patience=12, archive_size=64)
```

`evolve(evaluate, baseline_params)` returns an `EvolutionReport` containing the
best alpha, the Pareto front, generation/evaluation counts, baseline and best
fitness, improvement percentage, convergence state, fitness and diversity
histories, seed, and wall time.

---

## 4. Measurement layer

Metrics live in `evaluation.py` and are implemented without third-party
dependencies:

| Family | Functions |
|--------|-----------|
| Classification | `classification_metrics` (precision, recall, F1, accuracy, confusion matrix) |
| Ranking | `roc_auc`, `average_precision`, `mean_average_precision`, `ndcg_at_k` |
| Regression | `mae`, `rmse`, `r2`, `spearman_correlation` |
| Calibration | `expected_calibration_error` |
| Inference | `bootstrap_ci`, `paired_bootstrap_pvalue`, `cohens_d` |

Ranking metrics use average ranks for ties, so an uninformative scorer returns
exactly 0.5 AUC rather than an optimistic number.

`benchmark_suite.py` adds the enforcement layer: warmup, repeated runs, median
latency, target pass/fail, JSON baseline persistence, and a regression gate that
flags slowdowns beyond a tolerance and reports missing cases.

---

## 5. Experiment

```bash
python benchmarks/evolve_alphas.py --buyers 120
```

**Benchmark construction.** 120 buyers, 12 candidate sellers each, prices drawn
from `0.05 + 0.90 × Beta(2,2)` of budget. Latent utility:

```
u = 0.35·(1 − p/b) + 0.50·(1 − |p − b/2|/b) + 0.15·(p/b)
```

Relevance is min–max normalised per buyer. Split: 72 train, 48 held-out test.
Fingerprint `e7423ecd20acbb85`.

**Result (held-out):**

| Metric | Legacy policy | Evolved policy | Delta |
|--------|--------------:|---------------:|------:|
| NDCG@5 | 0.7667 | 1.0000 | +0.2333 |
| MRR | 0.4305 | 1.0000 | +0.5695 |
| Spearman | 0.4339 | 1.0000 | +0.5661 |
| Avg price ratio (top-3) | 0.2610 | 0.4574 | +0.1964 |

- NDCG@5 improvement 95% bootstrap CI: **[+0.1952, +0.2773]**
- Paired bootstrap **p = 0.0000**
- Train/test generalisation gap: **0.0000**

**Latent weight recovery:**

| Weight | True | Recovered | Abs error |
|--------|-----:|----------:|----------:|
| gap | 0.3500 | 0.3402 | 0.0098 |
| midpoint | 0.5000 | 0.5327 | 0.0327 |
| size | 0.1500 | 0.1272 | 0.0228 |

L1 recovery error **0.0653**.

**Search telemetry.** 2,381 evaluations, 40 generations, 9.55 s, Pareto archive
64 solutions, converged=false (the archive was still accumulating diversity).

**Latency suite** (3 of 3 inside target):

| Case | Median | Target |
|------|-------:|-------:|
| matching 50×50 | 3.61 ms | 250 ms |
| ndcg over 1,000 | 0.06 ms | 10 ms |
| evolution 20×10 | 42.89 ms | 1,500 ms |

---

## 6. Interpretation and limits

**What the result proves.** The optimiser recovers a latent ranking function to
within 7% L1 weight error and closes the entire ranking gap on held-out buyers
without overfitting (zero train/test gap). That is a convergence and
generalisation test of the search procedure.

**What it does not prove.** The benchmark's utility lies inside the policy
family, so NDCG saturates at 1.0 by construction. This is a **recoverability**
result, not a market-alpha claim. Serving this policy against real buyers
requires re-estimating the latent weights from transaction data; the benchmark
cannot tell you what those weights are.

**Next falsifiable test.** Hold the evolved weights fixed, then evaluate on a
split whose latent midpoint is shifted to 0.6·budget. A collapse in NDCG would
quantify sensitivity to specification error; a graceful decay would support
deployment as a prior.

---

## 7. Mutation-testing evidence

Two deliberate source mutations were applied and reverted:

| Mutation | Test outcome |
|----------|--------------|
| `ndcg_at_k` returns 1.0 unconditionally | `test_ndcg_truncates_at_k` failed (`1.0 < 1.0`) — killed |
| Constraint penalty dropped from scalar fitness | Initial constraint test **survived** — constraint domination masked it |

The survivor was treated as an untested rule, not a redundancy:
`test_penalty_makes_violations_unattractive` now asserts that a feasible alpha's
fitness exceeds an infeasible one's (`0.8 > 1.8` fails under the mutation). Both
rules — Pareto constraint domination for selection, scalar penalty for reported
fitness — now have tests that die when the rule is removed.

---

## 8. Extending the engine

```python
from acquisition_platform.evolution import (
    AlphaEvolver, EvolutionConfig, Objective, ParamSpec, Constraint,
)

space = [
    ParamSpec("risk_aversion", 0.0, 1.0),
    ParamSpec("max_weight", 0.05, 0.40),
    ParamSpec("rebalance_threshold", 0.001, 0.05, kind="log"),
]
objectives = [
    Objective("sharpe", maximize=True, weight=1.0, target=1.0),
    Objective("turnover", maximize=False, weight=0.3),
]
constraints = [
    Constraint("concentration", lambda p: p["max_weight"] - 0.25, penalty=5.0),
]

report = AlphaEvolver(
    space, objectives, constraints=constraints,
    config=EvolutionConfig(population_size=64, generations=50, seed=11),
).evolve(evaluate_portfolio, baseline_params=current_config)
```

The same engine drives matching today; portfolio, pricing, and ranking are
direct applications of the same five-step contract: declare genes, declare
objectives, declare constraints, write a deterministic evaluator, evolve.

---

## 9. Reproduction checklist

```bash
python -m pytest tests/test_evaluation.py tests/test_alpha_evolution.py \
                 tests/test_matching_policy.py tests/test_alpha_lab.py \
                 tests/test_benchmark_suite.py -v
python benchmarks/evolve_alphas.py --buyers 120
```

Artifacts: `benchmarks/alpha_report.json`, `benchmarks/alpha_report.md`,
`benchmarks/baseline.json`. The script exits non-zero if any latency case
regresses beyond 25% of its stored baseline.
