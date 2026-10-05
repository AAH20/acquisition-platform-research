"""Tests for recommendation module."""
import pytest
from acquisition_platform.recommendation import (
    UserProfile,
    Item,
    Recommendation,
    RecommendationEngine,
)


def _make_items() -> list[Item]:
    """Create a diverse catalog of items for testing."""
    return [
        Item(item_id="i1", features={"topic": "ml", "difficulty": "advanced"}, category="saas"),
        Item(item_id="i2", features={"topic": "ml", "difficulty": "beginner"}, category="saas"),
        Item(item_id="i3", features={"topic": "web", "difficulty": "beginner"}, category="ecommerce"),
        Item(item_id="i4", features={"topic": "web", "difficulty": "advanced"}, category="ecommerce"),
        Item(item_id="i5", features={"topic": "data", "difficulty": "intermediate"}, category="content"),
        Item(item_id="i6", features={"topic": "data", "difficulty": "advanced"}, category="content"),
    ]


def _make_users() -> list[UserProfile]:
    """Create users with different preferences and histories."""
    return [
        UserProfile(
            user_id="u1",
            preferences={"topic": "ml", "difficulty": "advanced"},
            history=["i1"],
        ),
        UserProfile(
            user_id="u2",
            preferences={"topic": "web", "difficulty": "beginner"},
            history=["i3"],
        ),
        UserProfile(
            user_id="u3",
            preferences={"topic": "data", "difficulty": "intermediate"},
            history=["i5"],
        ),
    ]


class TestRecommendationEngine:
    """TDD tests for the recommendation engine."""

    def test_recommendation_score(self):
        """Recommendation scored."""
        engine = RecommendationEngine()
        user = UserProfile(user_id="u1", preferences={"topic": "ml"}, history=[])
        item = Item(item_id="i1", features={"topic": "ml", "difficulty": "advanced"}, category="saas")
        score = engine.score_recommendation(user, item)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        assert score > 0.0

    def test_ranking(self):
        """Recommendations ranked."""
        engine = RecommendationEngine()
        users = _make_users()
        items = _make_items()
        recs = engine.rank_recommendations(users[0], items)
        assert len(recs) > 0
        scores = [r.score for r in recs]
        assert scores == sorted(scores, reverse=True)
        for rec in recs:
            assert isinstance(rec, Recommendation)
            assert rec.user.user_id == users[0].user_id

    def test_empty_recommendations(self):
        """Empty returns defaults."""
        engine = RecommendationEngine()
        user = UserProfile(user_id="u1", preferences={"topic": "ml"}, history=[])
        recs = engine.rank_recommendations(user, [])
        assert recs == []
        report = engine.generate_recommendation_report(recs)
        assert report["total"] == 0
        assert report["average_score"] == 0.0

    def test_personalization(self):
        """Personalization applied."""
        engine = RecommendationEngine()
        users = _make_users()
        items = _make_items()
        recs = engine.personalize(users[0], items)
        assert len(recs) > 0
        for rec in recs:
            assert isinstance(rec, Recommendation)
            assert rec.user.user_id == users[0].user_id
        # Personalized scores should be >= base scores
        base_recs = engine.rank_recommendations(users[0], items)
        base_scores = {r.item.item_id: r.score for r in base_recs}
        for rec in recs:
            assert rec.score >= base_scores.get(rec.item.item_id, 0.0)

    def test_collaborative_filtering(self):
        """Collaborative filtering applied."""
        engine = RecommendationEngine()
        users = _make_users()
        items = _make_items()
        recs = engine.collaborative_filtering(users[0], users, items)
        assert len(recs) > 0
        for rec in recs:
            assert isinstance(rec, Recommendation)
            assert rec.user.user_id == users[0].user_id
        # Items in similar users' history should have higher scores
        similar_user_items = set()
        for u in users[1:]:
            if u.preferences.get("topic") == users[0].preferences.get("topic"):
                similar_user_items.update(u.history)
        if similar_user_items:
            top_rec = recs[0]
            assert top_rec.item.item_id in similar_user_items or top_rec.score > 0

    def test_content_filtering(self):
        """Content filtering applied."""
        engine = RecommendationEngine()
        users = _make_users()
        items = _make_items()
        recs = engine.content_filtering(users[0], items)
        assert len(recs) > 0
        for rec in recs:
            assert isinstance(rec, Recommendation)
        # Items matching user preferences should score higher
        matching_items = [i for i in items if i.features.get("topic") == "ml"]
        non_matching = [i for i in items if i.features.get("topic") != "ml"]
        if matching_items and non_matching:
            matching_scores = [r.score for r in recs if r.item.item_id in {i.item_id for i in matching_items}]
            non_matching_scores = [r.score for r in recs if r.item.item_id in {i.item_id for i in non_matching}]
            if matching_scores and non_matching_scores:
                assert max(matching_scores) >= max(non_matching_scores)

    def test_recommendation_report(self):
        """Report generated."""
        engine = RecommendationEngine()
        users = _make_users()
        items = _make_items()
        recs = engine.rank_recommendations(users[0], items)
        report = engine.generate_recommendation_report(recs)
        assert isinstance(report, dict)
        assert "total" in report
        assert "average_score" in report
        assert "diversity_score" in report
        assert "categories" in report
        assert "top_item" in report
        assert report["total"] == len(recs)
        assert report["average_score"] >= 0.0
        assert 0.0 <= report["diversity_score"] <= 1.0
        assert isinstance(report["categories"], list)
        assert report["top_item"] is not None

    def test_cold_start(self):
        """Cold start handled."""
        engine = RecommendationEngine()
        items = _make_items()
        recs = engine.cold_start_recommendation(items)
        assert len(recs) > 0
        for rec in recs:
            assert isinstance(rec, Recommendation)
            assert rec.score > 0.0
            assert rec.explanation != ""

    def test_diversity(self):
        """Diversity scored."""
        engine = RecommendationEngine()
        users = _make_users()
        items = _make_items()
        recs = engine.rank_recommendations(users[0], items)
        diversity = engine.diversity_score(recs)
        assert isinstance(diversity, float)
        assert 0.0 <= diversity <= 1.0
        # With multiple categories in catalog, diversity should be > 0
        assert diversity > 0.0

    def test_explanation(self):
        """Explanation generated."""
        engine = RecommendationEngine()
        user = UserProfile(user_id="u1", preferences={"topic": "ml"}, history=[])
        item = Item(item_id="i1", features={"topic": "ml"}, category="saas")
        rec = Recommendation(user=user, item=item, score=0.8, explanation="")
        explanation = engine.explain_recommendation(rec)
        assert isinstance(explanation, str)
        assert len(explanation) > 0
