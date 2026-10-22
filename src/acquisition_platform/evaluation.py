"""Evaluation metrics and statistical significance testing.

This module provides the measurement layer for the platform's alpha research:

- classification metrics (precision, recall, F1, accuracy, confusion matrix)
- ranking metrics (ROC-AUC, average precision, MAP, NDCG@k)
- regression metrics (MAE, RMSE, R2, Spearman correlation)
- calibration (expected calibration error)
- resampling statistics (bootstrap confidence intervals, paired bootstrap
  p-values, Cohen's d)

All functions are pure and deterministic: any randomness is seeded explicitly,
so benchmark results are reproducible across runs and machines.
"""

from __future__ import annotations

import math
import random
import statistics
from dataclasses import dataclass
from typing import Callable, Sequence

from acquisition_platform.exceptions import (
    EmptyInputError,
    InvalidRangeError,
    ValidationError,
)


@dataclass(frozen=True)
class ConfusionMatrix:
    """Binary confusion matrix counts."""

    tp: int
    fp: int
    tn: int
    fn: int

    @property
    def total(self) -> int:
        """Total number of observations."""
        return self.tp + self.fp + self.tn + self.fn


@dataclass(frozen=True)
class ClassificationMetrics:
    """Binary classification quality metrics."""

    precision: float
    recall: float
    f1: float
    accuracy: float
    support: int
    confusion: ConfusionMatrix

    def to_dict(self) -> dict[str, float | int]:
        """Return a JSON-serialisable representation."""
        return {
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
            "accuracy": self.accuracy,
            "support": self.support,
            "tp": self.confusion.tp,
            "fp": self.confusion.fp,
            "tn": self.confusion.tn,
            "fn": self.confusion.fn,
        }


@dataclass(frozen=True)
class Interval:
    """A confidence interval produced by resampling."""

    low: float
    high: float
    confidence: float

    def to_dict(self) -> dict[str, float]:
        """Return a JSON-serialisable representation."""
        return {"low": self.low, "high": self.high, "confidence": self.confidence}


def _validate_pairs(
    y_true: Sequence[float], y_pred: Sequence[float]
) -> None:
    if not y_true or not y_pred:
        raise EmptyInputError("metric inputs cannot be empty")
    if len(y_true) != len(y_pred):
        raise ValidationError(
            f"length mismatch: y_true={len(y_true)}, y_pred={len(y_pred)}"
        )


def classification_metrics(
    y_true: Sequence[int], y_pred: Sequence[int]
) -> ClassificationMetrics:
    """Compute binary classification metrics.

    A truthy label is treated as the positive class.

    Args:
        y_true: Ground-truth labels.
        y_pred: Predicted labels.

    Returns:
        ClassificationMetrics with precision, recall, F1 and accuracy.

    Raises:
        EmptyInputError: If either sequence is empty.
        ValidationError: If the sequences differ in length.
    """
    _validate_pairs(y_true, y_pred)

    tp = fp = tn = fn = 0
    for truth, prediction in zip(y_true, y_pred):
        t = bool(truth)
        p = bool(prediction)
        if t and p:
            tp += 1
        elif not t and p:
            fp += 1
        elif not t and not p:
            tn += 1
        else:
            fn += 1

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0.0
    )
    accuracy = (tp + tn) / len(y_true)

    return ClassificationMetrics(
        precision=precision,
        recall=recall,
        f1=f1,
        accuracy=accuracy,
        support=tp + fn,
        confusion=ConfusionMatrix(tp=tp, fp=fp, tn=tn, fn=fn),
    )


