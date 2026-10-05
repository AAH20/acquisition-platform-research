"""Tests for due diligence scheduling module."""
import pytest
from acquisition_platform.due_diligence import (
    DueDiligenceTask,
    Reviewer,
    DueDiligenceSchedule,
    DueDiligenceScheduler,
    DDFactor,
    DDResult,
    DueDiligenceAnalyzer,
)


class TestDueDiligenceScheduler:
    """TDD tests for the due diligence scheduler."""

    def test_basic_schedule(self):
        """Tasks with durations and reviewers produce a valid schedule."""
        scheduler = DueDiligenceScheduler()
        tasks = [
            DueDiligenceTask(id="t1", name="Financial Review", duration=4.0, expertise="finance", dependencies=[]),
            DueDiligenceTask(id="t2", name="Legal Review", duration=3.0, expertise="legal", dependencies=[]),
        ]
        reviewers = [
            Reviewer(id="r1", name="Alice", expertise=["finance"], availability=8.0),
            Reviewer(id="r2", name="Bob", expertise=["legal"], availability=8.0),
        ]
        schedule = scheduler.schedule(tasks, reviewers)
        assert len(schedule.assignments) == 2
        assert schedule.makespan > 0
        assert len(schedule.reviewer_utilization) == 2

    def test_precedence_constraints(self):
        """Task B depends on task A — B must start after A finishes."""
        scheduler = DueDiligenceScheduler()
        tasks = [
            DueDiligenceTask(id="A", name="Audit", duration=3.0, expertise="finance", dependencies=[]),
            DueDiligenceTask(id="B", name="Report", duration=2.0, expertise="finance", dependencies=["A"]),
        ]
        reviewers = [
            Reviewer(id="r1", name="Alice", expertise=["finance"], availability=8.0),
        ]
        schedule = scheduler.schedule(tasks, reviewers)
        # Find assignments for A and B
        a_assign = next(a for a in schedule.assignments if a["task_id"] == "A")
        b_assign = next(a for a in schedule.assignments if a["task_id"] == "B")
        assert b_assign["start_time"] >= a_assign["start_time"] + a_assign["duration"]

    def test_multiple_reviewers(self):
        """Tasks assigned to different reviewers."""
        scheduler = DueDiligenceScheduler()
        tasks = [
            DueDiligenceTask(id="t1", name="Task1", duration=2.0, expertise="finance", dependencies=[]),
            DueDiligenceTask(id="t2", name="Task2", duration=2.0, expertise="legal", dependencies=[]),
        ]
        reviewers = [
            Reviewer(id="r1", name="Alice", expertise=["finance"], availability=8.0),
            Reviewer(id="r2", name="Bob", expertise=["legal"], availability=8.0),
        ]
        schedule = scheduler.schedule(tasks, reviewers)
        t1_assign = next(a for a in schedule.assignments if a["task_id"] == "t1")
        t2_assign = next(a for a in schedule.assignments if a["task_id"] == "t2")
        assert t1_assign["reviewer_id"] == "r1"
        assert t2_assign["reviewer_id"] == "r2"

    def test_makespan_calculation(self):
        """Total time (makespan) is correct for sequential tasks."""
        scheduler = DueDiligenceScheduler()
        tasks = [
            DueDiligenceTask(id="t1", name="Task1", duration=3.0, expertise="finance", dependencies=[]),
            DueDiligenceTask(id="t2", name="Task2", duration=4.0, expertise="finance", dependencies=["t1"]),
        ]
        reviewers = [
            Reviewer(id="r1", name="Alice", expertise=["finance"], availability=8.0),
        ]
        schedule = scheduler.schedule(tasks, reviewers)
        assert schedule.makespan == 7.0

    def test_empty_tasks(self):
        """No tasks returns empty schedule."""
        scheduler = DueDiligenceScheduler()
        reviewers = [
            Reviewer(id="r1", name="Alice", expertise=["finance"], availability=8.0),
        ]
        schedule = scheduler.schedule([], reviewers)
        assert schedule.assignments == []
        assert schedule.makespan == 0.0
        assert schedule.reviewer_utilization == {}

    def test_single_task(self):
        """One task assigned to one reviewer."""
        scheduler = DueDiligenceScheduler()
        tasks = [
            DueDiligenceTask(id="t1", name="Solo Task", duration=5.0, expertise="finance", dependencies=[]),
        ]
        reviewers = [
            Reviewer(id="r1", name="Alice", expertise=["finance"], availability=8.0),
        ]
        schedule = scheduler.schedule(tasks, reviewers)
        assert len(schedule.assignments) == 1
        assert schedule.assignments[0]["task_id"] == "t1"
        assert schedule.assignments[0]["reviewer_id"] == "r1"
        assert schedule.makespan == 5.0

    def test_unavailable_reviewer(self):
        """Reviewer not available — task cannot be scheduled."""
        scheduler = DueDiligenceScheduler()
        tasks = [
            DueDiligenceTask(id="t1", name="Big Task", duration=10.0, expertise="finance", dependencies=[]),
        ]
        reviewers = [
            Reviewer(id="r1", name="Alice", expertise=["finance"], availability=5.0),
        ]
        with pytest.raises(Exception):
            scheduler.schedule(tasks, reviewers)

    def test_reschedule(self):
        """Adding a task reschedules and updates the schedule."""
        scheduler = DueDiligenceScheduler()
        tasks = [
            DueDiligenceTask(id="t1", name="Task1", duration=3.0, expertise="finance", dependencies=[]),
        ]
        reviewers = [
            Reviewer(id="r1", name="Alice", expertise=["finance"], availability=8.0),
        ]
        schedule1 = scheduler.schedule(tasks, reviewers)
        assert len(schedule1.assignments) == 1

        new_task = DueDiligenceTask(id="t2", name="Task2", duration=2.0, expertise="finance", dependencies=[])
        scheduler.add_task(new_task)
        schedule2 = scheduler.reschedule()
        assert len(schedule2.assignments) == 2
        assert schedule2.makespan >= schedule1.makespan

    def test_parallel_tasks(self):
        """Independent tasks run in parallel with different reviewers."""
        scheduler = DueDiligenceScheduler()
        tasks = [
            DueDiligenceTask(id="t1", name="Task1", duration=4.0, expertise="finance", dependencies=[]),
            DueDiligenceTask(id="t2", name="Task2", duration=4.0, expertise="legal", dependencies=[]),
        ]
        reviewers = [
            Reviewer(id="r1", name="Alice", expertise=["finance"], availability=8.0),
            Reviewer(id="r2", name="Bob", expertise=["legal"], availability=8.0),
        ]
        schedule = scheduler.schedule(tasks, reviewers)
        # Both start at 0 — they run in parallel
        t1_assign = next(a for a in schedule.assignments if a["task_id"] == "t1")
        t2_assign = next(a for a in schedule.assignments if a["task_id"] == "t2")
        assert t1_assign["start_time"] == 0.0
        assert t2_assign["start_time"] == 0.0
        assert schedule.makespan == 4.0

    def test_expertise_matching(self):
        """Task requires specific expertise — only matching reviewer gets it."""
        scheduler = DueDiligenceScheduler()
        tasks = [
            DueDiligenceTask(id="t1", name="Tax Review", duration=3.0, expertise="tax", dependencies=[]),
        ]
        reviewers = [
            Reviewer(id="r1", name="Alice", expertise=["finance"], availability=8.0),
            Reviewer(id="r2", name="Bob", expertise=["tax"], availability=8.0),
        ]
        schedule = scheduler.schedule(tasks, reviewers)
        t1_assign = next(a for a in schedule.assignments if a["task_id"] == "t1")
        assert t1_assign["reviewer_id"] == "r2"

    def test_get_critical_path(self):
        """Critical path returns the longest dependency chain."""
        scheduler = DueDiligenceScheduler()
        tasks = [
            DueDiligenceTask(id="A", name="A", duration=2.0, expertise="finance", dependencies=[]),
            DueDiligenceTask(id="B", name="B", duration=3.0, expertise="finance", dependencies=["A"]),
            DueDiligenceTask(id="C", name="C", duration=1.0, expertise="finance", dependencies=["A"]),
        ]
        reviewers = [
            Reviewer(id="r1", name="Alice", expertise=["finance"], availability=8.0),
        ]
        scheduler.schedule(tasks, reviewers)
        critical_path = scheduler.get_critical_path()
        assert "A" in critical_path
        assert "B" in critical_path
        assert "C" not in critical_path

    def test_reviewer_utilization(self):
        """Reviewer utilization reflects assigned work."""
        scheduler = DueDiligenceScheduler()
        tasks = [
            DueDiligenceTask(id="t1", name="Task1", duration=4.0, expertise="finance", dependencies=[]),
            DueDiligenceTask(id="t2", name="Task2", duration=2.0, expertise="finance", dependencies=[]),
        ]
        reviewers = [
            Reviewer(id="r1", name="Alice", expertise=["finance"], availability=8.0),
        ]
        schedule = scheduler.schedule(tasks, reviewers)
        assert schedule.reviewer_utilization["r1"] == 6.0


