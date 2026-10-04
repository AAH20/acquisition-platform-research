"""Hybrid recommendation engine combining collaborative and content-based filtering.

This module implements a recommendation engine that blends:
- Collaborative filtering: users with similar preferences influence recommendations
- Content-based filtering: items with similar attributes to user preferences are boosted
- Diversity: recommendations span multiple categories to avoid filter bubbles
"""

from __future__ import annotations

from dataclasses import dataclass, field

from acquisition_platform.serialization import SerializableMixin
from acquisition_platform.caching import cached

from acquisition_platform.observability import get_logger, log_execution_time, log_module_call

logger = get_logger(__name__)


@dataclass
class UserProfile(SerializableMixin):
    """A user with preferences and interaction history.

    Attributes:
        user_id: Unique identifier for the user.
        preferences: Dict of preference key-value pairs (e.g., {"topic": "ml"}).
        history: List of item IDs the user has interacted with.
    """

    user_id: str
    preferences: dict[str, str] = field(default_factory=dict)
    history: list[str] = field(default_factory=list)


@dataclass
class ItemProfile(SerializableMixin):
    """An item with attributes and category metadata.

    Attributes:
        item_id: Unique identifier for the item.
        attributes: Dict of attribute key-value pairs (e.g., {"topic": "ml", "difficulty": "advanced"}).
        category: Category label for the item (e.g., "saas", "ecommerce").
    """

    item_id: str
    attributes: dict[str, str] = field(default_factory=dict)
    category: str = ""


@dataclass
class Recommendation(SerializableMixin):
    """A single recommendation with score and explanation.

    Attributes:
        item_id: The recommended item's ID.
        score: Relevance score in [0.0, 1.0].
        reason: Human-readable explanation for the recommendation.
    """

    item_id: str
    score: float
    reason: str


@dataclass
class RecommendationResult(SerializableMixin):
    """The result of a recommendation query.

    Attributes:
        recommendations: List of Recommendation objects, sorted by score descending.
        diversity_score: Measure of category diversity in [0.0, 1.0].
        coverage: Fraction of catalog categories represented in recommendations.
    """

    recommendations: list[Recommendation]
    diversity_score: float
    coverage: float


