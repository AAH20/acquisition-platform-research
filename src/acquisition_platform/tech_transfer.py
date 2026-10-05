"""Technology transfer module.

Implements technology transfer assessment for dual-use acquisition targets,
including transfer readiness, absorptive capacity, university spinoff scoring,
license valuation, risk assessment, knowledge transfer, and TTO evaluation.
"""
from dataclasses import dataclass
from typing import Any

from acquisition_platform.exceptions import ValidationError, InvalidRangeError


@dataclass
class TransferProfile:
    """Profile of a technology transfer candidate.

    Attributes:
        technology_id: Unique identifier for the technology.
        name: Human-readable technology name.
        trl: Technology Readiness Level (1-9).
        source_type: Source organization type (e.g., 'university', 'corporate', 'government').
        target_type: Target organization type (e.g., 'corporate', 'government', 'startup').
        complexity: Technology complexity in [0, 1], where 1 is most complex.
    """

    technology_id: str
    name: str
    trl: int
    source_type: str
    target_type: str
    complexity: float


@dataclass
class TransferResult:
    """Result of a technology transfer assessment.

    Attributes:
        profile: The transfer profile assessed.
        readiness_score: Transfer readiness score in [0, 1].
        absorptive_capacity: Absorptive capacity score in [0, 1].
        risk_level: Risk level classification ('low', 'medium', 'high').
        timeline_months: Estimated transfer timeline in months.
    """

    profile: TransferProfile
    readiness_score: float
    absorptive_capacity: float
    risk_level: str
    timeline_months: int


