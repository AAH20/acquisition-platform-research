"""Tests for recommendation module."""
import pytest
from acquisition_platform.recommendation import (
    UserProfile,
    ItemProfile,
    Recommendation,
    RecommendationResult,
    RecommendationEngine,
)


def _make_items() -> list[ItemProfile]:
    """Create a diverse catalog of items for testing."""
    return [
        ItemProfile(item_id="i1", attributes={"topic": "ml", "difficulty": "advanced"}, category="saas"),
        ItemProfile(item_id="i2", attributes={"topic": "ml", "difficulty": "beginner"}, category="saas"),
        ItemProfile(item_id="i3", attributes={"topic": "web", "difficulty": "beginner"}, category="ecommerce"),
        ItemProfile(item_id="i4", attributes={"topic": "web", "difficulty": "advanced"}, category="ecommerce"),
        ItemProfile(item_id="i5", attributes={"topic": "data", "difficulty": "intermediate"}, category="content"),
        ItemProfile(item_id="i6", attributes={"topic": "data", "difficulty": "advanced"}, category="content"),
        ItemProfile(item_id="i7", attributes={"topic": "ml", "difficulty": "intermediate"}, category="service"),
        ItemProfile(item_id="i8", attributes={"topic": "web", "difficulty": "intermediate"}, category="service"),
    ]


def _make_users() -> list[UserProfile]:
    """Create users with different preferences and histories."""
    return [
        UserProfile(
            user_id="u1",
            preferences={"topic": "ml", "difficulty": "advanced"},
            history=["i1", "i2"],
        ),
        UserProfile(
            user_id="u2",
            preferences={"topic": "web", "difficulty": "beginner"},
            history=["i3", "i4"],
        ),
        UserProfile(
            user_id="u3",
            preferences={"topic": "data", "difficulty": "intermediate"},
            history=["i5"],
        ),
    ]


