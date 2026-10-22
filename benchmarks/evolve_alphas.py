"""Run the alpha evolution experiment and write auditable report artifacts.

Usage:
    python benchmarks/evolve_alphas.py [--seed 7] [--population 60] [--generations 40]

Artifacts:
    benchmarks/alpha_report.json   -- full machine-readable result
    benchmarks/alpha_report.md     -- human-readable summary
    benchmarks/baseline.json       -- latency baseline (created on first run)

Exit codes:
    0 -- experiment completed and no benchmark regression
    1 -- a latency regression exceeded tolerance
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from acquisition_platform.alpha_lab import AlphaLab  # noqa: E402
from acquisition_platform.benchmark_suite import (  # noqa: E402
    BenchmarkCase,
    BenchmarkSuite,
    SuiteReport,
)
from acquisition_platform.evaluation import ndcg_at_k  # noqa: E402
from acquisition_platform.evolution import (  # noqa: E402
    AlphaEvolver,
    EvolutionConfig,
    Objective,
    ParamSpec,
)
from acquisition_platform.matching import Buyer, Seller, BuyerSellerMatcher  # noqa: E402


def build_latency_suite() -> BenchmarkSuite:
    """Benchmark three representative platform operations."""
    buyers = [
        Buyer(id=f"b{i}", budget=100.0 + i, preferences={"category": "saas"})
        for i in range(50)
    ]
    sellers = [
        Seller(id=f"s{i}", asking_price=20.0 + (i % 70), attributes={"category": "saas"})
        for i in range(50)
    ]
    matcher = BuyerSellerMatcher()

    relevances = [(i % 17) / 16.0 for i in range(1000)]

    def run_matching() -> None:
        matcher.match(buyers, sellers)

    def run_ndcg() -> None:
        ndcg_at_k(relevances, 10)

    def run_evolution() -> None:
        evolver = AlphaEvolver(
            [ParamSpec("x", -5.0, 5.0)],
            [Objective("score")],
            EvolutionConfig(population_size=20, generations=10, seed=3),
        )
        evolver.evolve(
            lambda p: {"score": -(p["x"] ** 2)},
            baseline_params={"x": 4.0},
        )

    suite = BenchmarkSuite("platform-core")
    suite.add(BenchmarkCase("matching_50x50", run_matching, target_ms=250.0))
    suite.add(BenchmarkCase("ndcg_1000", run_ndcg, target_ms=10.0))
    suite.add(BenchmarkCase("evolution_20x10", run_evolution, target_ms=1500.0))
    return suite


def write_markdown(path: Path, payload: dict[str, Any], suite: SuiteReport) -> None:
    metrics = payload["baseline_metrics"]
    evolved = payload["evolved_metrics"]
    report = payload["report"]
    ci = payload["improvement_ci"]
    recovered = payload["recovered_weights"]
    true_weights = payload["true_weights"]

    lines = [
        "# Alpha Report — Evolved Matching Policy",
        "",
        f"Seed **{report['seed']}**, population **{report['evaluations']} evaluations** across "
        f"**{report['generations_run']} generations** in {report['elapsed_seconds']:.2f}s.",
        "",
        "## Hold-out performance",
        "",
        "| Metric | Baseline | Evolved | Delta |",
        "|--------|---------:|--------:|------:|",
    ]
    for key in ("ndcg@5", "mrr", "spearman", "avg_price_ratio"):
        base = float(metrics[key])
        now = float(evolved[key])
        lines.append(f"| {key} | {base:.4f} | {now:.4f} | {now - base:+.4f} |")

    lines += [
        "",
        f"NDCG@5 improvement 95% CI: **[{ci['low']:+.4f}, {ci['high']:+.4f}]**, "
        f"paired bootstrap **p = {payload['p_value']:.4f}**.",
        "",
        "## Latent weight recovery",
        "",
        "| Weight | True | Recovered | Abs error |",
        "|--------|-----:|----------:|----------:|",
    ]
    for name in ("gap_weight", "midpoint_weight", "size_weight"):
        lines.append(
            f"| {name} | {float(true_weights[name]):.4f} | "
            f"{float(recovered[name]):.4f} | "
            f"{abs(float(true_weights[name]) - float(recovered[name])):.4f} |"
        )

    lines += [
        "",
        f"L1 recovery error **{float(payload['weight_error_l1']):.4f}**, "
        f"train/test generalisation gap **{float(payload['generalization_gap']):.4f}**.",
        "",
        "## Search telemetry",
        "",
        f"- Best fitness: {float(report['best_fitness']):.4f} "
        f"(baseline {float(report['baseline_fitness']):.4f}, "
        f"{float(report['improvement_pct']):+.1f}%)",
        f"- Pareto archive size: {len(report['pareto_front'])}",
        f"- Converged: {report['converged']} "
        f"(generation {report['convergence_generation']})",
        "",
        "## Latency suite",
        "",
        "| Case | Median ms | Target ms | Pass |",
        "|------|----------:|----------:|:----:|",
    ]
    for item in suite.results:
        lines.append(
            f"| {item.name} | {item.value:.2f} | {item.target:.2f} | "
            f"{'yes' if item.passed else 'no'} |"
        )
    lines += [
        "",
        f"Suite score: **{suite.passed}/{suite.total}** cases inside target.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--population", type=int, default=60)
    parser.add_argument("--generations", type=int, default=40)
    parser.add_argument("--buyers", type=int, default=120)
    args = parser.parse_args()

    out_dir = ROOT / "benchmarks"
    out_dir.mkdir(exist_ok=True)

    started = time.perf_counter()
    lab = AlphaLab(
        seed=args.seed,
        population_size=args.population,
        generations=args.generations,
    )
    benchmark = lab.build_benchmark(n_buyers=args.buyers, seed=args.seed)
    result = lab.evolve_matching_policy(benchmark)
    payload = result.to_dict()
    payload["metadata"] = {
        "buyers": args.buyers,
        "sellers_per_buyer": 12,
        "train_cases": len(benchmark.train),
        "test_cases": len(benchmark.test),
        "benchmark_fingerprint": benchmark.fingerprint()[:16],
        "wall_seconds": round(time.perf_counter() - started, 3),
    }

    suite = build_latency_suite()
    suite_report = suite.run(repeats=3, warmup=1)
    payload["latency"] = suite_report.to_dict()

    (out_dir / "alpha_report.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    write_markdown(out_dir / "alpha_report.md", payload, suite_report)

    baseline_path = out_dir / "baseline.json"
    regression_count = 0
    if baseline_path.exists():
        baseline = SuiteReport.load(baseline_path)
        regressions = suite_report.compare_to_baseline(baseline, tolerance=0.25)
        regression_count = len(regressions)
        for regression in regressions:
            print(
                f"REGRESSION {regression.name}: {regression.change_pct:+.1f}% "
                f"({regression.baseline:.2f} -> {regression.current:.2f} ms)"
            )
    else:
        suite_report.save(baseline_path)
        print(f"Baseline written to {baseline_path.relative_to(ROOT)}")

    print(
        f"NDCG@5 baseline={result.baseline_metrics['ndcg@5']:.4f} "
        f"evolved={result.evolved_metrics['ndcg@5']:.4f} "
        f"(p={result.p_value:.4f}, weight_L1={result.weight_error_l1:.4f}, "
        f"gap={result.generalization_gap:.4f})"
    )
    print(f"Artifacts: benchmarks/alpha_report.json, benchmarks/alpha_report.md")
    return 1 if regression_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
