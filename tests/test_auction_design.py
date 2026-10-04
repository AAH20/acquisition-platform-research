"""Tests for auction design module."""
import pytest
from acquisition_platform.auction_design import (
    AuctionConfig,
    AuctionDesigner,
    AuctionResult,
    Bid,
)


class TestVickreyAuction:
    """Tests for second-price sealed-bid (Vickrey) auction."""

    def test_vickrey_auction(self):
        """Winner pays second-highest bid, not their own bid."""
        designer = AuctionDesigner()
        bids = [
            Bid(bidder_id="alice", amount=100.0),
            Bid(bidder_id="bob", amount=80.0),
            Bid(bidder_id="carol", amount=60.0),
        ]
        config = AuctionConfig(format="vickrey", reserve_price=0.0, min_increment=1.0)
        result = designer.design_auction(bids, config)
        assert result.winner_id == "alice"
        assert result.winning_bid == 100.0
        assert result.revenue == 80.0
        assert result.format == "vickrey"


class TestGSPAuction:
    """Tests for generalized second-price (GSP) auction."""

    def test_gsp_auction(self):
        """Winner pays next-highest bid (GSP rule)."""
        designer = AuctionDesigner()
        bids = [
            Bid(bidder_id="alice", amount=100.0),
            Bid(bidder_id="bob", amount=80.0),
            Bid(bidder_id="carol", amount=60.0),
        ]
        config = AuctionConfig(format="gsp", reserve_price=0.0, min_increment=1.0)
        result = designer.design_auction(bids, config)
        assert result.winner_id == "alice"
        assert result.winning_bid == 100.0
        assert result.revenue == 80.0
        assert result.format == "gsp"


class TestEnglishAuction:
    """Tests for English (ascending-price) auction."""

    def test_english_auction(self):
        """Highest bidder wins at their bid amount."""
        designer = AuctionDesigner()
        bids = [
            Bid(bidder_id="alice", amount=100.0),
            Bid(bidder_id="bob", amount=80.0),
            Bid(bidder_id="carol", amount=60.0),
        ]
        config = AuctionConfig(format="english", reserve_price=0.0, min_increment=1.0)
        result = designer.design_auction(bids, config)
        assert result.winner_id == "alice"
        assert result.winning_bid == 100.0
        assert result.revenue == 100.0
        assert result.format == "english"


class TestDutchAuction:
    """Tests for Dutch (descending-price) auction."""

    def test_dutch_auction(self):
        """First to accept wins; highest bidder wins at their bid."""
        designer = AuctionDesigner()
        bids = [
            Bid(bidder_id="alice", amount=100.0),
            Bid(bidder_id="bob", amount=80.0),
            Bid(bidder_id="carol", amount=60.0),
        ]
        config = AuctionConfig(format="dutch", reserve_price=0.0, min_increment=1.0)
        result = designer.design_auction(bids, config)
        assert result.winner_id == "alice"
        assert result.winning_bid == 100.0
        assert result.revenue == 100.0
        assert result.format == "dutch"


class TestReservePrice:
    """Tests for reserve price enforcement."""

    def test_reserve_price(self):
        """Bids below reserve are rejected."""
        designer = AuctionDesigner()
        bids = [
            Bid(bidder_id="alice", amount=100.0),
            Bid(bidder_id="bob", amount=80.0),
            Bid(bidder_id="carol", amount=40.0),
        ]
        config = AuctionConfig(format="vickrey", reserve_price=50.0, min_increment=1.0)
        result = designer.design_auction(bids, config)
        assert result.winner_id == "alice"
        assert result.winning_bid == 100.0
        assert result.revenue == 80.0

    def test_all_bids_below_reserve(self):
        """No winner when all bids are below reserve."""
        designer = AuctionDesigner()
        bids = [
            Bid(bidder_id="alice", amount=30.0),
            Bid(bidder_id="bob", amount=20.0),
        ]
        config = AuctionConfig(format="vickrey", reserve_price=50.0, min_increment=1.0)
        result = designer.design_auction(bids, config)
        assert result.winner_id is None
        assert result.winning_bid == 0.0
        assert result.revenue == 0.0


