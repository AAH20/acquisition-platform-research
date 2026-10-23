"""Third-domain proof: first-price bid shading scored by a *sampled* objective.

The first two domains are evaluated exactly. The matching lab scores a policy on
a fixed benchmark, and the portfolio lab scores it on an analytic market where
the Sharpe ratio is a closed-form number. Both let the evolver compare
candidates on a noise-free objective.

This module is different on purpose. A bidder competes in a first-price sealed
bid auction against ``n - 1`` rivals who play the symmetric Bayes-Nash
equilibrium ``b(u) = ((n - 1) / n) u`` with values drawn uniformly. Its own
policy is the three-gene family

    b(v) = shade * v ** curve * (1 + low_value_tilt * (1 - v))

and its objective is *estimated* from a finite transcript of simulated
auctions. Every candidate is scored on a different transcript, so comparing two
candidates means comparing two noisy numbers. That is the whole point: the
shared :class:`~acquisition_platform.evolution.AlphaEvolver` has to work when
the objective is a sample, not a formula.

The domain has an exact answer, so the claim is falsifiable rather than
rhetorical:

- The family contains the equilibrium, and the equilibrium policy earns
  ``1 / (n (n + 1))`` per auction with win rate ``1 / n`` (revenue equivalence
  for the uniform independent-private-values model).
- The profit surface is single-peaked but very flat near the optimum, so profit
  is recovered far more precisely than the genes that produce it.
- Win rate is a poor proxy for profit: bidding truthfully wins more often than
  the equilibrium policy and earns exactly nothing.

Three sample sizes keep the measurement honest: the evolver only ever sees
``sample_size`` auctions per evaluation, a disjoint ``validation_size``
transcript selects one member of the Pareto front, and every number in the
report is measured on a disjoint ``audit_size`` transcript that no part of the
search touched.

Everything is stdlib-only and deterministic for a fixed seed.
"""

from __future__ import annotations

import hashlib
import math
import random
import statistics
import time
from collections.abc import Callable
from dataclasses import dataclass

from acquisition_platform.evolution import (
    Alpha,
    AlphaEvolver,
    EvolutionConfig,
    EvolutionReport,
    Objective,
    ParamSpec,
)
from acquisition_platform.exceptions import InvalidRangeError, ValidationError

PARAM_NAMES: tuple[str, str, str] = ("shade", "curve", "low_value_tilt")

SHADE_BOUNDS: tuple[float, float] = (0.40, 1.00)
CURVE_BOUNDS: tuple[float, float] = (0.80, 1.25)
TILT_BOUNDS: tuple[float, float] = (-0.60, 0.60)

GRID_SHADES: tuple[float, ...] = tuple(
    round(0.45 + 0.025 * index, 6) for index in range(23)
)
GRID_CURVES: tuple[float, ...] = tuple(
    round(0.80 + 0.05 * index, 6) for index in range(9)
)
GRID_TILTS: tuple[float, ...] = tuple(
    round(-0.50 + 0.25 * index, 6) for index in range(5)
)

EVAL_TAG = 1
VALIDATION_TAG = 2
GRID_TAG = 3
AUDIT_TAG = 4

_MODULUS = 2**32
_MULTIPLIER = 2_654_435_761
_TAG_STRIDE = 40_503
_INDEX_STRIDE = 1_000_003

_EQUILIBRIUM_CURVE = 1.0
_EQUILIBRIUM_TILT = 0.0


@dataclass(frozen=True)
class AuctionMarket:
    """A first-price auction market with symmetric equilibrium rivals.

    Args:
        n_bidders: Total number of bidders, including the learner. Must be at
            least two.

    Rivals are not strategic learners: every rival bids the symmetric Bayes-Nash
    equilibrium slope for a uniform independent-private-values first-price
    auction. The learner therefore faces a stationary environment whose best
    response is known in closed form.
    """

    n_bidders: int = 4

    def __post_init__(self) -> None:
        if self.n_bidders < 2:
            raise InvalidRangeError(
                f"n_bidders must be at least 2, got {self.n_bidders}"
            )

    @property
    def n_rivals(self) -> int:
        """Number of competing bidders."""
        return self.n_bidders - 1

    @property
    def rival_shade(self) -> float:
        """Slope ``(n - 1) / n`` every rival applies to its own value."""
        return self.n_rivals / self.n_bidders

    @property
    def equilibrium_profit(self) -> float:
        """Ex-ante profit per auction of the symmetric equilibrium policy."""
        return 1.0 / (self.n_bidders * (self.n_bidders + 1))

    @property
    def equilibrium_win_rate(self) -> float:
        """Win rate of the symmetric equilibrium policy, ``1 / n``."""
        return 1.0 / self.n_bidders

    def fingerprint(self) -> str:
        """Stable digest of the market definition."""
        digest = hashlib.sha256()
        digest.update(f"first-price|n={self.n_bidders}".encode())
        return digest.hexdigest()


