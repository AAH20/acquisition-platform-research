"""Tests for dynamic pricing module."""
import pytest
from acquisition_platform.dynamic_pricing import PricingEngine, PriceRecommendation


class TestPricingEngine:
    """TDD tests for the dynamic pricing engine (Stackelberg game)."""

    def test_basic_price_recommendation(self):
        engine = PricingEngine()
        rec = engine.recommend_price(
            base_value=100000,
            demand_level=0.7,
            competition_level=0.5,
            market_condition="normal",
        )
        assert rec.recommended_price > 0
        assert rec.confidence > 0

    def test_high_demand_increases_price(self):
        engine = PricingEngine()
        low_demand = engine.recommend_price(
            base_value=100000, demand_level=0.2, competition_level=0.5,
            market_condition="normal",
        )
        high_demand = engine.recommend_price(
            base_value=100000, demand_level=0.9, competition_level=0.5,
            market_condition="normal",
        )
        assert high_demand.recommended_price > low_demand.recommended_price

    def test_high_competition_decreases_price(self):
        engine = PricingEngine()
        low_comp = engine.recommend_price(
            base_value=100000, demand_level=0.5, competition_level=0.1,
            market_condition="normal",
        )
        high_comp = engine.recommend_price(
            base_value=100000, demand_level=0.5, competition_level=0.9,
            market_condition="normal",
        )
        assert high_comp.recommended_price < low_comp.recommended_price

    def test_bull_market_premium(self):
        engine = PricingEngine()
        normal = engine.recommend_price(
            base_value=100000, demand_level=0.5, competition_level=0.5,
            market_condition="normal",
        )
        bull = engine.recommend_price(
            base_value=100000, demand_level=0.5, competition_level=0.5,
            market_condition="bull",
        )
        assert bull.recommended_price > normal.recommended_price

    def test_bear_market_discount(self):
        engine = PricingEngine()
        normal = engine.recommend_price(
            base_value=100000, demand_level=0.5, competition_level=0.5,
            market_condition="normal",
        )
        bear = engine.recommend_price(
            base_value=100000, demand_level=0.5, competition_level=0.5,
            market_condition="bear",
        )
        assert bear.recommended_price < normal.recommended_price

    def test_price_within_bounds(self):
        engine = PricingEngine()
        rec = engine.recommend_price(
            base_value=100000, demand_level=0.5, competition_level=0.5,
            market_condition="normal",
        )
        assert rec.floor_price <= rec.recommended_price <= rec.ceiling_price

    def test_stackelberg_equilibrium_exists(self):
        engine = PricingEngine()
        rec = engine.recommend_price(
            base_value=100000, demand_level=0.5, competition_level=0.5,
            market_condition="normal",
        )
        assert rec.equilibrium_price > 0
