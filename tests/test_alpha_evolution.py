"""Tests for multi-gene, multi-objective alpha evolution.

Acceptance gates:
- The evolver must strictly improve on a baseline on a known surface.
- Runs must be reproducible under a fixed seed.
- Pareto fronts must contain only mutually non-dominated members.
- Hard constraints must be respected by the returned best alpha.
"""

from __future__ import annotations

import pytest

from acquisition_platform.evolution import (
    Alpha,
    AlphaEvolver,
    Constraint,
    EvolutionConfig,
    Objective,
    ParamSpec,
)
from acquisition_platform.exceptions import InvalidRangeError, ValidationError


def sphere(params: dict[str, float]) -> dict[str, float]:
    """Maximise the negative squared distance from the origin."""
    total = sum(v * v for v in params.values())
    return {"score": -total}


class TestParamSpec:
    def test_float_decode_clamps(self):
        spec = ParamSpec("x", 0.0, 1.0)
        assert spec.decode(1.5) == 1.0
        assert spec.decode(-2.0) == 0.0

    def test_int_decode_rounds(self):
        spec = ParamSpec("n", 1, 10, kind="int")
        assert spec.decode(4.6) == 5.0
        assert isinstance(spec.decode(4.6), float)

    def test_log_decode_is_positive(self):
        spec = ParamSpec("lr", 1e-4, 1e-1, kind="log")
        assert spec.decode(0.0) >= 1e-4
        assert spec.decode(1.0) <= 1e-1

    def test_log_requires_positive_bounds(self):
        with pytest.raises(InvalidRangeError):
            ParamSpec("lr", 0.0, 1.0, kind="log")

    def test_invalid_bounds_raise(self):
        with pytest.raises(InvalidRangeError):
            ParamSpec("x", 2.0, 1.0)

    def test_unknown_kind_raises(self):
        with pytest.raises(ValidationError):
            ParamSpec("x", 0.0, 1.0, kind="nope")