@dataclass(frozen=True)
class ExperimentBudget:
    """Sample sizes used by one experiment.

    Args:
        sample_size: Auctions in each transcript handed to the evolver.
        validation_size: Auctions used to pick one member of the Pareto front.
        grid_size: Auctions used by the brute-force grid comparator.
        audit_size: Auctions used to report every number in the result.
    """

    sample_size: int = 300
    validation_size: int = 1200
    grid_size: int = 4000
    audit_size: int = 6000

    def __post_init__(self) -> None:
        for name, value in (
            ("sample_size", self.sample_size),
            ("validation_size", self.validation_size),
            ("grid_size", self.grid_size),
            ("audit_size", self.audit_size),
        ):
            if value < 2:
                raise InvalidRangeError(f"{name} must be at least 2, got {value}")

    def to_dict(self) -> dict[str, int]:
        """Return a JSON-serialisable representation."""
        return {
            "sample_size": self.sample_size,
            "validation_size": self.validation_size,
            "grid_size": self.grid_size,
            "audit_size": self.audit_size,
        }


@dataclass(frozen=True)
class AuctionSample:
    """A frozen transcript of auctions.

    Attributes:
        values: The learner's private value in each auction, in ``[0, 1]``.
        rival_bids: The highest rival bid in each auction, in rival bid units.
        seed: Seed the transcript was drawn from.
    """

    values: tuple[float, ...]
    rival_bids: tuple[float, ...]
    seed: int

    def __post_init__(self) -> None:
        if not self.values:
            raise InvalidRangeError("an auction transcript needs at least one auction")
        if len(self.values) != len(self.rival_bids):
            raise ValidationError(
                f"values and rival_bids must align, got {len(self.values)} "
                f"and {len(self.rival_bids)}"
            )
        for value in self.values:
            if not 0.0 <= value <= 1.0:
                raise InvalidRangeError(f"value must be in [0, 1], got {value}")

    @property
    def size(self) -> int:
        """Number of auctions in the transcript."""
        return len(self.values)

    def fingerprint(self) -> str:
        """Stable digest of the transcript."""
        digest = hashlib.sha256()
        digest.update(f"sample|seed={self.seed}|size={self.size}".encode())
        for value, rival_bid in zip(self.values, self.rival_bids):
            digest.update(f"|{value:.9f}:{rival_bid:.9f}".encode())
        return digest.hexdigest()


@dataclass(frozen=True)
class BidOutcome:
    """A scored bidding policy.

    Attributes:
        label: Human-readable name of the policy being scored.
        params: The three policy genes.
        profit: Mean profit per auction, in value units.
        win_rate: Fraction of auctions won.
        auctions: Number of auctions the numbers were measured on.
        std_error: Standard error of ``profit`` across those auctions.
    """

    label: str
    params: dict[str, float]
    profit: float
    win_rate: float
    auctions: int
    std_error: float

    @property
    def total_profit(self) -> float:
        """Profit summed over the transcript."""
        return self.profit * self.auctions

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serialisable representation."""
        return {
            "label": self.label,
            "params": {name: round(value, 6) for name, value in self.params.items()},
            "profit": self.profit,
            "win_rate": self.win_rate,
            "auctions": self.auctions,
            "std_error": self.std_error,
            "total_profit": self.total_profit,
        }


@dataclass(frozen=True)
class NoiseProfile:
    """Dispersion of repeated finite-sample estimates of the same policy.

    Attributes:
        draws: Number of independent estimates.
        sample_size: Auctions per estimate.
        mean_profit: Mean of the estimates.
        stdev_profit: Standard deviation of the estimates.
        relative_noise: ``stdev_profit`` divided by ``mean_profit``.
    """

    draws: int
    sample_size: int
    mean_profit: float
    stdev_profit: float
    relative_noise: float

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serialisable representation."""
        return {
            "draws": self.draws,
            "sample_size": self.sample_size,
            "mean_profit": self.mean_profit,
            "stdev_profit": self.stdev_profit,
            "relative_noise": self.relative_noise,
        }


