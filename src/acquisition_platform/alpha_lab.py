"""Alpha lab: evolution of decision policies against labelled ground truth.

The lab builds a reproducible matching benchmark with a known latent utility
function, evolves a :class:`~acquisition_platform.matching.MatchingPolicy`
against the training split, and reports honest out-of-sample performance:

- baseline (legacy heuristic) versus evolved policy on a held-out split
- recovery error of the latent utility weights
- train/test generalisation gap
- bootstrap confidence interval and paired p-value for the NDCG improvement

The benchmark is synthetic by construction but the latent utility is a
documented behavioural assumption (buyers value fair-priced deals), so
recovering it is a falsifiable test of the optimiser rather than a fitted
number.
"""

from __future__ import annotations

import hashlib
import math
import random
import statistics
import time
from dataclasses import dataclass
from typing import Sequence

from acquisition_platform.evaluation import (
    Interval,
    bootstrap_ci,
    ndcg_at_k,
    paired_bootstrap_pvalue,
    spearman_correlation,
)
from acquisition_platform.evolution import (
    Alpha,
    AlphaEvolver,
    EvolutionConfig,
    EvolutionReport,
    Objective,
    ParamSpec,
)
from acquisition_platform.exceptions import InvalidRangeError, ValidationError
from acquisition_platform.matching import Buyer, Seller, MatchingPolicy

WEIGHT_NAMES: tuple[str, str, str] = ("gap_weight", "midpoint_weight", "size_weight")

DEFAULT_TRUE_WEIGHTS: dict[str, float] = {
    "gap_weight": 0.35,
    "midpoint_weight": 0.50,
    "size_weight": 0.15,
}


@dataclass(frozen=True)
class MatchingCase:
    """One buyer with a ranked-by-utility candidate set."""

    buyer: Buyer
    sellers: tuple[Seller, ...]
    relevance: tuple[float, ...]

    @property
    def buyer_id(self) -> str:
        """Identifier of the buyer in this case."""
        return self.buyer.id


@dataclass(frozen=True)
class MatchingSplit:
    """A set of matching cases."""

    cases: tuple[MatchingCase, ...]

    def __len__(self) -> int:
        return len(self.cases)


@dataclass(frozen=True)
class MatchingBenchmark:
    """Train/test benchmark with the latent utility weights."""

    train: MatchingSplit
    test: MatchingSplit
    true_weights: dict[str, float]
    seed: int

    def fingerprint(self) -> str:
        """Stable digest of the benchmark content."""
        digest = hashlib.sha256()
        for case in self.train.cases + self.test.cases:
            digest.update(case.buyer.id.encode())
            digest.update(case.buyer.budget.hex().encode())
            for seller, relevance in zip(case.sellers, case.relevance):
                digest.update(seller.id.encode())
                digest.update(seller.asking_price.hex().encode())
                digest.update(relevance.hex().encode())
        return digest.hexdigest()


