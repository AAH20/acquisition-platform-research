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
| matching 50×50 | 2.70 ms | 250 ms |
| ndcg over 1,000 | 0.06 ms | 10 ms |
| evolution 20×10 | 39.03 ms | 1,500 ms |

### Cross-validation

The single split above could be lucky. Re-running the entire procedure on five
disjoint folds, each with its own seed, gives:

| Fold | Train | Test | Baseline | Evolved | Delta |
|-----:|------:|-----:|---------:|--------:|------:|
| 0 | 96 | 24 | 0.7338 | 1.0000 | +0.2662 |
| 1 | 96 | 24 | 0.7459 | 1.0000 | +0.2541 |
| 2 | 96 | 24 | 0.8080 | 1.0000 | +0.1920 |
| 3 | 96 | 24 | 0.7711 | 1.0000 | +0.2289 |
| 4 | 96 | 24 | 0.7623 | 1.0000 | +0.2377 |

Mean delta **+0.2358 ± 0.0254**, win rate **100%**, p = 0.0000. The effect is
not an artefact of one split.

### Specification shift

The policy is trained at midpoint 0.5, then scored against benchmarks whose true
fair-value point moves while buyers and prices are held fixed:

| True midpoint | Legacy | Evolved | Delta |
|--------------:|-------:|--------:|------:|
| 0.40 | 0.9269 | 0.9106 | −0.0163 |
| 0.45 | 0.8674 | 0.9724 | +0.1050 |
| 0.50 | 0.7667 | 1.0000 | +0.2333 |
| 0.55 | 0.6291 | 0.9601 | +0.3311 |
| 0.60 | 0.4676 | 0.8482 | +0.3806 |
| 0.65 | 0.3128 | 0.7203 | +0.4075 |

Degradation is asymmetric. Moving the true midpoint **upward** hurts most
(1.0000 → 0.7203 at 0.65) because the size feature only partly substitutes for
a higher fair-value centre. Moving it **downward** barely matters: at 0.40 the
evolved policy is 0.016 points behind the legacy heuristic, which is nearly
optimal there by construction.

### Search strategy attribution

| Function | Dims | Evolutionary best | Evals | Random best | Evals |
|----------|-----:|------------------:|------:|------------:|------:|
| Rastrigin | 5 | 0.0000 | 497 | −25.3352 | 2,381 |

At equal budget, **random search also reaches 1.0000 NDCG@5** on the matching
policy. The landscape is smooth and four-dimensional, so this benchmark cannot
separate search strategies — a negative result about the benchmark, reported
rather than hidden. On a multimodal objective the evolver reaches the global
optimum with roughly one fifth of random search's evaluations.

### Grid oracle

A dense grid over the three weights (15³ − 1 = 3,374 evaluated policies) is the
practical oracle for this space:

| Search | Evaluations | Test NDCG@5 |
|--------|------------:|------------:|
| Grid (15³ points) | 3,374 | 1.0000 |
| Evolution | 2,381 | 1.0000 |

The evolver matches the grid while evaluating 29% fewer policies. Since both
saturate, this is an efficiency result, not a quality one.

### Misspecification: an unobservable signal

The policy sees price and budget only. The study benchmark adds a
seller-quality signal to the latent utility (`quality_weight = 0.6`), which the
policy cannot observe — roughly a third of the decision-relevant variance.

| Metric | Legacy | Evolved |
|--------|-------:|--------:|
| NDCG@5 | 0.6273 | 0.6786 |
| Top-1 utility regret | 0.4489 | 0.1515 |

Training NDCG reaches 0.7196; the train/test gap is 0.0410. The policy **cannot
approach the ceiling** — that is the point — but it removes 66% of the legacy
regret with the information it has. The honest reading: the in-family gain of
+0.2333 is an upper bound; with a third of the utility unobservable, the
realisable gain is +0.051 NDCG.

### Input-noise stability

Ranking under ±5% uniform price perturbation, five trials:

| Metric | Value |
|--------|------:|
| Mean Spearman vs unperturbed | 0.9708 |
| Worst trial | 0.9624 |
| Mean NDCG drop | 0.0032 |

