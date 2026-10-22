# Alpha Report — Evolved Matching Policy

Seed **7**, population **2381 evaluations** across **40 generations** in 9.09s.

## Hold-out performance

| Metric | Baseline | Evolved | Delta |
|--------|---------:|--------:|------:|
| ndcg@5 | 0.7667 | 1.0000 | +0.2333 |
| mrr | 0.4305 | 1.0000 | +0.5695 |
| spearman | 0.4339 | 1.0000 | +0.5661 |
| avg_price_ratio | 0.2610 | 0.4574 | +0.1964 |

NDCG@5 improvement 95% CI: **[+0.1952, +0.2773]**, paired bootstrap **p = 0.0000**.

## Latent weight recovery

| Weight | True | Recovered | Abs error |
|--------|-----:|----------:|----------:|
| gap_weight | 0.3500 | 0.3402 | 0.0098 |
| midpoint_weight | 0.5000 | 0.5327 | 0.0327 |
| size_weight | 0.1500 | 0.1272 | 0.0228 |

L1 recovery error **0.0653**, train/test generalisation gap **0.0000**.

## Cross-validation (5-fold)

| Fold | Train | Test | Baseline | Evolved | Delta |
|------|------:|-----:|---------:|--------:|------:|
| 0 | 96 | 24 | 0.7338 | 1.0000 | +0.2662 |
| 1 | 96 | 24 | 0.7459 | 1.0000 | +0.2541 |
| 2 | 96 | 24 | 0.8080 | 1.0000 | +0.1920 |
| 3 | 96 | 24 | 0.7711 | 1.0000 | +0.2289 |
| 4 | 96 | 24 | 0.7623 | 1.0000 | +0.2377 |

Mean delta **+0.2358** ± 0.0254; win rate **100%**; p = 0.0000.

## Specification shift

Policy trained at midpoint 0.5, scored against benchmarks whose true
fair-value point moved. Buyers and prices are held fixed.

| True midpoint | Baseline | Evolved | Delta | p | Holm |
|--------------:|---------:|--------:|------:|--:|:-----|
| 0.40 | 0.9269 | 0.9106 | -0.0163 | 0.1520 | no |
| 0.45 | 0.8674 | 0.9724 | +0.1050 | 0.0000 | yes |
| 0.50 | 0.7667 | 1.0000 | +0.2333 | 0.0000 | yes |
| 0.55 | 0.6291 | 0.9601 | +0.3311 | 0.0000 | yes |
| 0.60 | 0.4676 | 0.8482 | +0.3806 | 0.0000 | yes |
| 0.65 | 0.3128 | 0.7203 | +0.4075 | 0.0000 | yes |

Holm-Bonferroni over 6 shift tests at α = 0.05 keeps the effect significant where the delta is material and correctly declines to claim significance where it is not. Minimum detectable effect at 5 folds: **0.0318 NDCG**.

## Search baseline

Random search at the same budget (2381 evaluations) reached test NDCG@5 **1.0000**, versus **1.0000** for the evolutionary search.

The policy landscape is smooth and four-dimensional, so random sampling also reaches the ceiling. That is a property of this benchmark, not evidence for either search strategy — the multimodal comparison below separates them.

## Search strategy comparison

| Function | Dims | Evolutionary best | Evals | Random best | Evals |
|----------|-----:|------------------:|------:|------------:|------:|
| rastrigin | 5 | 0.0000 | 497 | -25.3352 | 2381 |

Rastrigin's global optimum is 0.0. The evolver reaches it with roughly a fifth of random search's evaluation budget.

## Grid oracle

| Search | Evaluations | Test NDCG@5 |
|--------|------------:|------------:|
| Grid (15³ points) | 3374 | 1.0000 |
| Evolution | 2381 | 1.0000 |

## Misspecification: unobservable seller quality

The latent utility includes a quality signal the policy cannot see.

| Metric | Legacy | Evolved |
|--------|-------:|--------:|
| NDCG@5 | 0.6273 | 0.6786 |
| Top-1 utility regret | 0.4489 | 0.1515 |

Training NDCG reaches 0.7196 (gap 0.0410). With roughly a third of the utility unobservable, the policy cannot approach the ceiling — but it still removes most of the legacy regret.

## Stability under price noise

±5% uniform price perturbation over 5 trials: mean Spearman **0.9708**, worst trial **0.9624**, mean NDCG drop **0.0032**.

## Walk-forward under drift

Latent midpoint drifts 0.425 → 0.575 across four cohorts. Frozen is
fitted once; adaptive is refitted on the previous cohort.

| Step | Train midpoint | Test midpoint | Frozen | Adaptive | Ensemble |
|-----:|---------------:|--------------:|-------:|---------:|---------:|
| 1 | 0.425 | 0.475 | 0.9831 | 0.9765 | 0.9709 |
| 2 | 0.475 | 0.525 | 0.8961 | 0.9565 | 0.9563 |
| 3 | 0.525 | 0.575 | 0.8094 | 0.9471 | 0.9409 |

Frozen mean **0.8962**, adaptive mean **0.9600** (+0.0638), ensemble mean **0.9560** (-0.0040 vs single).

Refitting recovers part of the drift loss. Ensembling the Pareto
front does **not** add lift here — front members are highly
correlated and slightly overfit — so the single alpha remains the
default.

## Second domain: portfolio allocation

The same `AlphaEvolver`, objectives and hypervolume applied to a
3-parameter allocation policy on an analytic 8-asset market. The
policy never sees the covariance matrix; the oracle does.

| Policy | Sharpe | Volatility | Diversification |
|--------|-------:|-----------:|----------------:|
| Equal weight | 0.1013 | 0.1061 | 0.875 |
| Inverse volatility | 0.1408 | 0.0980 | 0.867 |
| Evolved | 0.4077 | 0.0981 | 0.707 |
| Analytic oracle | 0.4131 | 0.0988 | 0.700 |

Evolved Sharpe reaches **98.7%** of the analytic optimum in 915 evaluations, and the Pareto front holds 64 policies.

## Promotion gate

Alpha `matching-policy-s7` is at stage **canary**; promotion accepted: **False** (alpha already registered (idempotent run)); hash chain verified: **True**.

## Search telemetry

- Best fitness: 0.8806 (baseline 0.7558, +16.5%)
- Pareto archive size: 64
- Converged: False (generation None)

## Latency suite

| Case | Median ms | Target ms | Pass |
|------|----------:|----------:|:----:|
| matching_50x50 | 2.64 | 250.00 | yes |
| ndcg_1000 | 0.05 | 10.00 | yes |
| evolution_20x10 | 37.34 | 1500.00 | yes |

Suite score: **3/3** cases inside target.