class TestShillBiddingDetection:
    """Tests for shill bidding detection."""

    def test_shill_bidding_detection(self):
        """Detect artificially inflated bids."""
        designer = AuctionDesigner()
        bids = [
            Bid(bidder_id="alice", amount=100.0),
            Bid(bidder_id="bob", amount=95.0),
            Bid(bidder_id="carol", amount=90.0),
            Bid(bidder_id="shill1", amount=99.0),
            Bid(bidder_id="shill2", amount=98.0),
        ]
        suspicious = designer.detect_shill_bidding(bids)
        assert "shill1" in suspicious
        assert "shill2" in suspicious
        assert "alice" not in suspicious

    def test_no_shill_bidding(self):
        """No suspicious bidders when bids are well-distributed."""
        designer = AuctionDesigner()
        bids = [
            Bid(bidder_id="alice", amount=100.0),
            Bid(bidder_id="bob", amount=70.0),
            Bid(bidder_id="carol", amount=40.0),
        ]
        suspicious = designer.detect_shill_bidding(bids)
        assert suspicious == []


class TestRevenueEstimation:
    """Tests for revenue estimation."""

    def test_revenue_estimation(self):
        """Estimate expected revenue for given bids and config."""
        designer = AuctionDesigner()
        bids = [
            Bid(bidder_id="alice", amount=100.0),
            Bid(bidder_id="bob", amount=80.0),
            Bid(bidder_id="carol", amount=60.0),
        ]
        config = AuctionConfig(format="vickrey", reserve_price=0.0, min_increment=1.0)
        estimated = designer.estimate_revenue(bids, config)
        assert estimated > 0
        assert estimated <= 100.0

    def test_revenue_estimation_with_reserve(self):
        """Revenue estimation accounts for reserve price."""
        designer = AuctionDesigner()
        bids = [
            Bid(bidder_id="alice", amount=100.0),
            Bid(bidder_id="bob", amount=80.0),
        ]
        config = AuctionConfig(format="vickrey", reserve_price=50.0, min_increment=1.0)
        estimated = designer.estimate_revenue(bids, config)
        assert estimated >= 50.0


class TestAuctionFormatSelection:
    """Tests for auction format selection."""

    def test_auction_format_selection(self):
        """Select optimal format based on parameters."""
        designer = AuctionDesigner()
        # Many bidders, high value -> English (competitive pressure)
        fmt = designer.select_format(num_bidders=10, item_value=1000000.0)
        assert fmt == "english"
        # Few bidders, low value -> Dutch (quick sale)
        fmt = designer.select_format(num_bidders=2, item_value=100.0)
        assert fmt == "dutch"
        # Moderate bidders -> Vickrey (truthful bidding)
        fmt = designer.select_format(num_bidders=5, item_value=10000.0)
        assert fmt == "vickrey"


class TestEmptyBids:
    """Tests for empty bid list."""

    def test_empty_bids(self):
        """No bids returns no winner."""
        designer = AuctionDesigner()
        config = AuctionConfig(format="vickrey", reserve_price=0.0, min_increment=1.0)
        result = designer.design_auction([], config)
        assert result.winner_id is None
        assert result.winning_bid == 0.0
        assert result.revenue == 0.0


class TestSingleBid:
    """Tests for single bid scenario."""

    def test_single_bid(self):
        """Single bid wins at reserve price."""
        designer = AuctionDesigner()
        bids = [Bid(bidder_id="alice", amount=100.0)]
        config = AuctionConfig(format="vickrey", reserve_price=50.0, min_increment=1.0)
        result = designer.design_auction(bids, config)
        assert result.winner_id == "alice"
        assert result.winning_bid == 100.0
        assert result.revenue == 50.0
