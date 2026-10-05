"""National Security Screening Module.

Screens technology acquisitions for national security concerns: CFIUS
(Committee on Foreign Investment in the United States) risk, foreign direct
investment (FDI) risk, TID (Technology, Infrastructure, Data) business
classification, security clearance requirements, mandatory filing triggers,
mitigation planning, and country/region political risk.

The module is intentionally deterministic and side-effect free so it can be
used inside larger acquisition pipelines.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

from acquisition_platform.observability import get_logger, log_execution_time

logger = get_logger(__name__)


@dataclass
class ScreeningItem:
    """A single technology item subject to national security screening."""

    technology_id: str
    name: str
    tid: bool
    foreign_investor: bool
    government_investor: bool
    clearance_required: str


@dataclass
class ScreeningResult:
    """Aggregate result of screening a portfolio of technology items."""

    items: list[ScreeningItem] = field(default_factory=list)
    cfius_risk: float = 0.0
    fdi_risk: float = 0.0
    clearance_required: bool = False
    filing_required: bool = False
    mitigation_plan: list[str] = field(default_factory=list)


class NationalSecurityScreener:
    """Screens technology portfolios for national security risk.

    Combines CFIUS exposure, FDI jurisdiction risk, TID classification,
    clearance needs, mandatory filing triggers, and mitigation planning into
    a single screening report.
    """

    # Clearance level -> normalized sensitivity weight in [0, 1]
    _CLEARANCE_LEVELS: ClassVar[dict[str, float]] = {
        "none": 0.0,
        "public_trust": 0.2,
        "confidential": 0.3,
        "secret": 0.6,
        "top_secret": 1.0,
    }

    # CFIUS risk component weights
    _TID_WEIGHT: float = 0.4
    _FOREIGN_WEIGHT: float = 0.3
    _GOVERNMENT_WEIGHT: float = 0.2
    _CLEARANCE_WEIGHT: float = 0.1

    # Country political / FDI risk scores in [0, 1]
    _COUNTRY_RISK: ClassVar[dict[str, float]] = {
        "CN": 0.9,
        "RU": 0.9,
        "IR": 0.9,
        "KP": 1.0,
        "SY": 0.85,
        "CU": 0.8,
        "VE": 0.75,
        "PK": 0.7,
        "SA": 0.4,
        "AE": 0.3,
        "IN": 0.3,
        "BR": 0.3,
        "DE": 0.2,
        "FR": 0.2,
        "JP": 0.2,
        "GB": 0.1,
        "CA": 0.1,
        "US": 0.1,
        "AU": 0.1,
    }

    # Default country risk for unknown jurisdictions
    _DEFAULT_COUNTRY_RISK: float = 0.5

    # Region political-risk modifiers (added to the country base score)
    _REGION_MODIFIER: ClassVar[dict[str, float]] = {
        "north_america": 0.0,
        "europe": 0.05,
        "oceania": 0.0,
        "east_asia": 0.1,
        "south_asia": 0.2,
        "latin_america": 0.2,
        "africa": 0.3,
        "middle_east": 0.3,
        "eurasia": 0.35,
    }

    @log_execution_time(logger)
    def screen(
        self,
        technology_id: str,
        name: str,
        tid: bool,
        foreign_investor: bool,
        government_investor: bool,
        clearance_required: str,
    ) -> ScreeningItem:
        """Create a screening item for a single technology.

        Args:
            technology_id: Unique identifier for the technology.
            name: Human-readable technology name.
            tid: Whether the item is a TID (Technology, Infrastructure, Data)
                business.
            foreign_investor: Whether a foreign investor is involved.
            government_investor: Whether a foreign government investor is
                involved.
            clearance_required: Required clearance level (e.g. 'none',
                'secret', 'top_secret').

        Returns:
            A ScreeningItem carrying the supplied classification flags.
        """
        return ScreeningItem(
            technology_id=technology_id,
            name=name,
            tid=tid,
            foreign_investor=foreign_investor,
            government_investor=government_investor,
            clearance_required=clearance_required,
        )

    @log_execution_time(logger)
    def cfius_risk(self, items: list[ScreeningItem]) -> float:
        """Compute normalized CFIUS risk in [0, 1] for a portfolio.

        Risk is the mean per-item exposure, where each item's exposure is a
        weighted combination of TID status, foreign investment, government
        investment, and clearance sensitivity. An empty portfolio is 0.0.

        Args:
            items: Portfolio of screening items.

        Returns:
            CFIUS risk score between 0.0 and 1.0.
        """
        if not items:
            return 0.0

        total = 0.0
        for item in items:
            clearance = self._CLEARANCE_LEVELS.get(
                (item.clearance_required or "none").lower(), 0.0
            )
            item_risk = (
                self._TID_WEIGHT * float(item.tid)
                + self._FOREIGN_WEIGHT * float(item.foreign_investor)
                + self._GOVERNMENT_WEIGHT * float(item.government_investor)
                + self._CLEARANCE_WEIGHT * clearance
            )
            total += item_risk

        return min(max(total / len(items), 0.0), 1.0)

    @log_execution_time(logger)
    def fdi_risk(self, items: list[ScreeningItem], countries: list[str]) -> float:
        """Assess foreign direct investment risk across jurisdictions.

        FDI risk combines the portfolio's foreign-investor exposure with the
        average political risk of the listed countries. Portfolios with no
        foreign investor, or empty portfolios, carry no FDI risk.

        Args:
            items: Portfolio of screening items.
            countries: ISO country codes of the foreign investors.

        Returns:
            FDI risk score between 0.0 and 1.0.
        """
        if not items:
            return 0.0

        foreign_items = [item for item in items if item.foreign_investor]
        if not foreign_items:
            return 0.0

        foreign_fraction = len(foreign_items) / len(items)
        gov_fraction = (
            sum(1 for item in foreign_items if item.government_investor)
            / len(foreign_items)
        )
        exposure = 0.6 * foreign_fraction + 0.4 * gov_fraction

        if countries:
            country_risk = sum(
                self._COUNTRY_RISK.get(c.upper(), self._DEFAULT_COUNTRY_RISK)
                for c in countries
            ) / len(countries)
        else:
            country_risk = self._DEFAULT_COUNTRY_RISK

        return min(max(exposure * country_risk, 0.0), 1.0)

    @log_execution_time(logger)
    def is_tid_business(self, items: list[ScreeningItem]) -> bool:
        """Check whether any item is a TID business.

        Args:
            items: Portfolio of screening items.

        Returns:
            True if at least one item is a TID business, False otherwise.
        """
        return any(item.tid for item in items)

    @log_execution_time(logger)
    def clearance_requirements(self, items: list[ScreeningItem]) -> list[str]:
        """Collect the distinct non-trivial clearance levels required.

        Args:
            items: Portfolio of screening items.

        Returns:
            Sorted list of unique clearance levels (excluding 'none').
        """
        levels = {
            (item.clearance_required or "none").lower()
            for item in items
            if (item.clearance_required or "none").lower() != "none"
        }
        return sorted(levels)

    @log_execution_time(logger)
    def mandatory_filing_required(self, items: list[ScreeningItem]) -> bool:
        """Determine whether a mandatory CFIUS filing is triggered.

        A mandatory filing is required when a TID business receives foreign
        investment, or when a foreign government investor is involved.

        Args:
            items: Portfolio of screening items.

        Returns:
            True if a mandatory filing is required, False otherwise.
        """
        for item in items:
            if item.government_investor:
                return True
            if item.tid and item.foreign_investor:
                return True
        return False

    @log_execution_time(logger)
    def generate_mitigation_plan(self, items: list[ScreeningItem]) -> list[str]:
        """Generate a national security mitigation plan for a portfolio.

        Args:
            items: Portfolio of screening items.

        Returns:
            Ordered list of mitigation steps; empty when there is no exposure.
        """
        if not items:
            return []

        plan: list[str] = []
        has_tid = any(item.tid for item in items)
        has_foreign = any(item.foreign_investor for item in items)
        has_gov = any(item.government_investor for item in items)
        has_clearance = bool(self.clearance_requirements(items))

        if has_tid:
            plan.append(
                "Establish a proxy board or security control agreement (SCA) "
                "to isolate TID business operations."
            )
        if has_foreign:
            plan.append(
                "Negotiate a CFIUS national security agreement requiring "
                "foreign investor reporting and access limitations."
            )
        if has_gov:
            plan.append(
                "Screen the foreign government investor and impose passive "
                "ownership limits with no board or operational control."
            )
        if has_clearance:
            plan.append(
                "Implement a personnel security clearance program and obtain "
                "facility clearance (FCL) for affected sites."
            )
        if self.mandatory_filing_required(items):
            plan.append(
                "Submit a mandatory CFIUS filing (Form 1595) within the "
                "statutory 30-day window."
            )
        if plan:
            plan.append(
                "Establish ongoing compliance monitoring with annual audits "
                "and reporting to the relevant security authority."
            )
        return plan

    @log_execution_time(logger)
    def political_risk(self, country: str, region: str) -> float:
        """Assess political risk for a country within a region.

        Args:
            country: ISO country code.
            region: Region name (e.g. 'east_asia', 'north_america').

        Returns:
            Political risk score between 0.0 and 1.0.
        """
        base = self._COUNTRY_RISK.get(country.upper(), self._DEFAULT_COUNTRY_RISK)
        modifier = self._REGION_MODIFIER.get(region.lower(), 0.0)
        return min(max(base + modifier, 0.0), 1.0)

    @log_execution_time(logger)
    def generate_screening_report(
        self, items: list[ScreeningItem]
    ) -> ScreeningResult:
        """Generate a full national security screening report.

        Args:
            items: Portfolio of screening items.

        Returns:
            ScreeningResult with CFIUS/FDI risk, clearance and filing flags,
            and a mitigation plan. Empty portfolios return safe defaults.
        """
        cfius = self.cfius_risk(items)
        fdi = self.fdi_risk(items, [])
        clearances = self.clearance_requirements(items)
        filing = self.mandatory_filing_required(items)
        plan = self.generate_mitigation_plan(items)

        return ScreeningResult(
            items=list(items),
            cfius_risk=cfius,
            fdi_risk=fdi,
            clearance_required=bool(clearances),
            filing_required=filing,
            mitigation_plan=plan,
        )
