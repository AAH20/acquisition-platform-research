"""Tests for post-merger integration module."""
import pytest

from acquisition_platform.post_merger import (
    IntegrationMetric,
    IntegrationPlan,
    PostMergerIntegrator,
    Synergy,
)


class TestPostMergerIntegrator:
    """TDD tests for the post-merger integration module."""

    def test_integration_score(self):
        """Integration health should be scored as a weighted average."""
        integrator = PostMergerIntegrator()
        metrics = [
            IntegrationMetric(name="culture", score=80.0, weight=0.4, category="culture"),
            IntegrationMetric(name="systems", score=60.0, weight=0.6, category="systems"),
        ]
        score = integrator.overall_score(metrics)
        expected = 80.0 * 0.4 + 60.0 * 0.6
        assert score == pytest.approx(expected)
        assert 0.0 <= score <= 100.0

    def test_culture_gap(self):
        """Culture gap should be assessed between acquirer and target."""
        integrator = PostMergerIntegrator()
        gap = integrator.culture_gap("hierarchical", "flat")
        assert gap > 0.0
        # Identical cultures should have zero gap
        assert integrator.culture_gap("flat", "flat") == 0.0
        # Gap should be symmetric
        assert integrator.culture_gap("hierarchical", "flat") == pytest.approx(
            integrator.culture_gap("flat", "hierarchical")
        )

    def test_synergy_tracking(self):
        """Synergies should be tracked with target, actual, and status."""
        integrator = PostMergerIntegrator()
        synergy = integrator.track_synergy("cost_synergy", target=10.0, actual=8.0)
        assert isinstance(synergy, Synergy)
        assert synergy.name == "cost_synergy"
        assert synergy.target == 10.0
        assert synergy.actual == 8.0
        assert synergy.status in {"on_track", "at_risk", "missed"}
        # Fully achieved synergy
        full = integrator.track_synergy("revenue_synergy", target=5.0, actual=5.0)
        assert full.status == "on_track"
        # Missed synergy
        missed = integrator.track_synergy("strategic", target=10.0, actual=2.0)
        assert missed.status == "missed"

    def test_integration_risk(self):
        """Integration risk should be identified from the score."""
        integrator = PostMergerIntegrator()
        assert integrator.risk_level(90.0) == "low"
        assert integrator.risk_level(70.0) == "medium"
        assert integrator.risk_level(40.0) == "high"
        assert integrator.risk_level(10.0) == "critical"

    def test_empty_integration(self):
        """Empty integration should return defaults."""
        integrator = PostMergerIntegrator()
        assert integrator.overall_score([]) == 0.0
        assert integrator.generate_timeline([]) == 0
        plan = integrator.generate_report([], [])
        assert isinstance(plan, IntegrationPlan)
        assert plan.metrics == []
        assert plan.synergies == []
        assert plan.overall_score == 0.0
        assert plan.timeline_months == 0

    def test_cross_border_integration(self):
        """Cross-border deals should surface regulatory and cultural challenges."""
        integrator = PostMergerIntegrator()
        challenges = integrator.cross_border_challenges(["US", "DE", "JP"])
        assert isinstance(challenges, list)
        assert len(challenges) > 0
        # More countries should mean at least as many challenges
        fewer = integrator.cross_border_challenges(["US"])
        assert len(challenges) >= len(fewer)
        # Empty input yields no challenges
        assert integrator.cross_border_challenges([]) == []

    def test_talent_retention(self):
        """Retention rate should be tracked as retained / acquired."""
        integrator = PostMergerIntegrator()
        rate = integrator.talent_retention_rate(acquired=100, retained=85)
        assert rate == pytest.approx(0.85)
        # Full retention
        assert integrator.talent_retention_rate(acquired=50, retained=50) == 1.0
        # Zero retention
        assert integrator.talent_retention_rate(acquired=50, retained=0) == 0.0

    def test_systems_integration(self):
        """Systems integration should be scored from system readiness."""
        integrator = PostMergerIntegrator()
        systems = [
            {"name": "erp", "ready": True},
            {"name": "crm", "ready": True},
            {"name": "hr", "ready": False},
        ]
        score = integrator.systems_integration_score(systems)
        assert 0.0 <= score <= 100.0
        # All ready should score 100
        all_ready = [{"name": "erp", "ready": True}, {"name": "crm", "ready": True}]
        assert integrator.systems_integration_score(all_ready) == 100.0
        # None ready should score 0
        none_ready = [{"name": "erp", "ready": False}]
        assert integrator.systems_integration_score(none_ready) == 0.0

    def test_integration_timeline(self):
        """Timeline should be generated in months based on metric count and scores."""
        integrator = PostMergerIntegrator()
        metrics = [
            IntegrationMetric(name="culture", score=50.0, weight=0.5, category="culture"),
            IntegrationMetric(name="systems", score=50.0, weight=0.5, category="systems"),
        ]
        timeline = integrator.generate_timeline(metrics)
        assert isinstance(timeline, int)
        assert timeline > 0
        # Lower scores (harder integration) should mean longer timeline
        good_metrics = [
            IntegrationMetric(name="culture", score=95.0, weight=0.5, category="culture"),
            IntegrationMetric(name="systems", score=95.0, weight=0.5, category="systems"),
        ]
        assert integrator.generate_timeline(good_metrics) < timeline

    def test_integration_report(self):
        """A full integration report should be generated as an IntegrationPlan."""
        integrator = PostMergerIntegrator()
        metrics = [
            IntegrationMetric(name="culture", score=80.0, weight=0.4, category="culture"),
            IntegrationMetric(name="systems", score=70.0, weight=0.6, category="systems"),
        ]
        synergies = [
            integrator.track_synergy("cost_synergy", target=10.0, actual=9.0),
            integrator.track_synergy("revenue_synergy", target=5.0, actual=3.0),
        ]
        plan = integrator.generate_report(metrics, synergies)
        assert isinstance(plan, IntegrationPlan)
        assert plan.metrics == metrics
        assert plan.synergies == synergies
        assert plan.overall_score == pytest.approx(integrator.overall_score(metrics))
        assert plan.risk_level == integrator.risk_level(plan.overall_score)
        assert plan.timeline_months == integrator.generate_timeline(metrics)

    def test_add_metric(self):
        """add_metric should create and return an IntegrationMetric."""
        integrator = PostMergerIntegrator()
        metric = integrator.add_metric("culture", score=75.0, weight=0.3, category="culture")
        assert isinstance(metric, IntegrationMetric)
        assert metric.name == "culture"
        assert metric.score == 75.0
        assert metric.weight == 0.3
        assert metric.category == "culture"
