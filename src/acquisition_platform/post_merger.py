"""Post-Merger Integration Module.

Tracks and scores the integration of an acquired company: culture gap,
synergy realization, talent retention, systems integration, cross-border
challenges, and overall integration health.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from acquisition_platform.exceptions import ValidationError
from acquisition_platform.serialization import SerializableMixin

from acquisition_platform.observability import get_logger, log_execution_time, log_module_call

logger = get_logger(__name__)


@dataclass
class IntegrationMetric(SerializableMixin):
    """A single integration health metric.

    Attributes:
        name: Human-readable metric name.
        score: Health score in [0, 100].
        weight: Relative weight in the overall score (0-1).
        category: Metric category (e.g. "culture", "systems", "talent").
    """

    name: str
    score: float
    weight: float
    category: str


@dataclass
class Synergy(SerializableMixin):
    """A tracked synergy from the merger.

    Attributes:
        name: Synergy name.
        target: Target value (e.g. $M of cost savings).
        actual: Realized value to date.
        status: One of "on_track", "at_risk", "missed".
    """

    name: str
    target: float
    actual: float
    status: str


@dataclass
class IntegrationPlan(SerializableMixin):
    """Result of post-merger integration assessment.

    Attributes:
        metrics: Integration health metrics.
        synergies: Tracked synergies.
        overall_score: Weighted overall integration score in [0, 100].
        risk_level: One of "low", "medium", "high", "critical".
        timeline_months: Estimated integration timeline in months.
    """

    metrics: list[IntegrationMetric] = field(default_factory=list)
    synergies: list[Synergy] = field(default_factory=list)
    overall_score: float = 0.0
    risk_level: str = "low"
    timeline_months: int = 0


class PostMergerIntegrator:
    """Assesses and tracks post-merger integration health.

    Scores integration metrics, assesses culture gaps, tracks synergy
    realization, identifies integration risk, and generates integration
    plans and timelines.
    """

    # Risk thresholds on the overall score (0-100)
    _RISK_LOW: float = 80.0
    _RISK_MEDIUM: float = 60.0
    _RISK_HIGH: float = 40.0

    # Synergy status thresholds (fraction of target achieved)
    _SYNERGY_ON_TRACK: float = 0.9
    _SYNERGY_AT_RISK: float = 0.5

    # Timeline model
    _BASE_TIMELINE_MONTHS: int = 6
    _PER_METRIC_MONTHS: int = 2
    # Score below this adds extra months per point of deficit
    _TIMELINE_SCORE_THRESHOLD: float = 70.0
    _TIMELINE_DEFICIT_MONTHS: float = 0.2

    # Culture gap: distance between culture profiles on a fixed scale
    _CULTURE_PROFILES: dict[str, float] = {
        "flat": 0.0,
        "entrepreneurial": 25.0,
        "matrix": 50.0,
        "hierarchical": 75.0,
        "bureaucratic": 100.0,
    }
    _MAX_CULTURE_GAP: float = 100.0

    # Cross-border challenge templates
    _CROSS_BORDER_CHALLENGES: list[str] = [
        "regulatory_filings",
        "tax_compliance",
        "currency_hedging",
        "cultural_differences",
        "data_privacy_gdpr",
        "employment_law",
        "systems_localization",
    ]

    @log_execution_time(logger)
    def add_metric(
        self, name: str, score: float, weight: float, category: str
    ) -> IntegrationMetric:
        """Create an integration metric.

        Args:
            name: Metric name.
            score: Health score in [0, 100].
            weight: Relative weight (0-1).
            category: Metric category.

        Returns:
            The created IntegrationMetric.

        Raises:
            ValidationError: If score or weight is out of range.
        """
        if not 0.0 <= score <= 100.0:
            raise ValidationError(f"score must be in [0, 100], got {score}")
        if not 0.0 <= weight <= 1.0:
            raise ValidationError(f"weight must be in [0, 1], got {weight}")
        return IntegrationMetric(name=name, score=score, weight=weight, category=category)

    @log_execution_time(logger)
    def culture_gap(self, acquirer_culture: str, target_culture: str) -> float:
        """Assess the culture gap between acquirer and target.

        Uses a fixed culture profile scale; unknown cultures are placed
        at the midpoint. The gap is the absolute distance, normalized
        to [0, 100].

        Args:
            acquirer_culture: Acquirer culture profile name.
            target_culture: Target culture profile name.

        Returns:
            Culture gap in [0, 100]; 0 means identical cultures.
        """
        a = self._CULTURE_PROFILES.get(acquirer_culture, 50.0)
        b = self._CULTURE_PROFILES.get(target_culture, 50.0)
        return abs(a - b)

    @log_execution_time(logger)
    def track_synergy(self, name: str, target: float, actual: float) -> Synergy:
        """Track a synergy and classify its status.

        Args:
            name: Synergy name.
            target: Target value.
            actual: Realized value to date.

        Returns:
            A Synergy with status "on_track", "at_risk", or "missed".

        Raises:
            ValidationError: If target is not positive.
        """
        if target <= 0:
            raise ValidationError(f"target must be positive, got {target}")
        ratio = actual / target
        if ratio >= self._SYNERGY_ON_TRACK:
            status = "on_track"
        elif ratio >= self._SYNERGY_AT_RISK:
            status = "at_risk"
        else:
            status = "missed"
        return Synergy(name=name, target=target, actual=actual, status=status)

    @log_execution_time(logger)
    def overall_score(self, metrics: list[IntegrationMetric]) -> float:
        """Compute the weighted overall integration score.

        Args:
            metrics: Integration metrics with scores and weights.

        Returns:
            Weighted average score in [0, 100]; 0.0 for empty input.
        """
        if not metrics:
            return 0.0
        total_weight = sum(m.weight for m in metrics)
        if total_weight <= 0:
            return 0.0
        return sum(m.score * m.weight for m in metrics) / total_weight

    @log_execution_time(logger)
    def risk_level(self, score: float) -> str:
        """Classify integration risk from the overall score.

        Args:
            score: Overall integration score in [0, 100].

        Returns:
            One of "low", "medium", "high", "critical".
        """
        if score >= self._RISK_LOW:
            return "low"
        if score >= self._RISK_MEDIUM:
            return "medium"
        if score >= self._RISK_HIGH:
            return "high"
        return "critical"

    @log_execution_time(logger)
    def cross_border_challenges(self, countries: list[str]) -> list[str]:
        """Identify cross-border integration challenges.

        Args:
            countries: List of country codes involved in the deal.

        Returns:
            List of challenge identifiers; empty for no countries.
        """
        if not countries:
            return []
        # Base challenges always apply to cross-border deals
        challenges = list(self._CROSS_BORDER_CHALLENGES[:4])
        # Each additional country beyond the first adds localization work
        if len(countries) > 1:
            challenges.append("multi_jurisdiction_coordination")
        if len(countries) > 2:
            challenges.append("transfer_pricing")
        return challenges

    @log_execution_time(logger)
    def talent_retention_rate(self, acquired: int, retained: int) -> float:
        """Compute talent retention rate.

        Args:
            acquired: Number of acquired employees.
            retained: Number retained to date.

        Returns:
            Retention rate in [0, 1].

        Raises:
            ValidationError: If acquired is zero or retained is invalid.
        """
        if acquired <= 0:
            raise ValidationError(f"acquired must be positive, got {acquired}")
        if not 0 <= retained <= acquired:
            raise ValidationError(
                f"retained must be in [0, {acquired}], got {retained}"
            )
        return retained / acquired

    @log_execution_time(logger)
    def systems_integration_score(self, systems: list[dict[str, Any]]) -> float:
        """Score systems integration readiness.

        Args:
            systems: List of dicts with a "ready" boolean per system.

        Returns:
            Percentage of systems ready in [0, 100]; 0.0 for empty input.
        """
        if not systems:
            return 0.0
        ready = sum(1 for s in systems if s.get("ready"))
        return 100.0 * ready / len(systems)

    @log_execution_time(logger)
    def generate_timeline(self, metrics: list[IntegrationMetric]) -> int:
        """Generate an integration timeline in months.

        The timeline grows with the number of metrics and with the
        deficit of the overall score below a healthy threshold.

        Args:
            metrics: Integration metrics.

        Returns:
            Estimated timeline in months (0 for empty input).
        """
        if not metrics:
            return 0
        months = self._BASE_TIMELINE_MONTHS + len(metrics) * self._PER_METRIC_MONTHS
        score = self.overall_score(metrics)
        if score < self._TIMELINE_SCORE_THRESHOLD:
            months += int(
                (self._TIMELINE_SCORE_THRESHOLD - score) * self._TIMELINE_DEFICIT_MONTHS
            )
        return months

    @log_execution_time(logger)
    def generate_report(
        self, metrics: list[IntegrationMetric], synergies: list[Synergy]
    ) -> IntegrationPlan:
        """Generate a full integration report.

        Args:
            metrics: Integration health metrics.
            synergies: Tracked synergies.

        Returns:
            An IntegrationPlan with score, risk level, and timeline.
        """
        score = self.overall_score(metrics)
        return IntegrationPlan(
            metrics=list(metrics),
            synergies=list(synergies),
            overall_score=score,
            risk_level=self.risk_level(score),
            timeline_months=self.generate_timeline(metrics),
        )