class RecommendationEngine:
    """Hybrid recommendation engine.

    Combines collaborative filtering (user-user similarity) with content-based
    filtering (item attribute matching) to produce personalized, diverse recommendations.
    """

    def __init__(self) -> None:
        self._users: dict[str, UserProfile] = {}
        self._items: dict[str, ItemProfile] = {}

    @log_execution_time(logger)
    def add_user_profile(self, user: UserProfile) -> None:
        """Register a user profile for collaborative filtering lookups."""
        self._users[user.user_id] = user

    @log_execution_time(logger)
    def add_item_profile(self, item: ItemProfile) -> None:
        """Register an item profile for content-based lookups."""
        self._items[item.item_id] = item

    @log_execution_time(logger)
    def get_similar_users(self, user_id: str) -> list[str]:
        """Find users with similar preferences using cosine similarity on preference vectors.

        Args:
            user_id: The target user's ID.

        Returns:
            List of user IDs sorted by similarity descending, excluding the target user.
        """
        target = self._users.get(user_id)
        if target is None:
            return []

        target_prefs = target.preferences
        if not target_prefs:
            return []

        similarities: list[tuple[str, float]] = []
        for uid, user in self._users.items():
            if uid == user_id:
                continue
            sim = self._preference_similarity(target_prefs, user.preferences)
            if sim > 0:
                similarities.append((uid, sim))

        similarities.sort(key=lambda x: x[1], reverse=True)
        return [uid for uid, _ in similarities]

    @log_execution_time(logger)
    def get_similar_items(self, item_id: str) -> list[str]:
        """Find items with similar attributes using Jaccard similarity.

        Args:
            item_id: The target item's ID.

        Returns:
            List of item IDs sorted by similarity descending, excluding the target item.
        """
        target = self._items.get(item_id)
        if target is None:
            return []

        target_attrs = target.attributes
        if not target_attrs:
            return []

        similarities: list[tuple[str, float]] = []
        for iid, item in self._items.items():
            if iid == item_id:
                continue
            sim = self._attribute_similarity(target_attrs, item.attributes)
            if sim > 0:
                similarities.append((iid, sim))

        similarities.sort(key=lambda x: x[1], reverse=True)
        return [iid for iid, _ in similarities]

    @log_execution_time(logger)
    def recommend(
        self,
        user: UserProfile,
        items: list[ItemProfile],
        k: int = 10,
    ) -> RecommendationResult:
        """Generate hybrid recommendations for a user.

        Scores each candidate item using a weighted combination of:
        - Content-based score: attribute match with user preferences
        - Collaborative score: preference overlap with similar users
        - Diversity bonus: penalty for over-represented categories

        Args:
            user: The target user profile.
            items: Candidate items to recommend from.
            k: Maximum number of recommendations to return.

        Returns:
            RecommendationResult with ranked recommendations and diversity metrics.
        """
        if not items or k <= 0:
            return RecommendationResult(
                recommendations=[],
                diversity_score=0.0,
                coverage=0.0,
            )

        # Ensure user and items are registered
        self.add_user_profile(user)
        for item in items:
            self.add_item_profile(item)

        # Get similar users for CF signal
        similar_user_ids = self.get_similar_users(user.user_id)
        similar_users = [self._users[uid] for uid in similar_user_ids if uid in self._users]

        # Score all candidates
        history_set = set(user.history)
        scored: list[tuple[ItemProfile, float, str]] = []

        for item in items:
            if item.item_id in history_set:
                continue

            content_score = self._content_score(user, item)
            cf_score = self._collaborative_score(similar_users, item)
            # Small baseline ensures every candidate has a positive score
            hybrid_score = 0.05 + 0.55 * content_score + 0.40 * cf_score

            reason = self._build_reason(content_score, cf_score, user, item)
            scored.append((item, hybrid_score, reason))

        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)

        # Apply diversity: greedy selection penalizing over-represented categories
        selected = self._diverse_select(scored, k)

        # Build recommendations
        recommendations = [
            Recommendation(item_id=item.item_id, score=round(score, 4), reason=reason)
            for item, score, reason in selected
        ]

        # Compute diversity metrics
        diversity_score = self._compute_diversity(recommendations, items)
        coverage = self._compute_coverage(recommendations, items)

        return RecommendationResult(
            recommendations=recommendations,
            diversity_score=round(diversity_score, 4),
            coverage=round(coverage, 4),
        )

    @cached(ttl=300.0, max_size=1024)
    def _preference_similarity(
        self, prefs_a: dict[str, str], prefs_b: dict[str, str]
    ) -> float:
        """Compute similarity between two preference dicts.

        Uses a weighted overlap: exact key-value matches count fully,
        shared keys with different values count partially.
        """
        if not prefs_a or not prefs_b:
            return 0.0

        all_keys = set(prefs_a.keys()) | set(prefs_b.keys())
        if not all_keys:
            return 0.0

        exact_matches = sum(
            1 for key in all_keys
            if key in prefs_a and key in prefs_b and prefs_a[key] == prefs_b[key]
        )
        shared_keys = len(set(prefs_a.keys()) & set(prefs_b.keys()))
        partial = shared_keys - exact_matches

        return (exact_matches + 0.3 * partial) / len(all_keys)

    @cached(ttl=300.0, max_size=1024)
    def _attribute_similarity(
        self, attrs_a: dict[str, str], attrs_b: dict[str, str]
    ) -> float:
        """Compute Jaccard similarity between two attribute dicts."""
        if not attrs_a or not attrs_b:
            return 0.0

        keys_a = set(attrs_a.keys())
        keys_b = set(attrs_b.keys())
        intersection = keys_a & keys_b
        union = keys_a | keys_b

        if not union:
            return 0.0

        # Jaccard on keys, weighted by value matches
        matching = sum(1 for k in intersection if attrs_a[k] == attrs_b[k])
        return matching / len(union)

    def _content_score(self, user: UserProfile, item: ItemProfile) -> float:
        """Score based on how well item attributes match user preferences."""
        if not user.preferences or not item.attributes:
            return 0.0

        matches = sum(
            1 for key, value in user.preferences.items()
            if item.attributes.get(key) == value
        )
        return matches / len(user.preferences)

    def _collaborative_score(
        self, similar_users: list[UserProfile], item: ItemProfile
    ) -> float:
        """Score based on similar users' history overlap with this item."""
        if not similar_users:
            return 0.0

        # Check if similar users have interacted with this item
        total = 0.0
        for sim_user in similar_users:
            if item.item_id in sim_user.history:
                total += 1.0
            # Also check attribute overlap with similar user preferences
            attr_overlap = self._attribute_similarity(sim_user.preferences, item.attributes)
            total += attr_overlap * 0.5

        return min(total / len(similar_users), 1.0)

    def _build_reason(
        self, content_score: float, cf_score: float, user: UserProfile, item: ItemProfile
    ) -> str:
        """Build a human-readable reason for the recommendation."""
        if content_score > 0 and cf_score > 0:
            return f"Matches your preferences and popular with similar users"
        elif content_score > 0:
            matching = [
                f"{k}={v}" for k, v in user.preferences.items()
                if item.attributes.get(k) == v
            ]
            return f"Matches your preferences: {', '.join(matching)}"
        elif cf_score > 0:
            return f"Popular with users similar to you"
        else:
            return f"Recommended for discovery in {item.category}"

    def _diverse_select(
        self,
        scored: list[tuple[ItemProfile, float, str]],
        k: int,
    ) -> list[tuple[ItemProfile, float, str]]:
        """Greedy selection that penalizes over-represented categories."""
        if not scored:
            return []

        selected: list[tuple[ItemProfile, float, str]] = []
        category_counts: dict[str, int] = {}
        remaining = list(scored)

        while len(selected) < k and remaining:
            best_idx = 0
            best_adjusted = -1.0

            for idx, (item, score, reason) in enumerate(remaining):
                cat = item.category
                penalty = 0.15 * category_counts.get(cat, 0)
                adjusted = score - penalty
                if adjusted > best_adjusted:
                    best_adjusted = adjusted
                    best_idx = idx

            chosen = remaining.pop(best_idx)
            selected.append(chosen)
            category_counts[chosen[0].category] = category_counts.get(chosen[0].category, 0) + 1

        return selected

    def _compute_diversity(
        self, recommendations: list[Recommendation], all_items: list[ItemProfile]
    ) -> float:
        """Compute diversity as the fraction of distinct categories in recommendations."""
        if not recommendations:
            return 0.0

        item_map = {item.item_id: item for item in all_items}
        categories = set()
        for rec in recommendations:
            item = item_map.get(rec.item_id)
            if item:
                categories.add(item.category)

        all_categories = {item.category for item in all_items}
        if not all_categories:
            return 0.0

        return len(categories) / len(all_categories)

    def _compute_coverage(
        self, recommendations: list[Recommendation], all_items: list[ItemProfile]
    ) -> float:
        """Compute coverage as fraction of catalog categories represented."""
        if not all_items:
            return 0.0

        all_categories = {item.category for item in all_items}
        item_map = {item.item_id: item for item in all_items}
        covered = set()
        for rec in recommendations:
            item = item_map.get(rec.item_id)
            if item:
                covered.add(item.category)

        return len(covered) / len(all_categories) if all_categories else 0.0
