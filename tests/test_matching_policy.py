"""Tests for the injectable matching policy.

Acceptance gate: the default policy must reproduce the legacy score exactly,
so existing matcher behaviour is preserved while the policy becomes evolvable.
"""

from __future__ import annotations

import pytest

from acquisition_platform.exceptions import InvalidRangeError, ValidationError
from acquisition_platform.matching import Buyer, Seller, BuyerSellerMatcher, MatchingPolicy


def buyer(budget: float = 100.0, category: str = "saas") -> Buyer:
    return Buyer(id="b1", budget=budget, preferences={"category": category})


def seller(price: float = 40.0, category: str = "saas") -> Seller:
    return Seller(id="s1", asking_price=price, attributes={"category": category})


class TestMatchingPolicy:
    def test_default_policy_matches_legacy_score(self):
        for price in (10.0, 40.0, 90.0):
            policy = MatchingPolicy()
            legacy = max(0.0, min(1.0, 1.0 - price / 100.0))
            assert policy.score(buyer(), seller(price)) == pytest.approx(legacy)

    def test_midpoint_feature_rewards_fair_price(self):
        policy = MatchingPolicy(gap_weight=0.0, midpoint_weight=1.0)
        fair = policy.score(buyer(100.0), seller(50.0))
        cheap = policy.score(buyer(100.0), seller(5.0))
        assert fair > cheap

    def test_size_feature_rewards_larger_deals(self):
        policy = MatchingPolicy(gap_weight=0.0, size_weight=1.0)
        large = policy.score(buyer(100.0), seller(80.0))
        small = policy.score(buyer(100.0), seller(10.0))
        assert large > small

    def test_bias_shifts_score(self):
        policy = MatchingPolicy(bias=0.2)
        assert policy.score(buyer(100.0), seller(100.0)) == pytest.approx(0.2)

    def test_score_is_clamped(self):
        policy = MatchingPolicy(scale=10.0, bias=5.0)
        assert policy.score(buyer(), seller()) <= 1.0
        assert policy.score(buyer(), seller()) >= 0.0

    def test_negative_scale_raises(self):
        with pytest.raises(InvalidRangeError):
            MatchingPolicy(scale=-1.0)

    def test_all_zero_weights_raise(self):
        with pytest.raises(ValidationError):
            MatchingPolicy(gap_weight=0.0, midpoint_weight=0.0, size_weight=0.0)

    def test_weights_roundtrip_through_params(self):
        policy = MatchingPolicy(gap_weight=0.4, midpoint_weight=0.5, size_weight=0.1)
        assert policy.to_params() == {
            "gap_weight": 0.4,
            "midpoint_weight": 0.5,
            "size_weight": 0.1,
            "bias": 0.0,
            "scale": 1.0,
        }
        assert MatchingPolicy.from_params(policy.to_params()) == policy

    def test_zero_budget_returns_zero(self):
        assert MatchingPolicy().score(buyer(0.0), seller(10.0)) == 0.0


class TestMatcherWithPolicy:
    def test_default_construction_preserves_behaviour(self):
        b = [Buyer("b1", 100.0, {"category": "saas"})]
        s = [Seller("s1", 40.0, {"category": "saas"})]
        matcher = BuyerSellerMatcher()
        matches = matcher.match(b, s)
        assert len(matches) == 1
        assert matches[0].score == pytest.approx(0.6)

    def test_custom_policy_changes_ranking(self):
        buyers = [Buyer("b1", 100.0, {"category": "saas"})]
        sellers = [
            Seller("cheap", 10.0, {"category": "saas"}),
            Seller("fair", 50.0, {"category": "saas"}),
        ]
        legacy = BuyerSellerMatcher().match(buyers, sellers)[0].seller_id
        midpoint = BuyerSellerMatcher(
            policy=MatchingPolicy(gap_weight=0.0, midpoint_weight=1.0)
        ).match(buyers, sellers)[0].seller_id
        assert legacy == "cheap"
        assert midpoint == "fair"

    def test_policy_is_exposed(self):
        matcher = BuyerSellerMatcher(policy=MatchingPolicy(bias=0.1))
        assert matcher.policy.bias == 0.1
