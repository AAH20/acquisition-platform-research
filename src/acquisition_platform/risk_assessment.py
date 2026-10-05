"""Risk assessment module.

Multi-factor risk scoring, classification, and mitigation generation
for acquisition targets across geographic, technology, financial,
and human-resource dimensions.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from acquisition_platform.exceptions import ValidationError, InvalidRangeError
from acquisition_platform.serialization import SerializableMixin

from acquisition_platform.observability import get_logger, log_execution_time, log_module_call

logger = get_logger(__name__)

# Risk level thresholds
_LOW_THRESHOLD = 3.0
_MEDIUM_THRESHOLD = 6.0
_HIGH_THRESHOLD = 8.0

# Country risk scores (0-10, higher = riskier)
_COUNTRY_RISK: dict[str, float] = {
    "US": 1.0, "CA": 1.2, "GB": 1.3, "DE": 1.4, "FR": 1.5,
    "JP": 1.2, "AU": 1.3, "NL": 1.4, "SE": 1.5, "CH": 1.0,
    "CN": 3.5, "IN": 3.0, "BR": 4.0, "MX": 3.5, "RU": 6.0,
    "ZA": 4.5, "NG": 6.5, "EG": 5.0, "TR": 4.5, "AR": 5.5,
    "VE": 8.0, "SY": 9.0, "KP": 9.5, "IR": 7.5, "AF": 8.5,
    "UA": 7.0, "MM": 7.5, "PK": 5.5, "BD": 4.0, "VN": 3.5,
    "ID": 3.5, "PH": 3.5, "TH": 3.0, "MY": 2.5, "SG": 1.5,
    "KR": 1.8, "TW": 2.5, "HK": 2.0, "SA": 3.5, "AE": 2.5,
    "IL": 3.0, "QA": 2.5, "KW": 2.5, "OM": 3.0, "BH": 2.5,
}

# Region risk modifiers (added to country score)
_REGION_MODIFIER: dict[str, float] = {
    "North America": 0.0,
    "Western Europe": 0.0,
    "Eastern Europe": 1.5,
    "East Asia": 0.5,
    "Southeast Asia": 1.0,
    "South Asia": 1.5,
    "Middle East": 2.0,
    "Africa": 2.5,
    "Latin America": 1.5,
    "Oceania": 0.0,
    "Central Asia": 2.0,
    "Caribbean": 1.5,
}


@dataclass
class RiskFactor(SerializableMixin):
    """A single risk factor with score, weight, and category.

    Attributes:
        name: Human-readable risk factor name.
        score: Risk score on a 0-10 scale (higher = riskier).
        weight: Importance weight (0-1), used in weighted aggregation.
        category: Risk category (e.g. "market", "technology", "financial").
    """

    name: str
    score: float
    weight: float
    category: str


@dataclass
class RiskAssessment(SerializableMixin):
    """Complete risk assessment result.

    Attributes:
        factors: List of individual risk factors assessed.
        total_score: Weighted aggregate risk score (0-10).
        risk_level: Classification: "low", "medium", "high", or "critical".
        mitigations: List of recommended mitigation strategies.
    """

    factors: list[RiskFactor]
    total_score: float
    risk_level: str
    mitigations: list[str] = field(default_factory=list)


class RiskAssessor:
    """Multi-factor risk assessment engine.

    Provides methods to score individual risk factors, aggregate them
    into a portfolio-level assessment, classify risk levels, and
    generate mitigation strategies.
    """

    def __init__(self) -> None:
        self._assessments: list[RiskAssessment] = []

    # ------------------------------------------------------------------
    # Core scoring
    # ------------------------------------------------------------------

    @log_execution_time(logger)
    def assess_risk(self, name: str, score: float, weight: float, category: str) -> RiskFactor:
        """Create a validated RiskFactor.

        Args:
            name: Human-readable risk factor name.
            score: Risk score (0-10).
            weight: Importance weight (0-1).
            category: Risk category string.

        Returns:
            A validated RiskFactor instance.

        Raises:
            ValidationError: If name is empty or category is empty.
            InvalidRangeError: If score or weight is outside valid range.
        """
        if not name or not name.strip():
            raise ValidationError("Risk factor name cannot be empty")
        if not category or not category.strip():
            raise ValidationError("Risk factor category cannot be empty")
        if not 0 <= score <= 10:
            raise InvalidRangeError(f"Score must be between 0 and 10, got {score}")
        if not 0 <= weight <= 1:
            raise InvalidRangeError(f"Weight must be between 0 and 1, got {weight}")
        return RiskFactor(name=name, score=score, weight=weight, category=category)

    @log_execution_time(logger)
    def total_score(self, factors: list[RiskFactor]) -> float:
        """Compute weighted total risk score.

        Args:
            factors: List of risk factors to aggregate.

        Returns:
            Weighted sum of factor scores. Returns 0.0 for empty list.
        """
        if not factors:
            return 0.0
        return sum(f.score * f.weight for f in factors)

    @log_execution_time(logger)
    def risk_level(self, score: float) -> str:
        """Classify a numeric risk score into a level.

        Args:
            score: Risk score (0-10).

        Returns:
            One of "low", "medium", "high", or "critical".

        Raises:
            InvalidRangeError: If score is outside [0, 10].
        """
        if not 0 <= score <= 10:
            raise InvalidRangeError(f"Score must be between 0 and 10, got {score}")
        if score < _LOW_THRESHOLD:
            return "low"
        if score < _MEDIUM_THRESHOLD:
            return "medium"
        if score < _HIGH_THRESHOLD:
            return "high"
        return "critical"

    # ------------------------------------------------------------------
    # Domain-specific risk scorers
    # ------------------------------------------------------------------

    @log_execution_time(logger)
    def geographic_risk(self, country: str, region: str) -> float:
        """Assess geographic/political risk for a country and region.

        Args:
            country: ISO 3166-1 alpha-2 country code.
            region: Geographic region name.

        Returns:
            Risk score on a 0-10 scale.

        Raises:
            ValidationError: If country or region is empty.
        """
        if not country or not country.strip():
            raise ValidationError("Country code cannot be empty")
        if not region or not region.strip():
            raise ValidationError("Region cannot be empty")

        country_upper = country.upper().strip()
        country_score = _COUNTRY_RISK.get(country_upper, 5.0)
        region_mod = _REGION_MODIFIER.get(region.strip(), 1.5)
        raw = country_score + region_mod
        return min(raw, 10.0)

    @log_execution_time(logger)
    def technology_risk(self, trl: int, complexity: float) -> float:
        """Assess technology risk based on TRL and complexity.

        Args:
            trl: Technology Readiness Level (1-9).
            complexity: Technical complexity score (0-10).

        Returns:
            Risk score on a 0-10 scale.

        Raises:
            InvalidRangeError: If trl is outside [1, 9] or complexity outside [0, 10].
        """
        if not 1 <= trl <= 9:
            raise InvalidRangeError(f"TRL must be between 1 and 9, got {trl}")
        if not 0 <= complexity <= 10:
            raise InvalidRangeError(f"Complexity must be between 0 and 10, got {complexity}")
        # Lower TRL = higher risk; higher complexity = higher risk
        trl_risk = (9 - trl) / 8.0 * 10.0
        return min(trl_risk * 0.6 + complexity * 0.4, 10.0)

    @log_execution_time(logger)
    def financial_risk(self, leverage: float, liquidity: float) -> float:
        """Assess financial risk based on leverage and liquidity.

        Args:
            leverage: Debt-to-equity ratio (0-1 normalized).
            liquidity: Current ratio or liquidity score (0-1 normalized).

        Returns:
            Risk score on a 0-10 scale.

        Raises:
            InvalidRangeError: If leverage or liquidity is outside [0, 1].
        """
        if not 0 <= leverage <= 1:
            raise InvalidRangeError(f"Leverage must be between 0 and 1, got {leverage}")
        if not 0 <= liquidity <= 1:
            raise InvalidRangeError(f"Liquidity must be between 0 and 1, got {liquidity}")
        # Higher leverage = higher risk; lower liquidity = higher risk
        return min(leverage * 0.6 * 10.0 + (1.0 - liquidity) * 0.4 * 10.0, 10.0)

    @log_execution_time(logger)
    def hr_risk(self, key_person_dependency: float, turnover: float) -> float:
        """Assess human-resource risk.

        Args:
            key_person_dependency: Reliance on key individuals (0-1).
            turnover: Annual employee turnover rate (0-1).

        Returns:
            Risk score on a 0-10 scale.

        Raises:
            InvalidRangeError: If inputs are outside [0, 1].
        """
        if not 0 <= key_person_dependency <= 1:
            raise InvalidRangeError(
                f"Key person dependency must be between 0 and 1, got {key_person_dependency}"
            )
        if not 0 <= turnover <= 1:
            raise InvalidRangeError(f"Turnover must be between 0 and 1, got {turnover}")
        return min(key_person_dependency * 0.5 * 10.0 + turnover * 0.5 * 10.0, 10.0)

    # ------------------------------------------------------------------
    # Mitigation and reporting
    # ------------------------------------------------------------------

    @log_execution_time(logger)
    def generate_mitigations(self, factors: list[RiskFactor]) -> list[str]:
        """Generate mitigation strategies for high-risk factors.

        Args:
            factors: List of risk factors to analyze.

        Returns:
            List of mitigation strategy strings. Empty if no high-risk factors.
        """
        mitigations: list[str] = []
        for f in factors:
            if f.score < _MEDIUM_THRESHOLD:
                continue
            category_lower = f.category.lower()
            if "market" in category_lower or "geographic" in category_lower:
                mitigations.append(
                    f"Diversify geographic exposure to reduce {f.name} risk"
                )
            elif "technology" in category_lower or "tech" in category_lower:
                mitigations.append(
                    f"Conduct independent technology audit for {f.name}"
                )
            elif "financial" in category_lower or "credit" in category_lower:
                mitigations.append(
                    f"Hedge financial exposure and secure credit facilities for {f.name}"
                )
            elif "hr" in category_lower or "human" in category_lower:
                mitigations.append(
                    f"Implement retention plans and cross-training to mitigate {f.name}"
                )
            elif "operational" in category_lower or "ops" in category_lower:
                mitigations.append(
                    f"Establish operational redundancies for {f.name}"
                )
            elif "legal" in category_lower or "regulatory" in category_lower:
                mitigations.append(
                    f"Engage local legal counsel to address {f.name}"
                )
            else:
                mitigations.append(
                    f"Develop contingency plan for {f.name}"
                )
        return mitigations

    @log_execution_time(logger)
    def generate_report(self, factors: list[RiskFactor]) -> RiskAssessment:
        """Generate a complete risk assessment report.

        Args:
            factors: List of risk factors to include.

        Returns:
            A RiskAssessment with total score, risk level, and mitigations.
        """
        score = self.total_score(factors)
        level = self.risk_level(score)
        mitigations = self.generate_mitigations(factors)
        report = RiskAssessment(
            factors=list(factors),
            total_score=score,
            risk_level=level,
            mitigations=mitigations,
        )
        self._assessments.append(report)
        return report

    # ------------------------------------------------------------------
    # Portfolio aggregation
    # ------------------------------------------------------------------

    @log_execution_time(logger)
    def portfolio_risk(self, assessments: list[RiskAssessment]) -> dict[str, float | str]:
        """Aggregate multiple assessments into a portfolio-level view.

        Args:
            assessments: List of RiskAssessment instances.

        Returns:
            Dict with "portfolio_score", "max_score", "min_score",
            "avg_score", and "portfolio_level".

        Raises:
            ValidationError: If assessments list is empty.
        """
        if not assessments:
            raise ValidationError("At least one assessment is required for portfolio aggregation")
        scores = [a.total_score for a in assessments]
        portfolio_score = sum(scores) / len(scores)
        return {
            "portfolio_score": portfolio_score,
            "max_score": max(scores),
            "min_score": min(scores),
            "avg_score": portfolio_score,
            "portfolio_level": self.risk_level(portfolio_score),
        }
