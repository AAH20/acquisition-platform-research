# Alpha Report — Evolved Matching Policy

Seed **7**, population **2381 evaluations** across **40 generations** in 9.51s.

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

## Search telemetry

- Best fitness: 0.8806 (baseline 0.7558, +16.5%)
- Pareto archive size: 64
- Converged: False (generation None)

## Latency suite

| Case | Median ms | Target ms | Pass |
|------|----------:|----------:|:----:|
| matching_50x50 | 2.52 | 250.00 | yes |
| ndcg_1000 | 0.06 | 10.00 | yes |
| evolution_20x10 | 40.45 | 1500.00 | yes |

Suite score: **3/3** cases inside target.
