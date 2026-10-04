"""Search ranking engine using submodular maximization.

Submodular maximization is NP-hard in general. This module implements a
greedy approximation that balances relevance, diversity, and personalization
to produce a ranked list of listings.
"""

from dataclasses import dataclass
from typing import Any

from acquisition_platform.exceptions import EmptyInputError, InvalidRangeError
from acquisition_platform.serialization import SerializableMixin


@dataclass
class Listing(SerializableMixin):
    """A searchable listing with relevance and category metadata."""

    id: str
    title: str
    relevance: float
    category: str = ""


@dataclass
class RankedListing(SerializableMixin):
    """A listing with its computed ranking score."""

    id: str
    title: str
    score: float
    category: str


class SearchRanker:
    """Ranks listings by relevance, diversity, and personalization.

    Uses a greedy submodular maximization approach:
    - Score = relevance * diversity_factor * personalization_factor
    - diversity_factor: 1.0 for first occurrence of a category, 0.7 for subsequent
    - personalization_factor: 1.3 if category matches user preference, else 1.0
    """

    def rank(
        self,
        query: str,
        listings: list[Listing],
        user_preferences: dict[str, Any] | None = None,
    ) -> list[RankedListing]:
        """Rank listings by computed score, deduplicated by id.

        Args:
            query: The search query string.
            listings: List of Listing objects to rank.
            user_preferences: Optional dict with user preference signals
                (e.g., {"category": "saas"}).

        Returns:
            List of RankedListing sorted by score descending, deduplicated by id.
        """
        if not listings:
            raise EmptyInputError("listings list cannot be empty")

        for listing in listings:
            if listing.relevance < 0 or listing.relevance > 1:
                raise InvalidRangeError(
                    f"listing '{listing.id}' has invalid relevance: {listing.relevance}"
                )

        preferred_category = None
        if user_preferences:
            preferred_category = user_preferences.get("category")

        # Track category occurrences for diversity penalty
        category_counts: dict[str, int] = {}
        scored: list[RankedListing] = []

        for listing in listings:
            # Diversity factor: 1.0 for first occurrence, 0.7 for subsequent
            cat = listing.category
            if cat in category_counts:
                diversity_factor = 0.7
            else:
                diversity_factor = 1.0
            category_counts[cat] = category_counts.get(cat, 0) + 1

            # Personalization factor: 1.3 if category matches preference
            if preferred_category and cat == preferred_category:
                personalization_factor = 1.3
            else:
                personalization_factor = 1.0

            score = listing.relevance * diversity_factor * personalization_factor

            scored.append(
                RankedListing(
                    id=listing.id,
                    title=listing.title,
                    score=score,
                    category=listing.category,
                )
            )

        # Deduplicate by id, keeping highest scoring
        best_by_id: dict[str, RankedListing] = {}
        for item in scored:
            if item.id not in best_by_id or item.score > best_by_id[item.id].score:
                best_by_id[item.id] = item

        # Sort by score descending
        results = sorted(best_by_id.values(), key=lambda r: r.score, reverse=True)

        return results