@dataclass
class PolicyEvolution:
    """Outcome of evolving a matching policy."""

    report: EvolutionReport
    selected_alpha: Alpha
    baseline_metrics: dict[str, float]
    evolved_metrics: dict[str, float]
    train_metrics: dict[str, float]
    baseline_train_metrics: dict[str, float]
    recovered_weights: dict[str, float]
    true_weights: dict[str, float]
    weight_error_l1: float
    generalization_gap: float
    improvement_ci: Interval
    p_value: float

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serialisable representation."""
        return {
            "report": self.report.to_dict(),
            "selected_alpha": self.selected_alpha.to_dict(),
            "baseline_metrics": dict(self.baseline_metrics),
            "evolved_metrics": dict(self.evolved_metrics),
            "train_metrics": dict(self.train_metrics),
            "baseline_train_metrics": dict(self.baseline_train_metrics),
            "recovered_weights": dict(self.recovered_weights),
            "true_weights": dict(self.true_weights),
            "weight_error_l1": self.weight_error_l1,
            "generalization_gap": self.generalization_gap,
            "improvement_ci": self.improvement_ci.to_dict(),
            "p_value": self.p_value,
        }


@dataclass(frozen=True)
class RobustnessPoint:
    """Performance under one specification shift."""

    offset: float
    baseline_ndcg: float
    evolved_ndcg: float
    delta: float

    def to_dict(self) -> dict[str, float]:
        """Return a JSON-serialisable representation."""
        return {
            "offset": self.offset,
            "baseline_ndcg": self.baseline_ndcg,
            "evolved_ndcg": self.evolved_ndcg,
            "delta": self.delta,
        }


@dataclass(frozen=True)
class FoldResult:
    """Out-of-fold result for one cross-validation split."""

    fold: int
    train_size: int
    test_size: int
    baseline_ndcg: float
    evolved_ndcg: float
    delta: float

    def to_dict(self) -> dict[str, float | int]:
        """Return a JSON-serialisable representation."""
        return {
            "fold": self.fold,
            "train_size": self.train_size,
            "test_size": self.test_size,
            "baseline_ndcg": self.baseline_ndcg,
            "evolved_ndcg": self.evolved_ndcg,
            "delta": self.delta,
        }


@dataclass(frozen=True)
class CVReport:
    """Aggregated k-fold cross-validation of the evolution procedure."""

    n_splits: int
    folds: tuple[FoldResult, ...]
    mean_delta: float
    std_delta: float
    mean_evolved_ndcg: float
    mean_baseline_ndcg: float
    win_rate: float
    p_value: float

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serialisable representation."""
        return {
            "n_splits": self.n_splits,
            "folds": [fold.to_dict() for fold in self.folds],
            "mean_delta": self.mean_delta,
            "std_delta": self.std_delta,
            "mean_evolved_ndcg": self.mean_evolved_ndcg,
            "mean_baseline_ndcg": self.mean_baseline_ndcg,
            "win_rate": self.win_rate,
            "p_value": self.p_value,
        }


def _normalise_weights(weights: dict[str, float]) -> dict[str, float]:
    clipped = {name: max(0.0, weights.get(name, 0.0)) for name in WEIGHT_NAMES}
    total = sum(clipped.values())
    if total <= 0.0:
        return {name: 1.0 / len(WEIGHT_NAMES) for name in WEIGHT_NAMES}
    return {name: value / total for name, value in clipped.items()}


def _ranked_relevance(policy: MatchingPolicy, case: MatchingCase) -> list[float]:
    scored = [
        (policy.score(case.buyer, seller), relevance)
        for seller, relevance in zip(case.sellers, case.relevance)
    ]
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [relevance for _, relevance in scored]


def _price_ratio(policy: MatchingPolicy, case: MatchingCase, top_k: int = 3) -> float:
    scored = [
        (policy.score(case.buyer, seller), seller.asking_price / case.buyer.budget)
        for seller in case.sellers
    ]
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return sum(ratio for _, ratio in scored[:top_k]) / top_k


def _metrics(policy: MatchingPolicy, split: MatchingSplit) -> dict[str, float]:
    ndcgs: list[float] = []
    reciprocal_ranks: list[float] = []
    correlations: list[float] = []
    price_ratios: list[float] = []

    for case in split.cases:
        ordered = _ranked_relevance(policy, case)
        ndcgs.append(ndcg_at_k(ordered, 5))

        reciprocal = 0.0
        for rank, relevance in enumerate(ordered, start=1):
            if relevance >= 0.75:
                reciprocal = 1.0 / rank
                break
        reciprocal_ranks.append(reciprocal)

        model_scores = [
            policy.score(case.buyer, seller) for seller in case.sellers
        ]
        correlations.append(spearman_correlation(model_scores, list(case.relevance)))
        price_ratios.append(_price_ratio(policy, case))

    count = len(split.cases)
    return {
        "ndcg@5": sum(ndcgs) / count,
        "mrr": sum(reciprocal_ranks) / count,
        "spearman": sum(correlations) / count,
        "avg_price_ratio": sum(price_ratios) / count,
    }


