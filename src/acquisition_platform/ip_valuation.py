"""IP/patent valuation module.

Implements patent-level and portfolio-level valuation using multiple
methodologies: Relief-from-Royalty (RFR), income approach, and market
approach. Also provides freedom-to-operate (FTO) scoring and patent
thicket detection.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from acquisition_platform.exceptions import (
    DivisionByZeroError,
    InvalidRangeError,
    ValidationError,
)
from acquisition_platform.serialization import SerializableMixin

# Base value for a single patent under the Relief-from-Royalty method
_BASE_PATENT_VALUE: float = 100_000.0

# Maximum citation count that adds value (diminishing returns beyond this)
_MAX_CITATIONS_FOR_IMPACT: int = 100

# Status multipliers for patent valuation
_STATUS_MULTIPLIERS: dict[str, float] = {
    "granted": 1.0,
    "pending": 0.5,
    "expired": 0.1,
}

# Stopwords excluded from title similarity comparison
_STOPWORDS: frozenset[str] = frozenset({
    "a", "an", "the", "of", "for", "to", "in", "on", "at", "by",
    "with", "from", "and", "or", "is", "are", "was", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did",
    "will", "would", "could", "should", "may", "might", "can",
    "this", "that", "these", "those", "it", "its",
})


@dataclass
class Patent(SerializableMixin):
    """Represents a single patent.

    Attributes:
        patent_id: Unique patent identifier (e.g., "US-1234567").
        title: Patent title.
        status: Patent status — "granted", "pending", or "expired".
        citations: Number of forward citations received.
        filed_date: Filing date (ISO format string).
        granted_date: Grant date (ISO format string, empty if not granted).
    """

    patent_id: str
    title: str
    status: str
    citations: int
    filed_date: str
    granted_date: str


@dataclass
class PatentPortfolio(SerializableMixin):
    """Aggregated valuation result for a portfolio of patents.

    Attributes:
        patents: The patents in the portfolio.
        total_value: Sum of individual patent valuations.
        fto_score: Freedom-to-operate score in [0, 1].
        thicket_detected: True if a patent thicket is identified.
    """

    patents: list[Patent] = field(default_factory=list)
    total_value: float = 0.0
    fto_score: float = 1.0
    thicket_detected: bool = False


class IPValuator:
    """Valuates patents and patent portfolios using multiple methods."""

    # ------------------------------------------------------------------
    # Relief-from-Royalty
    # ------------------------------------------------------------------

    def value_patent(self, patent: Patent) -> float:
        """Value a single patent using the Relief-from-Royalty method.

        Formula: base_value * citation_impact * status_multiplier

        Args:
            patent: The patent to value.

        Returns:
            Estimated patent value in USD.
        """
        citation_factor = self.citation_impact(patent.citations)
        status_multiplier = self.granted_vs_pending(patent.status)
        return _BASE_PATENT_VALUE * citation_factor * status_multiplier

    def citation_impact(self, citations: int) -> float:
        """Compute the citation impact multiplier.

        Each citation adds 1% to the base value, capped at 100 citations
        (max multiplier = 2.0).

        Args:
            citations: Number of forward citations.

        Returns:
            Multiplier in [1.0, 2.0].

        Raises:
            ValidationError: If citations is negative.
        """
        if citations < 0:
            raise ValidationError(
                f"citations must be non-negative, got {citations}"
            )
        effective = min(citations, _MAX_CITATIONS_FOR_IMPACT)
        return 1.0 + effective / 100.0

    def granted_vs_pending(self, status: str) -> float:
        """Return the value multiplier for a given patent status.

        Args:
            status: Patent status string.

        Returns:
            Multiplier: granted=1.0, pending=0.5, expired=0.1.

        Raises:
            ValidationError: If status is not recognized.
        """
        key = status.lower().strip()
        if key not in _STATUS_MULTIPLIERS:
            raise ValidationError(
                f"Unknown patent status: {status!r}. "
                f"Expected one of: {list(_STATUS_MULTIPLIERS)}"
            )
        return _STATUS_MULTIPLIERS[key]

    # ------------------------------------------------------------------
    # Portfolio valuation
    # ------------------------------------------------------------------

    def value_portfolio(self, patents: list[Patent]) -> PatentPortfolio:
        """Value a portfolio of patents.

        Args:
            patents: List of patents to value.

        Returns:
            PatentPortfolio with total value, FTO score, and thicket flag.
        """
        total_value = sum(self.value_patent(p) for p in patents)
        thicket = self.thicket_detected(patents)
        fto = self.fto_score(patents, [])
        return PatentPortfolio(
            patents=list(patents),
            total_value=total_value,
            fto_score=fto,
            thicket_detected=thicket,
        )

    # ------------------------------------------------------------------
    # Income approach
    # ------------------------------------------------------------------

    def income_approach(
        self, revenue: float, margin: float, discount_rate: float
    ) -> float:
        """Value IP using the income (DCF-like) approach.

        Formula: (revenue * margin) / discount_rate

        Args:
            revenue: Annual revenue attributable to the IP.
            margin: Profit margin in [0, 1].
            discount_rate: Discount rate (WACC) > 0.

        Returns:
            Estimated IP value.

        Raises:
            ValidationError: If revenue is negative.
            InvalidRangeError: If margin is outside [0, 1].
            DivisionByZeroError: If discount_rate is zero.
        """
        if revenue < 0:
            raise ValidationError(
                f"revenue must be non-negative, got {revenue}"
            )
        if not 0.0 <= margin <= 1.0:
            raise InvalidRangeError(
                f"margin must be in [0, 1], got {margin}"
            )
        if discount_rate == 0:
            raise DivisionByZeroError("discount_rate cannot be zero")
        return (revenue * margin) / discount_rate

    # ------------------------------------------------------------------
    # Market approach
    # ------------------------------------------------------------------

    def market_approach(self, comps_multiple: float, revenue: float) -> float:
        """Value IP using the market (comps) approach.

        Formula: comps_multiple * revenue

        Args:
            comps_multiple: Comparable-company valuation multiple.
            revenue: Annual revenue attributable to the IP.

        Returns:
            Estimated IP value.

        Raises:
            ValidationError: If revenue or comps_multiple is negative.
        """
        if revenue < 0:
            raise ValidationError(
                f"revenue must be non-negative, got {revenue}"
            )
        if comps_multiple < 0:
            raise ValidationError(
                f"comps_multiple must be non-negative, got {comps_multiple}"
            )
        return comps_multiple * revenue

    # ------------------------------------------------------------------
    # Freedom-to-Operate
    # ------------------------------------------------------------------

    def fto_score(
        self, patents: list[Patent], competitor_patents: list[Patent]
    ) -> float:
        """Compute freedom-to-operate score.

        The score is the fraction of our patents that do NOT overlap
        (by title similarity) with any competitor patent. A score of 1.0
        means full freedom to operate; 0.0 means every patent overlaps.

        Args:
            patents: Our patents.
            competitor_patents: Competitor patents to check against.

        Returns:
            FTO score in [0, 1].
        """
        if not patents:
            return 1.0
        if not competitor_patents:
            return 1.0

        competitor_tokens = [
            self._title_tokens(p.title) for p in competitor_patents
        ]

        non_overlapping = 0
        for patent in patents:
            our_tokens = self._title_tokens(patent.title)
            overlaps = any(
                our_tokens & comp_tokens for comp_tokens in competitor_tokens
            )
            if not overlaps:
                non_overlapping += 1

        return non_overlapping / len(patents)

    # ------------------------------------------------------------------
    # Patent thicket detection
    # ------------------------------------------------------------------

    def thicket_detected(self, patents: list[Patent]) -> bool:
        """Detect whether a set of patents forms a thicket.

        A thicket is identified when two or more patents share significant
        title keywords, indicating overlapping technology areas that create
        a dense web of IP rights.

        Args:
            patents: Patents to analyze.

        Returns:
            True if a thicket is detected.
        """
        if len(patents) < 2:
            return False

        token_sets = [self._title_tokens(p.title) for p in patents]
        for i in range(len(token_sets)):
            for j in range(i + 1, len(token_sets)):
                if token_sets[i] & token_sets[j]:
                    return True
        return False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _title_tokens(title: str) -> set[str]:
        """Extract significant lowercase tokens from a patent title."""
        words = re.findall(r"[a-z]+", title.lower())
        return {w for w in words if w not in _STOPWORDS}
