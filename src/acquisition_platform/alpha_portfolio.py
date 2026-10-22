"""Second-domain proof: the same :class:`AlphaEvolver` on portfolio allocation.

The matching domain is a ranking problem with sampled buyers. This module is
deliberately different: an analytic mean-variance market where Sharpe ratio is
exact (no sampling noise), the policy is a continuous weight map, and the
optimum can be computed by projected gradient ascent.

If the evolver only worked on the matching benchmark, the "reusable substrate"
claim would be false. Here the engine, objectives, constraints and hypervolume
are reused unchanged; only the genome and the evaluator differ.

Everything is stdlib-only and deterministic for a fixed seed.
"""

from __future__ import annotations

import hashlib
import math
import random
import statistics
import time
from dataclasses import dataclass
from typing import Sequence

from acquisition_platform.evaluation import hypervolume_2d
from acquisition_platform.evolution import (
    AlphaEvolver,
    EvolutionConfig,
    EvolutionReport,
    Objective,
    ParamSpec,
)
from acquisition_platform.exceptions import InvalidRangeError, ValidationError

PARAM_NAMES = ("return_tilt", "risk_penalty", "sector_tilt")


@dataclass(frozen=True)
class Asset:
    """One investable asset with known expected return and volatility."""

    asset_id: str
    expected_return: float
    volatility: float
    sector: int

    def __post_init__(self) -> None:
        if self.volatility <= 0.0:
            raise InvalidRangeError(
                f"asset '{self.asset_id}' volatility must be positive"
            )


@dataclass(frozen=True)
class Market:
    """Analytic market: assets plus a block correlation structure."""

    assets: tuple[Asset, ...]
    within_sector_correlation: float = 0.60
    cross_sector_correlation: float = 0.15
    risk_free_rate: float = 0.02

    def __post_init__(self) -> None:
        if len(self.assets) < 2:
            raise ValidationError("market needs at least two assets")
        for value in (self.within_sector_correlation, self.cross_sector_correlation):
            if not -1.0 <= value <= 1.0:
                raise InvalidRangeError("correlations must be in [-1, 1]")

    @property
    def size(self) -> int:
        """Number of assets."""
        return len(self.assets)

    def covariance(self) -> list[list[float]]:
        """Covariance matrix implied by the block correlation structure."""
        size = self.size
        matrix = [[0.0] * size for _ in range(size)]
        for i, left in enumerate(self.assets):
            for j, right in enumerate(self.assets):
                if i == j:
                    matrix[i][j] = left.volatility**2
                else:
                    correlation = (
                        self.within_sector_correlation
                        if left.sector == right.sector
                        else self.cross_sector_correlation
                    )
                    matrix[i][j] = correlation * left.volatility * right.volatility
        return matrix

    def fingerprint(self) -> str:
        """Stable digest of the market definition."""
        digest = hashlib.sha256()
        for asset in self.assets:
            digest.update(
                f"{asset.asset_id}:{asset.expected_return:.6f}:"
                f"{asset.volatility:.6f}:{asset.sector}".encode()
            )
        digest.update(
            f"{self.within_sector_correlation}:{self.cross_sector_correlation}:"
            f"{self.risk_free_rate}".encode()
        )
        return digest.hexdigest()


