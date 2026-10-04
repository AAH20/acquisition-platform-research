"""Tests for fraud detection module."""
import pytest
from acquisition_platform.fraud_detection import FraudDetector, FraudScore, FraudSignal


class TestFraudDetector:
    """TDD tests for the fraud detection engine."""

    def test_clean_listing_returns_low_risk(self):
        detector = FraudDetector()
        signals = [
            FraudSignal(name="identity_verified", value=1.0),
            FraudSignal(name="financial_consistency", value=0.95),
            FraudSignal(name="traffic_authenticity", value=0.90),
        ]
        score = detector.score(signals)
        assert score.risk_level == "low"
        assert score.score < 0.3

    def test_suspicious_listing_returns_high_risk(self):
        detector = FraudDetector()
        signals = [
            FraudSignal(name="identity_verified", value=0.2),
            FraudSignal(name="financial_consistency", value=0.15),
            FraudSignal(name="traffic_authenticity", value=0.10),
        ]
        score = detector.score(signals)
        assert score.risk_level == "high"
        assert score.score > 0.7

    def test_medium_risk_for_mixed_signals(self):
        detector = FraudDetector()
        signals = [
            FraudSignal(name="identity_verified", value=0.8),
            FraudSignal(name="financial_consistency", value=0.4),
            FraudSignal(name="traffic_authenticity", value=0.6),
        ]
        score = detector.score(signals)
        assert score.risk_level == "medium"

    def test_fraud_score_has_explanation(self):
        detector = FraudDetector()
        signals = [
            FraudSignal(name="identity_verified", value=0.2),
            FraudSignal(name="financial_consistency", value=0.15),
        ]
        score = detector.score(signals)
        assert len(score.explanations) > 0

    def test_missing_signals_increases_risk(self):
        detector = FraudDetector()
        signals = [FraudSignal(name="identity_verified", value=0.9)]
        score = detector.score(signals)
        # Missing signals should increase uncertainty
        assert score.confidence < 0.8

    def test_graph_analysis_detects_ring_fraud(self):
        detector = FraudDetector()
        # Simulate a ring of connected fraudulent accounts
        graph = {
            "nodes": ["a", "b", "c", "d"],
            "edges": [("a", "b"), ("b", "c"), ("c", "d"), ("d", "a")],
        }
        result = detector.analyze_graph(graph)
        assert result.has_ring
        assert result.risk_score > 0.5

    def test_real_time_scoring_under_500ms(self):
        import time
        detector = FraudDetector()
        signals = [FraudSignal(name=f"signal_{i}", value=0.5) for i in range(10)]
        start = time.time()
        detector.score(signals)
        elapsed = (time.time() - start) * 1000
        assert elapsed < 500