class TestAlphaEvolver:
    def _evolver(self, **overrides):
        config = EvolutionConfig(
            population_size=24, generations=20, seed=11, **overrides
        )
        space = [ParamSpec(f"x{i}", -5.0, 5.0) for i in range(3)]
        return AlphaEvolver(space, [Objective("score")], config=config)

    def test_improves_over_baseline(self):
        evolver = self._evolver()
        report = evolver.evolve(sphere, baseline_params={"x0": 4.0, "x1": 4.0, "x2": 4.0})
        assert report.best_fitness > report.baseline_fitness
        assert report.improvement_pct > 0

    def test_best_alpha_near_optimum(self):
        evolver = self._evolver()
        report = evolver.evolve(sphere, baseline_params={"x0": 4.0, "x1": 4.0, "x2": 4.0})
        assert abs(report.best_fitness) < 0.5

    def test_deterministic_under_seed(self):
        a = self._evolver().evolve(sphere, baseline_params={"x0": 3.0, "x1": 3.0, "x2": 3.0})
        b = self._evolver().evolve(sphere, baseline_params={"x0": 3.0, "x1": 3.0, "x2": 3.0})
        assert a.best.vector == b.best.vector
        assert a.best_fitness == b.best_fitness

    def test_different_seeds_diverge(self):
        a = self._evolver().evolve(sphere, baseline_params={"x0": 3.0, "x1": 3.0, "x2": 3.0})
        evolver_b = AlphaEvolver(
            [ParamSpec(f"x{i}", -5.0, 5.0) for i in range(3)],
            [Objective("score")],
            EvolutionConfig(population_size=24, generations=20, seed=99),
        )
        b = evolver_b.evolve(sphere, baseline_params={"x0": 3.0, "x1": 3.0, "x2": 3.0})
        assert a.best.vector != b.best.vector

    def test_report_history_lengths(self):
        report = self._evolver().evolve(sphere)
        assert len(report.fitness_history) == report.generations_run
        assert len(report.diversity_history) == report.generations_run

    def test_elitism_is_monotonic(self):
        report = self._evolver().evolve(sphere)
        history = report.fitness_history
        assert all(history[i + 1] >= history[i] - 1e-9 for i in range(len(history) - 1))

    def test_pareto_front_is_non_dominated(self):
        space = [ParamSpec("x", 0.0, 1.0)]
        objectives = [Objective("a"), Objective("b")]

        def tradeoff(params):
            x = params["x"]
            return {"a": x, "b": 1.0 - x}

        evolver = AlphaEvolver(
            space, objectives, EvolutionConfig(population_size=30, generations=15, seed=5)
        )
        report = evolver.evolve(tradeoff, baseline_params={"x": 0.5})
        assert len(report.pareto_front) >= 2
        for candidate in report.pareto_front:
            for other in report.pareto_front:
                if candidate is other:
                    continue
                dominated = (
                    other.objectives["a"] >= candidate.objectives["a"]
                    and other.objectives["b"] >= candidate.objectives["b"]
                    and (
                        other.objectives["a"] > candidate.objectives["a"]
                        or other.objectives["b"] > candidate.objectives["b"]
                    )
                )
                assert not dominated

    def test_archive_respects_cap(self):
        space = [ParamSpec("x", 0.0, 1.0)]
        objectives = [Objective("a"), Objective("b")]

        def tradeoff(params):
            x = params["x"]
            return {"a": x, "b": 1.0 - x}

        evolver = AlphaEvolver(
            space,
            objectives,
            EvolutionConfig(population_size=30, generations=12, seed=2, archive_size=5),
        )
        report = evolver.evolve(tradeoff, baseline_params={"x": 0.5})
        assert len(report.pareto_front) <= 5
        assert len(evolver.hall_of_fame) <= 5

    def test_constraint_is_respected(self):
        space = [ParamSpec("x", 0.0, 10.0), ParamSpec("y", 0.0, 10.0)]
        objectives = [Objective("score")]

        def objective(params):
            return {"score": params["x"] + params["y"]}

        constraint = Constraint("budget", lambda p: p["x"] + p["y"] - 1.0, penalty=10.0)
        evolver = AlphaEvolver(
            space,
            objectives,
            constraints=[constraint],
            config=EvolutionConfig(population_size=30, generations=20, seed=4),
        )
        report = evolver.evolve(objective, baseline_params={"x": 0.5, "y": 0.5})
        assert report.best.params["x"] + report.best.params["y"] <= 1.0 + 0.05

    def test_penalty_makes_violations_unattractive(self):
        space = [ParamSpec("x", 0.0, 10.0), ParamSpec("y", 0.0, 10.0)]

        def objective(params: dict[str, float]) -> dict[str, float]:
            return {"score": params["x"] + params["y"]}

        constraint = Constraint("budget", lambda p: p["x"] + p["y"] - 1.0, penalty=10.0)
        evolver = AlphaEvolver(
            space,
            [Objective("score")],
            EvolutionConfig(population_size=10, generations=1, seed=4),
            constraints=[constraint],
        )
        evolver._evaluate_fn = objective
        feasible = evolver._make_alpha((0.4, 0.4), 0)
        infeasible = evolver._make_alpha((0.9, 0.9), 0)
        assert infeasible.total_violation > 0.0
        assert feasible.fitness > infeasible.fitness

    def test_empty_space_raises(self):
        with pytest.raises(ValidationError):
            AlphaEvolver([], [Objective("score")])

    def test_empty_objectives_raises(self):
        with pytest.raises(ValidationError):
            AlphaEvolver([ParamSpec("x", 0.0, 1.0)], [])

    def test_invalid_objective_weight_raises(self):
        with pytest.raises(InvalidRangeError):
            Objective("score", weight=0.0)

    def test_adaptive_mutation_reduces_sigma_when_improving(self):
        evolver = self._evolver()
        evolver.evolve(sphere)
        assert evolver.mutation_sigma <= 0.2
        assert evolver.mutation_sigma >= 0.01
