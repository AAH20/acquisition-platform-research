"""Buyer-Seller matching engine using a greedy approximation to the GAP (Generalized Assignment Problem).

The Generalized Assignment Problem (GAP) is an NP-hard combinatorial optimization
problem where the goal is to assign a set of tasks (sellers) to a set of agents
(buyers) such that each task is assigned to at most one agent, each agent has a
capacity constraint (budget), and the total profit is maximized.

This module implements a greedy approximation:
1. Generate all feasible (buyer, seller) pairs where the buyer can afford the
   seller and their categories match.
2. Score each pair using a price-ratio formula with a category bonus.
3. Sort pairs by score descending.
4. Greedily assign pairs, ensuring each buyer and each seller is matched at most
   once.

This runs in O(n*m*log(n*m)) time where n = number of buyers, m = number of
sellers, which is efficient for the typical scale of acquisition matching.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from acquisition_platform.exceptions import EmptyInputError, InvalidRangeError, ValidationError
from acquisition_platform.serialization import SerializableMixin


@dataclass
class Buyer(SerializableMixin):
    """Represents a buyer in the acquisition marketplace."""

    id: str
    budget: float
    preferences: dict[str, Any]


@dataclass
class Seller(SerializableMixin):
    """Represents a seller in the acquisition marketplace."""

    id: str
    asking_price: float
    attributes: dict[str, Any]


@dataclass
class Match(SerializableMixin):
    """Represents a matched buyer-seller pair with scoring metadata."""

    buyer_id: str
    seller_id: str
    score: float
    confidence: float


@dataclass(frozen=True)
class MatchingPolicy:
    """Parameterised scoring policy for buyer-seller matching.

    The score blends three interpretable signals:

    - ``gap``: ``1 - asking_price / budget`` — cheaper deals score higher.
    - ``midpoint``: ``1 - |asking_price - budget/2| / budget`` — deals priced
      near half the buyer's budget score higher (a "fair value" signal).
    - ``size``: ``min(1, asking_price / budget)`` — larger deals score higher.

    The defaults (``gap_weight=1``, everything else zero) reproduce the legacy
    scoring function exactly, so existing behaviour is preserved. Evolution can
    then search the weight space to recover a better policy.

    Args:
        gap_weight: Weight of the budget-gap signal.
        midpoint_weight: Weight of the fair-value signal.
        size_weight: Weight of the deal-size signal.
        bias: Constant added before scaling.
        scale: Multiplier applied to the blended signal; must be positive.
    """

    gap_weight: float = 1.0
    midpoint_weight: float = 0.0
    size_weight: float = 0.0
    bias: float = 0.0
    scale: float = 1.0

    def __post_init__(self) -> None:
        if self.scale <= 0.0:
            raise InvalidRangeError(f"scale must be positive, got {self.scale}")
        if self.gap_weight < 0 or self.midpoint_weight < 0 or self.size_weight < 0:
            raise InvalidRangeError("policy weights must be non-negative")
        if self.gap_weight == 0 and self.midpoint_weight == 0 and self.size_weight == 0:
            raise ValidationError("at least one policy weight must be positive")

    def score(self, buyer: Buyer, seller: Seller) -> float:
        """Score a feasible pair.

        Args:
            buyer: The buyer side of the pair.
            seller: The seller side of the pair.

        Returns:
            Score clamped to [0, 1]; 0.0 for a non-positive budget.
        """
        if buyer.budget <= 0:
            return 0.0
        price_ratio = seller.asking_price / buyer.budget
        gap = 1.0 - price_ratio
        midpoint = 1.0 - abs(seller.asking_price - buyer.budget / 2.0) / buyer.budget
        size = min(1.0, price_ratio)
        blended = (
            self.gap_weight * gap
            + self.midpoint_weight * midpoint
            + self.size_weight * size
            + self.bias
        )
        return max(0.0, min(1.0, self.scale * blended))

    def to_params(self) -> dict[str, float]:
        """Return the policy as a flat parameter dictionary."""
        return {
            "gap_weight": self.gap_weight,
            "midpoint_weight": self.midpoint_weight,
            "size_weight": self.size_weight,
            "bias": self.bias,
            "scale": self.scale,
        }

    @classmethod
    def from_params(cls, params: dict[str, float]) -> "MatchingPolicy":
        """Build a policy from a flat parameter dictionary."""
        return cls(
            gap_weight=params.get("gap_weight", 1.0),
            midpoint_weight=params.get("midpoint_weight", 0.0),
            size_weight=params.get("size_weight", 0.0),
            bias=params.get("bias", 0.0),
            scale=params.get("scale", 1.0),
        )


class BuyerSellerMatcher:
    """Greedy GAP solver for matching buyers to sellers.

    The matcher uses a greedy approximation to the Generalized Assignment Problem:
    it generates all feasible pairs, scores them, and assigns them in descending
    score order while respecting the one-to-one matching constraint.
    """

    def __init__(self, policy: MatchingPolicy | None = None) -> None:
        """Initialise the matcher.

        Args:
            policy: Optional scoring policy. Defaults to the legacy policy,
                which scores purely on the budget gap.
        """
        self.policy = policy or MatchingPolicy()

    def match(self, buyers: list[Buyer], sellers: list[Seller]) -> list[Match]:
        """Match buyers to sellers using greedy GAP approximation.

        Args:
            buyers: List of Buyer objects with budgets and preferences.
            sellers: List of Seller objects with asking prices and attributes.

        Returns:
            List of Match objects sorted by score descending. Each buyer and each
            seller appears in at most one match.
        """
        if not buyers:
            raise EmptyInputError("buyers list cannot be empty")
        if not sellers:
            raise EmptyInputError("sellers list cannot be empty")

        for buyer in buyers:
            if buyer.budget <= 0:
                raise ValidationError(
                    f"buyer '{buyer.id}' has invalid budget: {buyer.budget}"
                )
        for seller in sellers:
            if seller.asking_price <= 0:
                raise ValidationError(
                    f"seller '{seller.id}' has invalid asking_price: {seller.asking_price}"
                )

        # Generate all feasible pairs with scores
        candidates: list[tuple[float, float, Buyer, Seller]] = []
        for buyer in buyers:
            for seller in sellers:
                if not self._is_feasible(buyer, seller):
                    continue
                score = self._compute_score(buyer, seller)
                confidence = self._compute_confidence(buyer, seller, score)
                candidates.append((score, confidence, buyer, seller))

        # Sort by score descending (greedy: best matches first)
        candidates.sort(key=lambda x: x[0], reverse=True)

        # Greedy assignment: each buyer and seller matched at most once
        matched_buyers: set[str] = set()
        matched_sellers: set[str] = set()
        matches: list[Match] = []

        for score, confidence, buyer, seller in candidates:
            if buyer.id in matched_buyers or seller.id in matched_sellers:
                continue
            matches.append(
                Match(
                    buyer_id=buyer.id,
                    seller_id=seller.id,
                    score=score,
                    confidence=confidence,
                )
            )
            matched_buyers.add(buyer.id)
            matched_sellers.add(seller.id)

        return matches

    def match_batch(
        self, buyers: list[Buyer], sellers: list[Seller], chunk_size: int = 100
    ) -> list[Match]:
        """Match buyers to sellers in batches (chunks).

        Splits both buyer and seller lists into chunks and runs the matching
        algorithm on each chunk pair. This reduces peak memory usage for
        large datasets at the cost of missing cross-chunk matches.

        Args:
            buyers: List of Buyer objects.
            sellers: List of Seller objects.
            chunk_size: Number of items per chunk.

        Returns:
            Combined list of Match objects from all chunk pairs.

        Raises:
            EmptyInputError: If buyers or sellers is empty.
            ValidationError: If chunk_size is not positive.
        """
        if not buyers:
            raise EmptyInputError("buyers list cannot be empty")
        if not sellers:
            raise EmptyInputError("sellers list cannot be empty")
        if chunk_size <= 0:
            raise ValidationError(f"chunk_size must be positive, got {chunk_size}")

        all_matches: list[Match] = []
        for i in range(0, len(buyers), chunk_size):
            buyer_chunk = buyers[i : i + chunk_size]
            for j in range(0, len(sellers), chunk_size):
                seller_chunk = sellers[j : j + chunk_size]
                matches = self.match(buyer_chunk, seller_chunk)
                all_matches.extend(matches)
        return all_matches

    def export_matches(self, matches: list[Match], path: str) -> None:
        """Export matches to a JSON file."""
        from acquisition_platform.data_io import export_to_json
        data = [
            {"buyer_id": m.buyer_id, "seller_id": m.seller_id, "score": m.score, "confidence": m.confidence}
            for m in matches
        ]
        export_to_json(data, path)

    def import_buyers_sellers(self, path: str) -> tuple[list[Buyer], list[Seller]]:
        """Import buyers and sellers from a JSON file."""
        from acquisition_platform.data_io import import_from_json
        data = import_from_json(path)
        buyers = [Buyer(id=b["id"], budget=b["budget"], preferences=b.get("preferences", {})) for b in data.get("buyers", [])]
        sellers = [Seller(id=s["id"], asking_price=s["asking_price"], attributes=s.get("attributes", {})) for s in data.get("sellers", [])]
        return buyers, sellers

    def _is_feasible(self, buyer: Buyer, seller: Seller) -> bool:
        """Check if a buyer-seller pair is feasible.

        A pair is feasible if:
        1. The buyer's budget is >= the seller's asking price.
        2. The buyer's preferred category matches the seller's category.
        """
        if buyer.budget < seller.asking_price:
            return False
        buyer_category = buyer.preferences.get("category")
        seller_category = seller.attributes.get("category")
        if buyer_category != seller_category:
            return False
        return True

    def _compute_score(self, buyer: Buyer, seller: Seller) -> float:
        """Compute the match score for a feasible pair.

        Delegates to :class:`MatchingPolicy`. The default policy scores
        ``1 - asking_price / budget`` clamped to [0, 1], preserving the
        historical behaviour of this matcher.

        Args:
            buyer: The buyer side of the pair.
            seller: The seller side of the pair.

        Returns:
            Match score in [0, 1].
        """
        return self.policy.score(buyer, seller)

    def _compute_confidence(self, buyer: Buyer, seller: Seller, score: float) -> float:
        """Compute the confidence score for a match.

        Confidence = score * (1 - abs(asking_price - budget/2) / budget)

        Confidence is highest when the asking price is close to half the buyer's
        budget, indicating a "fair" price from the buyer's perspective. The
        confidence is clamped to [0, 1].
        """
        if buyer.budget <= 0:
            return 0.0
        half_budget = buyer.budget / 2.0
        price_deviation = abs(seller.asking_price - half_budget) / buyer.budget
        confidence = score * (1.0 - price_deviation)
        return max(0.0, min(1.0, confidence))