class AlphaLab:
    """Benchmark builder and policy evolver."""

    def __init__(
        self,
        seed: int = 7,
        population_size: int = 40,
        generations: int = 30,
    ) -> None:
        if population_size < 2:
            raise InvalidRangeError("population_size must be at least 2")
        if generations < 1:
            raise InvalidRangeError("generations must be at least 1")
        self.seed = seed
        self.population_size = population_size
        self.generations = generations

    # -- benchmark ---------------------------------------------------------

    def build_benchmark(
        self,
        n_buyers: int = 72,
        sellers_per_buyer: int = 12,
        seed: int | None = None,
        midpoint_ratio: float = 0.5,
    ) -> MatchingBenchmark:
        """Build a deterministic matching benchmark.

        Each buyer has a latent utility over candidates: the true weights blend
        budget gap, mid-budget price fit, and deal size. Relevance is the
        min-max normalised utility per buyer, so NDCG is comparable across
        cases regardless of budget scale.

        Args:
            n_buyers: Total number of buyers across both splits.
            sellers_per_buyer: Candidate sellers per buyer.
            seed: Benchmark seed; defaults to the lab seed.
            midpoint_ratio: True fair-value point as a fraction of budget. The
                default 0.5 matches the policy family; other values are used to
                measure specification shift.

        Returns:
            MatchingBenchmark with disjoint 60/40 train/test splits.
        """
        if n_buyers < 10:
            raise InvalidRangeError("n_buyers must be at least 10")
        if sellers_per_buyer < 3:
            raise InvalidRangeError("sellers_per_buyer must be at least 3")
        if not 0.0 < midpoint_ratio <= 1.0:
            raise InvalidRangeError(
                f"midpoint_ratio must be in (0, 1], got {midpoint_ratio}"
            )

        generator = random.Random(self.seed if seed is None else seed)
        categories = ["saas", "fintech", "health", "energy", "logistics", "industrial"]
        cases: list[MatchingCase] = []

        for buyer_index in range(n_buyers):
            budget = round(generator.uniform(60.0, 600.0), 2)
            category = categories[buyer_index % len(categories)]
            buyer = Buyer(
                id=f"b{buyer_index:03d}",
                budget=budget,
                preferences={"category": category},
            )

            sellers: list[Seller] = []
            utilities: list[float] = []
            for seller_index in range(sellers_per_buyer):
                fraction = 0.05 + 0.90 * generator.betavariate(2.0, 2.0)
                price = round(budget * fraction, 2)
                seller = Seller(
                    id=f"s{buyer_index:03d}_{seller_index:02d}",
                    asking_price=price,
                    attributes={"category": category},
                )
                sellers.append(seller)
                utilities.append(self._utility(budget, price, midpoint_ratio))

            low, high = min(utilities), max(utilities)
            span = high - low
            relevance = [
                (value - low) / span if span > 0 else 0.5 for value in utilities
            ]
            cases.append(
                MatchingCase(
                    buyer=buyer,
                    sellers=tuple(sellers),
                    relevance=tuple(relevance),
                )
            )

        generator.shuffle(cases)
        split_point = int(len(cases) * 0.6)
        return MatchingBenchmark(
            train=MatchingSplit(tuple(cases[:split_point])),
            test=MatchingSplit(tuple(cases[split_point:])),
            true_weights=dict(DEFAULT_TRUE_WEIGHTS),
            seed=self.seed if seed is None else seed,
        )

    @staticmethod
    def _utility(budget: float, price: float, midpoint_ratio: float = 0.5) -> float:
        price_ratio = price / budget
        gap = 1.0 - price_ratio
        midpoint = 1.0 - abs(price - midpoint_ratio * budget) / budget
        size = min(1.0, price_ratio)
        return (
            DEFAULT_TRUE_WEIGHTS["gap_weight"] * gap
            + DEFAULT_TRUE_WEIGHTS["midpoint_weight"] * midpoint
            + DEFAULT_TRUE_WEIGHTS["size_weight"] * size
        )

    # -- evolution ---------------------------------------------------------

    def evolve_matching_policy(
        self, benchmark: MatchingBenchmark, seed: int | None = None
    ) -> PolicyEvolution:
        """Evolve a matching policy on the training split.

        Two objectives are optimised: NDCG@5 (ranking quality against the
        latent utility) and value (cheapness of the top candidates). They
        genuinely conflict, so the run produces a non-trivial Pareto front.
        The final alpha is selected by training NDCG@5, the primary metric.

        Args:
            benchmark: Benchmark produced by :meth:`build_benchmark`.
            seed: Optional run seed; defaults to the lab seed.

        Returns:
            PolicyEvolution with baseline, evolved and recovery statistics.
        """
        run_seed = self.seed if seed is None else seed
        space = [
            ParamSpec("gap_weight", 0.0, 1.0),
            ParamSpec("midpoint_weight", 0.0, 1.0),
            ParamSpec("size_weight", 0.0, 1.0),
            ParamSpec("bias", -0.2, 0.2),
        ]
        objectives = [
            Objective("ndcg@5", maximize=True, weight=1.0, target=0.90),
            Objective("value", maximize=True, weight=0.35),
        ]

        def evaluate(params: dict[str, float]) -> dict[str, float]:
            policy = MatchingPolicy.from_params(params)
            metrics = _metrics(policy, benchmark.train)
            return {
                "ndcg@5": metrics["ndcg@5"],
                "value": 1.0 - metrics["avg_price_ratio"],
            }

        evolver = AlphaEvolver(
            space,
            objectives,
            config=EvolutionConfig(
                population_size=self.population_size,
                generations=self.generations,
                seed=run_seed,
                elitism=2,
                patience=self.generations,
            ),
        )
        report = evolver.evolve(
            evaluate,
            baseline_params={
                "gap_weight": 1.0,
                "midpoint_weight": 0.0,
                "size_weight": 0.0,
                "bias": 0.0,
            },
        )

        candidates: Sequence[Alpha] = list(report.pareto_front) + [report.best]
        selected = max(
            candidates,
            key=lambda alpha: (alpha.objectives["ndcg@5"], alpha.fitness),
        )

        baseline_policy = MatchingPolicy()
        evolved_policy = MatchingPolicy.from_params(selected.params)

        baseline_train = _metrics(baseline_policy, benchmark.train)
        baseline_test = _metrics(baseline_policy, benchmark.test)
        train_metrics = _metrics(evolved_policy, benchmark.train)
        evolved_metrics = _metrics(evolved_policy, benchmark.test)

        per_case_baseline = [
            ndcg_at_k(_ranked_relevance(baseline_policy, case), 5)
            for case in benchmark.test.cases
        ]
        per_case_evolved = [
            ndcg_at_k(_ranked_relevance(evolved_policy, case), 5)
            for case in benchmark.test.cases
        ]

        recovered = _normalise_weights(
            {name: selected.params.get(name, 0.0) for name in WEIGHT_NAMES}
        )
        true_weights = _normalise_weights(benchmark.true_weights)
        error = sum(abs(recovered[name] - true_weights[name]) for name in WEIGHT_NAMES)

        return PolicyEvolution(
            report=report,
            selected_alpha=selected,
            baseline_metrics=baseline_test,
            evolved_metrics=evolved_metrics,
            train_metrics=train_metrics,
            baseline_train_metrics=baseline_train,
            recovered_weights=recovered,
            true_weights=true_weights,
            weight_error_l1=error,
            generalization_gap=abs(train_metrics["ndcg@5"] - evolved_metrics["ndcg@5"]),
            improvement_ci=bootstrap_ci(
                [e - b for e, b in zip(per_case_evolved, per_case_baseline)],
                n_resamples=1000,
                seed=run_seed,
            ),
            p_value=paired_bootstrap_pvalue(
                per_case_evolved, per_case_baseline, n_resamples=1000, seed=run_seed
            ),
        )

    # -- robustness, validation and baselines ------------------------------

    def robustness_curve(
        self,
        params: dict[str, float],
        offsets: Sequence[float],
        n_buyers: int = 120,
        sellers_per_buyer: int = 12,
    ) -> list[RobustnessPoint]:
        """Evaluate one policy across shifted fair-value assumptions.

        The policy is trained at midpoint 0.5. Each offset rebuilds the
        benchmark with the latent utility centred elsewhere, holding buyers and
        prices fixed, so the curve isolates specification error from sampling
        noise.

        Args:
            params: Evolved policy parameters.
            offsets: True midpoint ratios to test, in (0, 1].
            n_buyers: Buyers per shifted benchmark.
            sellers_per_buyer: Candidate sellers per buyer.

        Returns:
            One point per offset, in the order supplied.
        """
        if not offsets:
            raise ValidationError("offsets cannot be empty")
        policy = MatchingPolicy.from_params(params)
        baseline = MatchingPolicy()
        points: list[RobustnessPoint] = []
        for offset in offsets:
            if not 0.0 < offset <= 1.0:
                raise InvalidRangeError(
                    f"offset must be in (0, 1], got {offset}"
                )
            shifted = self.build_benchmark(
                n_buyers=n_buyers,
                sellers_per_buyer=sellers_per_buyer,
                seed=self.seed,
                midpoint_ratio=offset,
            )
            evolved_ndcg = _metrics(policy, shifted.test)["ndcg@5"]
            baseline_ndcg = _metrics(baseline, shifted.test)["ndcg@5"]
            points.append(
                RobustnessPoint(
                    offset=offset,
                    baseline_ndcg=baseline_ndcg,
                    evolved_ndcg=evolved_ndcg,
                    delta=evolved_ndcg - baseline_ndcg,
                )
            )
        return points

    def cross_validate(
        self,
        n_splits: int = 5,
        n_buyers: int = 120,
        sellers_per_buyer: int = 12,
    ) -> CVReport:
        """Run k-fold cross-validation of the whole evolution procedure.

        Each fold re-runs the search on its training partition and is scored on
        the held-out partition, so the reported delta is out-of-sample in every
        fold. Fold seeds differ, which also measures seed sensitivity.

        Args:
            n_splits: Number of folds, at least 2.
            n_buyers: Total buyers to partition.
            sellers_per_buyer: Candidate sellers per buyer.

        Returns:
            CVReport with per-fold and aggregate statistics.
        """
        if n_splits < 2:
            raise InvalidRangeError("n_splits must be at least 2")
        benchmark = self.build_benchmark(
            n_buyers=n_buyers,
            sellers_per_buyer=sellers_per_buyer,
            seed=self.seed,
        )
        cases = list(benchmark.train.cases) + list(benchmark.test.cases)
        if n_splits > len(cases):
            raise InvalidRangeError("n_splits exceeds the number of cases")

        fold_size = len(cases) // n_splits
        folds: list[FoldResult] = []
        for fold in range(n_splits):
            start = fold * fold_size
            end = len(cases) if fold == n_splits - 1 else start + fold_size
            test_cases = cases[start:end]
            train_cases = cases[:start] + cases[end:]
            fold_benchmark = MatchingBenchmark(
                train=MatchingSplit(tuple(train_cases)),
                test=MatchingSplit(tuple(test_cases)),
                true_weights=benchmark.true_weights,
                seed=self.seed + fold,
            )
            outcome = self.evolve_matching_policy(fold_benchmark, seed=self.seed + fold)
            baseline_ndcg = outcome.baseline_metrics["ndcg@5"]
            evolved_ndcg = outcome.evolved_metrics["ndcg@5"]
            folds.append(
                FoldResult(
                    fold=fold,
                    train_size=len(train_cases),
                    test_size=len(test_cases),
                    baseline_ndcg=baseline_ndcg,
                    evolved_ndcg=evolved_ndcg,
                    delta=evolved_ndcg - baseline_ndcg,
                )
            )

        deltas = [fold.delta for fold in folds]
        return CVReport(
            n_splits=n_splits,
            folds=tuple(folds),
            mean_delta=statistics.fmean(deltas),
            std_delta=statistics.pstdev(deltas),
            mean_evolved_ndcg=statistics.fmean([f.evolved_ndcg for f in folds]),
            mean_baseline_ndcg=statistics.fmean([f.baseline_ndcg for f in folds]),
            win_rate=sum(1 for delta in deltas if delta > 0) / len(deltas),
            p_value=paired_bootstrap_pvalue(
                [f.evolved_ndcg for f in folds],
                [f.baseline_ndcg for f in folds],
                n_resamples=1000,
                seed=self.seed,
            ),
        )

    def random_search_baseline(
        self,
        benchmark: MatchingBenchmark,
        budget: int = 200,
        seed: int | None = None,
    ) -> dict[str, object]:
        """Sample the policy space uniformly and keep the best training policy.

        This is the comparison that tells you whether the evolutionary search
        earns its cost: at the same evaluation budget, does random sampling find
        an equally good policy?

        Args:
            benchmark: Benchmark to search against.
            budget: Number of random policies to evaluate.
            seed: Sampler seed; defaults to the lab seed.

        Returns:
            Dictionary with the best parameters and train/test NDCG@5.
        """
        if budget < 1:
            raise InvalidRangeError("budget must be at least 1")
        generator = random.Random(self.seed if seed is None else seed)
        best_params: dict[str, float] = {
            "gap_weight": 1.0,
            "midpoint_weight": 0.0,
            "size_weight": 0.0,
            "bias": 0.0,
        }
        best_train = -1.0
        for _ in range(budget):
            candidate = {
                "gap_weight": generator.uniform(0.0, 1.0),
                "midpoint_weight": generator.uniform(0.0, 1.0),
                "size_weight": generator.uniform(0.0, 1.0),
                "bias": generator.uniform(-0.2, 0.2),
            }
            train_ndcg = _metrics(
                MatchingPolicy.from_params(candidate), benchmark.train
            )["ndcg@5"]
            if train_ndcg > best_train:
                best_train = train_ndcg
                best_params = candidate
        test_ndcg = _metrics(
            MatchingPolicy.from_params(best_params), benchmark.test
        )["ndcg@5"]
        return {
            "params": best_params,
            "train_ndcg@5": best_train,
            "test_ndcg@5": test_ndcg,
            "evaluations": budget,
        }