The policy is stable to small pricing errors, which matters because quoted
prices are noisy in practice.

---

## 6. Interpretation and limits

**What the result proves.** The optimiser recovers a latent ranking function to
within 7% L1 weight error, closes the entire ranking gap on held-out buyers, and
generalises without overfitting (zero train/test gap; 5/5 folds positive). That
is a convergence and generalisation test of the search procedure.

**What it does not prove.** The benchmark's utility lies inside the policy
family, so NDCG saturates at 1.0 by construction. This is a **recoverability**
result, not a market-alpha claim. Serving this policy against real buyers
requires re-estimating the latent weights from transaction data; the benchmark
cannot tell you what those weights are.

**Search attribution.** Because random search ties on this policy, the
matching-policy experiment says nothing about evolutionary search efficiency.
The Rastrigin comparison is the evidence for that claim, and it is scoped to
multimodal objectives. The grid oracle adds a second, narrower result: on this
space the evolver matches exhaustive search with 29% fewer evaluations.

**Misspecification is the binding constraint, not optimisation.** When a third
of the utility is unobservable, the realisable NDCG gain falls from +0.2333 to
**+0.051**, even though the optimiser still removes 66% of legacy regret. Any
deployment claim should be scaled by that ratio, and the first engineering
priority is adding the missing signal — seller quality, buyer intent, or
conversion history — not tuning the search.

**Specification sensitivity (measured).** The evolved policy dominates the
legacy heuristic at every shift except 0.40, where it trails by 0.016. Upward
shifts are the material risk: at a true midpoint of 0.65 the policy retains
0.7203 NDCG, still far above the legacy 0.3128 but well below its ceiling.
Deployment as a prior should therefore be paired with periodic re-estimation of
the midpoint, not treated as a fixed policy.

---

## 7. Governance: registry and promotion

Measurement alone does not control risk; the artifact needs a lifecycle.
`alpha_registry.py` is an append-only, hash-chained event log: register →
promote → rollback, where each record commits to the previous record's hash.
Editing a stored metric breaks `verify()`, which is the property an audit needs
and a mutable status table cannot provide.

Stages: **shadow → canary → production**, with rollback available from any
stage. Promotion is refused unless every gate passes, and the refusal names each
failure.

```python
from acquisition_platform import AlphaRegistry, EvaluationCard, PromotionGate

registry = AlphaRegistry("benchmarks/alpha_registry.json")
registry.register(card)                      # shadow
decision = registry.promote(
    card.alpha_id,
    PromotionGate(min_ndcg=0.90, min_delta=0.05, max_p_value=0.05),
)
# PromotionDecision(promoted=True, stage='canary', reasons=())
```

Gates measured on this run: NDCG 1.0000 ≥ 0.90; delta 0.2333 ≥ 0.05;
p 0.0000 ≤ 0.05; gap 0.0000 ≤ 0.10 → promoted to canary, chain verified.
The tamper test rewrites a stored NDCG in the JSON file, reloads the registry,
and asserts `verify()` returns `False`.

Lifecycle diagram: `diagrams/alpha_registry.mmd`.

---

## 8. Mutation-testing evidence

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

## 9. Extending the engine

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

## 10. Reproduction checklist

```bash
python -m pytest tests/test_evaluation.py tests/test_alpha_evolution.py \
                 tests/test_matching_policy.py tests/test_alpha_lab.py \
                 tests/test_alpha_robustness.py tests/test_alpha_registry.py \
                 tests/test_alpha_misspecification.py \
                 tests/test_benchmark_suite.py -v
python benchmarks/evolve_alphas.py --buyers 120
```

Artifacts: `benchmarks/alpha_report.json`, `benchmarks/alpha_report.md`,
`benchmarks/baseline.json`, `benchmarks/alpha_registry.json`. The script exits
non-zero if any latency case regresses beyond 25% **and** more than 2 ms over
its stored baseline — the absolute floor exists because scheduler jitter can
double a sub-5 ms median without any code change.
