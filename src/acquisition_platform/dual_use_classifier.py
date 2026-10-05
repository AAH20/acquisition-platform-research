"""Dual-use technology classifier.

Classifies acquisition targets by their dual-use potential: technologies
that have both meaningful military and commercial applications. Computes
domain-specific application scores, an overall dual-use score, a category
label, and the regulatory flags (ITAR/EAR) that a deal team must action.

The dual-use score is the geometric mean of the military and commercial
application scores, scaled by a TRL maturity factor. Using a geometric
mean means a technology must be present in *both* domains to score highly;
strength in a single domain alone yields a low dual-use score.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from acquisition_platform.observability import get_logger, log_execution_time

logger = get_logger(__name__)

# Number of listed applications that saturates a domain's application score.
_SATURATION_COUNT: int = 3

# Threshold above which a dual-use technology is considered "high" dual-use.
_HIGH_DUAL_USE_THRESHOLD: float = 0.5

# TRL scale used for the maturity factor.
_MIN_TRL: int = 1
_MAX_TRL: int = 9

# Export control regimes.
_ITAR: str = "ITAR"
_EAR: str = "EAR"

# Regulatory flag constants.
FLAG_ITAR_CONTROLLED: str = "ITAR_CONTROLLED"
FLAG_EAR_CONTROLLED: str = "EAR_CONTROLLED"
FLAG_DUAL_USE_REVIEW: str = "DUAL_USE_REVIEW_REQUIRED"
FLAG_ENHANCED_DUE_DILIGENCE: str = "ENHANCED_DUE_DILIGENCE"
FLAG_MILITARY_END_USE: str = "MILITARY_END_USE_SCREENING"


@dataclass
class TechnologyProfile:
    """A technology and its known military/commercial applications.

    Attributes:
        name: Human-readable technology name.
        category: Declared category (e.g., 'defense', 'commercial', 'dual_use').
        military_apps: Known military applications of the technology.
        commercial_apps: Known commercial applications of the technology.
        trl: Technology readiness level (1-9).
        export_control: Export control regime (e.g., 'ITAR', 'EAR', 'none').
    """

    name: str = ""
    category: str = ""
    military_apps: list[str] = field(default_factory=list)
    commercial_apps: list[str] = field(default_factory=list)
    trl: int = 1
    export_control: str = "none"


@dataclass
class ClassificationResult:
    """Result of classifying a single technology profile.

    Attributes:
        profile: The classified technology profile.
        dual_use_score: Overall dual-use score in [0, 1].
        classification: One of 'high_dual_use', 'low_dual_use',
            'military_only', 'commercial_only', or 'neither'.
        regulatory_flags: Applicable regulatory flags.
    """

    profile: TechnologyProfile = field(default_factory=TechnologyProfile)
    dual_use_score: float = 0.0
    classification: str = "neither"
    regulatory_flags: list[str] = field(default_factory=list)


class DualUseClassifier:
    """Classifies technologies by their dual-use potential."""

    @log_execution_time(logger)
    def military_application_score(self, profile: TechnologyProfile) -> float:
        """Score the strength of a technology's military applications.

        The score is the number of listed military applications normalized
        by the saturation count, boosted for defense-category technologies
        and ITAR-controlled items, and capped at 1.0. Technologies with no
        listed military applications score 0.0.

        Args:
            profile: The technology profile to score.

        Returns:
            Military application score in [0, 1].
        """
        if not profile.military_apps:
            return 0.0

        base = min(1.0, len(profile.military_apps) / _SATURATION_COUNT)
        if profile.category.strip().lower() == "defense":
            base += 0.2
        if profile.export_control.strip().upper() == _ITAR:
            base += 0.2
        return min(base, 1.0)

    @log_execution_time(logger)
    def commercial_application_score(self, profile: TechnologyProfile) -> float:
        """Score the strength of a technology's commercial applications.

        The score is the number of listed commercial applications normalized
        by the saturation count, boosted for commercial-category technologies,
        and capped at 1.0. Technologies with no listed commercial
        applications score 0.0.

        Args:
            profile: The technology profile to score.

        Returns:
            Commercial application score in [0, 1].
        """
        if not profile.commercial_apps:
            return 0.0

        base = min(1.0, len(profile.commercial_apps) / _SATURATION_COUNT)
        if profile.category.strip().lower() == "commercial":
            base += 0.2
        return min(base, 1.0)

    @log_execution_time(logger)
    def dual_use_score(self, profile: TechnologyProfile) -> float:
        """Compute the overall dual-use score for a technology.

        The score is the geometric mean of the military and commercial
        application scores, scaled by a TRL maturity factor. A technology
        must be strong in both domains to score highly; a technology present
        in only one domain scores 0.0.

        Args:
            profile: The technology profile to score.

        Returns:
            Dual-use score in [0, 1].
        """
        military = self.military_application_score(profile)
        commercial = self.commercial_application_score(profile)

        if military <= 0.0 or commercial <= 0.0:
            return 0.0

        geometric_mean: float = (military * commercial) ** 0.5
        maturity = self._maturity_factor(profile.trl)
        return float(min(1.0, geometric_mean * maturity))

    @log_execution_time(logger)
    def classify_category(self, profile: TechnologyProfile) -> str:
        """Classify a technology into a dual-use category.

        Args:
            profile: The technology profile to classify.

        Returns:
            One of 'military_only', 'commercial_only', 'dual_use', or
            'neither'.
        """
        has_military = bool(profile.military_apps)
        has_commercial = bool(profile.commercial_apps)

        if has_military and has_commercial:
            return "dual_use"
        if has_military:
            return "military_only"
        if has_commercial:
            return "commercial_only"
        return "neither"

    @log_execution_time(logger)
    def regulatory_flags(self, profile: TechnologyProfile) -> list[str]:
        """Determine the regulatory flags applicable to a technology.

        Args:
            profile: The technology profile to evaluate.

        Returns:
            List of applicable regulatory flag strings. Empty for
            technologies with no export control and no dual-use character.
        """
        flags: list[str] = []
        export_control = profile.export_control.strip().upper()

        if export_control == _ITAR:
            flags.append(FLAG_ITAR_CONTROLLED)
        elif export_control == _EAR:
            flags.append(FLAG_EAR_CONTROLLED)

        category = self.classify_category(profile)
        if category == "dual_use":
            flags.append(FLAG_DUAL_USE_REVIEW)
            if self.dual_use_score(profile) >= _HIGH_DUAL_USE_THRESHOLD:
                flags.append(FLAG_ENHANCED_DUE_DILIGENCE)

        if profile.military_apps:
            flags.append(FLAG_MILITARY_END_USE)

        return flags

    @log_execution_time(logger)
    def classify(self, profile: TechnologyProfile) -> ClassificationResult:
        """Classify a technology by dual-use potential.

        Args:
            profile: The technology profile to classify.

        Returns:
            ClassificationResult with the dual-use score, classification
            label, and regulatory flags.
        """
        category = self.classify_category(profile)
        score = self.dual_use_score(profile)

        if category == "dual_use":
            classification = (
                "high_dual_use" if score >= _HIGH_DUAL_USE_THRESHOLD else "low_dual_use"
            )
        else:
            classification = category

        return ClassificationResult(
            profile=profile,
            dual_use_score=score,
            classification=classification,
            regulatory_flags=self.regulatory_flags(profile),
        )

    @log_execution_time(logger)
    def generate_classification_report(
        self, results: list[ClassificationResult]
    ) -> dict[str, Any]:
        """Aggregate classification results into a summary report.

        Args:
            results: Classification results to aggregate.

        Returns:
            Report dict with total count, average dual-use score, counts by
            classification label, and the number of dual-use technologies.
        """
        total = len(results)
        if total == 0:
            return {
                "total": 0,
                "average_dual_use_score": 0.0,
                "by_classification": {},
                "dual_use_count": 0,
                "regulatory_flag_count": 0,
            }

        average = sum(r.dual_use_score for r in results) / total

        by_classification: dict[str, int] = {}
        for result in results:
            by_classification[result.classification] = (
                by_classification.get(result.classification, 0) + 1
            )

        dual_use_count = by_classification.get("high_dual_use", 0) + by_classification.get(
            "low_dual_use", 0
        )
        flag_count = sum(len(r.regulatory_flags) for r in results)

        return {
            "total": total,
            "average_dual_use_score": average,
            "by_classification": by_classification,
            "dual_use_count": dual_use_count,
            "regulatory_flag_count": flag_count,
        }

    @staticmethod
    def _maturity_factor(trl: int) -> float:
        """Map a TRL level to a maturity factor in [0.5, 1.0].

        Args:
            trl: Technology readiness level (1-9).

        Returns:
            Maturity factor in [0.5, 1.0]; out-of-range TRL is clamped.
        """
        if trl < _MIN_TRL:
            trl = _MIN_TRL
        elif trl > _MAX_TRL:
            trl = _MAX_TRL
        return 0.5 + 0.5 * (trl - _MIN_TRL) / (_MAX_TRL - _MIN_TRL)