def run_alpha_lab(
    seed: int = 7, population_size: int = 40, generations: int = 30
) -> PolicyEvolution:
    """Convenience entry point: build the benchmark and evolve in one call."""
    lab = AlphaLab(seed=seed, population_size=population_size, generations=generations)
    benchmark = lab.build_benchmark(seed=seed)
    return lab.evolve_matching_policy(benchmark)


@dataclass(frozen=True)
class SearchComparison:
    """Evolutionary search versus uniform random search at equal budget."""

    function: str
    dimensions: int
    budget: int
    evolutionary_best: float
    random_best: float
    evolutionary_evals: int
    random_evals: int
    wall_seconds: float

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serialisable representation."""
        return {
            "function": self.function,
            "dimensions": self.dimensions,
            "budget": self.budget,
            "evolutionary_best": self.evolutionary_best,
            "random_best": self.random_best,
            "evolutionary_evals": self.evolutionary_evals,
            "random_evals": self.random_evals,
            "wall_seconds": self.wall_seconds,
        }


def compare_search_strategies(
    budget: int = 2000,
    seed: int = 7,
    dimensions: int = 5,
    population_size: int = 40,
) -> SearchComparison:
    """Compare NSGA-II against uniform random search on a multimodal objective.

    The matching-policy benchmark is smooth and low-dimensional, so random
    sampling can reach its ceiling — a useful negative result about that
    benchmark. This function measures where search strategy *does* matter, using
    the Rastrigin function, whose local optima are dense enough that uniform
    sampling rarely lands near the global optimum.

    Args:
        budget: Evaluation budget per strategy.
        seed: Seed for both strategies.
        dimensions: Problem dimension.
        population_size: Population for the evolutionary run.

    Returns:
        SearchComparison with the best fitness found by each strategy.
    """
    if budget < 10:
        raise InvalidRangeError("budget must be at least 10")
    if dimensions < 1:
        raise InvalidRangeError("dimensions must be at least 1")

    generations = max(1, (budget - population_size) // population_size)
    space = [ParamSpec(f"x{i}", -5.12, 5.12) for i in range(dimensions)]

    def rastrigin(params: dict[str, float]) -> dict[str, float]:
        total = sum(
            value * value - 10.0 * math.cos(2.0 * math.pi * value) + 10.0
            for value in params.values()
        )
        return {"score": -total}

    started = time.perf_counter()
    evolver = AlphaEvolver(
        space,
        [Objective("score")],
        EvolutionConfig(
            population_size=population_size,
            generations=generations,
            seed=seed,
        ),
    )
    report = evolver.evolve(rastrigin)

    generator = random.Random(seed)
    best_random = float("-inf")
    for _ in range(budget):
        total = sum(
            (value := generator.uniform(-5.12, 5.12)) * value
            - 10.0 * math.cos(2.0 * math.pi * value)
            + 10.0
            for _ in range(dimensions)
        )
        best_random = max(best_random, -total)

    return SearchComparison(
        function="rastrigin",
        dimensions=dimensions,
        budget=budget,
        evolutionary_best=report.best_fitness,
        random_best=best_random,
        evolutionary_evals=report.evaluations,
        random_evals=budget,
        wall_seconds=time.perf_counter() - started,
    )
