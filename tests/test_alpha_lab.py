"""Tests for the alpha lab: evolving a real matching policy against ground truth.

Acceptance gates:
- The lab must recover the latent utility weights within a stated tolerance.
- The evolved policy must beat the legacy heuristic on a HELD-OUT split.
- Train/test gap must stay small enough to rule out memorisation.
"""

from __future__ import annotations

import json

import pytest

from acquisition_platform.alpha_lab import AlphaLab, MatchingBenchmark


@pytest.fixture(scope="module")
def lab() -> AlphaLab:
    return AlphaLab(seed=7, population_size=40, generations=30)


@pytest.fixture(scope="module")
def matching_benchmark(lab: AlphaLab) -> MatchingBenchmark:
    return lab.build_benchmark(n_buyers=72, sellers_per_buyer=12, seed=7)


@pytest.fixture(scope="module")
def result(lab: AlphaLab, matching_benchmark: MatchingBenchmark):
    return lab.evolve_matching_policy(matching_benchmark)


class TestBenchmarkConstruction:
    def test_deterministic_fingerprint(self, lab, matching_benchmark):
        again = lab.build_benchmark(n_buyers=72, sellers_per_buyer=12, seed=7)
        assert matching_benchmark.fingerprint() == again.fingerprint()

    def test_train_test_are_disjoint(self, matching_benchmark):
        train_ids = {b.buyer_id for b in matching_benchmark.train.cases}
        test_ids = {b.buyer_id for b in matching_benchmark.test.cases}
        assert not train_ids & test_ids
        assert len(train_ids) + len(test_ids) == 72

    def test_each_case_has_candidates(self, matching_benchmark):
        assert all(len(c.sellers) == 12 for c in matching_benchmark.train.cases)

    def test_relevance_is_normalised(self, matching_benchmark):
        for case in matching_benchmark.train.cases:
            assert all(0.0 <= r <= 1.0 for r in case.relevance)


class TestEvolutionOutcome:
    def test_report_is_populated(self, result):
        assert result.report.best_fitness > float("-inf")
        assert result.report.generations_run > 0
        assert len(result.report.pareto_front) >= 1

    def test_baseline_is_a_valid_ranking(self, result):
        assert 0.0 <= result.baseline_metrics["ndcg@5"] <= 1.0
        assert 0.0 <= result.baseline_metrics["mrr"] <= 1.0

    def test_evolved_beats_baseline_on_holdout(self, result):
        assert (
            result.evolved_metrics["ndcg@5"]
            > result.baseline_metrics["ndcg@5"] + 0.05
        )

    def test_weights_are_recovered(self, result):
        assert result.weight_error_l1 < 0.30

    def test_generalisation_gap_is_small(self, result):
        assert result.generalization_gap <= 0.10

    def test_evolved_weights_are_non_negative(self, result):
        assert all(v >= 0.0 for v in result.recovered_weights.values())

    def test_result_serialises(self, result):
        payload = result.to_dict()
        assert json.loads(json.dumps(payload))["evolved_metrics"]["ndcg@5"] > 0
        assert payload["report"]["best_fitness"] == pytest.approx(
            result.report.best_fitness
        )