@dataclass(frozen=True)
class SeedSummary:
    """Across-seed dispersion of one evolution configuration.

    Every seed is scored on the same audit transcript, so the spread reflects
    the search rather than the measurement.

    Attributes:
        seeds: Seeds that were run.
        profits: Audited profit of the selected policy for each seed.
        shades: Audited ``shade`` gene of the selected policy for each seed.
        mean_profit: Mean audited profit.
        stdev_profit: Standard deviation of the audited profit.
        min_profit: Worst audited profit.
        max_profit: Best audited profit.
        mean_shade: Mean recovered ``shade`` gene.
        stdev_shade: Standard deviation of the recovered ``shade`` gene.
        evaluations: Evaluation counts, one per seed.
        mean_share_of_equilibrium: Mean profit as a fraction of the closed form.
    """

    seeds: tuple[int, ...]
    profits: tuple[float, ...]
    shades: tuple[float, ...]
    mean_profit: float
    stdev_profit: float
    min_profit: float
    max_profit: float
    mean_shade: float
    stdev_shade: float
    evaluations: tuple[int, ...]
    mean_share_of_equilibrium: float

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serialisable representation."""
        return {
            "seeds": list(self.seeds),
            "profits": list(self.profits),
            "shades": list(self.shades),
            "mean_profit": self.mean_profit,
            "stdev_profit": self.stdev_profit,
            "min_profit": self.min_profit,
            "max_profit": self.max_profit,
            "mean_shade": self.mean_shade,
            "stdev_shade": self.stdev_shade,
            "evaluations": list(self.evaluations),
            "mean_share_of_equilibrium": self.mean_share_of_equilibrium,
        }


@dataclass(frozen=True)
class AuctionReport:
    """Outcome of evolving a bid-shading policy on one market.

    ``evolved`` is the Pareto-front member that maximised profit on the
    validation transcript. ``scalar_best`` is the single highest-fitness alpha,
    reported separately because it is *not* the profit optimum.

    Attributes:
        market: The market that was run.
        market_fingerprint: Digest of the market definition.
        budget: Sample sizes used.
        evolved: Validation-selected policy, audited.
        truthful: Baseline that bids its own value, audited.
        equilibrium: Closed-form Bayes-Nash policy, audited.
        grid_oracle: Best point of an exhaustive grid search, audited.
        scalar_best: Highest-fitness alpha, audited.
        pareto_size: Number of members in the final Pareto front.
        hypervolume: Hypervolume of that front, or ``None``.
        evaluations: Number of objective evaluations the evolver spent.
        seed: Seed of the run.
        elapsed_seconds: Wall-clock duration of the run.
    """

    market: AuctionMarket
    market_fingerprint: str
    budget: ExperimentBudget
    evolved: BidOutcome
    truthful: BidOutcome
    equilibrium: BidOutcome
    grid_oracle: BidOutcome
    scalar_best: BidOutcome
    pareto_size: int
    hypervolume: float | None
    evaluations: int
    seed: int
    elapsed_seconds: float

    @property
    def share_of_equilibrium(self) -> float:
        """Audited profit as a fraction of the closed-form equilibrium profit."""
        best = self.market.equilibrium_profit
        if best <= 0.0:
            return 0.0
        return self.evolved.profit / best

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serialisable representation."""
        return {
            "market_fingerprint": self.market_fingerprint,
            "n_bidders": self.market.n_bidders,
            "budget": self.budget.to_dict(),
            "evolved": self.evolved.to_dict(),
            "truthful": self.truthful.to_dict(),
            "equilibrium": self.equilibrium.to_dict(),
            "grid_oracle": self.grid_oracle.to_dict(),
            "scalar_best": self.scalar_best.to_dict(),
            "pareto_size": self.pareto_size,
            "hypervolume": self.hypervolume,
            "share_of_equilibrium": self.share_of_equilibrium,
            "evaluations": self.evaluations,
            "seed": self.seed,
            "elapsed_seconds": self.elapsed_seconds,
        }


