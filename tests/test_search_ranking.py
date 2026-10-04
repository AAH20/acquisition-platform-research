"""Tests for search ranking module."""
import pytest

from acquisition_platform.exceptions import EmptyInputError
from acquisition_platform.search_ranking import SearchRanker, RankedListing, Listing


class TestSearchRanker:
    """TDD tests for the search ranking engine (submodular max)."""

    def test_empty_listings_raises(self):
        ranker = SearchRanker()
        with pytest.raises(EmptyInputError):
            ranker.rank("", [])

    def test_single_listing_returns_single_result(self):
        ranker = SearchRanker()
        listings = [Listing(id="l1", title="SaaS Platform", relevance=0.9)]
        results = ranker.rank("saas", listings)
        assert len(results) == 1

    def test_higher_relevance_ranks_higher(self):
        ranker = SearchRanker()
        listings = [
            Listing(id="l1", title="Low", relevance=0.3),
            Listing(id="l2", title="High", relevance=0.9),
        ]
        results = ranker.rank("test", listings)
        assert results[0].id == "l2"

    def test_diversity_penalty_reduces_similar_listings(self):
        ranker = SearchRanker()
        listings = [
            Listing(id="l1", title="SaaS A", relevance=0.9, category="saas"),
            Listing(id="l2", title="SaaS B", relevance=0.85, category="saas"),
            Listing(id="l3", title="E-commerce", relevance=0.7, category="ecommerce"),
        ]
        results = ranker.rank("platform", listings)
        # Should include diverse categories
        categories = [r.category for r in results]
        assert len(set(categories)) >= 2

    def test_ranked_listing_has_score(self):
        ranker = SearchRanker()
        listings = [Listing(id="l1", title="Test", relevance=0.8)]
        results = ranker.rank("test", listings)
        assert results[0].score > 0

    def test_personalization_boosts_preferred_category(self):
        ranker = SearchRanker()
        listings = [
            Listing(id="l1", title="SaaS", relevance=0.7, category="saas"),
            Listing(id="l2", title="E-commerce", relevance=0.7, category="ecommerce"),
        ]
        results = ranker.rank("platform", listings, user_preferences={"category": "saas"})
        assert results[0].id == "l1"

    def test_no_duplicate_listings_in_results(self):
        ranker = SearchRanker()
        listings = [
            Listing(id="l1", title="Test", relevance=0.9),
            Listing(id="l1", title="Test", relevance=0.9),
        ]
        results = ranker.rank("test", listings)
        ids = [r.id for r in results]
        assert len(ids) == len(set(ids))