class TechTransferAnalyzer:
    """Analyzes technology transfer readiness and outcomes."""

    def assess_transfer_readiness(self, profile: TransferProfile) -> float:
        """Assess transfer readiness based on TRL and complexity.

        Formula: (trl / 9) * (1 - complexity)
        Higher TRL and lower complexity = higher readiness.

        Args:
            profile: The transfer profile to assess.

        Returns:
            Readiness score in [0, 1].

        Raises:
            ValidationError: If trl is outside [1, 9].
            InvalidRangeError: If complexity is outside [0, 1].
        """
        if not isinstance(profile.trl, int) or profile.trl < 1 or profile.trl > 9:
            raise ValidationError(
                f"trl must be an integer between 1 and 9, got {profile.trl}"
            )
        if not 0.0 <= profile.complexity <= 1.0:
            raise InvalidRangeError(
                f"complexity must be in [0, 1], got {profile.complexity}"
            )
        return (profile.trl / 9.0) * (1.0 - profile.complexity)

    def absorptive_capacity(self, target_capability: float, source_capability: float) -> float:
        """Assess absorptive capacity based on capability gap.

        Formula: min(target / source, 1.0) if source > 0 else 0.0

        Args:
            target_capability: Target organization's capability in [0, 1].
            source_capability: Source organization's capability in [0, 1].

        Returns:
            Absorptive capacity score in [0, 1].

        Raises:
            InvalidRangeError: If either capability is outside [0, 1].
        """
        if not 0.0 <= target_capability <= 1.0:
            raise InvalidRangeError(
                f"target_capability must be in [0, 1], got {target_capability}"
            )
        if not 0.0 <= source_capability <= 1.0:
            raise InvalidRangeError(
                f"source_capability must be in [0, 1], got {source_capability}"
            )
        if source_capability == 0.0:
            return 0.0
        return min(target_capability / source_capability, 1.0)

    def university_spinoff_score(self, spinoff: dict[str, Any]) -> float:
        """Score a university spinoff based on key metrics.

        Args:
            spinoff: Dictionary with keys 'trl', 'patents', 'funding', 'team_size'.

        Returns:
            Spinoff score in [0, 1]. Empty dict returns 0.0.
        """
        if not spinoff:
            return 0.0

        trl = spinoff.get("trl", 1)
        patents = spinoff.get("patents", 0)
        funding = spinoff.get("funding", 0)
        team_size = spinoff.get("team_size", 0)

        # Normalize components
        trl_score = min(trl / 9.0, 1.0)
        patent_score = min(patents / 10.0, 1.0)
        funding_score = min(funding / 1_000_000.0, 1.0)
        team_score = min(team_size / 10.0, 1.0)

        # Weighted average
        return float(
            trl_score * 0.3
            + patent_score * 0.25
            + funding_score * 0.25
            + team_score * 0.2
        )

    def value_license(self, revenue: float, royalty_rate: float, duration: int) -> float:
        """Value a license using the income approach.

        Formula: revenue * royalty_rate * duration

        Args:
            revenue: Annual revenue attributable to the license.
            royalty_rate: Royalty rate as a decimal (e.g., 0.05 for 5%).
            duration: License duration in years.

        Returns:
            Estimated license value in USD.

        Raises:
            ValidationError: If revenue or duration is negative.
            InvalidRangeError: If royalty_rate is outside [0, 1].
        """
        if revenue < 0:
            raise ValidationError(f"revenue must be non-negative, got {revenue}")
        if not 0.0 <= royalty_rate <= 1.0:
            raise InvalidRangeError(
                f"royalty_rate must be in [0, 1], got {royalty_rate}"
            )
        if duration < 0:
            raise ValidationError(f"duration must be non-negative, got {duration}")
        return revenue * royalty_rate * duration

    def transfer_risk(self, profile: TransferProfile) -> float:
        """Assess transfer risk based on TRL and complexity.

        Formula: (1 - trl/9) * complexity
        Low TRL and high complexity = high risk.

        Args:
            profile: The transfer profile to assess.

        Returns:
            Risk score in [0, 1].

        Raises:
            ValidationError: If trl is outside [1, 9].
            InvalidRangeError: If complexity is outside [0, 1].
        """
        if not isinstance(profile.trl, int) or profile.trl < 1 or profile.trl > 9:
            raise ValidationError(
                f"trl must be an integer between 1 and 9, got {profile.trl}"
            )
        if not 0.0 <= profile.complexity <= 1.0:
            raise InvalidRangeError(
                f"complexity must be in [0, 1], got {profile.complexity}"
            )
        return (1.0 - profile.trl / 9.0) * profile.complexity

    def knowledge_transfer_score(
        self, source_knowledge: list[str], target_knowledge: list[str]
    ) -> float:
        """Score knowledge transfer based on knowledge area overlap.

        Formula: |intersection| / |union|
        Higher overlap = higher transfer score.

        Args:
            source_knowledge: List of source knowledge areas.
            target_knowledge: List of target knowledge areas.

        Returns:
            Knowledge transfer score in [0, 1]. Empty lists return 1.0.
        """
        if not source_knowledge or not target_knowledge:
            return 1.0
        source_set = set(k.lower() for k in source_knowledge)
        target_set = set(k.lower() for k in target_knowledge)
        intersection = source_set & target_set
        union = source_set | target_set
        if not union:
            return 1.0
        return len(intersection) / len(union)

    def tto_assessment(self, tto: dict[str, Any]) -> float:
        """Assess Technology Transfer Office (TTO) effectiveness.

        Args:
            tto: Dictionary with keys 'staff_count', 'patents_licensed',
                 'startups_created', 'revenue_generated'.

        Returns:
            TTO assessment score in [0, 1]. Empty dict returns 0.0.
        """
        if not tto:
            return 0.0

        staff = tto.get("staff_count", 0)
        patents = tto.get("patents_licensed", 0)
        startups = tto.get("startups_created", 0)
        revenue = tto.get("revenue_generated", 0)

        # Normalize components
        staff_score = min(staff / 20.0, 1.0)
        patent_score = min(patents / 50.0, 1.0)
        startup_score = min(startups / 10.0, 1.0)
        revenue_score = min(revenue / 10_000_000.0, 1.0)

        # Weighted average
        return float(
            staff_score * 0.2
            + patent_score * 0.3
            + startup_score * 0.2
            + revenue_score * 0.3
        )

    def transfer_timeline(self, profile: TransferProfile) -> int:
        """Estimate transfer timeline in months.

        Formula: base 6 months + (9 - trl) * 2 + complexity * 12

        Args:
            profile: The transfer profile to assess.

        Returns:
            Estimated timeline in months (minimum 3).

        Raises:
            ValidationError: If trl is outside [1, 9].
            InvalidRangeError: If complexity is outside [0, 1].
        """
        if not isinstance(profile.trl, int) or profile.trl < 1 or profile.trl > 9:
            raise ValidationError(
                f"trl must be an integer between 1 and 9, got {profile.trl}"
            )
        if not 0.0 <= profile.complexity <= 1.0:
            raise InvalidRangeError(
                f"complexity must be in [0, 1], got {profile.complexity}"
            )
        months = 6 + (9 - profile.trl) * 2 + int(profile.complexity * 12)
        return max(months, 3)

    def generate_transfer_report(self, profile: TransferProfile) -> TransferResult:
        """Generate a complete transfer assessment report.

        Args:
            profile: The transfer profile to assess.

        Returns:
            TransferResult with all assessment metrics.
        """
        readiness = self.assess_transfer_readiness(profile)
        risk = self.transfer_risk(profile)

        # Risk level classification
        if risk < 0.3:
            risk_level = "low"
        elif risk < 0.6:
            risk_level = "medium"
        else:
            risk_level = "high"

        # Absorptive capacity: assume target has capability proportional to TRL
        absorptive = self.absorptive_capacity(
            target_capability=profile.trl / 9.0,
            source_capability=0.8,
        )

        timeline = self.transfer_timeline(profile)

        return TransferResult(
            profile=profile,
            readiness_score=readiness,
            absorptive_capacity=absorptive,
            risk_level=risk_level,
            timeline_months=timeline,
        )
