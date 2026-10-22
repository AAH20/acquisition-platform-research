"""Tests for the evaluation metrics library.

Acceptance gates:
- Classification metrics must match hand-computed values exactly.
- Ranking metrics must respect graded relevance and truncation.
- Statistical helpers must be deterministic under a fixed seed.
"""

from __future__ import annotations

import math

import pytest

from acquisition_platform.evaluation import (
    Interval,
    average_precision,
    bootstrap_ci,
    classification_metrics,
    cohens_d,
    expected_calibration_error,
    mae,
    mean_average_precision,
    ndcg_at_k,
    paired_bootstrap_pvalue,
    r2,
    rmse,
    roc_auc,
    spearman_correlation,
)
from acquisition_platform.exceptions import EmptyInputError, InvalidRangeError, ValidationError


class TestClassificationMetrics:
    def test_confusion_matrix_counts(self):
        metrics = classification_metrics(
            [1, 1, 0, 0, 1, 0], [1, 0, 0, 1, 1, 0]
        )
        assert metrics.confusion.tp == 2
        assert metrics.confusion.fp == 1
        assert metrics.confusion.tn == 2
        assert metrics.confusion.fn == 1

    def test_precision_recall_f1(self):
        metrics = classification_metrics([1, 1, 0, 0], [1, 0, 0, 0])
        assert metrics.precision == pytest.approx(1.0)
        assert metrics.recall == pytest.approx(0.5)
        assert metrics.f1 == pytest.approx(2 / 3)

    def test_accuracy(self):
        metrics = classification_metrics([1, 0, 1, 0], [1, 0, 0, 0])
        assert metrics.accuracy == pytest.approx(0.75)

    def test_support_is_positive_count(self):
        metrics = classification_metrics([1, 1, 0], [1, 0, 0])
        assert metrics.support == 2

    def test_no_positive_predictions_precision_zero(self):
        metrics = classification_metrics([1, 0, 1], [0, 0, 0])
        assert metrics.precision == 0.0
        assert metrics.recall == 0.0

    def test_mismatched_lengths_raise(self):
        with pytest.raises(ValidationError):
            classification_metrics([1, 0], [1])

    def test_empty_raises(self):
        with pytest.raises(EmptyInputError):
            classification_metrics([], [])


class TestRankingMetrics:
    def test_roc_auc_perfect_ranking(self):
        assert roc_auc([0, 0, 1, 1], [0.1, 0.2, 0.8, 0.9]) == pytest.approx(1.0)

    def test_roc_auc_inverted_ranking(self):
        assert roc_auc([0, 0, 1, 1], [0.9, 0.8, 0.2, 0.1]) == pytest.approx(0.0)

    def test_roc_auc_with_ties_is_half(self):
        assert roc_auc([0, 1], [0.5, 0.5]) == pytest.approx(0.5)

    def test_roc_auc_single_class_raises(self):
        with pytest.raises(ValidationError):
            roc_auc([1, 1, 1], [0.2, 0.5, 0.9])

    def test_average_precision_perfect(self):
        assert average_precision([1, 1, 0, 0], [0.9, 0.8, 0.2, 0.1]) == pytest.approx(1.0)

    def test_average_precision_known_value(self):
        # positives at ranks 1 and 3 -> (1/1 + 2/3) / 2
        ap = average_precision([1, 0, 1, 0], [0.9, 0.8, 0.7, 0.1])
        assert ap == pytest.approx((1.0 + 2 / 3) / 2)

    def test_ndcg_perfect_ranking(self):
        assert ndcg_at_k([3.0, 2.0, 1.0], 3) == pytest.approx(1.0)

    def test_ndcg_truncates_at_k(self):
        full = ndcg_at_k([3.0, 2.0, 1.0], 3)
        truncated = ndcg_at_k([3.0, 1.0, 2.0], 2)
        assert truncated < full

    def test_ndcg_all_zero_relevance(self):
        assert ndcg_at_k([0.0, 0.0, 0.0], 3) == 0.0

    def test_ndcg_invalid_k_raises(self):
        with pytest.raises(InvalidRangeError):
            ndcg_at_k([1.0, 2.0], 0)

    def test_mean_average_precision(self):
        lists = [[1, 0, 1], [1, 1, 0]]
        map_value = mean_average_precision(lists)
        # list1 AP = (1 + 2/3)/2, list2 AP = 1.0
        assert map_value == pytest.approx(((1 + 2 / 3) / 2 + 1.0) / 2)

    def test_map_empty_lists_raise(self):
        with pytest.raises(EmptyInputError):
            mean_average_precision([])


