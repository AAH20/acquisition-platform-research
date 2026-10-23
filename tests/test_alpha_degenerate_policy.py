"""Regression tests: a degenerate genome must score worst, not crash the run.

The evolver samples the closed box [0,1]^3 for the weights, so the all-zero
vertex is reachable. `MatchingPolicy` correctly rejects a policy with no
positive weight, but the *search* must treat that genotype as unfit rather than
propagating the validation error out of `evolve_matching_policy`.

Observed before the fix: 3 of 40 seeds (7.5%) raised
`ValidationError: at least one policy weight must be positive`.
"""

from __future__ import annotations

import pytest

from acquisition_platform.alpha_lab import AlphaLab, _policy_objectives

ZERO_GENOME = {
    "gap_weight": 0.0,
    "midpoint_weight": 0.0,
    "size_weight": 0.0,
    "bias": 0.2,
}


@pytest.fixture(scope="module")
def lab() -> AlphaLab:
    return AlphaLab(seed=7, population_size=24, generations=12)


@pytest.fixture(scope="module")
def matching_benchmark(lab: AlphaLab):
    return lab.build_benchmark(n_buyers=60, sellers_per_buyer=10, seed=7)


class TestDegenerateGenome:
    def test_zero_weight_genome_scores_worst(self, matching_benchmark):
        scores = _policy_objectives(ZERO_GENOME, matching_benchmark.train)
        assert scores["ndcg@5"] == 0.0
        assert scores["value"] == 0.0

    def test_a_valid_genome_still_scores(self, matching_benchmark):
        scores = _policy_objectives(
            {
                "gap_weight": 1.0,
                "midpoint_weight": 0.0,
                "size_weight": 0.0,
                "bias": 0.0,
            },
            matching_benchmark.train,
        )
        assert scores["ndcg@5"] > 0.5
        assert scores["value"] > 0.0


class TestSeedsThatHitTheVertex:
    @pytest.mark.parametrize("seed", [12, 17, 37])
    def test_evolution_completes(self, lab, matching_benchmark, seed):
        result = lab.evolve_matching_policy(matching_benchmark, seed=seed)
        assert 0.0 < result.evolved_metrics["ndcg@5"] <= 1.0
        assert result.report.evaluations > 0