def _require_genes(params: dict[str, float]) -> None:
    """Raise if ``params`` is missing a gene or has one outside its box."""
    missing = [name for name in PARAM_NAMES if name not in params]
    if missing:
        raise ValidationError(f"policy parameters missing genes: {missing}")
    for name, bounds in (
        ("shade", SHADE_BOUNDS),
        ("curve", CURVE_BOUNDS),
        ("low_value_tilt", TILT_BOUNDS),
    ):
        value = params[name]
        if not bounds[0] <= value <= bounds[1]:
            raise InvalidRangeError(
                f"gene '{name}' must be in [{bounds[0]}, {bounds[1]}], got {value}"
            )


def equilibrium_params(market: AuctionMarket) -> dict[str, float]:
    """Return the policy genes of the symmetric Bayes-Nash equilibrium."""
    return {
        "shade": market.rival_shade,
        "curve": _EQUILIBRIUM_CURVE,
        "low_value_tilt": _EQUILIBRIUM_TILT,
    }


def truthful_params() -> dict[str, float]:
    """Return the naive baseline policy that bids its own value."""
    return {"shade": 1.0, "curve": 1.0, "low_value_tilt": 0.0}


def bid_for_value(value: float, params: dict[str, float]) -> float:
    """Bid the policy submits for a private value.

    Args:
        value: The bidder's private value, in ``[0, 1]``.
        params: The three policy genes.

    Returns:
        The bid. It is non-negative by construction: the gene box keeps
        ``shade`` positive and ``1 + low_value_tilt * (1 - v)`` at least 0.4.

    Raises:
        InvalidRangeError: If ``value`` is outside ``[0, 1]`` or a gene is
            outside its box.
        ValidationError: If ``params`` is missing a gene.
    """
    if not 0.0 <= value <= 1.0:
        raise InvalidRangeError(f"value must be in [0, 1], got {value}")
    _require_genes(params)
    shade = params["shade"]
    curve = params["curve"]
    tilt = params["low_value_tilt"]
    if value == 0.0:
        return 0.0
    bid: float = shade * (value**curve) * (1.0 + tilt * (1.0 - value))
    return bid


def sample_auctions(market: AuctionMarket, size: int, seed: int) -> AuctionSample:
    """Draw a transcript of ``size`` independent first-price auctions.

    Args:
        market: Market definition.
        size: Number of auctions to simulate.
        seed: Seed for the transcript.

    Returns:
        A frozen :class:`AuctionSample`.

    Raises:
        InvalidRangeError: If ``size`` is below one.
    """
    if size < 1:
        raise InvalidRangeError(f"size must be positive, got {size}")
    generator = random.Random(seed)
    cap = market.rival_shade
    n_rivals = market.n_rivals
    values: list[float] = []
    rival_bids: list[float] = []
    for _ in range(size):
        values.append(generator.random())
        rival_bids.append(cap * max(generator.random() for _ in range(n_rivals)))
    return AuctionSample(
        values=tuple(values), rival_bids=tuple(rival_bids), seed=seed
    )


def _profit_of(
    shade: float, curve: float, tilt: float, sample: AuctionSample
) -> float:
    """Mean profit per auction of an inlined policy; the hot path."""
    values = sample.values
    rival_bids = sample.rival_bids
    total = 0.0
    for index, value in enumerate(values):
        bid = shade * (value**curve) * (1.0 + tilt * (1.0 - value))
        if bid > rival_bids[index]:
            total += value - bid
    return total / len(values)


def score_policy(
    params: dict[str, float], sample: AuctionSample, label: str = "policy"
) -> BidOutcome:
    """Score a policy on a transcript.

    Args:
        params: The three policy genes.
        sample: Transcript to score against.
        label: Name recorded on the outcome.

    Returns:
        A :class:`BidOutcome` with profit, win rate and the profit standard
        error.

    Raises:
        InvalidRangeError: If a gene is outside its box.
        ValidationError: If ``params`` is missing a gene.
    """
    _require_genes(params)
    shade = params["shade"]
    curve = params["curve"]
    tilt = params["low_value_tilt"]
    per_auction: list[float] = []
    wins = 0
    for value, rival_bid in zip(sample.values, sample.rival_bids):
        bid = shade * (value**curve) * (1.0 + tilt * (1.0 - value))
        if bid > rival_bid:
            wins += 1
            per_auction.append(value - bid)
        else:
            per_auction.append(0.0)
    size = sample.size
    mean = statistics.fmean(per_auction)
    spread = statistics.stdev(per_auction) if size > 1 else 0.0
    return BidOutcome(
        label=label,
        params={name: params[name] for name in PARAM_NAMES},
        profit=mean,
        win_rate=wins / size,
        auctions=size,
        std_error=spread / math.sqrt(size),
    )


