"""Tests for auction design module."""
import pytest
from acquisition_platform.auction_design import (
    AuctionDesigner,
    AuctionResult,
    Bidder,
)


class TestVickreyAuction:
    def test_vickrey_auction(self):
        """Vickrey auction: winner pays second-highest valuation."""
        designer = AuctionDesigner()
        bidders = [
            Bidder(bidder_id="alice", valuation=100.0, budget=200.0),
            Bidder(bidder_id="bob", valuation=80.0, budget=200.0),
            Bidder(bidder_id="carol", valuation=60.0, budget=200.0),
        ]
        result = designer.vickrey_auction(bidders)
        assert result.winner == "alice"
        assert result.price == 80.0
        assert result.revenue == 80.0
        assert result.efficiency == 1.0
        assert result.collusion_detected is False


class TestGSPAuction:
    def test_gsp_auction(self):
        """GSP auction: winner pays next-highest bid."""
        designer = AuctionDesigner()
        bidders = [
            Bidder(bidder_id="alice", valuation=100.0, budget=200.0),
            Bidder(bidder_id="bob", valuation=80.0, budget=200.0),
            Bidder(bidder_id="carol", valuation=60.0, budget=200.0),
        ]
        result = designer.gsp_auction(bidders)
        assert result.winner == "alice"
        assert result.price == 80.0
        assert result.revenue == 80.0


class TestMyersonAuction:
    def test_myerson_auction(self):
        """Myerson optimal auction uses virtual valuations."""
        designer = AuctionDesigner()
        bidders = [
            Bidder(bidder_id="alice", valuation=100.0, budget=200.0),
            Bidder(bidder_id="bob", valuation=80.0, budget=200.0),
            Bidder(bidder_id="carol", valuation=60.0, budget=200.0),
        ]
        result = designer.myerson_auction(bidders)
        assert result.winner == "alice"
        assert result.revenue > 0


class TestEmptyAuction:
    def test_empty_auction(self):
        """Empty auction returns defaults."""
        designer = AuctionDesigner()
        result = designer.vickrey_auction([])
        assert result.winner == ""
        assert result.price == 0.0
        assert result.revenue == 0.0
        assert result.efficiency == 0.0
        assert result.collusion_detected is False


class TestRevenueEquivalence:
    def test_revenue_equivalence(self):
        """Revenue equivalence checked between two auctions."""
        designer = AuctionDesigner()
        bidders = [
            Bidder(bidder_id="alice", valuation=100.0, budget=200.0),
            Bidder(bidder_id="bob", valuation=80.0, budget=200.0),
        ]
        result1 = designer.vickrey_auction(bidders)
        result2 = designer.gsp_auction(bidders)
        assert designer.revenue_equivalence(result1, result2) is True


class TestBidderValuation:
    def test_bidder_valuation(self):
        """Bidder valuation scored."""
        designer = AuctionDesigner()
        bidder = Bidder(bidder_id="alice", valuation=100.0, budget=200.0)
        assert designer.bidder_valuation(bidder) == 100.0
        # Budget-constrained bidder
        bidder2 = Bidder(bidder_id="bob", valuation=100.0, budget=50.0)
        assert designer.bidder_valuation(bidder2) == 50.0


class TestAuctionReport:
    def test_auction_report(self):
        """Report generated from auction result."""
        designer = AuctionDesigner()
        bidders = [
            Bidder(bidder_id="alice", valuation=100.0, budget=200.0),
            Bidder(bidder_id="bob", valuation=80.0, budget=200.0),
        ]
        result = designer.vickrey_auction(bidders)
        report = designer.generate_auction_report(result)
        assert isinstance(report, dict)
        assert report["winner"] == "alice"
        assert report["revenue"] == 80.0


class TestOptimalReserve:
    def test_optimal_reserve(self):
        """Optimal reserve price computed."""
        designer = AuctionDesigner()
        bidders = [
            Bidder(bidder_id="alice", valuation=100.0, budget=200.0),
            Bidder(bidder_id="bob", valuation=80.0, budget=200.0),
            Bidder(bidder_id="carol", valuation=60.0, budget=200.0),
        ]
        reserve = designer.optimal_reserve(bidders)
        assert reserve > 0
        assert reserve <= 100.0


class TestAuctionEfficiency:
    def test_auction_efficiency(self):
        """Efficiency scored."""
        designer = AuctionDesigner()
        bidders = [
            Bidder(bidder_id="alice", valuation=100.0, budget=200.0),
            Bidder(bidder_id="bob", valuation=80.0, budget=200.0),
        ]
        result = designer.vickrey_auction(bidders)
        efficiency = designer.auction_efficiency(result)
        assert efficiency == 1.0


class TestCollusionDetection:
    def test_collusion_detection(self):
        """Collusion detected when bids are suspiciously similar."""
        designer = AuctionDesigner()
        # Suspicious: all bids nearly identical
        collusive_bids = [100.0, 99.5, 99.0, 98.5]
        assert designer.detect_collusion(collusive_bids) is True
        # Normal: well-distributed bids
        normal_bids = [100.0, 70.0, 40.0]
        assert designer.detect_collusion(normal_bids) is False
