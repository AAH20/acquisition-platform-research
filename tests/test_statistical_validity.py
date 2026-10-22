"""Tests for multiple-testing control, power analysis, and hypervolume.

Falsifiable predictions:
- Holm-Bonferroni rejects a prefix of the sorted p-values and never rejects
  after the first failure.
- The minimum detectable effect shrinks as sqrt(n) and matches the closed form.
- 2-D hypervolume is exact for a known trade-off front and ignores dominated
  points.
- The evolver reports hypervolume only when a reference point and exactly two
  objectives are supplied.
"""

from __future__ import annotations

import pytest

from acquisition_platform.evaluation import (
    holm_bonferroni,
    hypervolume_2d,
    minimum_detectable_effect,
)
from acquisition_platform.evolution import (
    AlphaEvolver,
    EvolutionConfig,
    Objective,
    ParamSpec,
)
from acquisition_platform.exceptions import InvalidRangeError, ValidationError


class TestHolmBonferroni:
    def test_rejects_only_surviving_prefix(self):
        assert holm_bonferroni([0.001, 0.04, 0.045]) == [True, False, False]

    def test_all_significant_when_below_scaled_thresholds(self):
        assert holm_bonferroni([0.01, 0.02, 0.03]) == [True, True, True]

    def test_preserves_input_order(self):
        assert holm_bonferroni([0.9, 0.01]) == [False, True]

    def test_empty_input(self):
        assert holm_bonferroni([]) == []

    def test_rejects_out_of_range_p_value(self):
        with pytest.raises(InvalidRangeError):
            holm_bonferroni([0.5, 1.2])

    def test_rejects_invalid_alpha(self):
        with pytest.raises(InvalidRangeError):
            holm_bonferroni([0.5], alpha=0.0)

    def test_is_stricter_than_uncorrected_testing(self):
        p_values = [0.02, 0.03, 0.04]
        assert all(p < 0.05 for p in p_values)
        assert not all(holm_bonferroni(p_values))


class TestMinimumDetectableEffect:
    def test_matches_closed_form(self):
        # (1.959964 + 0.841621) * 0.0254 / sqrt(5) = 0.03182
        assert minimum_detectable_effect(0.0254, 5) == pytest.approx(0.0318, abs=5e-5)

    def test_shrinks_with_sample_size(self):
        assert minimum_detectable_effect(0.1, 100) < minimum_detectable_effect(0.1, 10)

    def test_higher_power_requires_larger_effect(self):
        assert minimum_detectable_effect(0.1, 20, power=0.9) > minimum_detectable_effect(
            0.1, 20, power=0.8
        )

    def test_rejects_non_positive_sd(self):
        with pytest.raises(InvalidRangeError):
            minimum_detectable_effect(0.0, 10)

    def test_rejects_small_sample(self):
        with pytest.raises(InvalidRangeError):
            minimum_detectable_effect(0.1, 1)


class TestHypervolume:
    def test_single_point_fills_its_box(self):
        assert hypervolume_2d([(1.0, 1.0)], (0.0, 0.0)) == pytest.approx(1.0)

    def test_tradeoff_front(self):
        assert hypervolume_2d([(1.0, 0.5), (0.5, 1.0)], (0.0, 0.0)) == pytest.approx(0.75)

    def test_dominated_point_adds_nothing(self):
        assert hypervolume_2d([(1.0, 1.0), (0.5, 0.5)], (0.0, 0.0)) == pytest.approx(1.0)

    def test_points_below_reference_are_ignored(self):
        assert hypervolume_2d([(1.0, 1.0), (0.2, 0.2)], (0.5, 0.5)) == pytest.approx(
            0.25
        )

    def test_empty_is_zero(self):
        assert hypervolume_2d([], (0.0, 0.0)) == 0.0

    def test_requires_two_dimensions(self):
        with pytest.raises(ValidationError):
            hypervolume_2d([(1.0, 1.0, 1.0)], (0.0, 0.0))  # type: ignore[list-item]


class TestEvolverHypervolume:
    def test_two_objective_tradeoff_front(self):
        objectives = (Objective("a"), Objective("b"))

        def evaluate(params: dict[str, float]) -> dict[str, float]:
            return {"a": 1.0 - params["x"], "b": params["x"]}

        config = EvolutionConfig(
            population_size=24,
            generations=15,
            seed=3,
            reference_point=(0.0, 0.0),
        )
        report = AlphaEvolver([ParamSpec("x", 0.0, 1.0)], objectives, config).evolve(
            evaluate
        )
        assert report.hypervolume is not None
        # The true front is a + b = 1, so the dominated area is 0.5.
        assert 0.40 <= report.hypervolume <= 0.5001

    def test_single_objective_reports_none(self):
        objectives = (Objective("a"),)

        def evaluate(params: dict[str, float]) -> dict[str, float]:
            return {"a": params["x"]}

        config = EvolutionConfig(population_size=10, generations=3, seed=1)
        report = AlphaEvolver([ParamSpec("x", 0.0, 1.0)], objectives, config).evolve(
            evaluate
        )
        assert report.hypervolume is None
