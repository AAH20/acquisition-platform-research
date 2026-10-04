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


@dataclass
class Buyer:
    """Represents a buyer in the acquisition marketplace."""

    id: str
    budget: float
    preferences: dict


@dataclass
class Seller:
    """Represents a seller in the acquisition marketplace."""

    id: str
    asking_price: float
    attributes: dict


@dataclass
class Match:
    """Represents a matched buyer-seller pair with scoring metadata."""

    buyer_id: str
    seller_id: str
    score: float
    confidence: float


class BuyerSellerMatcher:
    """Greedy GAP solver for matching buyers to sellers.

    The matcher uses a greedy approximation to the Generalized Assignment Problem:
    it generates all feasible pairs, scores them, and assigns them in descending
    score order while respecting the one-to-one matching constraint.
    """

    def match(self, buyers: list[Buyer], sellers: list[Seller]) -> list[Match]:
        """Match buyers to sellers using greedy GAP approximation.

        Args:
            buyers: List of Buyer objects with budgets and preferences.
            sellers: List of Seller objects with asking prices and attributes.

        Returns:
            List of Match objects sorted by score descending. Each buyer and each
            seller appears in at most one match.
        """
        if not buyers or not sellers:
            return []

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

        Score = (1 - asking_price / budget) * category_match_bonus

        Since category mismatch results in no match, the category_match_bonus
        is always 1.0 for feasible pairs. The score is clamped to [0, 1].

        A higher score indicates a better match: the seller's asking price is
        a smaller fraction of the buyer's budget.
        """
        if buyer.budget <= 0:
            return 0.0
        price_ratio = seller.asking_price / buyer.budget
        category_bonus = 1.0  # Always 1.0 since mismatches are filtered out
        score = (1.0 - price_ratio) * category_bonus
        return max(0.0, min(1.0, score))

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
