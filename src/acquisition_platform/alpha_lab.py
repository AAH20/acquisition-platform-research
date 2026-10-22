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
import random
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

        Returns:
            MatchingBenchmark with disjoint 60/40 train/test splits.
        """
        if n_buyers < 10:
            raise InvalidRangeError("n_buyers must be at least 10")
        if sellers_per_buyer < 3:
            raise InvalidRangeError("sellers_per_buyer must be at least 3")

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
                utilities.append(self._utility(budget, price))

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
    def _utility(budget: float, price: float) -> float:
        price_ratio = price / budget
        gap = 1.0 - price_ratio
        midpoint = 1.0 - abs(price - budget / 2.0) / budget
        size = min(1.0, price_ratio)
        return (
            DEFAULT_TRUE_WEIGHTS["gap_weight"] * gap
            + DEFAULT_TRUE_WEIGHTS["midpoint_weight"] * midpoint
            + DEFAULT_TRUE_WEIGHTS["size_weight"] * size
        )

    # -- evolution ---------------------------------------------------------

    def evolve_matching_policy(self, benchmark: MatchingBenchmark) -> PolicyEvolution:
        """Evolve a matching policy on the training split.

        Two objectives are optimised: NDCG@5 (ranking quality against the
        latent utility) and value (cheapness of the top candidates). They
        genuinely conflict, so the run produces a non-trivial Pareto front.
        The final alpha is selected by training NDCG@5, the primary metric.

        Args:
            benchmark: Benchmark produced by :meth:`build_benchmark`.

        Returns:
            PolicyEvolution with baseline, evolved and recovery statistics.
        """
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
                seed=self.seed,
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
                seed=self.seed,
            ),
            p_value=paired_bootstrap_pvalue(
                per_case_evolved, per_case_baseline, n_resamples=1000, seed=self.seed
            ),
        )


def run_alpha_lab(
    seed: int = 7, population_size: int = 40, generations: int = 30
) -> PolicyEvolution:
    """Convenience entry point: build the benchmark and evolve in one call."""
    lab = AlphaLab(seed=seed, population_size=population_size, generations=generations)
    benchmark = lab.build_benchmark(seed=seed)
    return lab.evolve_matching_policy(benchmark)