class TestRecommendationEngine:
    """TDD tests for the recommendation engine."""

    def test_basic_recommendation(self):
        """Recommend items for a user with history and preferences."""
        engine = RecommendationEngine()
        users = _make_users()
        items = _make_items()
        for u in users:
            engine.add_user_profile(u)
        for it in items:
            engine.add_item_profile(it)

        result = engine.recommend(users[0], items, k=3)
        assert isinstance(result, RecommendationResult)
        assert len(result.recommendations) > 0
        assert len(result.recommendations) <= 3
        for rec in result.recommendations:
            assert isinstance(rec, Recommendation)
            assert rec.item_id in {it.item_id for it in items}
            assert rec.score > 0
            assert rec.reason

    def test_cold_start(self):
        """New user with no history still gets recommendations."""
        engine = RecommendationEngine()
        items = _make_items()
        for it in items:
            engine.add_item_profile(it)

        cold_user = UserProfile(
            user_id="cold_user",
            preferences={"topic": "ml"},
            history=[],
        )
        result = engine.recommend(cold_user, items, k=3)
        assert isinstance(result, RecommendationResult)
        assert len(result.recommendations) > 0
        assert len(result.recommendations) <= 3

    def test_collaborative_filtering(self):
        """Users with similar preferences get similar recommendations."""
        engine = RecommendationEngine()
        users = _make_users()
        items = _make_items()
        for u in users:
            engine.add_user_profile(u)
        for it in items:
            engine.add_item_profile(it)

        # u1 and u3 both have "advanced" difficulty preference
        similar = engine.get_similar_users("u1")
        assert isinstance(similar, list)
        # u1 should find at least one similar user
        assert len(similar) >= 1

    def test_content_based(self):
        """Items with similar attributes are found as similar."""
        engine = RecommendationEngine()
        items = _make_items()
        for it in items:
            engine.add_item_profile(it)

        similar = engine.get_similar_items("i1")
        assert isinstance(similar, list)
        # i1 (ml, advanced) should find i2 (ml, beginner) or i7 (ml, intermediate)
        assert len(similar) >= 1
        assert "i1" not in similar

    def test_hybrid(self):
        """Hybrid mode combines CF and content-based signals."""
        engine = RecommendationEngine()
        users = _make_users()
        items = _make_items()
        for u in users:
            engine.add_user_profile(u)
        for it in items:
            engine.add_item_profile(it)

        result = engine.recommend(users[0], items, k=5)
        assert isinstance(result, RecommendationResult)
        assert len(result.recommendations) > 0
        # Hybrid should produce scores that reflect both signals
        scores = [r.score for r in result.recommendations]
        assert all(s > 0 for s in scores)

    def test_diversity(self):
        """Recommendations span multiple categories."""
        engine = RecommendationEngine()
        users = _make_users()
        items = _make_items()
        for u in users:
            engine.add_user_profile(u)
        for it in items:
            engine.add_item_profile(it)

        result = engine.recommend(users[0], items, k=5)
        categories = set()
        item_map = {it.item_id: it for it in items}
        for rec in result.recommendations:
            categories.add(item_map[rec.item_id].category)
        # Should have more than one category in top-5
        assert len(categories) >= 2
        assert result.diversity_score > 0

    def test_personalization(self):
        """Different users get different recommendations."""
        engine = RecommendationEngine()
        users = _make_users()
        items = _make_items()
        for u in users:
            engine.add_user_profile(u)
        for it in items:
            engine.add_item_profile(it)

        result_u1 = engine.recommend(users[0], items, k=3)
        result_u2 = engine.recommend(users[1], items, k=3)

        top_u1 = [r.item_id for r in result_u1.recommendations]
        top_u2 = [r.item_id for r in result_u2.recommendations]
        # Different users should get different top recommendations
        assert top_u1 != top_u2

    def test_empty_catalog(self):
        """No items returns empty recommendation list."""
        engine = RecommendationEngine()
        user = UserProfile(user_id="u1", preferences={"topic": "ml"}, history=[])
        result = engine.recommend(user, [], k=5)
        assert isinstance(result, RecommendationResult)
        assert len(result.recommendations) == 0

    def test_single_item(self):
        """One item in catalog returns at most one recommendation."""
        engine = RecommendationEngine()
        items = [ItemProfile(item_id="only", attributes={"topic": "ml"}, category="saas")]
        for it in items:
            engine.add_item_profile(it)
        user = UserProfile(user_id="u1", preferences={"topic": "ml"}, history=[])
        result = engine.recommend(user, items, k=5)
        assert len(result.recommendations) <= 1

    def test_top_k(self):
        """Returns exactly k recommendations when catalog is large enough."""
        engine = RecommendationEngine()
        items = _make_items()
        for it in items:
            engine.add_item_profile(it)
        user = UserProfile(user_id="u1", preferences={"topic": "ml"}, history=["i1"])
        result = engine.recommend(user, items, k=4)
        assert len(result.recommendations) == 4

    def test_recommendation_result_has_coverage(self):
        """RecommendationResult includes coverage metric."""
        engine = RecommendationEngine()
        items = _make_items()
        for it in items:
            engine.add_item_profile(it)
        user = UserProfile(user_id="u1", preferences={"topic": "ml"}, history=[])
        result = engine.recommend(user, items, k=3)
        assert 0.0 <= result.coverage <= 1.0

    def test_history_items_excluded(self):
        """Items already in user history are not recommended."""
        engine = RecommendationEngine()
        items = _make_items()
        for it in items:
            engine.add_item_profile(it)
        user = UserProfile(user_id="u1", preferences={"topic": "ml"}, history=["i1", "i2"])
        result = engine.recommend(user, items, k=5)
        recommended_ids = {r.item_id for r in result.recommendations}
        assert "i1" not in recommended_ids
        assert "i2" not in recommended_ids

    def test_add_user_profile(self):
        """add_user_profile stores the user for CF lookups."""
        engine = RecommendationEngine()
        user = UserProfile(user_id="u1", preferences={"topic": "ml"}, history=["i1"])
        engine.add_user_profile(user)
        similar = engine.get_similar_users("u1")
        assert isinstance(similar, list)

    def test_add_item_profile(self):
        """add_item_profile stores the item for content-based lookups."""
        engine = RecommendationEngine()
        item = ItemProfile(item_id="i1", attributes={"topic": "ml"}, category="saas")
        engine.add_item_profile(item)
        similar = engine.get_similar_items("i1")
        assert isinstance(similar, list)
