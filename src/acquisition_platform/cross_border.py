"""Cross-Border M&A Deal Analyzer.

Handles currency risk assessment, regulatory risk scoring, tax optimization,
cultural distance calculation, deal structure recommendations, financing
strategy, treaty benefits, and timeline estimation for cross-border M&A
transactions.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from acquisition_platform.exceptions import ValidationError
from acquisition_platform.serialization import SerializableMixin

from acquisition_platform.observability import get_logger, log_execution_time, log_module_call

logger = get_logger(__name__)


# Currency volatility scores (annualized volatility as a fraction)
_CURRENCY_VOLATILITY: dict[str, float] = {
    "USD": 0.08,
    "EUR": 0.10,
    "GBP": 0.12,
    "JPY": 0.11,
    "CHF": 0.09,
    "CAD": 0.09,
    "AUD": 0.11,
    "CNY": 0.06,
    "INR": 0.10,
    "BRL": 0.18,
    "MXN": 0.15,
    "KRW": 0.12,
    "SGD": 0.07,
    "HKD": 0.05,
    "SEK": 0.11,
    "NOK": 0.12,
    "DKK": 0.10,
    "NZD": 0.12,
    "ZAR": 0.16,
    "RUB": 0.20,
}

# Regulatory complexity scores by country (0-1)
_REGULATORY_COMPLEXITY: dict[str, float] = {
    "US": 0.7,
    "DE": 0.6,
    "UK": 0.6,
    "FR": 0.6,
    "JP": 0.5,
    "CN": 0.8,
    "BR": 0.7,
    "IN": 0.7,
    "AU": 0.5,
    "CA": 0.5,
    "KR": 0.5,
    "SG": 0.3,
    "HK": 0.4,
    "CH": 0.4,
    "NL": 0.5,
    "SE": 0.4,
    "NO": 0.4,
    "DK": 0.4,
    "NZ": 0.4,
    "MX": 0.6,
    "ZA": 0.6,
    "RU": 0.8,
}

# Corporate tax rates by country
_TAX_RATES: dict[str, float] = {
    "US": 0.21,
    "DE": 0.30,
    "UK": 0.25,
    "FR": 0.25,
    "JP": 0.30,
    "CN": 0.25,
    "BR": 0.34,
    "IN": 0.25,
    "AU": 0.30,
    "CA": 0.26,
    "KR": 0.24,
    "SG": 0.17,
    "HK": 0.165,
    "CH": 0.18,
    "NL": 0.25,
    "SE": 0.22,
    "NO": 0.22,
    "DK": 0.22,
    "NZ": 0.28,
    "MX": 0.30,
    "ZA": 0.27,
    "RU": 0.20,
}

# Cultural distance matrix (Hofstede-based, normalized 0-1)
_CULTURAL_DISTANCE: dict[tuple[str, str], float] = {
    ("US", "DE"): 0.35,
    ("US", "UK"): 0.15,
    ("US", "FR"): 0.40,
    ("US", "JP"): 0.55,
    ("US", "CN"): 0.65,
    ("US", "BR"): 0.45,
    ("US", "IN"): 0.50,
    ("US", "AU"): 0.20,
    ("US", "CA"): 0.15,
    ("DE", "UK"): 0.30,
    ("DE", "FR"): 0.25,
    ("DE", "JP"): 0.50,
    ("DE", "CN"): 0.60,
    ("DE", "BR"): 0.40,
    ("DE", "IN"): 0.45,
    ("DE", "AU"): 0.35,
    ("DE", "CA"): 0.30,
    ("UK", "FR"): 0.30,
    ("UK", "JP"): 0.50,
    ("UK", "CN"): 0.60,
    ("UK", "BR"): 0.40,
    ("UK", "IN"): 0.45,
    ("UK", "AU"): 0.15,
    ("UK", "CA"): 0.15,
    ("FR", "JP"): 0.50,
    ("FR", "CN"): 0.60,
    ("FR", "BR"): 0.35,
    ("FR", "IN"): 0.45,
    ("FR", "AU"): 0.35,
    ("FR", "CA"): 0.30,
    ("JP", "CN"): 0.40,
    ("JP", "BR"): 0.55,
    ("JP", "IN"): 0.50,
    ("JP", "AU"): 0.50,
    ("JP", "CA"): 0.50,
    ("CN", "BR"): 0.55,
    ("CN", "IN"): 0.45,
    ("CN", "AU"): 0.60,
    ("CN", "CA"): 0.60,
    ("BR", "IN"): 0.50,
    ("BR", "AU"): 0.45,
    ("BR", "CA"): 0.40,
    ("IN", "AU"): 0.50,
    ("IN", "CA"): 0.45,
    ("AU", "CA"): 0.15,
}

# Tax treaty benefits by country pair
_TREATY_BENEFITS: dict[tuple[str, str], list[str]] = {
    ("US", "DE"): [
        "Reduced withholding tax on dividends (5%)",
        "Reduced withholding tax on interest (0%)",
        "Reduced withholding tax on royalties (0%)",
        "Permanent establishment protection",
        "Mutual agreement procedure",
    ],
    ("US", "UK"): [
        "Reduced withholding tax on dividends (5%)",
        "Reduced withholding tax on interest (0%)",
        "Reduced withholding tax on royalties (0%)",
        "Permanent establishment protection",
        "Mutual agreement procedure",
    ],
    ("US", "FR"): [
        "Reduced withholding tax on dividends (5%)",
        "Reduced withholding tax on interest (0%)",
        "Reduced withholding tax on royalties (0%)",
        "Permanent establishment protection",
        "Mutual agreement procedure",
    ],
    ("US", "JP"): [
        "Reduced withholding tax on dividends (10%)",
        "Reduced withholding tax on interest (10%)",
        "Reduced withholding tax on royalties (10%)",
        "Permanent establishment protection",
        "Mutual agreement procedure",
    ],
    ("US", "CN"): [
        "Reduced withholding tax on dividends (10%)",
        "Reduced withholding tax on interest (10%)",
        "Reduced withholding tax on royalties (10%)",
        "Permanent establishment protection",
        "Mutual agreement procedure",
    ],
    ("US", "BR"): [
        "Reduced withholding tax on dividends (15%)",
        "Reduced withholding tax on interest (15%)",
        "Reduced withholding tax on royalties (15%)",
        "Permanent establishment protection",
        "Mutual agreement procedure",
    ],
    ("US", "IN"): [
        "Reduced withholding tax on dividends (15%)",
        "Reduced withholding tax on interest (15%)",
        "Reduced withholding tax on royalties (15%)",
        "Permanent establishment protection",
        "Mutual agreement procedure",
    ],
    ("US", "AU"): [
        "Reduced withholding tax on dividends (15%)",
        "Reduced withholding tax on interest (10%)",
        "Reduced withholding tax on royalties (10%)",
        "Permanent establishment protection",
        "Mutual agreement procedure",
    ],
    ("US", "CA"): [
        "Reduced withholding tax on dividends (5%)",
        "Reduced withholding tax on interest (0%)",
        "Reduced withholding tax on royalties (0%)",
        "Permanent establishment protection",
        "Mutual agreement procedure",
    ],
    ("DE", "UK"): [
        "Reduced withholding tax on dividends (0%)",
        "Reduced withholding tax on interest (0%)",
        "Reduced withholding tax on royalties (0%)",
        "Permanent establishment protection",
        "Mutual agreement procedure",
    ],
    ("DE", "FR"): [
        "Reduced withholding tax on dividends (0%)",
        "Reduced withholding tax on interest (0%)",
        "Reduced withholding tax on royalties (0%)",
        "Permanent establishment protection",
        "Mutual agreement procedure",
    ],
    ("DE", "JP"): [
        "Reduced withholding tax on dividends (10%)",
        "Reduced withholding tax on interest (10%)",
        "Reduced withholding tax on royalties (10%)",
        "Permanent establishment protection",
        "Mutual agreement procedure",
    ],
    ("DE", "CN"): [
        "Reduced withholding tax on dividends (10%)",
        "Reduced withholding tax on interest (10%)",
        "Reduced withholding tax on royalties (10%)",
        "Permanent establishment protection",
        "Mutual agreement procedure",
    ],
    ("DE", "BR"): [
        "Reduced withholding tax on dividends (15%)",
        "Reduced withholding tax on interest (15%)",
        "Reduced withholding tax on royalties (15%)",
        "Permanent establishment protection",
        "Mutual agreement procedure",
    ],
    ("DE", "IN"): [
        "Reduced withholding tax on dividends (15%)",
        "Reduced withholding tax on interest (15%)",
        "Reduced withholding tax on royalties (15%)",
        "Permanent establishment protection",
        "Mutual agreement procedure",
    ],
    ("DE", "AU"): [
        "Reduced withholding tax on dividends (15%)",
        "Reduced withholding tax on interest (10%)",
        "Reduced withholding tax on royalties (10%)",
        "Permanent establishment protection",
        "Mutual agreement procedure",
    ],
    ("DE", "CA"): [
        "Reduced withholding tax on dividends (5%)",
        "Reduced withholding tax on interest (0%)",
        "Reduced withholding tax on royalties (0%)",
        "Permanent establishment protection",
        "Mutual agreement procedure",
    ],
    ("UK", "FR"): [
        "Reduced withholding tax on dividends (0%)",
        "Reduced withholding tax on interest (0%)",
        "Reduced withholding tax on royalties (0%)",
        "Permanent establishment protection",
        "Mutual agreement procedure",
    ],
    ("UK", "JP"): [
        "Reduced withholding tax on dividends (10%)",
        "Reduced withholding tax on interest (10%)",
        "Reduced withholding tax on royalties (10%)",
        "Permanent establishment protection",
        "Mutual agreement procedure",
    ],
    ("UK", "CN"): [
        "Reduced withholding tax on dividends (10%)",
        "Reduced withholding tax on interest (10%)",
        "Reduced withholding tax on royalties (10%)",
        "Permanent establishment protection",
        "Mutual agreement procedure",
    ],
    ("UK", "BR"): [
        "Reduced withholding tax on dividends (15%)",
        "Reduced withholding tax on interest (15%)",
        "Reduced withholding tax on royalties (15%)",
        "Permanent establishment protection",
        "Mutual agreement procedure",
    ],
    ("UK", "IN"): [
        "Reduced withholding tax on dividends (15%)",
        "Reduced withholding tax on interest (15%)",
        "Reduced withholding tax on royalties (15%)",
        "Permanent establishment protection",
        "Mutual agreement procedure",
    ],
    ("UK", "AU"): [
        "Reduced withholding tax on dividends (0%)",
        "Reduced withholding tax on interest (0%)",
        "Reduced withholding tax on royalties (0%)",
        "Permanent establishment protection",
        "Mutual agreement procedure",
    ],
    ("UK", "CA"): [
        "Reduced withholding tax on dividends (5%)",
        "Reduced withholding tax on interest (0%)",
        "Reduced withholding tax on royalties (0%)",
        "Permanent establishment protection",
        "Mutual agreement procedure",
    ],
    ("FR", "JP"): [
        "Reduced withholding tax on dividends (10%)",
        "Reduced withholding tax on interest (10%)",
        "Reduced withholding tax on royalties (10%)",
        "Permanent establishment protection",
        "Mutual agreement procedure",
    ],
    ("FR", "CN"): [
        "Reduced withholding tax on dividends (10%)",
        "Reduced withholding tax on interest (10%)",
        "Reduced withholding tax on royalties (10%)",
        "Permanent establishment protection",
        "Mutual agreement procedure",
    ],
    ("FR", "BR"): [
        "Reduced withholding tax on dividends (15%)",
        "Reduced withholding tax on interest (15%)",
        "Reduced withholding tax on royalties (15%)",
        "Permanent establishment protection",
        "Mutual agreement procedure",
    ],
    ("FR", "IN"): [
        "Reduced withholding tax on dividends (15%)",
        "Reduced withholding tax on interest (15%)",
        "Reduced withholding tax on royalties (15%)",
        "Permanent establishment protection",
        "Mutual agreement procedure",
    ],
    ("FR", "AU"): [
        "Reduced withholding tax on dividends (15%)",
        "Reduced withholding tax on interest (10%)",
        "Reduced withholding tax on royalties (10%)",
        "Permanent establishment protection",
        "Mutual agreement procedure",
    ],
    ("FR", "CA"): [
        "Reduced withholding tax on dividends (5%)",
        "Reduced withholding tax on interest (0%)",
        "Reduced withholding tax on royalties (0%)",
        "Permanent establishment protection",
        "Mutual agreement procedure",
    ],
    ("JP", "CN"): [
        "Reduced withholding tax on dividends (10%)",
        "Reduced withholding tax on interest (10%)",
        "Reduced withholding tax on royalties (10%)",
        "Permanent establishment protection",
        "Mutual agreement procedure",
    ],
    ("JP", "BR"): [
        "Reduced withholding tax on dividends (15%)",
        "Reduced withholding tax on interest (15%)",
        "Reduced withholding tax on royalties (15%)",
        "Permanent establishment protection",
        "Mutual agreement procedure",
    ],
    ("JP", "IN"): [
        "Reduced withholding tax on dividends (15%)",
        "Reduced withholding tax on interest (15%)",
        "Reduced withholding tax on royalties (15%)",
        "Permanent establishment protection",
        "Mutual agreement procedure",
    ],
    ("JP", "AU"): [
        "Reduced withholding tax on dividends (15%)",
        "Reduced withholding tax on interest (10%)",
        "Reduced withholding tax on royalties (10%)",
        "Permanent establishment protection",
        "Mutual agreement procedure",
    ],
    ("JP", "CA"): [
        "Reduced withholding tax on dividends (10%)",
        "Reduced withholding tax on interest (10%)",
        "Reduced withholding tax on royalties (10%)",
        "Permanent establishment protection",
        "Mutual agreement procedure",
    ],
    ("CN", "BR"): [
        "Reduced withholding tax on dividends (15%)",
        "Reduced withholding tax on interest (15%)",
        "Reduced withholding tax on royalties (15%)",
        "Permanent establishment protection",
        "Mutual agreement procedure",
    ],
    ("CN", "IN"): [
        "Reduced withholding tax on dividends (10%)",
        "Reduced withholding tax on interest (10%)",
        "Reduced withholding tax on royalties (10%)",
        "Permanent establishment protection",
        "Mutual agreement procedure",
    ],
    ("CN", "AU"): [
        "Reduced withholding tax on dividends (15%)",
        "Reduced withholding tax on interest (10%)",
        "Reduced withholding tax on royalties (10%)",
        "Permanent establishment protection",
        "Mutual agreement procedure",
    ],
    ("CN", "CA"): [
        "Reduced withholding tax on dividends (10%)",
        "Reduced withholding tax on interest (10%)",
        "Reduced withholding tax on royalties (10%)",
        "Permanent establishment protection",
        "Mutual agreement procedure",
    ],
    ("BR", "IN"): [
        "Reduced withholding tax on dividends (15%)",
        "Reduced withholding tax on interest (15%)",
        "Reduced withholding tax on royalties (15%)",
        "Permanent establishment protection",
        "Mutual agreement procedure",
    ],
    ("BR", "AU"): [
        "Reduced withholding tax on dividends (15%)",
        "Reduced withholding tax on interest (10%)",
        "Reduced withholding tax on royalties (10%)",
        "Permanent establishment protection",
        "Mutual agreement procedure",
    ],
    ("BR", "CA"): [
        "Reduced withholding tax on dividends (15%)",
        "Reduced withholding tax on interest (15%)",
        "Reduced withholding tax on royalties (15%)",
        "Permanent establishment protection",
        "Mutual agreement procedure",
    ],
    ("IN", "AU"): [
        "Reduced withholding tax on dividends (15%)",
        "Reduced withholding tax on interest (10%)",
        "Reduced withholding tax on royalties (10%)",
        "Permanent establishment protection",
        "Mutual agreement procedure",
    ],
    ("IN", "CA"): [
        "Reduced withholding tax on dividends (15%)",
        "Reduced withholding tax on interest (15%)",
        "Reduced withholding tax on royalties (15%)",
        "Permanent establishment protection",
        "Mutual agreement procedure",
    ],
    ("AU", "CA"): [
        "Reduced withholding tax on dividends (15%)",
        "Reduced withholding tax on interest (10%)",
        "Reduced withholding tax on royalties (10%)",
        "Permanent establishment protection",
        "Mutual agreement procedure",
    ],
}

# Default treaty benefits for pairs not explicitly listed
_DEFAULT_TREATY_BENEFITS = [
    "Reduced withholding tax on dividends",
    "Reduced withholding tax on interest",
    "Reduced withholding tax on royalties",
    "Permanent establishment protection",
    "Mutual agreement procedure",
]


@dataclass
class CrossBorderDeal(SerializableMixin):
    """A cross-border M&A deal between two countries."""

    acquirer_country: str
    target_country: str
    deal_value: float
    currency: str
    industry: str


@dataclass
class CrossBorderResult(SerializableMixin):
    """Result of cross-border M&A deal analysis."""

    deal: CrossBorderDeal
    currency_risk: float = 0.0
    regulatory_risk: float = 0.0
    tax_optimization: float = 0.0
    cultural_distance: float = 0.0
    timeline_months: int = 0


class CrossBorderAnalyzer:
    """Analyzer for cross-border M&A transactions.

    Assesses currency risk, regulatory risk, tax optimization opportunities,
    cultural distance, deal structure, financing strategy, treaty benefits,
    and timeline estimation.
    """

    @log_execution_time(logger)
    def assess_currency_risk(self, deal: CrossBorderDeal) -> float:
        """Assess currency risk for a cross-border deal.

        Risk is based on the volatility of the target currency relative
        to the acquirer's home currency (assumed USD).

        Args:
            deal: The cross-border deal to analyze.

        Returns:
            Currency risk score in [0, 1].

        Raises:
            ValidationError: If deal_value is negative.
        """
        if deal.deal_value < 0:
            raise ValidationError("deal_value cannot be negative")

        if not deal.currency or not deal.acquirer_country:
            return 0.0

        currency = deal.currency.upper()
        volatility = _CURRENCY_VOLATILITY.get(currency, 0.15)

        # Normalize volatility to [0, 1] (max volatility ~0.20)
        risk = min(volatility / 0.20, 1.0)
        return risk

    @log_execution_time(logger)
    def assess_regulatory_risk(self, deal: CrossBorderDeal) -> float:
        """Assess regulatory risk for a cross-border deal.

        Risk is based on the regulatory complexity of both countries
        and the industry sector.

        Args:
            deal: The cross-border deal to analyze.

        Returns:
            Regulatory risk score in [0, 1].

        Raises:
            ValidationError: If deal_value is negative.
        """
        if deal.deal_value < 0:
            raise ValidationError("deal_value cannot be negative")

        if not deal.acquirer_country or not deal.target_country:
            return 0.0

        acquirer = deal.acquirer_country.upper()
        target = deal.target_country.upper()

        acquirer_risk = _REGULATORY_COMPLEXITY.get(acquirer, 0.5)
        target_risk = _REGULATORY_COMPLEXITY.get(target, 0.5)

        # Industry multiplier: some industries face more regulation
        industry_multipliers = {
            "technology": 1.0,
            "healthcare": 1.2,
            "finance": 1.3,
            "energy": 1.2,
            "defense": 1.5,
            "telecommunications": 1.3,
            "media": 1.1,
            "consumer": 0.9,
            "industrial": 1.0,
            "materials": 1.0,
        }
        multiplier = industry_multipliers.get(deal.industry.lower(), 1.0)

        # Weighted combination: target country risk is more important
        raw_risk = 0.3 * acquirer_risk + 0.7 * target_risk
        risk = min(raw_risk * multiplier, 1.0)
        return risk

    @log_execution_time(logger)
    def tax_optimization(self, deal: CrossBorderDeal) -> float:
        """Calculate tax optimization score for a cross-border deal.

        Score represents the potential tax savings from treaty optimization,
        based on the difference between the two countries' tax rates.

        Args:
            deal: The cross-border deal to analyze.

        Returns:
            Tax optimization score in [0, 1].

        Raises:
            ValidationError: If deal_value is negative.
        """
        if deal.deal_value < 0:
            raise ValidationError("deal_value cannot be negative")

        if not deal.acquirer_country or not deal.target_country:
            return 0.0

        acquirer = deal.acquirer_country.upper()
        target = deal.target_country.upper()

        acquirer_rate = _TAX_RATES.get(acquirer, 0.25)
        target_rate = _TAX_RATES.get(target, 0.25)

        # Tax optimization potential is higher when rates differ more
        rate_diff = abs(acquirer_rate - target_rate)
        # Normalize: max possible diff is ~0.14 (e.g., DE 0.30 vs SG 0.17)
        score = min(rate_diff / 0.14, 1.0)
        return score

    @log_execution_time(logger)
    def cultural_distance(self, country1: str, country2: str) -> float:
        """Calculate cultural distance between two countries.

        Uses Hofstede-based cultural dimensions normalized to [0, 1].

        Args:
            country1: First country code.
            country2: Second country code.

        Returns:
            Cultural distance score in [0, 1].
        """
        if not country1 or not country2:
            return 0.0

        c1 = country1.upper()
        c2 = country2.upper()

        if c1 == c2:
            return 0.0

        # Check both orderings
        distance = _CULTURAL_DISTANCE.get((c1, c2))
        if distance is None:
            distance = _CULTURAL_DISTANCE.get((c2, c1))
        if distance is None:
            # Default moderate distance for unknown pairs
            distance = 0.5

        return distance

    @log_execution_time(logger)
    def recommend_deal_structure(self, deal: CrossBorderDeal) -> str:
        """Recommend a deal structure based on deal characteristics.

        Args:
            deal: The cross-border deal to analyze.

        Returns:
            Recommended deal structure as a string.

        Raises:
            ValidationError: If deal_value is negative.
        """
        if deal.deal_value < 0:
            raise ValidationError("deal_value cannot be negative")

        if not deal.acquirer_country or not deal.target_country:
            return "Direct acquisition"

        value = deal.deal_value
        industry = deal.industry.lower()

        # Large deals in sensitive industries may need joint venture
        if value > 1_000_000_000 and industry in ("defense", "telecommunications", "energy"):
            return "Joint venture with local partner"

        # Medium-large deals may benefit from holding company structure
        if value > 500_000_000:
            return "Holding company acquisition"

        # Technology deals often use asset purchase for IP protection
        if industry == "technology" and value > 100_000_000:
            return "Asset purchase with IP holding company"

        # Default: stock purchase
        return "Stock purchase"

    @log_execution_time(logger)
    def financing_strategy(self, deal: CrossBorderDeal) -> str:
        """Recommend a financing strategy based on deal characteristics.

        Args:
            deal: The cross-border deal to analyze.

        Returns:
            Recommended financing strategy as a string.

        Raises:
            ValidationError: If deal_value is negative.
        """
        if deal.deal_value < 0:
            raise ValidationError("deal_value cannot be negative")

        if not deal.acquirer_country or not deal.target_country:
            return "Cash financing"

        value = deal.deal_value
        currency = deal.currency.upper()

        # Very large deals need mixed financing
        if value > 2_000_000_000:
            return "Mixed financing (cash + debt + equity)"

        # Large deals in volatile currencies need hedging
        if value > 500_000_000 and currency in ("BRL", "RUB", "MXN", "ZAR"):
            return "Debt financing with currency hedging"

        # Medium deals can use debt
        if value > 100_000_000:
            return "Debt financing"

        # Small deals: cash
        return "Cash financing"

    @log_execution_time(logger)
    def treaty_benefits(self, country1: str, country2: str) -> list[str]:
        """Assess tax treaty benefits between two countries.

        Args:
            country1: First country code.
            country2: Second country code.

        Returns:
            List of treaty benefit descriptions.
        """
        if not country1 or not country2:
            return []

        c1 = country1.upper()
        c2 = country2.upper()

        if c1 == c2:
            return []

        # Check both orderings
        benefits = _TREATY_BENEFITS.get((c1, c2))
        if benefits is None:
            benefits = _TREATY_BENEFITS.get((c2, c1))
        if benefits is None:
            benefits = _DEFAULT_TREATY_BENEFITS

        return list(benefits)

    @log_execution_time(logger)
    def cross_border_timeline(self, deal: CrossBorderDeal) -> int:
        """Estimate deal timeline in months.

        Timeline is based on deal value, regulatory complexity, and
        cultural distance between countries.

        Args:
            deal: The cross-border deal to analyze.

        Returns:
            Estimated timeline in months.

        Raises:
            ValidationError: If deal_value is negative.
        """
        if deal.deal_value < 0:
            raise ValidationError("deal_value cannot be negative")

        if not deal.acquirer_country or not deal.target_country:
            return 0

        # Base timeline
        base_months = 6

        # Deal value factor
        value = deal.deal_value
        if value > 2_000_000_000:
            base_months += 12
        elif value > 1_000_000_000:
            base_months += 9
        elif value > 500_000_000:
            base_months += 6
        elif value > 100_000_000:
            base_months += 3

        # Regulatory complexity factor
        acquirer = deal.acquirer_country.upper()
        target = deal.target_country.upper()
        acquirer_risk = _REGULATORY_COMPLEXITY.get(acquirer, 0.5)
        target_risk = _REGULATORY_COMPLEXITY.get(target, 0.5)
        avg_risk = (acquirer_risk + target_risk) / 2
        base_months += int(avg_risk * 6)

        # Cultural distance factor
        cultural_dist = self.cultural_distance(acquirer, target)
        base_months += int(cultural_dist * 4)

        return base_months

    @log_execution_time(logger)
    def generate_cross_border_report(self, deal: CrossBorderDeal) -> CrossBorderResult:
        """Generate a comprehensive cross-border deal analysis report.

        Args:
            deal: The cross-border deal to analyze.

        Returns:
            CrossBorderResult with all analysis dimensions.

        Raises:
            ValidationError: If deal_value is negative.
        """
        if deal.deal_value < 0:
            raise ValidationError("deal_value cannot be negative")

        currency_risk = self.assess_currency_risk(deal)
        regulatory_risk = self.assess_regulatory_risk(deal)
        tax_opt = self.tax_optimization(deal)
        cultural_dist = self.cultural_distance(deal.acquirer_country, deal.target_country)
        timeline = self.cross_border_timeline(deal)

        return CrossBorderResult(
            deal=deal,
            currency_risk=currency_risk,
            regulatory_risk=regulatory_risk,
            tax_optimization=tax_opt,
            cultural_distance=cultural_dist,
            timeline_months=timeline,
        )
