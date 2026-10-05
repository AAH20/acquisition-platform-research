"""Technology Readiness Level (TRL) assessment module.

Implements TRL 1-9 assessment for dual-use acquisition targets.
TRL is a 9-point scale (NASA/DoD/ISO 16290) measuring technology maturity.
Higher TRL = lower risk = higher valuation multiplier = lower WACC adjustment.
"""
from dataclasses import dataclass, field

from acquisition_platform.exceptions import ValidationError
from acquisition_platform.serialization import SerializableMixin

MIN_TRL = 1
MAX_TRL = 9
DEFAULT_BASE_WACC = 0.10


@dataclass
class TRLAssessment(SerializableMixin):
    """A single technology's TRL assessment.

    Attributes:
        technology_id: Unique identifier for the technology.
        name: Human-readable technology name.
        trl_level: TRL level 1-9.
        category: Technology category (e.g., 'software', 'hardware').
    """

    technology_id: str
    name: str
    trl_level: int
    category: str


@dataclass
class TRLPortfolio(SerializableMixin):
    """Aggregate TRL assessment for a portfolio of technologies.

    Attributes:
        assessments: List of individual TRL assessments.
        portfolio_score: Average TRL normalized to [0, 1] (avg TRL / 9).
        risk_adjusted_wacc: Base WACC + average TRL risk premium.
    """

    assessments: list[TRLAssessment] = field(default_factory=list)
    portfolio_score: float = 0.0
    risk_adjusted_wacc: float = 0.0


class TRLAssessor:
    """Assesses technology readiness and computes risk-adjusted metrics."""

    def assess(
        self,
        technology_id: str,
        name: str,
        trl_level: int,
        category: str,
    ) -> TRLAssessment:
        """Create a TRL assessment after validating the TRL level.

        Args:
            technology_id: Unique identifier for the technology.
            name: Human-readable technology name.
            trl_level: TRL level (1-9).
            category: Technology category.

        Returns:
            TRLAssessment instance.

        Raises:
            ValidationError: If trl_level is outside [1, 9].
        """
        self._validate_trl(trl_level)
        return TRLAssessment(
            technology_id=technology_id,
            name=name,
            trl_level=trl_level,
            category=category,
        )

    def valuation_multiplier(self, trl_level: int) -> float:
        """Compute valuation multiplier for a TRL level.

        Linearly interpolates from 0.05 (TRL 1) to 1.0 (TRL 9).
        Based on the Ambastha Readiness Valuation Framework (ARVF).

        Args:
            trl_level: TRL level (1-9).

        Returns:
            Valuation multiplier in [0.05, 1.0].

        Raises:
            ValidationError: If trl_level is outside [1, 9].
        """
        self._validate_trl(trl_level)
        # Linear interpolation: 0.05 at TRL 1, 1.0 at TRL 9
        return 0.05 + (trl_level - MIN_TRL) * (1.0 - 0.05) / (MAX_TRL - MIN_TRL)

    def risk_premium(self, trl_level: int) -> float:
        """Compute risk premium for a TRL level.

        Linearly interpolates from 0.15 (TRL 1) to 0.02 (TRL 9).
        Lower TRL = higher technical failure risk = higher premium.

        Args:
            trl_level: TRL level (1-9).

        Returns:
            Risk premium in [0.02, 0.15].

        Raises:
            ValidationError: If trl_level is outside [1, 9].
        """
        self._validate_trl(trl_level)
        # Linear interpolation: 0.15 at TRL 1, 0.02 at TRL 9
        return 0.15 - (trl_level - MIN_TRL) * (0.15 - 0.02) / (MAX_TRL - MIN_TRL)

    def portfolio_score(self, assessments: list[TRLAssessment]) -> TRLPortfolio:
        """Compute aggregate TRL score for a portfolio.

        Portfolio score = average TRL / 9, normalized to [0, 1].
        Risk-adjusted WACC = DEFAULT_BASE_WACC + average risk premium.

        Args:
            assessments: List of TRL assessments.

        Returns:
            TRLPortfolio with aggregate metrics.
        """
        if not assessments:
            return TRLPortfolio(assessments=[], portfolio_score=0.0, risk_adjusted_wacc=0.0)

        avg_trl = sum(a.trl_level for a in assessments) / len(assessments)
        avg_risk_premium = sum(self.risk_premium(a.trl_level) for a in assessments) / len(assessments)

        return TRLPortfolio(
            assessments=list(assessments),
            portfolio_score=avg_trl / MAX_TRL,
            risk_adjusted_wacc=DEFAULT_BASE_WACC + avg_risk_premium,
        )

    def classify(self, trl_level: int) -> str:
        """Classify technology by TRL level.

        Args:
            trl_level: TRL level (1-9).

        Returns:
            Classification string:
                - 1-3: 'basic_research'
                - 4-6: 'development_validation'
                - 7-8: 'deployment'
                - 9: 'proven_in_operation'

        Raises:
            ValidationError: If trl_level is outside [1, 9].
        """
        self._validate_trl(trl_level)
        if trl_level <= 3:
            return "basic_research"
        elif trl_level <= 6:
            return "development_validation"
        elif trl_level <= 8:
            return "deployment"
        else:
            return "proven_in_operation"

    def adjust_wacc(self, base_wacc: float, trl_level: int) -> float:
        """Adjust WACC by adding the TRL risk premium.

        Args:
            base_wacc: Base weighted average cost of capital.
            trl_level: TRL level (1-9).

        Returns:
            Risk-adjusted WACC = base_wacc + risk_premium(trl_level).

        Raises:
            ValidationError: If trl_level is outside [1, 9].
        """
        self._validate_trl(trl_level)
        return base_wacc + self.risk_premium(trl_level)

    @staticmethod
    def _validate_trl(trl_level: int) -> None:
        """Validate TRL level is in [1, 9]."""
        if not isinstance(trl_level, int) or trl_level < MIN_TRL or trl_level > MAX_TRL:
            raise ValidationError(
                f"trl_level must be an integer between {MIN_TRL} and {MAX_TRL}, got {trl_level}"
            )
