"""Sovereign Wealth Fund matching module.

Matches SWF profiles to investment opportunities using multi-criteria scoring.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class SWFProfile:
    """Sovereign Wealth Fund profile with investment criteria."""

    name: str
    aum: float
    horizon_years: int
    risk_tolerance: float
    geographic_focus: list[str]
    sector_focus: list[str]
    min_deal_size: float
    max_deal_size: float


@dataclass
class Opportunity:
    """Investment opportunity with key attributes."""

    name: str
    sector: str
    geography: str
    deal_size: float
    expected_return: float
    risk_score: float
    trl: int


@dataclass
class SWFMatch:
    """Result of matching an SWF profile to an opportunity."""

    swf: SWFProfile
    opportunity: Opportunity
    score: float
    fit_level: str


class SWFMatcher:
    """Matches Sovereign Wealth Funds to investment opportunities."""

    def create_profile(
        self,
        name: str,
        aum: float,
        horizon_years: int,
        risk_tolerance: float,
        geographic_focus: list[str],
        sector_focus: list[str],
        min_deal_size: float,
        max_deal_size: float,
    ) -> SWFProfile:
        """Create an SWF profile."""
        return SWFProfile(
            name=name,
            aum=aum,
            horizon_years=horizon_years,
            risk_tolerance=risk_tolerance,
            geographic_focus=geographic_focus,
            sector_focus=sector_focus,
            min_deal_size=min_deal_size,
            max_deal_size=max_deal_size,
        )

    def match(self, swf: SWFProfile, opportunity: Opportunity | list[Opportunity]) -> SWFMatch | list[SWFMatch]:
        """Match SWF to opportunity or list of opportunities."""
        if isinstance(opportunity, list):
            return [self._match_single(swf, opp) for opp in opportunity]
        return self._match_single(swf, opportunity)

    def _match_single(self, swf: SWFProfile, opportunity: Opportunity) -> SWFMatch:
        """Match SWF to a single opportunity."""
        score = self.criteria_score(swf, opportunity)
        fit_level = self._fit_level(score)
        return SWFMatch(swf=swf, opportunity=opportunity, score=score, fit_level=fit_level)

    def criteria_score(self, swf: SWFProfile, opportunity: Opportunity) -> float:
        """Compute overall investment criteria score (0-1)."""
        geo = self.geographic_preference(swf, opportunity)
        sector = self.sector_preference(swf, opportunity)
        horizon = self.horizon_matching(swf, opportunity)
        risk = self.risk_tolerance_score(swf, opportunity)
        size = self._deal_size_fit(swf, opportunity)
        score = (geo * 0.25 + sector * 0.25 + horizon * 0.2 + risk * 0.2 + size * 0.1)
        return max(0.0, min(1.0, score))

    def portfolio_fit(self, swf: SWFProfile, opportunities: list[Opportunity]) -> float:
        """Assess how well a portfolio of opportunities fits the SWF (0-1)."""
        if not opportunities:
            return 0.0
        scores = [self.criteria_score(swf, opp) for opp in opportunities]
        return max(0.0, min(1.0, sum(scores) / len(scores)))

    def geographic_preference(self, swf: SWFProfile, opportunity: Opportunity) -> float:
        """Score geographic alignment (0-1)."""
        if not swf.geographic_focus:
            return 0.5
        if opportunity.geography in swf.geographic_focus:
            return 1.0
        return 0.0

    def sector_preference(self, swf: SWFProfile, opportunity: Opportunity) -> float:
        """Score sector alignment (0-1)."""
        if not swf.sector_focus:
            return 0.5
        if opportunity.sector in swf.sector_focus:
            return 1.0
        return 0.0

    def horizon_matching(self, swf: SWFProfile, opportunity: Opportunity) -> float:
        """Score investment horizon compatibility (0-1).

        Higher TRL (technology readiness level) aligns with longer horizons.
        """
        if swf.horizon_years <= 0:
            return 0.0
        # Map TRL 1-9 to expected years: lower TRL = longer time to market
        years_to_market = max(1, 10 - opportunity.trl)
        if years_to_market <= swf.horizon_years:
            return 1.0
        return max(0.0, 1.0 - (years_to_market - swf.horizon_years) / swf.horizon_years)

    def risk_tolerance_score(self, swf: SWFProfile, opportunity: Opportunity) -> float:
        """Score risk tolerance alignment (0-1).

        Perfect when opportunity risk equals SWF risk tolerance.
        """
        diff = abs(opportunity.risk_score - swf.risk_tolerance)
        return max(0.0, 1.0 - diff)

    def generate_match_report(self, matches: list[SWFMatch]) -> dict[str, Any]:
        """Generate a summary report from a list of matches."""
        if not matches:
            return {
                "total_matches": 0,
                "average_score": 0.0,
                "matches": [],
            }
        avg_score = sum(m.score for m in matches) / len(matches)
        return {
            "total_matches": len(matches),
            "average_score": avg_score,
            "matches": [
                {
                    "swf_name": m.swf.name,
                    "opportunity_name": m.opportunity.name,
                    "score": m.score,
                    "fit_level": m.fit_level,
                }
                for m in matches
            ],
        }

    def _fit_level(self, score: float) -> str:
        """Classify fit level from score."""
        if score >= 0.7:
            return "high"
        if score >= 0.4:
            return "medium"
        return "low"

    def _deal_size_fit(self, swf: SWFProfile, opportunity: Opportunity) -> float:
        """Score deal size fit (0-1)."""
        if opportunity.deal_size < swf.min_deal_size:
            return 0.0
        if opportunity.deal_size > swf.max_deal_size:
            return 0.0
        return 1.0
