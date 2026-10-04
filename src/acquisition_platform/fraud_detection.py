"""Fraud detection engine for acquisition platform.

Dense subgraph detection is NP-hard in general; this module uses practical
heuristics (weighted signal scoring and small-cycle detection) that run in
polynomial time and are suitable for real-time screening.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FraudSignal:
    """A single fraud-related signal extracted from a listing or account."""

    name: str
    value: float


@dataclass
class FraudScore:
    """Result of scoring a set of fraud signals."""

    score: float
    risk_level: str
    confidence: float
    explanations: list[str] = field(default_factory=list)


@dataclass
class GraphAnalysis(FraudScore):
    """Result of analyzing a relationship graph for fraud rings."""

    has_ring: bool = False
    risk_score: float = 0.0


class FraudDetector:
    """Detects fraudulent listings using signal scoring and graph analysis."""

    WEIGHTS: dict[str, float] = {
        "identity_verified": 0.3,
        "financial_consistency": 0.3,
        "traffic_authenticity": 0.2,
    }
    DEFAULT_WEIGHT: float = 0.1
    TOTAL_EXPECTED_SIGNALS: int = 3

    def score(self, signals: list[FraudSignal]) -> FraudScore:
        """Compute a fraud score from a list of signals.

        The score is a weighted average of signal values. Confidence reflects
        how many of the expected signals were provided.
        """
        if not signals:
            return FraudScore(
                score=0.0,
                risk_level="low",
                confidence=0.0,
                explanations=["No signals provided"],
            )

        total_weight = 0.0
        weighted_sum = 0.0
        explanations: list[str] = []

        for signal in signals:
            weight = self.WEIGHTS.get(signal.name, self.DEFAULT_WEIGHT)
            # Invert: high signal value = low fraud risk
            fraud_value = 1.0 - signal.value
            contribution = fraud_value * weight
            weighted_sum += contribution
            total_weight += weight
            explanations.append(
                f"{signal.name}: value={signal.value:.2f}, weight={weight:.1f}, "
                f"contribution={contribution:.3f}"
            )

        score = weighted_sum / total_weight if total_weight > 0 else 0.0
        score = max(0.0, min(1.0, score))

        missing = max(0, self.TOTAL_EXPECTED_SIGNALS - len(signals))
        confidence = 1.0 - (missing / self.TOTAL_EXPECTED_SIGNALS)

        if score < 0.3:
            risk_level = "low"
        elif score <= 0.7:
            risk_level = "medium"
        else:
            risk_level = "high"

        return FraudScore(
            score=score,
            risk_level=risk_level,
            confidence=confidence,
            explanations=explanations,
        )

    def analyze_graph(self, graph: dict[str, Any]) -> GraphAnalysis:
        """Analyze a relationship graph for fraud rings.

        Detects cycles of length 3-4 which indicate coordinated fraud rings.
        Returns a GraphAnalysis with has_ring and risk_score attributes.
        """
        nodes: list[str] = graph.get("nodes", [])
        edges: list[tuple[str, str]] = graph.get("edges", [])

        adjacency: dict[str, set[str]] = {node: set() for node in nodes}
        for src, dst in edges:
            if src in adjacency and dst in adjacency:
                adjacency[src].add(dst)
                adjacency[dst].add(src)

        has_ring = self._has_cycle_of_length_3_or_4(adjacency, nodes)

        if has_ring:
            risk_score = 0.8
            risk_level = "high"
            explanations = [
                f"Fraud ring detected: cycle of length 3-4 found among {len(nodes)} nodes"
            ]
        else:
            risk_score = 0.1
            risk_level = "low"
            explanations = [
                f"No fraud ring detected in graph with {len(nodes)} nodes"
            ]

        return GraphAnalysis(
            score=risk_score,
            risk_level=risk_level,
            confidence=1.0,
            explanations=explanations,
            has_ring=has_ring,
            risk_score=risk_score,
        )

    def _has_cycle_of_length_3_or_4(
        self, adjacency: dict[str, set[str]], nodes: list[str]
    ) -> bool:
        """Check if the graph contains a cycle of length 3 or 4."""
        node_set = set(nodes)

        # Check for triangles (3-cycles)
        for node in nodes:
            neighbors = adjacency[node]
            for n1 in neighbors:
                if n1 <= node:
                    continue
                for n2 in neighbors:
                    if n2 <= n1:
                        continue
                    if n2 in adjacency[n1]:
                        return True

        # Check for 4-cycles
        for node in nodes:
            neighbors = adjacency[node]
            for n1 in neighbors:
                if n1 <= node:
                    continue
                for n2 in adjacency[n1]:
                    if n2 == node or n2 <= node:
                        continue
                    for n3 in adjacency[n2]:
                        if n3 == n1 or n3 == node or n3 <= node:
                            continue
                        if node in adjacency[n3]:
                            return True

        return False
