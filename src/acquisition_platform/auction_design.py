"""Auction design module for acquisition platform.

This module implements multiple auction formats used in M&A and
procurement contexts. Auction design is a mechanism design problem
where the goal is to structure the bidding process to maximize
revenue or efficiency while preventing manipulation.

Supported formats:
- Vickrey (second-price sealed-bid): Winner pays second-highest bid.
- GSP (Generalized Second Price): Winner pays next-highest bid.
- English (ascending-price): Highest bidder wins at their bid.
- Dutch (descending-price): First to accept wins at their bid.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from acquisition_platform.exceptions import ValidationError
from acquisition_platform.serialization import SerializableMixin

from acquisition_platform.observability import get_logger, log_execution_time, log_module_call

logger = get_logger(__name__)


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
        winner_id: Winning bidder's ID (None if no winner).
        winning_bid: The winning bid amount.
        revenue: Revenue collected by the seller.
        format: Auction format used.
    """

    winner_id: Optional[str]
    winning_bid: float
    revenue: float
    format: str


class AuctionDesigner:
    """Designs and evaluates auction formats.

    This class implements multiple auction formats and provides
    tools for revenue estimation, reserve price optimization,
    shill bidding detection, and format selection.
    """

    VALID_FORMATS = {"vickrey", "gsp", "english", "dutch"}

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
                winner_id=None,
                winning_bid=0.0,
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
            winner_id=winner.bidder_id,
            winning_bid=winner.amount,
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
