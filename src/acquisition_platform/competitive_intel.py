"""Competitive intelligence module.

Competitor profiling, market share analysis, competitive positioning,
war gaming, signal tracking, and alerting for acquisition strategy.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from acquisition_platform.exceptions import ValidationError, InvalidRangeError
from acquisition_platform.serialization import SerializableMixin

from acquisition_platform.observability import get_logger, log_execution_time, log_module_call

logger = get_logger(__name__)

# Positioning score weights
_STRENGTH_WEIGHT = 0.4
_MARKET_SHARE_WEIGHT = 0.35
_STRATEGY_WEIGHT = 0.25

# War game scenario impact factors
_WAR_GAME_FACTORS: dict[str, float] = {
    "price_war": 0.8,
    "product_launch": 0.6,
    "market_entry": 0.7,
    "merger": 0.9,
    "technology_shift": 0.75,
    "regulatory_change": 0.5,
}

# Response prediction templates
_RESPONSE_TEMPLATES: dict[str, str] = {
    "price_cut": "Likely to match price cut within 2-4 weeks to defend market share",
    "product_launch": "Expected to accelerate R&D and announce competing product within 6 months",
    "market_entry": "May form strategic partnerships to block new entrant",
    "merger": "Could pursue counter-acquisition or defensive alliance",
    "technology_shift": "Likely to invest in acquiring or licensing new technology",
    "marketing_push": "Expected to increase marketing spend and promotional activity",
}


@dataclass
class CompetitorProfile(SerializableMixin):
    """A competitor's profile with market position and strategy.

    Attributes:
        name: Competitor name.
        market_share: Market share percentage (0-100).
        strengths: List of competitive strengths.
        weaknesses: List of competitive weaknesses.
        strategy: Described competitive strategy.
    """

    name: str
    market_share: float
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    strategy: str = ""


@dataclass
class CompetitiveSignal(SerializableMixin):
    """A competitive intelligence signal.

    Attributes:
        signal_type: Type of signal (e.g. "pricing", "product_launch").
        source: Source of the signal.
        timestamp: ISO 8601 timestamp string.
        impact: Impact score (0-1, higher = more impactful).
    """

    signal_type: str
    source: str
    timestamp: str
    impact: float


@dataclass
class CompetitiveIntelResult(SerializableMixin):
    """Complete competitive intelligence result.

    Attributes:
        competitors: List of profiled competitors.
        signals: List of tracked competitive signals.
        positioning_score: Overall competitive positioning score (0-100).
        alerts: List of generated competitive alerts.
    """

    competitors: list[CompetitorProfile]
    signals: list[CompetitiveSignal]
    positioning_score: float
    alerts: list[str] = field(default_factory=list)


class CompetitiveIntelAnalyzer:
    """Competitive intelligence analysis engine.

    Provides methods to profile competitors, analyze market share,
    score competitive positioning, run war game scenarios, predict
    competitive responses, track signals, and generate alerts.
    """

    def __init__(self) -> None:
        self._profiles: list[CompetitorProfile] = []
        self._signals: list[CompetitiveSignal] = []

    # ------------------------------------------------------------------
    # Competitor profiling
    # ------------------------------------------------------------------

    @log_execution_time(logger)
    def profile_competitor(
        self,
        name: str,
        market_share: float,
        strengths: list[str],
        weaknesses: list[str],
        strategy: str,
    ) -> CompetitorProfile:
        """Create a validated CompetitorProfile.

        Args:
            name: Competitor name.
            market_share: Market share percentage (0-100).
            strengths: List of competitive strengths.
            weaknesses: List of competitive weaknesses.
            strategy: Competitive strategy description.

        Returns:
            A validated CompetitorProfile instance.

        Raises:
            ValidationError: If name is empty.
            InvalidRangeError: If market_share is outside [0, 100].
        """
        if not name or not name.strip():
            raise ValidationError("Competitor name cannot be empty")
        if not 0 <= market_share <= 100:
            raise InvalidRangeError(
                f"Market share must be between 0 and 100, got {market_share}"
            )
        profile = CompetitorProfile(
            name=name.strip(),
            market_share=market_share,
            strengths=list(strengths),
            weaknesses=list(weaknesses),
            strategy=strategy,
        )
        self._profiles.append(profile)
        return profile

    # ------------------------------------------------------------------
    # Market share analysis
    # ------------------------------------------------------------------

    @log_execution_time(logger)
    def market_share_analysis(
        self, competitors: list[CompetitorProfile]
    ) -> dict[str, float | str | int]:
        """Analyze market share distribution across competitors.

        Args:
            competitors: List of competitor profiles.

        Returns:
            Dict with total_share, average_share, leader, leader_share,
            and competitor_count.

        Raises:
            ValidationError: If competitors list is empty.
        """
        if not competitors:
            raise ValidationError("At least one competitor is required for analysis")
        shares = [c.market_share for c in competitors]
        total = sum(shares)
        leader = max(competitors, key=lambda c: c.market_share)
        return {
            "total_share": total,
            "average_share": total / len(competitors),
            "leader": leader.name,
            "leader_share": leader.market_share,
            "competitor_count": len(competitors),
        }

    # ------------------------------------------------------------------
    # Competitive positioning
    # ------------------------------------------------------------------

    @log_execution_time(logger)
    def competitive_positioning(
        self, competitors: list[CompetitorProfile], target: str
    ) -> float:
        """Score competitive positioning for a target competitor.

        Args:
            competitors: List of competitor profiles.
            target: Name of the competitor to score.

        Returns:
            Positioning score (0-100).

        Raises:
            ValidationError: If target not found in competitors.
        """
        if not competitors:
            raise ValidationError("At least one competitor is required")
        target_profile = None
        for c in competitors:
            if c.name == target:
                target_profile = c
                break
        if target_profile is None:
            raise ValidationError(f"Target competitor '{target}' not found")

        # Strength component: more strengths = higher score
        strength_score = min(len(target_profile.strengths) / 5.0, 1.0) * 100

        # Market share component: direct percentage
        share_score = target_profile.market_share

        # Strategy component: having a defined strategy adds points
        strategy_score = 50.0 if target_profile.strategy else 0.0

        raw = (
            strength_score * _STRENGTH_WEIGHT
            + share_score * _MARKET_SHARE_WEIGHT
            + strategy_score * _STRATEGY_WEIGHT
        )
        return min(raw, 100.0)

    # ------------------------------------------------------------------
    # War gaming
    # ------------------------------------------------------------------

    @log_execution_time(logger)
    def war_game_scenario(
        self, competitors: list[CompetitorProfile], scenario: str
    ) -> float:
        """Score a war game scenario's competitive impact.

        Args:
            competitors: List of competitor profiles.
            scenario: Scenario type (e.g. "price_war", "product_launch").

        Returns:
            War game impact score (0-100).

        Raises:
            ValidationError: If competitors list is empty or scenario unknown.
        """
        if not competitors:
            raise ValidationError("At least one competitor is required")
        if not scenario or not scenario.strip():
            raise ValidationError("Scenario cannot be empty")

        scenario_key = scenario.strip().lower()
        factor = _WAR_GAME_FACTORS.get(scenario_key)
        if factor is None:
            raise ValidationError(f"Unknown war game scenario: {scenario}")

        # Average market share indicates concentration (higher = more impact)
        avg_share = sum(c.market_share for c in competitors) / len(competitors)
        # More competitors = more complex dynamics
        complexity = min(len(competitors) / 5.0, 1.0)

        raw = factor * 60.0 + avg_share * 0.3 + complexity * 10.0
        return min(raw, 100.0)

    # ------------------------------------------------------------------
    # Response prediction
    # ------------------------------------------------------------------

    @log_execution_time(logger)
    def predict_competitive_response(
        self, competitor: CompetitorProfile, action: str
    ) -> str:
        """Predict how a competitor will respond to a market action.

        Args:
            competitor: The competitor profile.
            action: The action taken (e.g. "price_cut", "product_launch").

        Returns:
            Predicted response description.

        Raises:
            ValidationError: If action is empty.
        """
        if not action or not action.strip():
            raise ValidationError("Action cannot be empty")

        action_key = action.strip().lower()
        template = _RESPONSE_TEMPLATES.get(
            action_key,
            f"Likely to respond with counter-strategy to {action}",
        )

        # Adjust prediction based on competitor characteristics
        if competitor.market_share > 50:
            template += " (dominant player - aggressive response expected)"
        elif competitor.market_share < 10:
            template += " (niche player - limited response capability)"
        elif competitor.weaknesses:
            template += f" (constrained by: {', '.join(competitor.weaknesses[:2])})"

        return template

    # ------------------------------------------------------------------
    # Signal tracking
    # ------------------------------------------------------------------

    @log_execution_time(logger)
    def track_signal(
        self,
        signal_type: str,
        source: str,
        timestamp: str,
        impact: float,
    ) -> CompetitiveSignal:
        """Create and track a competitive intelligence signal.

        Args:
            signal_type: Type of signal.
            source: Signal source.
            timestamp: ISO 8601 timestamp.
            impact: Impact score (0-1).

        Returns:
            A validated CompetitiveSignal instance.

        Raises:
            ValidationError: If signal_type or source is empty.
            InvalidRangeError: If impact is outside [0, 1].
        """
        if not signal_type or not signal_type.strip():
            raise ValidationError("Signal type cannot be empty")
        if not source or not source.strip():
            raise ValidationError("Signal source cannot be empty")
        if not 0 <= impact <= 1:
            raise InvalidRangeError(f"Impact must be between 0 and 1, got {impact}")

        signal = CompetitiveSignal(
            signal_type=signal_type.strip(),
            source=source.strip(),
            timestamp=timestamp,
            impact=impact,
        )
        self._signals.append(signal)
        return signal

    # ------------------------------------------------------------------
    # Return on competitive intelligence
    # ------------------------------------------------------------------

    @log_execution_time(logger)
    def roci_calculation(self, investment: float, value_generated: float) -> float:
        """Calculate return on competitive intelligence investment.

        Args:
            investment: CI investment amount.
            value_generated: Value generated from CI activities.

        Returns:
            ROI ratio (value_generated - investment) / investment.

        Raises:
            InvalidRangeError: If investment is zero or negative.
        """
        if investment <= 0:
            raise InvalidRangeError(f"Investment must be positive, got {investment}")
        return (value_generated - investment) / investment

    # ------------------------------------------------------------------
    # Alerting
    # ------------------------------------------------------------------

    @log_execution_time(logger)
    def generate_competitive_alert(
        self, threshold: float, signals: list[CompetitiveSignal]
    ) -> list[str]:
        """Generate alerts for signals exceeding an impact threshold.

        Args:
            threshold: Impact threshold (0-1).
            signals: List of signals to evaluate.

        Returns:
            List of alert message strings.

        Raises:
            InvalidRangeError: If threshold is outside [0, 1].
        """
        if not 0 <= threshold <= 1:
            raise InvalidRangeError(f"Threshold must be between 0 and 1, got {threshold}")

        alerts: list[str] = []
        for s in signals:
            if s.impact >= threshold:
                alerts.append(
                    f"HIGH IMPACT: {s.signal_type} signal from {s.source} "
                    f"(impact={s.impact:.2f}, time={s.timestamp})"
                )
        return alerts

    # ------------------------------------------------------------------
    # Report generation
    # ------------------------------------------------------------------

    @log_execution_time(logger)
    def generate_competitive_report(
        self,
        competitors: list[CompetitorProfile],
        signals: list[CompetitiveSignal],
    ) -> CompetitiveIntelResult:
        """Generate a complete competitive intelligence report.

        Args:
            competitors: List of competitor profiles.
            signals: List of competitive signals.

        Returns:
            A CompetitiveIntelResult with all analysis results.
        """
        if not competitors:
            return CompetitiveIntelResult(
                competitors=[],
                signals=list(signals),
                positioning_score=0.0,
                alerts=[],
            )

        # Positioning score: average across all competitors
        positioning_scores = [
            self.competitive_positioning(competitors, c.name) for c in competitors
        ]
        avg_positioning = sum(positioning_scores) / len(positioning_scores)

        # Generate alerts from high-impact signals
        alerts = self.generate_competitive_alert(threshold=0.7, signals=signals)

        return CompetitiveIntelResult(
            competitors=list(competitors),
            signals=list(signals),
            positioning_score=avg_positioning,
            alerts=alerts,
        )
