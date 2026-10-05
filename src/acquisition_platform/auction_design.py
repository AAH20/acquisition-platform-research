"""Auction design module for acquisition platform.

This module implements multiple auction formats used in M&A and
procurement contexts. Auction design is a mechanism design problem
where the goal is to structure the bidding process to maximize
revenue or efficiency while preventing manipulation.

Supported formats:
- Vickrey (second-price sealed-bid): Winner pays second-highest bid.
- GSP (Generalized Second Price): Winner pays next-highest bid.
- Myerson (optimal auction): Uses virtual valuations for optimal revenue.
- English (ascending-price): Highest bidder wins at their bid.
- Dutch (descending-price): First to accept wins at their bid.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from acquisition_platform.exceptions import ValidationError
from acquisition_platform.serialization import SerializableMixin

from acquisition_platform.observability import get_logger, log_execution_time, log_module_call

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class Bid(SerializableMixin):
    """A single bid in an auction.

    Attributes:
        bidder_id: Unique identifier for the bidder.
        amount: Bid amount.
    """

    bidder_id: str
    amount: float


@dataclass
class Bidder(SerializableMixin):
    """A bidder in an auction.

    Attributes:
        bidder_id: Unique identifier for the bidder.
        valuation: The bidder's private valuation of the item.
        budget: The bidder's maximum budget (bid cannot exceed this).
    """

    bidder_id: str
    valuation: float
    budget: float


@dataclass
class AuctionConfig(SerializableMixin):
    """Configuration for an auction.

    Attributes:
        format: Auction format ("vickrey", "gsp", "english", "dutch").
        reserve_price: Minimum acceptable bid.
        min_increment: Minimum bid increment.
    """

    format: str
    reserve_price: float
    min_increment: float


@dataclass
class AuctionResult(SerializableMixin):
    """Result of an auction.

    Attributes:
        winner: Winning bidder's ID ("" if no winner).
        price: Price paid by the winner.
        revenue: Revenue collected by the seller.
        efficiency: Allocation efficiency (1.0 = winner has highest valuation).
        collusion_detected: Whether collusive bidding was detected.
        format: Auction format used.
    """

    winner: str = ""
    price: float = 0.0
    revenue: float = 0.0
    efficiency: float = 0.0
    collusion_detected: bool = False
    format: str = ""

    @property
    def winner_id(self) -> Optional[str]:
        """Backward-compatible alias for winner."""
        return self.winner if self.winner else None

    @property
    def winning_bid(self) -> float:
        """Backward-compatible alias for price."""
        return self.price


# ---------------------------------------------------------------------------
# Auction designer
# ---------------------------------------------------------------------------


class AuctionDesigner:
    """Designs and evaluates auction formats.

    This class implements multiple auction formats and provides
    tools for revenue estimation, reserve price optimization,
    shill bidding detection, and format selection.
    """

    VALID_FORMATS = {"vickrey", "gsp", "english", "dutch"}

    # -----------------------------------------------------------------------
    # New API (Bidder-based)
    # -----------------------------------------------------------------------

    @log_execution_time(logger)
    def vickrey_auction(self, bidders: list[Bidder]) -> AuctionResult:
        """Run a second-price sealed-bid (Vickrey) auction.

        The winner is the bidder with the highest valuation and pays
        the second-highest valuation (or 0 if only one bidder).

        Args:
            bidders: List of bidders.

        Returns:
            AuctionResult with winner, price, revenue, efficiency, and
            collusion detection flag.
        """
        if not bidders:
            return AuctionResult(
                winner="",
                price=0.0,
                revenue=0.0,
                efficiency=0.0,
                collusion_detected=False,
                format="vickrey",
            )

        sorted_bidders = sorted(bidders, key=lambda b: b.valuation, reverse=True)
        winner = sorted_bidders[0]
        second_valuation = sorted_bidders[1].valuation if len(sorted_bidders) > 1 else 0.0

        collusion = self.detect_collusion([b.valuation for b in bidders])

        return AuctionResult(
            winner=winner.bidder_id,
            price=second_valuation,
            revenue=second_valuation,
            efficiency=1.0,
            collusion_detected=collusion,
            format="vickrey",
        )

    @log_execution_time(logger)
    def gsp_auction(self, bidders: list[Bidder]) -> AuctionResult:
        """Run a generalized second-price (GSP) auction.

        For a single-item auction, GSP is equivalent to Vickrey: the
        highest bidder wins and pays the next-highest bid.

        Args:
            bidders: List of bidders.

        Returns:
            AuctionResult with winner, price, revenue, efficiency, and
            collusion detection flag.
        """
        if not bidders:
            return AuctionResult(
                winner="",
                price=0.0,
                revenue=0.0,
                efficiency=0.0,
                collusion_detected=False,
                format="gsp",
            )

        sorted_bidders = sorted(bidders, key=lambda b: b.valuation, reverse=True)
        winner = sorted_bidders[0]
        next_valuation = sorted_bidders[1].valuation if len(sorted_bidders) > 1 else 0.0

        collusion = self.detect_collusion([b.valuation for b in bidders])

        return AuctionResult(
            winner=winner.bidder_id,
            price=next_valuation,
            revenue=next_valuation,
            efficiency=1.0,
            collusion_detected=collusion,
            format="gsp",
        )

    @log_execution_time(logger)
    def myerson_auction(self, bidders: list[Bidder]) -> AuctionResult:
        """Run a Myerson optimal auction.

        Uses virtual valuations to determine the optimal allocation.
        For valuations normalized to [0, 1], the virtual valuation is
        2*v - 1. The winner is the bidder with the highest positive
        virtual valuation, paying the optimal reserve price.

        Args:
            bidders: List of bidders.

        Returns:
            AuctionResult with winner, price, revenue, efficiency, and
            collusion detection flag.
        """
        if not bidders:
            return AuctionResult(
                winner="",
                price=0.0,
                revenue=0.0,
                efficiency=0.0,
                collusion_detected=False,
                format="myerson",
            )

        collusion = self.detect_collusion([b.valuation for b in bidders])

        # Normalize valuations to [0, 1] for virtual valuation computation
        max_val = max(b.valuation for b in bidders)
        if max_val <= 0:
            return AuctionResult(
                winner="",
                price=0.0,
                revenue=0.0,
                efficiency=0.0,
                collusion_detected=collusion,
                format="myerson",
            )

        # Virtual valuation: phi(v) = 2v - 1 (for uniform [0,1])
        # Winner has highest positive virtual valuation
        best_bidder = None
        best_phi = 0.0
        for b in bidders:
            v_norm = b.valuation / max_val
            phi = 2.0 * v_norm - 1.0
            if phi > best_phi:
                best_phi = phi
                best_bidder = b

        if best_bidder is None:
            return AuctionResult(
                winner="",
                price=0.0,
                revenue=0.0,
                efficiency=0.0,
                collusion_detected=collusion,
                format="myerson",
            )

        # Optimal reserve: price at which virtual valuation = 0 => v = 0.5
        # Price = max(reserve, second-highest virtual valuation mapped back)
        sorted_bidders = sorted(bidders, key=lambda b: b.valuation, reverse=True)
        second_val = sorted_bidders[1].valuation if len(sorted_bidders) > 1 else 0.0
        reserve = 0.5 * max_val
        price = max(reserve, second_val)

        return AuctionResult(
            winner=best_bidder.bidder_id,
            price=price,
            revenue=price,
            efficiency=1.0,
            collusion_detected=collusion,
            format="myerson",
        )

    @log_execution_time(logger)
    def revenue_equivalence(self, auction1: AuctionResult, auction2: AuctionResult) -> bool:
        """Check revenue equivalence between two auction results.

        Two auctions are revenue-equivalent if they produce the same
        expected revenue (within a small tolerance).

        Args:
            auction1: First auction result.
            auction2: Second auction result.

        Returns:
            True if revenues are approximately equal.
        """
        tolerance = 1e-6
        return abs(auction1.revenue - auction2.revenue) <= tolerance

    @log_execution_time(logger)
    def bidder_valuation(self, bidder: Bidder) -> float:
        """Compute the effective valuation of a bidder.

        The effective valuation is the minimum of the bidder's
        valuation and their budget (budget-constrained bidders cannot
        bid more than their budget).

        Args:
            bidder: The bidder.

        Returns:
            Effective valuation (min of valuation and budget).
        """
        return min(bidder.valuation, bidder.budget)

    @log_execution_time(logger)
    def optimal_reserve(self, bidders: list[Bidder]) -> float:
        """Compute the optimal reserve price for a set of bidders.

        Uses the median of bidder valuations as a heuristic for the
        optimal reserve price, balancing the trade-off between selling
        the item and maximizing revenue.

        Args:
            bidders: List of bidders.

        Returns:
            Optimal reserve price (0.0 if no bidders).
        """
        if not bidders:
            return 0.0
        valuations = sorted(b.valuation for b in bidders)
        n = len(valuations)
        if n % 2 == 1:
            return valuations[n // 2]
        return (valuations[n // 2 - 1] + valuations[n // 2]) / 2

    @log_execution_time(logger)
    def auction_efficiency(self, result: AuctionResult) -> float:
        """Compute the efficiency of an auction result.

        Efficiency is 1.0 when the winner has the highest valuation
        (allocative efficiency), and 0.0 otherwise.

        Args:
            result: The auction result.

        Returns:
            Efficiency score in [0.0, 1.0].
        """
        return result.efficiency

    @log_execution_time(logger)
    def detect_collusion(self, bids: list[float]) -> bool:
        """Detect potentially collusive bidding patterns.

        Collusion is detected when bids are suspiciously similar
        (low coefficient of variation), suggesting coordination
        among bidders.

        Args:
            bids: List of bid amounts.

        Returns:
            True if collusive behavior is detected.
        """
        if len(bids) < 2:
            return False

        mean = sum(bids) / len(bids)
        if mean <= 0:
            return False

        variance: float = sum((b - mean) ** 2 for b in bids) / len(bids)
        std: float = variance**0.5
        cv: float = std / mean

        # Low coefficient of variation indicates suspiciously uniform bids
        return cv < 0.05

    @log_execution_time(logger)
    def generate_auction_report(self, result: AuctionResult) -> dict[str, object]:
        """Generate a detailed report from an auction result.

        Args:
            result: The auction result.

        Returns:
            Dictionary with auction summary.
        """
        return {
            "winner": result.winner,
            "price": result.price,
            "revenue": result.revenue,
            "efficiency": result.efficiency,
            "collusion_detected": result.collusion_detected,
            "format": result.format,
        }

    # -----------------------------------------------------------------------
    # Legacy API (Bid-based, backward compatible)
    # -----------------------------------------------------------------------

    @log_execution_time(logger)
    def design_auction(self, bids: list[Bid], config: AuctionConfig) -> AuctionResult:
        """Run an auction with the given bids and configuration.

        Args:
            bids: List of bids.
            config: Auction configuration.

        Returns:
            AuctionResult with winner, winning bid, and revenue.

        Raises:
            ValidationError: If the auction format is unknown.
        """
        if config.format not in self.VALID_FORMATS:
            raise ValidationError(f"Unknown auction format: {config.format}")

        valid_bids = [b for b in bids if b.amount >= config.reserve_price]
        if not valid_bids:
            return AuctionResult(
                winner="",
                price=0.0,
                revenue=0.0,
                format=config.format,
            )

        sorted_bids = sorted(valid_bids, key=lambda b: b.amount, reverse=True)
        winner = sorted_bids[0]

        if config.format in ("vickrey", "gsp"):
            if len(sorted_bids) == 1:
                revenue = config.reserve_price
            else:
                revenue = sorted_bids[1].amount
        else:  # english, dutch
            revenue = winner.amount

        return AuctionResult(
            winner=winner.bidder_id,
            price=winner.amount,
            revenue=revenue,
            format=config.format,
        )

    @log_execution_time(logger)
    def optimize_reserve_price(self, bids: list[Bid]) -> float:
        """Compute the optimal reserve price for a set of bids.

        Uses the median of the bids as a heuristic for the optimal
        reserve price, balancing the trade-off between selling the
        item and maximizing revenue.

        Args:
            bids: List of bids.

        Returns:
            Optimal reserve price (0.0 if no bids).
        """
        if not bids:
            return 0.0
        amounts = sorted(b.amount for b in bids)
        n = len(amounts)
        if n % 2 == 1:
            return amounts[n // 2]
        return (amounts[n // 2 - 1] + amounts[n // 2]) / 2

    @log_execution_time(logger)
    def detect_shill_bidding(self, bids: list[Bid]) -> list[str]:
        """Detect potentially fraudulent shill bidding.

        Shill bids are artificially inflated bids placed by the
        seller or colluding parties to drive up the price. They
        are identified as bids within a small threshold of the
        highest bid (but not the highest bid itself).

        Args:
            bids: List of bids.

        Returns:
            List of suspicious bidder IDs.
        """
        if len(bids) < 2:
            return []

        max_bid = max(b.amount for b in bids)
        threshold = 0.05 * max_bid

        suspicious = []
        for b in bids:
            if b.amount < max_bid and (max_bid - b.amount) < threshold:
                suspicious.append(b.bidder_id)
        return suspicious

    @log_execution_time(logger)
    def estimate_revenue(self, bids: list[Bid], config: AuctionConfig) -> float:
        """Estimate expected revenue for an auction.

        Uses the actual bids to compute a point estimate of the
        expected revenue based on the auction format.

        Args:
            bids: List of bids.
            config: Auction configuration.

        Returns:
            Estimated revenue.

        Raises:
            ValidationError: If the auction format is unknown.
        """
        if config.format not in self.VALID_FORMATS:
            raise ValidationError(f"Unknown auction format: {config.format}")

        valid_bids = [b for b in bids if b.amount >= config.reserve_price]
        if not valid_bids:
            return 0.0

        sorted_bids = sorted(valid_bids, key=lambda b: b.amount, reverse=True)

        if config.format in ("vickrey", "gsp"):
            if len(sorted_bids) == 1:
                return config.reserve_price
            return sorted_bids[1].amount
        else:  # english, dutch
            return sorted_bids[0].amount

    @log_execution_time(logger)
    def select_format(self, num_bidders: int, item_value: float) -> str:
        """Select the optimal auction format based on parameters.

        Selection criteria:
        - Many bidders (>= 8) and high value (>= 500000): English
          (competitive pressure maximizes revenue).
        - Few bidders (<= 3) and low value (<= 1000): Dutch
          (quick sale with minimal overhead).
        - Otherwise: Vickrey (truthful bidding, good revenue).

        Args:
            num_bidders: Number of expected bidders.
            item_value: Estimated value of the item.

        Returns:
            Recommended auction format.
        """
        if num_bidders >= 8 and item_value >= 500000:
            return "english"
        if num_bidders <= 3 and item_value <= 1000:
            return "dutch"
        return "vickrey"
