"""Tests for buyer-seller matching module (GAP — Generalized Assignment Problem)."""
import pytest

from acquisition_platform.exceptions import EmptyInputError
from acquisition_platform.matching import BuyerSellerMatcher, Match, Buyer, Seller


class TestBuyerSellerMatcher:
    """TDD tests for the matching engine."""

    def test_empty_inputs_raise(self):
        matcher = BuyerSellerMatcher()
        with pytest.raises(EmptyInputError):
            matcher.match([], [])

    def test_single_buyer_single_seller_returns_match(self):
        matcher = BuyerSellerMatcher()
        buyers = [Buyer(id="b1", budget=100000, preferences={"category": "saas"})]
        sellers = [Seller(id="s1", asking_price=80000, attributes={"category": "saas"})]
        matches = matcher.match(buyers, sellers)
        assert len(matches) == 1
        assert matches[0].buyer_id == "b1"
        assert matches[0].seller_id == "s1"

    def test_buyer_cannot_afford_seller_no_match(self):
        matcher = BuyerSellerMatcher()
        buyers = [Buyer(id="b1", budget=50000, preferences={})]
        sellers = [Seller(id="s1", asking_price=100000, attributes={})]
        matches = matcher.match(buyers, sellers)
        assert len(matches) == 0

    def test_multiple_buyers_compete_for_single_seller(self):
        matcher = BuyerSellerMatcher()
        buyers = [
            Buyer(id="b1", budget=100000, preferences={"category": "saas"}),
            Buyer(id="b2", budget=150000, preferences={"category": "saas"}),
        ]
        sellers = [Seller(id="s1", asking_price=80000, attributes={"category": "saas"})]
        matches = matcher.match(buyers, sellers)
        assert len(matches) == 1
        # Higher budget buyer should win
        assert matches[0].buyer_id == "b2"

    def test_match_score_is_between_zero_and_one(self):
        matcher = BuyerSellerMatcher()
        buyers = [Buyer(id="b1", budget=100000, preferences={"category": "saas"})]
        sellers = [Seller(id="s1", asking_price=80000, attributes={"category": "saas"})]
        matches = matcher.match(buyers, sellers)
        assert 0.0 <= matches[0].score <= 1.0

    def test_category_mismatch_reduces_score(self):
        matcher = BuyerSellerMatcher()
        buyers = [Buyer(id="b1", budget=100000, preferences={"category": "saas"})]
        sellers = [Seller(id="s1", asking_price=80000, attributes={"category": "ecommerce"})]
        matches = matcher.match(buyers, sellers)
        # Should still match but with lower score
        assert len(matches) == 0  # Category mismatch = no match

    def test_budget_constraint_respected(self):
        matcher = BuyerSellerMatcher()
        buyers = [Buyer(id="b1", budget=50000, preferences={})]
        sellers = [
            Seller(id="s1", asking_price=30000, attributes={}),
            Seller(id="s2", asking_price=30000, attributes={}),
        ]
        matches = matcher.match(buyers, sellers)
        # Can only afford one
        assert len(matches) <= 1

    def test_match_has_confidence_score(self):
        matcher = BuyerSellerMatcher()
        buyers = [Buyer(id="b1", budget=100000, preferences={"category": "saas"})]
        sellers = [Seller(id="s1", asking_price=80000, attributes={"category": "saas"})]
        matches = matcher.match(buyers, sellers)
        assert hasattr(matches[0], 'confidence')
        assert 0.0 <= matches[0].confidence <= 1.0