class TestDueDiligenceAnalyzer:
    """TDD tests for the due diligence analyzer."""

    def test_dd_score(self):
        """Due diligence score calculated as weighted average."""
        analyzer = DueDiligenceAnalyzer()
        factors = [
            DDFactor(name="Revenue Quality", category="financial", score=8.0, weight=2.0, status="pass"),
            DDFactor(name="Margin Stability", category="financial", score=6.0, weight=1.0, status="pass"),
        ]
        score = analyzer.overall_score(factors)
        expected = (8.0 * 2.0 + 6.0 * 1.0) / 3.0
        assert score == pytest.approx(expected)

    def test_financial_dd(self):
        """Financial DD scored from financial-category factors only."""
        analyzer = DueDiligenceAnalyzer()
        factors = [
            DDFactor(name="Revenue Quality", category="financial", score=8.0, weight=1.0, status="pass"),
            DDFactor(name="Margin Stability", category="financial", score=6.0, weight=1.0, status="pass"),
            DDFactor(name="Litigation", category="legal", score=3.0, weight=1.0, status="flagged"),
        ]
        assert analyzer.financial_dd(factors) == pytest.approx(7.0)
        assert analyzer.legal_dd(factors) == pytest.approx(3.0)

    def test_legal_dd(self):
        """Legal DD scored from legal-category factors only."""
        analyzer = DueDiligenceAnalyzer()
        factors = [
            DDFactor(name="Litigation", category="legal", score=3.0, weight=1.0, status="flagged"),
            DDFactor(name="IP Ownership", category="legal", score=7.0, weight=2.0, status="pass"),
            DDFactor(name="Code Quality", category="technical", score=9.0, weight=1.0, status="pass"),
        ]
        score = analyzer.legal_dd(factors)
        assert score == pytest.approx((3.0 * 1.0 + 7.0 * 2.0) / 3.0)

    def test_technical_dd(self):
        """Technical DD scored from technical-category factors only."""
        analyzer = DueDiligenceAnalyzer()
        factors = [
            DDFactor(name="Code Quality", category="technical", score=9.0, weight=1.0, status="pass"),
            DDFactor(name="Tech Debt", category="technical", score=5.0, weight=1.0, status="pass"),
            DDFactor(name="Revenue Quality", category="financial", score=8.0, weight=1.0, status="pass"),
        ]
        assert analyzer.technical_dd(factors) == pytest.approx(7.0)

    def test_empty_dd(self):
        """Empty DD returns defaults."""
        analyzer = DueDiligenceAnalyzer()
        assert analyzer.overall_score([]) == 0.0
        assert analyzer.financial_dd([]) == 0.0
        assert analyzer.legal_dd([]) == 0.0
        assert analyzer.technical_dd([]) == 0.0
        report = analyzer.generate_dd_report([])
        assert report.factors == []
        assert report.overall_score == 0.0
        assert report.risk_level == "critical"
        assert isinstance(report.recommendation, str) and report.recommendation
        assert isinstance(report.timeline_days, int) and report.timeline_days > 0

    def test_dd_risk(self):
        """DD risk assessed from overall score."""
        analyzer = DueDiligenceAnalyzer()
        assert analyzer.risk_level(9.0) == "low"
        assert analyzer.risk_level(7.0) == "low"
        assert analyzer.risk_level(5.0) == "medium"
        assert analyzer.risk_level(3.0) == "high"
        assert analyzer.risk_level(0.0) == "critical"

    def test_dd_report(self):
        """Report generated with all DD fields."""
        analyzer = DueDiligenceAnalyzer()
        factors = [
            DDFactor(name="Revenue Quality", category="financial", score=8.0, weight=1.0, status="pass"),
            DDFactor(name="Litigation", category="legal", score=4.0, weight=1.0, status="flagged"),
            DDFactor(name="Code Quality", category="technical", score=6.0, weight=1.0, status="pass"),
        ]
        report = analyzer.generate_dd_report(factors)
        assert isinstance(report, DDResult)
        assert len(report.factors) == 3
        assert report.overall_score == pytest.approx(6.0)
        assert report.risk_level in ("low", "medium", "high", "critical")
        assert isinstance(report.recommendation, str) and report.recommendation
        assert isinstance(report.timeline_days, int) and report.timeline_days > 0

    def test_dd_checklist(self):
        """Checklist generated from factors."""
        analyzer = DueDiligenceAnalyzer()
        factors = [
            DDFactor(name="Revenue Quality", category="financial", score=8.0, weight=1.0, status="pass"),
            DDFactor(name="Litigation", category="legal", score=4.0, weight=1.0, status="flagged"),
        ]
        checklist = analyzer.generate_checklist(factors)
        assert isinstance(checklist, list)
        assert len(checklist) == 2
        assert all(isinstance(item, str) for item in checklist)
        assert any("Revenue Quality" in item for item in checklist)
        assert any("Litigation" in item for item in checklist)

    def test_dd_timeline(self):
        """Timeline generated in days."""
        analyzer = DueDiligenceAnalyzer()
        factors = [
            DDFactor(name="F1", category="financial", score=8.0, weight=1.0, status="pass"),
            DDFactor(name="F2", category="legal", score=4.0, weight=1.0, status="fail"),
        ]
        timeline = analyzer.dd_timeline(factors)
        assert isinstance(timeline, int)
        assert timeline > 0

    def test_dd_recommendation(self):
        """Recommendation generated from score and risk."""
        analyzer = DueDiligenceAnalyzer()
        rec_low = analyzer.dd_recommendation(9.0, "low")
        rec_critical = analyzer.dd_recommendation(1.0, "critical")
        assert isinstance(rec_low, str) and rec_low
        assert isinstance(rec_critical, str) and rec_critical
        assert rec_low != rec_critical

    def test_add_factor(self):
        """add_factor returns a validated DDFactor."""
        analyzer = DueDiligenceAnalyzer()
        factor = analyzer.add_factor("Revenue Quality", "financial", 8.0, 1.0, "pass")
        assert isinstance(factor, DDFactor)
        assert factor.name == "Revenue Quality"
        assert factor.category == "financial"
        assert factor.score == 8.0
        assert factor.weight == 1.0
        assert factor.status == "pass"