def grid_search(sample: AuctionSample) -> dict[str, float]:
    """Exhaustively score the coarse gene grid and keep the best mean profit.

    The grid is deliberately small enough to be a plausible brute-force
    comparator under the same estimated objective: 1035 candidates on a single
    transcript.

    Args:
        sample: Transcript to search on.

    Returns:
        The genes of the highest-profit grid point.
    """
    best_params = {
        "shade": GRID_SHADES[0],
        "curve": GRID_CURVES[0],
        "low_value_tilt": GRID_TILTS[0],
    }
    best_profit = -math.inf
    for shade in GRID_SHADES:
        for curve in GRID_CURVES:
            for tilt in GRID_TILTS:
                profit = _profit_of(shade, curve, tilt, sample)
                if profit > best_profit:
                    best_profit = profit
                    best_params = {
                        "shade": shade,
                        "curve": curve,
                        "low_value_tilt": tilt,
                    }
    return best_params


class AuctionLab:
    """Evolve a bid-shading policy with the shared :class:`AlphaEvolver`.

    Args:
        seed: Master seed; every transcript is derived from it.
        population_size: Population size handed to the evolver.
        generations: Generation cap handed to the evolver.
        budget: Sample sizes for evaluation, validation, grid and audit.
    """

    def __init__(
        self,
        seed: int = 7,
        population_size: int = 32,
        generations: int = 20,
        budget: ExperimentBudget | None = None,
    ) -> None:
        if population_size < 2:
            raise InvalidRangeError(f"population_size must be >= 2, got {population_size}")
        if generations < 1:
            raise InvalidRangeError(f"generations must be >= 1, got {generations}")
        self.seed = seed
        self.population_size = population_size
        self.generations = generations
        self.budget = ExperimentBudget() if budget is None else budget

    def _seed_for(self, tag: int, index: int) -> int:
        """Derive a reproducible transcript seed from the master seed."""
        mixed = (
            self.seed * _MULTIPLIER + tag * _TAG_STRIDE + index * _INDEX_STRIDE
        ) % _MODULUS
        return mixed

    def evaluate(
        self, params: dict[str, float], market: AuctionMarket, draw: int = 0
    ) -> dict[str, float]:
        """Score a policy on one ``sample_size`` transcript.

        Args:
            params: The three policy genes.
            market: Market definition.
            draw: Transcript index; the evolver advances this on every call.

        Returns:
            The noisy objective vector ``{"profit": ..., "win_rate": ...}``.
        """
        sample = sample_auctions(
            market, size=self.budget.sample_size, seed=self._seed_for(EVAL_TAG, draw)
        )
        outcome = score_policy(params, sample)
        return {"profit": outcome.profit, "win_rate": outcome.win_rate}

    def _audit_sample(self, market: AuctionMarket) -> AuctionSample:
        """The held-out transcript every reported number is measured on."""
        return sample_auctions(
            market, size=self.budget.audit_size, seed=self._seed_for(AUDIT_TAG, 0)
        )

    def estimate_noise(
        self,
        params: dict[str, float],
        market: AuctionMarket,
        draws: int = 32,
    ) -> NoiseProfile:
        """Measure how much the estimated objective moves between draws.

        Args:
            params: The three policy genes; normally the equilibrium policy.
            market: Market definition.
            draws: Number of independent estimates.

        Returns:
            A :class:`NoiseProfile` over the repeated estimates.

        Raises:
            InvalidRangeError: If ``draws`` is below two.
        """
        if draws < 2:
            raise InvalidRangeError(f"draws must be at least 2, got {draws}")
        estimates = [
            self.evaluate(params, market, draw=draw)["profit"]
            for draw in range(draws)
        ]
        mean = statistics.fmean(estimates)
        spread = statistics.stdev(estimates)
        return NoiseProfile(
            draws=draws,
            sample_size=self.budget.sample_size,
            mean_profit=mean,
            stdev_profit=spread,
            relative_noise=spread / mean if abs(mean) > 1e-12 else 0.0,
        )

    def _evolve(
        self, market: AuctionMarket
    ) -> tuple[EvolutionReport, dict[str, float]]:
        """Run the evolver and pick a deployment candidate from the front.

        Selection is a separate step from evolution: the highest-fitness alpha
        buys win rate at the cost of profit, so the candidate is the front
        member with the highest profit on the validation transcript.
        """
        space = (
            ParamSpec("shade", SHADE_BOUNDS[0], SHADE_BOUNDS[1]),
            ParamSpec("curve", CURVE_BOUNDS[0], CURVE_BOUNDS[1]),
            ParamSpec("low_value_tilt", TILT_BOUNDS[0], TILT_BOUNDS[1]),
        )
        objectives = (Objective("profit"), Objective("win_rate"))
        config = EvolutionConfig(
            population_size=self.population_size,
            generations=self.generations,
            seed=self.seed,
            reference_point=(-0.02, 0.0),
        )
        evolver = AlphaEvolver(space, objectives, config)
        counter = 0

        def objective(params: dict[str, float]) -> dict[str, float]:
            nonlocal counter
            counter += 1
            return self.evaluate(params, market, draw=counter)

        callback: Callable[[dict[str, float]], dict[str, float]] = objective
        report = evolver.evolve(callback, baseline_params=truthful_params())

        validation = sample_auctions(
            market,
            size=self.budget.validation_size,
            seed=self._seed_for(VALIDATION_TAG, 0),
        )
        frontline: list[Alpha] = list(report.pareto_front) or [report.best]
        selected = max(
            frontline,
            key=lambda alpha: score_policy(alpha.params, validation).profit,
        )
        return report, {name: selected.params[name] for name in PARAM_NAMES}

    def run(self, market: AuctionMarket | None = None) -> AuctionReport:
        """Evolve, select, then audit every policy on the same transcript.

        Args:
            market: Market to run; defaults to a four-bidder market.

        Returns:
            An :class:`AuctionReport` whose numbers all come from the audit
            transcript.
        """
        active = AuctionMarket() if market is None else market
        started = time.perf_counter()
        report, selected = self._evolve(active)

        grid_sample = sample_auctions(
            active, size=self.budget.grid_size, seed=self._seed_for(GRID_TAG, 0)
        )
        grid_params = grid_search(grid_sample)

        audit = self._audit_sample(active)
        return AuctionReport(
            market=active,
            market_fingerprint=active.fingerprint(),
            budget=self.budget,
            evolved=score_policy(selected, audit, label="evolved"),
            truthful=score_policy(truthful_params(), audit, label="truthful"),
            equilibrium=score_policy(
                equilibrium_params(active), audit, label="equilibrium"
            ),
            grid_oracle=score_policy(grid_params, audit, label="grid_oracle"),
            scalar_best=score_policy(report.best.params, audit, label="scalar_best"),
            pareto_size=len(report.pareto_front),
            hypervolume=report.hypervolume,
            evaluations=report.evaluations,
            seed=self.seed,
            elapsed_seconds=time.perf_counter() - started,
        )

    def seed_sweep(
        self,
        market: AuctionMarket | None = None,
        seeds: tuple[int, ...] = (1, 2, 3, 4, 5, 6),
    ) -> SeedSummary:
        """Repeat the search across seeds and score every result on one audit set.

        Args:
            market: Market to run; defaults to a four-bidder market.
            seeds: Seeds to run.

        Returns:
            A :class:`SeedSummary` of audited profit and of the recovered
            ``shade`` gene.

        Raises:
            ValidationError: If ``seeds`` is empty.
        """
        if not seeds:
            raise ValidationError("seeds must not be empty")
        active = AuctionMarket() if market is None else market
        audit = self._audit_sample(active)
        profits: list[float] = []
        shades: list[float] = []
        evaluations: list[int] = []
        for seed in seeds:
            clone = AuctionLab(
                seed=seed,
                population_size=self.population_size,
                generations=self.generations,
                budget=self.budget,
            )
            report, selected = clone._evolve(active)
            outcome = score_policy(selected, audit)
            profits.append(outcome.profit)
            shades.append(selected["shade"])
            evaluations.append(report.evaluations)

        mean_profit = statistics.fmean(profits)
        return SeedSummary(
            seeds=tuple(seeds),
            profits=tuple(profits),
            shades=tuple(shades),
            mean_profit=mean_profit,
            stdev_profit=statistics.stdev(profits) if len(profits) > 1 else 0.0,
            min_profit=min(profits),
            max_profit=max(profits),
            mean_shade=statistics.fmean(shades),
            stdev_shade=statistics.stdev(shades) if len(shades) > 1 else 0.0,
            evaluations=tuple(evaluations),
            mean_share_of_equilibrium=mean_profit / active.equilibrium_profit,
        )
