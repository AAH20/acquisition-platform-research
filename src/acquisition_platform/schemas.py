"""Shared schemas and value objects for the acquisition platform.

This module defines common data types used across all engines:
- Money: A monetary value with amount and currency
- Confidence: A confidence score with a qualitative level
- RiskLevel: Enumeration of risk tiers
- Category: Enumeration of business categories
- Utility functions: clamp, classify_risk, format_money
"""

from dataclasses import dataclass
from enum import Enum


class RiskLevel(Enum):
    """Risk level classification."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Category(Enum):
    """Business category classification."""

    SAAS = "saas"
    ECOMMERCE = "ecommerce"
    CONTENT = "content"
    SERVICE = "service"
    OTHER = "other"


@dataclass(frozen=True)
class Money:
    """A monetary value with amount and currency.

    Attributes:
        amount: The monetary amount.
        currency: ISO 4217 currency code (e.g., "USD", "EUR").
    """

    amount: float
    currency: str


@dataclass(frozen=True)
class Confidence:
    """A confidence score with a qualitative level.

    Attributes:
        score: Confidence score in [0.0, 1.0].
        level: Qualitative level (e.g., "low", "medium", "high").
    """

    score: float
    level: str


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value to the range [min_val, max_val].

    Args:
        value: The value to clamp.
        min_val: The minimum allowed value.
        max_val: The maximum allowed value.

    Returns:
        The clamped value.
    """
    return max(min_val, min(max_val, value))


def classify_risk(score: float) -> RiskLevel:
    """Classify a risk score into a RiskLevel.

    Score ranges:
        [0.0, 0.3) -> LOW
        [0.3, 0.6) -> MEDIUM
        [0.6, 0.9) -> HIGH
        [0.9, 1.0] -> CRITICAL

    Args:
        score: Risk score, typically in [0.0, 1.0]. Values outside
            this range are clamped.

    Returns:
        The corresponding RiskLevel.
    """
    score = clamp(score, 0.0, 1.0)
    if score < 0.3:
        return RiskLevel.LOW
    elif score < 0.6:
        return RiskLevel.MEDIUM
    elif score < 0.9:
        return RiskLevel.HIGH
    else:
        return RiskLevel.CRITICAL


def format_money(amount: float, currency: str) -> str:
    """Format a monetary amount with the appropriate currency symbol.

    Args:
        amount: The monetary amount.
        currency: ISO 4217 currency code.

    Returns:
        Formatted string with currency symbol and amount.
    """
    symbols = {
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
        "JPY": "¥",
    }
    symbol = symbols.get(currency, currency + " ")
    if amount < 0:
        return f"-{symbol}{abs(amount):,.2f}"
    return f"{symbol}{amount:,.2f}"
