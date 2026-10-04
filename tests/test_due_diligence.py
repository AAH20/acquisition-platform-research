"""Tests for due diligence scheduling module."""
import pytest
from acquisition_platform.due_diligence import (
    DueDiligenceTask,
    Reviewer,
    DueDiligenceSchedule,
    DueDiligenceScheduler,
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