class TestRegressionMetrics:
    def test_mae(self):
        assert mae([1.0, 2.0, 3.0], [1.5, 1.5, 3.0]) == pytest.approx(1.0 / 3)

    def test_rmse(self):
        assert rmse([0.0, 0.0], [3.0, 4.0]) == pytest.approx(math.sqrt(12.5))

    def test_r2_perfect(self):
        assert r2([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) == pytest.approx(1.0)

    def test_r2_zero_variance_raises(self):
        with pytest.raises(ValidationError):
            r2([1.0, 1.0, 1.0], [1.0, 1.0, 1.0])

    def test_spearman_monotonic(self):
        assert spearman_correlation([1, 2, 3, 4], [10, 20, 30, 40]) == pytest.approx(1.0)

    def test_spearman_inverse(self):
        assert spearman_correlation([1, 2, 3, 4], [40, 30, 20, 10]) == pytest.approx(-1.0)


class TestCalibration:
    def test_ece_perfect_calibration(self):
        probs = [0.0, 1.0, 0.0, 1.0]
        labels = [0, 1, 0, 1]
        assert expected_calibration_error(probs, labels, n_bins=2) == pytest.approx(0.0)

    def test_ece_detects_miscalibration(self):
        probs = [0.9, 0.9, 0.9, 0.9]
        labels = [0, 0, 0, 0]
        assert expected_calibration_error(probs, labels, n_bins=10) == pytest.approx(0.9)

    def test_ece_invalid_bins_raise(self):
        with pytest.raises(InvalidRangeError):
            expected_calibration_error([0.5], [1], n_bins=0)


class TestStatistics:
    def test_bootstrap_interval_is_deterministic(self):
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        a = bootstrap_ci(values, seed=42, n_resamples=500)
        b = bootstrap_ci(values, seed=42, n_resamples=500)
        assert isinstance(a, Interval)
        assert (a.low, a.high) == (b.low, b.high)

    def test_bootstrap_interval_contains_mean(self):
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        interval = bootstrap_ci(values, seed=7, n_resamples=800)
        assert interval.low <= 3.0 <= interval.high

    def test_bootstrap_empty_raises(self):
        with pytest.raises(EmptyInputError):
            bootstrap_ci([], seed=1)

    def test_paired_pvalue_identical_samples_is_one(self):
        values = [1.0, 2.0, 3.0]
        assert paired_bootstrap_pvalue(values, values, seed=1, n_resamples=300) == pytest.approx(1.0)

    def test_paired_pvalue_separated_samples_is_small(self):
        a = [10.0, 11.0, 12.0, 13.0, 14.0]
        b = [1.0, 2.0, 3.0, 4.0, 5.0]
        assert paired_bootstrap_pvalue(a, b, seed=3, n_resamples=500) < 0.05

    def test_cohens_d_large_effect(self):
        a = [10.0, 11.0, 12.0, 13.0, 14.0]
        b = [1.0, 2.0, 3.0, 4.0, 5.0]
        assert cohens_d(a, b) > 2.0

    def test_cohens_d_zero_variance(self):
        assert cohens_d([1.0, 1.0], [1.0, 1.0]) == 0.0