@dataclass(frozen=True)
class Allocation:
    """A weight vector and its realised statistics."""

    weights: tuple[float, ...]
    expected_return: float
    volatility: float
    sharpe: float
    diversification: float

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serialisable representation."""
        return {
            "weights": [round(weight, 6) for weight in self.weights],
            "expected_return": self.expected_return,
            "volatility": self.volatility,
            "sharpe": self.sharpe,
            "diversification": self.diversification,
        }


@dataclass(frozen=True)
class PortfolioReport:
    """Outcome of evolving an allocation policy on one market."""

    market_fingerprint: str
    evolved: Allocation
    equal_weight: Allocation
    inverse_volatility: Allocation
    oracle: Allocation
    pareto_size: int
    hypervolume: float | None
    evaluations: int
    seed: int
    elapsed_seconds: float

    @property
    def share_of_oracle(self) -> float:
        """Evolved Sharpe as a fraction of the analytic optimum's Sharpe."""
        if abs(self.oracle.sharpe) < 1e-12:
            return 0.0
        return self.evolved.sharpe / self.oracle.sharpe

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serialisable representation."""
        return {
            "market_fingerprint": self.market_fingerprint,
            "evolved": self.evolved.to_dict(),
            "equal_weight": self.equal_weight.to_dict(),
            "inverse_volatility": self.inverse_volatility.to_dict(),
            "oracle": self.oracle.to_dict(),
            "pareto_size": self.pareto_size,
            "hypervolume": self.hypervolume,
            "share_of_oracle": self.share_of_oracle,
            "evaluations": self.evaluations,
            "seed": self.seed,
            "elapsed_seconds": self.elapsed_seconds,
        }


def _zscore(values: Sequence[float]) -> list[float]:
    """Cross-sectional z-score; returns zeros when dispersion is zero."""
    mean = statistics.fmean(values)
    spread = statistics.pstdev(values)
    if spread < 1e-12:
        return [0.0] * len(values)
    return [(value - mean) / spread for value in values]


def _cap_weights(weights: Sequence[float], cap: float) -> list[float]:
    """Scale to sum to one while respecting a per-asset cap."""
    size = len(weights)
    capped = [max(0.0, weight) for weight in weights]
    total = sum(capped)
    if total <= 0.0:
        capped = [1.0 / size] * size
    else:
        capped = [weight / total for weight in capped]
    for _ in range(20):
        over = [index for index, weight in enumerate(capped) if weight > cap + 1e-12]
        if not over:
            break
        excess = sum(capped[index] - cap for index in over)
        for index in over:
            capped[index] = cap
        free = [
            index for index, weight in enumerate(capped) if weight < cap - 1e-12
        ]
        free_total = sum(capped[index] for index in free)
        if not free or free_total <= 0.0:
            break
        for index in free:
            capped[index] += excess * capped[index] / free_total
    return capped


def portfolio_stats(weights: Sequence[float], market: Market) -> Allocation:
    """Expected return, volatility, Sharpe and diversification of a portfolio."""
    if len(weights) != market.size:
        raise ValidationError(
            f"expected {market.size} weights, got {len(weights)}"
        )
    expected = sum(
        weight * asset.expected_return
        for weight, asset in zip(weights, market.assets)
    )
    covariance = market.covariance()
    variance = sum(
        weights[i] * covariance[i][j] * weights[j]
        for i in range(market.size)
        for j in range(market.size)
    )
    volatility = math.sqrt(max(variance, 0.0))
    excess = expected - market.risk_free_rate
    sharpe = excess / volatility if volatility > 1e-12 else 0.0
    concentration = sum(weight**2 for weight in weights)
    return Allocation(
        weights=tuple(weights),
        expected_return=expected,
        volatility=volatility,
        sharpe=sharpe,
        diversification=max(0.0, 1.0 - concentration),
    )


def policy_weights(
    params: dict[str, float], market: Market, max_weight: float
) -> list[float]:
    """Map three tilt parameters to a capped weight vector.

    The policy sees only cross-sectional observables: expected return, volatility
    and sector momentum. It cannot see the covariance matrix, so the evolver is
    optimising a heuristic, not the analytic optimum.
    """
    returns = [asset.expected_return for asset in market.assets]
    vols = [asset.volatility for asset in market.assets]
    z_return = _zscore(returns)
    z_vol = _zscore(vols)

    sector_returns: dict[int, list[float]] = {}
    for asset in market.assets:
        sector_returns.setdefault(asset.sector, []).append(asset.expected_return)
    sector_mean = {
        sector: statistics.fmean(values) for sector, values in sector_returns.items()
    }
    momentum = [sector_mean[asset.sector] for asset in market.assets]
    z_momentum = _zscore(momentum)

    return_tilt = params["return_tilt"]
    risk_penalty = params["risk_penalty"]
    sector_tilt = params["sector_tilt"]

    scores = [
        return_tilt * z_return[i]
        - risk_penalty * z_vol[i]
        + sector_tilt * z_momentum[i]
        for i in range(market.size)
    ]
    largest = max(scores)
    exponentials = [math.exp(score - largest) for score in scores]
    return _cap_weights(exponentials, max_weight)


def _project_to_capped_simplex(vector: Sequence[float], cap: float) -> list[float]:
    """Euclidean projection onto {w: sum(w)=1, 0 <= w <= cap}."""
    low = min(vector) - 1.0
    high = max(vector)
    for _ in range(80):
        midpoint = (low + high) / 2.0
        total = sum(min(cap, max(0.0, value - midpoint)) for value in vector)
        if total > 1.0:
            low = midpoint
        else:
            high = midpoint
    shift = (low + high) / 2.0
    return [min(cap, max(0.0, value - shift)) for value in vector]


def max_sharpe_allocation(market: Market, max_weight: float, steps: int = 400) -> Allocation:
    """Analytic oracle: projected gradient ascent on the Sharpe ratio."""
    size = market.size
    covariance = market.covariance()
    means = [asset.expected_return for asset in market.assets]
    weights = [1.0 / size] * size
    best = portfolio_stats(weights, market)
    learning_rate = 0.35

    for _ in range(steps):
        current = portfolio_stats(weights, market)
        sigma_w = [
            sum(covariance[i][j] * weights[j] for j in range(size))
            for i in range(size)
        ]
        if current.volatility <= 1e-12:
            break
        gradient = [
            (means[i] - current.sharpe * sigma_w[i] / current.volatility)
            / current.volatility
            for i in range(size)
        ]
        weights = _project_to_capped_simplex(
            [weights[i] + learning_rate * gradient[i] for i in range(size)], cap=max_weight
        )
        candidate = portfolio_stats(weights, market)
        if candidate.sharpe > best.sharpe:
            best = candidate
    return best


class PortfolioLab:
    """Evolve an allocation policy with the shared :class:`AlphaEvolver`."""

    def __init__(
        self,
        seed: int = 7,
        population_size: int = 48,
        generations: int = 30,
        max_weight: float = 0.35,
    ) -> None:
        if not 0.0 < max_weight <= 1.0:
            raise InvalidRangeError("max_weight must be in (0, 1]")
        self.seed = seed
        self.population_size = population_size
        self.generations = generations
        self.max_weight = max_weight

    def build_market(
        self,
        n_assets: int = 8,
        n_sectors: int = 3,
        dispersion: float = 0.05,
        seed: int | None = None,
    ) -> Market:
        """Generate a market with a persistent sector effect."""
        if n_assets < 2:
            raise InvalidRangeError("n_assets must be at least 2")
        if n_sectors < 1 or n_sectors > n_assets:
            raise InvalidRangeError("n_sectors must be in [1, n_assets]")
        if self.max_weight * n_assets < 1.0:
            raise InvalidRangeError(
                "max_weight is too small to invest across all assets"
            )
        base = self.seed if seed is None else seed
        generator = random.Random(base)
        sector_effects = [generator.uniform(-dispersion, dispersion) for _ in range(n_sectors)]
        assets = []
        for index in range(n_assets):
            sector = index % n_sectors
            assets.append(
                Asset(
                    asset_id=f"asset-{index:02d}",
                    expected_return=0.05
                    + sector_effects[sector]
                    + generator.uniform(-dispersion / 2.0, dispersion / 2.0),
                    volatility=generator.uniform(0.12, 0.30),
                    sector=sector,
                )
            )
        return Market(assets=tuple(assets))

    def evaluate(self, params: dict[str, float], market: Market) -> dict[str, float]:
        """Objective vector for one policy."""
        weights = policy_weights(params, market, self.max_weight)
        stats = portfolio_stats(weights, market)
        return {
            "sharpe": stats.sharpe,
            "diversification": stats.diversification,
        }

    def evolve(self, market: Market) -> PortfolioReport:
        """Run the shared evolver on the allocation policy."""
        started = time.perf_counter()
        space = [ParamSpec(name, 0.0, 3.0) for name in PARAM_NAMES]
        objectives = (
            Objective("sharpe"),
            Objective("diversification"),
        )
        config = EvolutionConfig(
            population_size=self.population_size,
            generations=self.generations,
            seed=self.seed,
            reference_point=(-0.05, 0.0),
        )
        evolver = AlphaEvolver(space, objectives, config)
        report = evolver.evolve(
            lambda params: self.evaluate(params, market),
            baseline_params={name: 0.0 for name in PARAM_NAMES},
        )
        best_params = dict(report.best.params)
        evolved = portfolio_stats(
            policy_weights(best_params, market, self.max_weight), market
        )
        size = market.size
        equal = portfolio_stats([1.0 / size] * size, market)
        inverse = portfolio_stats(
            _cap_weights(
                [1.0 / asset.volatility for asset in market.assets], self.max_weight
            ),
            market,
        )
        oracle = max_sharpe_allocation(market, self.max_weight)
        return PortfolioReport(
            market_fingerprint=market.fingerprint(),
            evolved=evolved,
            equal_weight=equal,
            inverse_volatility=inverse,
            oracle=oracle,
            pareto_size=len(report.pareto_front),
            hypervolume=report.hypervolume,
            evaluations=report.evaluations,
            seed=self.seed,
            elapsed_seconds=time.perf_counter() - started,
        )