def _average_ranks(values: Sequence[float]) -> list[float]:
    """Return 1-based ranks with ties resolved to their average rank."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    index = 0
    while index < len(order):
        end = index
        while (
            end + 1 < len(order)
            and values[order[end + 1]] == values[order[index]]
        ):
            end += 1
        average = (index + end) / 2.0 + 1.0
        for position in range(index, end + 1):
            ranks[order[position]] = average
        index = end + 1
    return ranks


def roc_auc(y_true: Sequence[int], scores: Sequence[float]) -> float:
    """Compute ROC-AUC using the Mann-Whitney rank statistic.

    Ties in scores receive the average rank, which yields 0.5 for a
    completely uninformative scorer.

    Args:
        y_true: Binary ground-truth labels.
        scores: Continuous scores; higher means more likely positive.

    Returns:
        Area under the ROC curve in [0, 1].

    Raises:
        EmptyInputError: If either sequence is empty.
        ValidationError: If lengths differ or only one class is present.
    """
    _validate_pairs(y_true, scores)
    positives = sum(1 for label in y_true if label)
    negatives = len(y_true) - positives
    if positives == 0 or negatives == 0:
        raise ValidationError("roc_auc requires both positive and negative labels")

    ranks = _average_ranks(scores)
    rank_sum = sum(
        rank for rank, label in zip(ranks, y_true) if label
    )
    auc = (rank_sum - positives * (positives + 1) / 2.0) / (positives * negatives)
    return max(0.0, min(1.0, auc))


def average_precision(y_true: Sequence[int], scores: Sequence[float]) -> float:
    """Compute average precision for a binary relevance ranking.

    Args:
        y_true: Binary relevance labels.
        scores: Ranking scores; higher is ranked first.

    Returns:
        Average precision, or 0.0 when there are no positives.
    """
    _validate_pairs(y_true, scores)
    positives = sum(1 for label in y_true if label)
    if positives == 0:
        return 0.0

    ordered = sorted(zip(scores, y_true), key=lambda pair: pair[0], reverse=True)
    hits = 0
    precision_sum = 0.0
    for rank, (_, label) in enumerate(ordered, start=1):
        if label:
            hits += 1
            precision_sum += hits / rank
    return precision_sum / positives


def ndcg_at_k(relevances: Sequence[float], k: int) -> float:
    """Compute normalised discounted cumulative gain at rank k.

    Args:
        relevances: Graded relevance in the order produced by the ranker.
        k: Truncation depth.

    Returns:
        NDCG@k in [0, 1]; 0.0 when all relevance is zero.

    Raises:
        InvalidRangeError: If k is not positive.
        EmptyInputError: If relevances is empty.
    """
    if k <= 0:
        raise InvalidRangeError(f"k must be positive, got {k}")
    if not relevances:
        raise EmptyInputError("relevances cannot be empty")

    def dcg(values: Sequence[float]) -> float:
        return sum(
            value / math.log2(position + 2)
            for position, value in enumerate(values[:k])
        )

    ideal = sorted(relevances, reverse=True)
    ideal_dcg = dcg(ideal)
    if ideal_dcg <= 0.0:
        return 0.0
    return dcg(relevances) / ideal_dcg


def mean_average_precision(ranked_relevance: Sequence[Sequence[int]]) -> float:
    """Compute mean average precision across ranked relevance lists.

    Args:
        ranked_relevance: One binary relevance list per query, ranked.

    Returns:
        Mean of the per-query average precisions.

    Raises:
        EmptyInputError: If no query lists are supplied.
    """
    if not ranked_relevance:
        raise EmptyInputError("ranked_relevance cannot be empty")

    scores: list[float] = []
    for ranking in ranked_relevance:
        positives = sum(1 for label in ranking if label)
        if positives == 0:
            scores.append(0.0)
            continue
        hits = 0
        precision_sum = 0.0
        for rank, label in enumerate(ranking, start=1):
            if label:
                hits += 1
                precision_sum += hits / rank
        scores.append(precision_sum / positives)
    return sum(scores) / len(scores)


def mae(y_true: Sequence[float], y_pred: Sequence[float]) -> float:
    """Compute mean absolute error."""
    _validate_pairs(y_true, y_pred)
    return sum(abs(t - p) for t, p in zip(y_true, y_pred)) / len(y_true)


def rmse(y_true: Sequence[float], y_pred: Sequence[float]) -> float:
    """Compute root mean squared error."""
    _validate_pairs(y_true, y_pred)
    total = sum((t - p) ** 2 for t, p in zip(y_true, y_pred))
    return math.sqrt(total / len(y_true))


def r2(y_true: Sequence[float], y_pred: Sequence[float]) -> float:
    """Compute the coefficient of determination.

    Raises:
        ValidationError: If y_true has zero variance.
    """
    _validate_pairs(y_true, y_pred)
    mean_true = sum(y_true) / len(y_true)
    total_variance = sum((value - mean_true) ** 2 for value in y_true)
    if total_variance == 0.0:
        raise ValidationError("r2 is undefined for constant y_true")
    residual = sum((t - p) ** 2 for t, p in zip(y_true, y_pred))
    return 1.0 - residual / total_variance


def spearman_correlation(
    a: Sequence[float], b: Sequence[float]
) -> float:
    """Compute Spearman's rank correlation with tie correction.

    Args:
        a: First sample.
        b: Second sample.

    Returns:
        Rank correlation in [-1, 1].
    """
    _validate_pairs(a, b)
    ranks_a = _average_ranks(a)
    ranks_b = _average_ranks(b)
    mean_a = sum(ranks_a) / len(ranks_a)
    mean_b = sum(ranks_b) / len(ranks_b)
    covariance = sum(
        (ra - mean_a) * (rb - mean_b) for ra, rb in zip(ranks_a, ranks_b)
    )
    variance_a = sum((ra - mean_a) ** 2 for ra in ranks_a)
    variance_b = sum((rb - mean_b) ** 2 for rb in ranks_b)
    denominator = math.sqrt(variance_a * variance_b)
    if denominator == 0.0:
        return 0.0
    return covariance / denominator


def expected_calibration_error(
    probabilities: Sequence[float], labels: Sequence[int], n_bins: int = 10
) -> float:
    """Compute expected calibration error for probabilistic predictions.

    Args:
        probabilities: Predicted probabilities in [0, 1].
        labels: Binary outcomes.
        n_bins: Number of equal-width confidence bins.

    Returns:
        Weighted mean absolute difference between confidence and accuracy.

    Raises:
        InvalidRangeError: If n_bins is not positive.
        ValidationError: If a probability is outside [0, 1].
    """
    if n_bins <= 0:
        raise InvalidRangeError(f"n_bins must be positive, got {n_bins}")
    _validate_pairs(probabilities, labels)
    for probability in probabilities:
        if probability < 0.0 or probability > 1.0:
            raise ValidationError(f"probability out of range: {probability}")

    bin_totals = [0] * n_bins
    bin_confidence = [0.0] * n_bins
    bin_correct = [0] * n_bins

    for probability, label in zip(probabilities, labels):
        index = min(int(probability * n_bins), n_bins - 1)
        bin_totals[index] += 1
        bin_confidence[index] += probability
        bin_correct[index] += 1 if label else 0

    total = len(probabilities)
    error = 0.0
    for index in range(n_bins):
        if bin_totals[index] == 0:
            continue
        mean_confidence = bin_confidence[index] / bin_totals[index]
        accuracy = bin_correct[index] / bin_totals[index]
        error += (bin_totals[index] / total) * abs(accuracy - mean_confidence)
    return error


def _percentile(sorted_values: Sequence[float], quantile: float) -> float:
    if len(sorted_values) == 1:
        return sorted_values[0]
    position = quantile * (len(sorted_values) - 1)
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return sorted_values[lower]
    weight = position - lower
    return sorted_values[lower] * (1.0 - weight) + sorted_values[upper] * weight


def bootstrap_ci(
    values: Sequence[float],
    statistic: Callable[[Sequence[float]], float] = statistics.fmean,
    n_resamples: int = 2000,
    confidence: float = 0.95,
    seed: int = 0,
) -> Interval:
    """Compute a percentile bootstrap confidence interval.

    Args:
        values: Sample to resample.
        statistic: Function summarising a resample.
        n_resamples: Number of bootstrap resamples.
        confidence: Confidence level in (0, 1).
        seed: Seed for reproducibility.

    Returns:
        Interval with low and high bounds.
    """
    if not values:
        raise EmptyInputError("bootstrap_ci requires a non-empty sample")
    if n_resamples <= 0:
        raise InvalidRangeError(f"n_resamples must be positive, got {n_resamples}")
    if not 0.0 < confidence < 1.0:
        raise InvalidRangeError(f"confidence must be in (0, 1), got {confidence}")

    generator = random.Random(seed)
    size = len(values)
    estimates = [
        statistic([values[generator.randrange(size)] for _ in range(size)])
        for _ in range(n_resamples)
    ]
    estimates.sort()
    alpha = (1.0 - confidence) / 2.0
    return Interval(
        low=_percentile(estimates, alpha),
        high=_percentile(estimates, 1.0 - alpha),
        confidence=confidence,
    )


def paired_bootstrap_pvalue(
    a: Sequence[float],
    b: Sequence[float],
    n_resamples: int = 2000,
    seed: int = 0,
) -> float:
    """Two-sided paired bootstrap p-value for mean(a) != mean(b).

    Args:
        a: Treatment measurements.
        b: Baseline measurements, paired by index.
        n_resamples: Number of bootstrap resamples.
        seed: Seed for reproducibility.

    Returns:
        p-value in [0, 1].
    """
    _validate_pairs(a, b)
    differences = [x - y for x, y in zip(a, b)]
    generator = random.Random(seed)
    size = len(differences)
    at_or_below = 0
    at_or_above = 0
    for _ in range(n_resamples):
        total = sum(
            differences[generator.randrange(size)] for _ in range(size)
        )
        if total <= 0.0:
            at_or_below += 1
        if total >= 0.0:
            at_or_above += 1
    p_value = 2.0 * min(at_or_below, at_or_above) / n_resamples
    return max(0.0, min(1.0, p_value))


def cohens_d(a: Sequence[float], b: Sequence[float]) -> float:
    """Compute Cohen's d effect size for two independent samples.

    Args:
        a: Treatment measurements.
        b: Baseline measurements.

    Returns:
        Standardised mean difference; 0.0 when pooled variance is zero.
    """
    _validate_pairs(a, b)
    if len(a) < 2:
        raise ValidationError("cohens_d requires at least two observations per sample")
    mean_a = statistics.fmean(a)
    mean_b = statistics.fmean(b)
    variance_a = statistics.variance(a)
    variance_b = statistics.variance(b)
    degrees = len(a) + len(b) - 2
    pooled = math.sqrt(
        ((len(a) - 1) * variance_a + (len(b) - 1) * variance_b) / degrees
    )
    if pooled == 0.0:
        return 0.0
    return (mean_a - mean_b) / pooled


def holm_bonferroni(p_values: Sequence[float], alpha: float = 0.05) -> list[bool]:
    """Holm-Bonferroni step-down correction for multiple comparisons.

    Controls the family-wise error rate without assuming independence, which
    makes it the right correction for a set of shift points that share data.

    Args:
        p_values: Raw p-values, one per hypothesis.
        alpha: Family-wise error rate, in (0, 1).

    Returns:
        One rejection flag per input, in input order. Rejections form a prefix
        of the ascending p-value order; the first failure stops the procedure.

    Raises:
        InvalidRangeError: If ``alpha`` is outside (0, 1) or any p-value is
            outside [0, 1].
    """
    if not 0.0 < alpha < 1.0:
        raise InvalidRangeError(f"alpha must be in (0, 1), got {alpha}")
    for value in p_values:
        if not 0.0 <= value <= 1.0:
            raise InvalidRangeError(f"p-value must be in [0, 1], got {value}")
    if not p_values:
        return []

    total = len(p_values)
    order = sorted(range(total), key=lambda index: p_values[index])
    decisions = [False] * total
    for position, index in enumerate(order):
        threshold = alpha / (total - position)
        if p_values[index] <= threshold:
            decisions[index] = True
        else:
            break
    return decisions


def minimum_detectable_effect(
    standard_deviation: float,
    sample_size: int,
    power: float = 0.8,
    alpha: float = 0.05,
) -> float:
    """Smallest detectable mean difference for a two-sided paired test.

    Uses the normal approximation ``(z_{1-alpha/2} + z_{power}) * sd / sqrt(n)``.
    Report this alongside any measured effect so a null result can be
    distinguished from an underpowered one.

    Args:
        standard_deviation: Standard deviation of the paired differences.
        sample_size: Number of paired observations.
        power: Desired power, in (0, 1).
        alpha: Two-sided significance level, in (0, 1).

    Returns:
        The minimum detectable effect in the units of the input.

    Raises:
        InvalidRangeError: If any argument is outside its valid range.
    """
    if standard_deviation <= 0.0:
        raise InvalidRangeError(
            f"standard_deviation must be positive, got {standard_deviation}"
        )
    if sample_size < 2:
        raise InvalidRangeError(f"sample_size must be at least 2, got {sample_size}")
    if not 0.0 < power < 1.0:
        raise InvalidRangeError(f"power must be in (0, 1), got {power}")
    if not 0.0 < alpha < 1.0:
        raise InvalidRangeError(f"alpha must be in (0, 1), got {alpha}")

    normal = statistics.NormalDist()
    multiplier = normal.inv_cdf(1.0 - alpha / 2.0) + normal.inv_cdf(power)
    return multiplier * standard_deviation / math.sqrt(sample_size)


def hypervolume_2d(
    points: Sequence[Sequence[float]], reference: Sequence[float]
) -> float:
    """Exact dominated hypervolume for a two-objective maximisation problem.

    Args:
        points: Objective vectors, each of length 2.
        reference: Worst point defining the lower corner of the dominated
            region, length 2.

    Returns:
        Area of the region dominated by at least one point and bounded by
        ``reference``. Points at or below the reference contribute nothing.

    Raises:
        ValidationError: If any point or the reference is not two-dimensional.
    """
    if len(reference) != 2:
        raise ValidationError(
            f"reference must have exactly 2 values, got {len(reference)}"
        )
    for point in points:
        if len(point) != 2:
            raise ValidationError(
                f"each point must have exactly 2 values, got {len(point)}"
            )

    ref_first, ref_second = float(reference[0]), float(reference[1])
    kept: list[tuple[float, float]] = []
    best_second = ref_second
    candidates = sorted(
        (
            (float(point[0]), float(point[1]))
            for point in points
            if point[0] > ref_first and point[1] > ref_second
        ),
        key=lambda pair: -pair[0],
    )
    for first, second in candidates:
        if second > best_second:
            kept.append((first, second))
            best_second = second

    volume = 0.0
    for position, (first, second) in enumerate(kept):
        next_first = kept[position + 1][0] if position + 1 < len(kept) else ref_first
        volume += (first - next_first) * (second - ref_second)
    return volume
