"""Due diligence scheduling module.

Schedules due diligence tasks across reviewers with expertise matching,
precedence constraints, and parallel execution.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from acquisition_platform.exceptions import ValidationError, InvalidRangeError
from acquisition_platform.serialization import SerializableMixin

from acquisition_platform.observability import get_logger, log_execution_time, log_module_call

logger = get_logger(__name__)


@dataclass
class DueDiligenceTask(SerializableMixin):
    """A due diligence task.

    Attributes:
        id: Unique task identifier.
        name: Human-readable task name.
        duration: Estimated hours required.
        expertise: Required expertise domain (e.g. "finance", "legal").
        dependencies: IDs of tasks that must complete before this one starts.
    """

    id: str
    name: str
    duration: float
    expertise: str
    dependencies: list[str] = field(default_factory=list)


@dataclass
class Reviewer(SerializableMixin):
    """A reviewer available for due diligence tasks.

    Attributes:
        id: Unique reviewer identifier.
        name: Human-readable reviewer name.
        expertise: List of expertise domains this reviewer covers.
        availability: Total hours available.
    """

    id: str
    name: str
    expertise: list[str]
    availability: float


@dataclass
class DueDiligenceSchedule(SerializableMixin):
    """Result of scheduling due diligence tasks.

    Attributes:
        assignments: List of assignment dicts with keys:
            task_id, reviewer_id, start_time, duration.
        makespan: Total time to complete all tasks (hours).
        reviewer_utilization: Dict mapping reviewer_id -> total assigned hours.
    """

    assignments: list[dict[str, Any]]
    makespan: float
    reviewer_utilization: dict[str, float]


class DueDiligenceScheduler:
    """Schedules due diligence tasks across reviewers.

    Uses a greedy list-scheduling algorithm:
    1. Topologically sort tasks by dependencies.
    2. For each task, find the earliest-starting qualified reviewer
       whose availability and dependency constraints are satisfied.
    3. Assign the task and update reviewer timelines.
    """

    def __init__(self) -> None:
        self._tasks: list[DueDiligenceTask] = []
        self._reviewers: list[Reviewer] = []
        self._schedule: DueDiligenceSchedule | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @log_execution_time(logger)
    def schedule(
        self,
        tasks: list[DueDiligenceTask],
        reviewers: list[Reviewer],
    ) -> DueDiligenceSchedule:
        """Schedule tasks across reviewers.

        Args:
            tasks: Tasks to schedule.
            reviewers: Available reviewers.

        Returns:
            A DueDiligenceSchedule with assignments, makespan, and utilization.

        Raises:
            ValidationError: If a task cannot be scheduled (no qualified
                reviewer, insufficient availability, or circular dependency).
        """
        if not tasks:
            self._schedule = DueDiligenceSchedule(
                assignments=[], makespan=0.0, reviewer_utilization={}
            )
            return self._schedule

        if not reviewers:
            raise ValidationError("At least one reviewer is required")

        self._tasks = list(tasks)
        self._reviewers = list(reviewers)
        self._schedule = self._compute_schedule()
        return self._schedule

    @log_execution_time(logger)
    def add_task(self, task: DueDiligenceTask) -> None:
        """Add a task and mark the schedule for recomputation.

        Args:
            task: The task to add.
        """
        self._tasks.append(task)
        self._schedule = None  # Invalidate cached schedule

    @log_execution_time(logger)
    def reschedule(self) -> DueDiligenceSchedule:
        """Recompute the schedule from current tasks and reviewers.

        Returns:
            The updated DueDiligenceSchedule.

        Raises:
            ValidationError: If no tasks have been added yet.
        """
        if not self._tasks:
            raise ValidationError("No tasks to schedule")
        if not self._reviewers:
            raise ValidationError("No reviewers available")
        self._schedule = self._compute_schedule()
        return self._schedule

    @log_execution_time(logger)
    def get_critical_path(self) -> list[str]:
        """Return the critical path (longest dependency chain by duration).

        Returns:
            List of task IDs on the critical path, in order.
        """
        if not self._tasks:
            return []

        # Build adjacency: task -> list of (dependent_task, duration)
        task_map = {t.id: t for t in self._tasks}
        successors: dict[str, list[tuple[str, float]]] = {t.id: [] for t in self._tasks}
        in_degree: dict[str, int] = {t.id: 0 for t in self._tasks}

        for t in self._tasks:
            for dep_id in t.dependencies:
                if dep_id in task_map:
                    successors[dep_id].append((t.id, t.duration))
                    in_degree[t.id] += 1

        # Longest path via topological order (Kahn's algorithm)
        # dist[task_id] = longest path duration ending at this task
        dist: dict[str, float] = {t.id: t.duration for t in self._tasks}
        predecessor: dict[str, str | None] = {t.id: None for t in self._tasks}

        queue = [tid for tid, deg in in_degree.items() if deg == 0]
        topo_order: list[str] = []

        while queue:
            tid = queue.pop(0)
            topo_order.append(tid)
            for succ_id, succ_dur in successors[tid]:
                candidate = dist[tid] + succ_dur
                if candidate > dist[succ_id]:
                    dist[succ_id] = candidate
                    predecessor[succ_id] = tid
                in_degree[succ_id] -= 1
                if in_degree[succ_id] == 0:
                    queue.append(succ_id)

        if len(topo_order) != len(self._tasks):
            raise ValidationError("Circular dependency detected")

        # Trace back from the task with maximum distance
        end_task = max(dist, key=lambda tid: dist[tid])
        path: list[str] = []
        current: str | None = end_task
        while current is not None:
            path.append(current)
            current = predecessor[current]
        path.reverse()
        return path

    # ------------------------------------------------------------------
    # Internal scheduling algorithm
    # ------------------------------------------------------------------

    def _compute_schedule(self) -> DueDiligenceSchedule:
        """Core scheduling algorithm."""
        task_map = {t.id: t for t in self._tasks}
        reviewer_map = {r.id: r for r in self._reviewers}

        # Topological sort of tasks
        sorted_tasks = self._topological_sort(task_map)

        # Track reviewer timelines: reviewer_id -> list of (start, end)
        reviewer_timeline: dict[str, list[tuple[float, float]]] = {
            r.id: [] for r in self._reviewers
        }
        # Track reviewer total assigned hours
        reviewer_load: dict[str, float] = {r.id: 0.0 for r in self._reviewers}
        # Track task finish times
        task_finish: dict[str, float] = {}

        assignments: list[dict[str, Any]] = []

        for task in sorted_tasks:
            # Earliest start based on dependencies
            dep_ready = 0.0
            for dep_id in task.dependencies:
                if dep_id in task_finish:
                    dep_ready = max(dep_ready, task_finish[dep_id])

            # Find best reviewer: qualified, available, earliest start
            best_reviewer_id: str | None = None
            best_start: float = float("inf")

            for reviewer in self._reviewers:
                if task.expertise not in reviewer.expertise:
                    continue
                if reviewer_load[reviewer.id] + task.duration > reviewer.availability:
                    continue

                # Find earliest slot for this reviewer after dep_ready
                start = self._earliest_slot(
                    reviewer_timeline[reviewer.id], dep_ready, task.duration
                )
                if start < best_start:
                    best_start = start
                    best_reviewer_id = reviewer.id

            if best_reviewer_id is None:
                raise ValidationError(
                    f"Cannot schedule task '{task.id}': no qualified reviewer "
                    f"with sufficient availability"
                )

            # Assign task
            end_time = best_start + task.duration
            reviewer_timeline[best_reviewer_id].append((best_start, end_time))
            reviewer_timeline[best_reviewer_id].sort()
            reviewer_load[best_reviewer_id] += task.duration
            task_finish[task.id] = end_time

            assignments.append({
                "task_id": task.id,
                "reviewer_id": best_reviewer_id,
                "start_time": best_start,
                "duration": task.duration,
            })

        makespan = max(task_finish.values()) if task_finish else 0.0
        utilization = {
            rid: load for rid, load in reviewer_load.items() if load > 0
        }

        return DueDiligenceSchedule(
            assignments=assignments,
            makespan=makespan,
            reviewer_utilization=utilization,
        )

    def _topological_sort(
        self, task_map: dict[str, DueDiligenceTask]
    ) -> list[DueDiligenceTask]:
        """Kahn's algorithm for topological sorting."""
        in_degree: dict[str, int] = {t.id: 0 for t in self._tasks}
        successors: dict[str, list[str]] = {t.id: [] for t in self._tasks}

        for t in self._tasks:
            for dep_id in t.dependencies:
                if dep_id not in task_map:
                    raise ValidationError(
                        f"Task '{t.id}' depends on unknown task '{dep_id}'"
                    )
                successors[dep_id].append(t.id)
                in_degree[t.id] += 1

        queue = [tid for tid, deg in in_degree.items() if deg == 0]
        result: list[DueDiligenceTask] = []

        while queue:
            tid = queue.pop(0)
            result.append(task_map[tid])
            for succ_id in successors[tid]:
                in_degree[succ_id] -= 1
                if in_degree[succ_id] == 0:
                    queue.append(succ_id)

        if len(result) != len(self._tasks):
            raise ValidationError("Circular dependency detected in tasks")

        return result

    @staticmethod
    def _earliest_slot(
        timeline: list[tuple[float, float]],
        earliest: float,
        duration: float,
    ) -> float:
        """Find the earliest time slot of given duration after `earliest`."""
        if not timeline:
            return earliest

        # Try to fit before first task
        if earliest + duration <= timeline[0][0]:
            return earliest

        # Try gaps between tasks
        for i in range(len(timeline) - 1):
            gap_start = max(earliest, timeline[i][1])
            gap_end = timeline[i + 1][0]
            if gap_start + duration <= gap_end:
                return gap_start

        # After last task
        return max(earliest, timeline[-1][1])


# ----------------------------------------------------------------------
# Due diligence analysis (scoring, risk, reporting)
# ----------------------------------------------------------------------

# Risk level thresholds for due diligence scores (0-10, higher = better)
_DD_LOW_THRESHOLD = 7.0
_DD_MEDIUM_THRESHOLD = 4.0
_DD_HIGH_THRESHOLD = 2.0

# Base timeline (days) for a due diligence engagement
_DD_BASE_TIMELINE_DAYS = 30
# Additional days per factor reviewed
_DD_DAYS_PER_FACTOR = 5
# Extra days required when any factor has failed
_DD_FAIL_OVERHEAD_DAYS = 10


@dataclass
class DDFactor(SerializableMixin):
    """A single due diligence factor.

    Attributes:
        name: Human-readable factor name (e.g. "Revenue Quality").
        category: Due diligence category (e.g. "financial", "legal",
            "technical").
        score: Factor score on a 0-10 scale (higher = better).
        weight: Importance weight used in weighted aggregation.
        status: Review status (e.g. "pass", "flagged", "fail").
    """

    name: str
    category: str
    score: float
    weight: float
    status: str


@dataclass
class DDResult(SerializableMixin):
    """Complete due diligence analysis result.

    Attributes:
        factors: List of individual factors assessed.
        overall_score: Weighted aggregate score (0-10).
        risk_level: Classification: "low", "medium", "high", or "critical".
        recommendation: Human-readable recommendation string.
        timeline_days: Estimated due diligence timeline in days.
    """

    factors: list[DDFactor]
    overall_score: float
    risk_level: str
    recommendation: str
    timeline_days: int


class DueDiligenceAnalyzer:
    """Due diligence scoring and reporting engine.

    Scores individual due diligence factors by category (financial,
    legal, technical), aggregates them into an overall score, classifies
    risk, and generates checklists, timelines, and recommendations.
    """

    def __init__(self) -> None:
        self._factors: list[DDFactor] = []
        self._reports: list[DDResult] = []

    # ------------------------------------------------------------------
    # Factor management
    # ------------------------------------------------------------------

    @log_execution_time(logger)
    def add_factor(
        self,
        name: str,
        category: str,
        score: float,
        weight: float,
        status: str,
    ) -> DDFactor:
        """Create and store a validated DDFactor.

        Args:
            name: Human-readable factor name.
            category: Due diligence category (e.g. "financial").
            score: Factor score (0-10).
            weight: Importance weight (0-1).
            status: Review status (e.g. "pass", "flagged", "fail").

        Returns:
            The created DDFactor instance.

        Raises:
            ValidationError: If name/category/status is empty.
            InvalidRangeError: If score or weight is outside valid range.
        """
        if not name or not name.strip():
            raise ValidationError("DD factor name cannot be empty")
        if not category or not category.strip():
            raise ValidationError("DD factor category cannot be empty")
        if not status or not status.strip():
            raise ValidationError("DD factor status cannot be empty")
        if not 0 <= score <= 10:
            raise InvalidRangeError(f"Score must be between 0 and 10, got {score}")
        if not 0 <= weight <= 1:
            raise InvalidRangeError(f"Weight must be between 0 and 1, got {weight}")
        factor = DDFactor(
            name=name.strip(),
            category=category.strip(),
            score=float(score),
            weight=float(weight),
            status=status.strip(),
        )
        self._factors.append(factor)
        return factor

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    @log_execution_time(logger)
    def _category_score(self, factors: list[DDFactor], category: str) -> float:
        """Weighted average score for factors in a category (0.0 if none)."""
        matching = [f for f in factors if f.category.lower() == category.lower()]
        if not matching:
            return 0.0
        total_weight = sum(f.weight for f in matching)
        if total_weight == 0:
            return 0.0
        return sum(f.score * f.weight for f in matching) / total_weight

    @log_execution_time(logger)
    def financial_dd(self, factors: list[DDFactor]) -> float:
        """Score financial due diligence factors.

        Args:
            factors: Factors to score; only "financial" category counts.

        Returns:
            Weighted average score (0-10). 0.0 if no financial factors.
        """
        return self._category_score(factors, "financial")

    @log_execution_time(logger)
    def legal_dd(self, factors: list[DDFactor]) -> float:
        """Score legal due diligence factors.

        Args:
            factors: Factors to score; only "legal" category counts.

        Returns:
            Weighted average score (0-10). 0.0 if no legal factors.
        """
        return self._category_score(factors, "legal")

    @log_execution_time(logger)
    def technical_dd(self, factors: list[DDFactor]) -> float:
        """Score technical due diligence factors.

        Args:
            factors: Factors to score; only "technical" category counts.

        Returns:
            Weighted average score (0-10). 0.0 if no technical factors.
        """
        return self._category_score(factors, "technical")

    @log_execution_time(logger)
    def overall_score(self, factors: list[DDFactor]) -> float:
        """Compute the weighted overall due diligence score.

        Args:
            factors: All factors to aggregate.

        Returns:
            Weighted average score (0-10). 0.0 for an empty list.
        """
        if not factors:
            return 0.0
        total_weight = sum(f.weight for f in factors)
        if total_weight == 0:
            return 0.0
        return sum(f.score * f.weight for f in factors) / total_weight

    # ------------------------------------------------------------------
    # Risk classification
    # ------------------------------------------------------------------

    @log_execution_time(logger)
    def risk_level(self, score: float) -> str:
        """Classify a due diligence score into a risk level.

        Args:
            score: Due diligence score (0-10, higher = better).

        Returns:
            One of "low", "medium", "high", or "critical".

        Raises:
            InvalidRangeError: If score is outside [0, 10].
        """
        if not 0 <= score <= 10:
            raise InvalidRangeError(f"Score must be between 0 and 10, got {score}")
        if score >= _DD_LOW_THRESHOLD:
            return "low"
        if score >= _DD_MEDIUM_THRESHOLD:
            return "medium"
        if score >= _DD_HIGH_THRESHOLD:
            return "high"
        return "critical"

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    @log_execution_time(logger)
    def generate_checklist(self, factors: list[DDFactor]) -> list[str]:
        """Generate a review checklist from due diligence factors.

        Args:
            factors: Factors to include in the checklist.

        Returns:
            List of checklist item strings, one per factor.
        """
        checklist: list[str] = []
        for f in factors:
            checklist.append(
                f"[{f.status.upper()}] {f.name} ({f.category}): "
                f"verify documentation and confirm score {f.score}/10"
            )
        return checklist

    @log_execution_time(logger)
    def dd_timeline(self, factors: list[DDFactor]) -> int:
        """Estimate the due diligence timeline in days.

        Args:
            factors: Factors to be reviewed.

        Returns:
            Estimated timeline in days (always positive).
        """
        days = _DD_BASE_TIMELINE_DAYS + _DD_DAYS_PER_FACTOR * len(factors)
        if any(f.status.lower() == "fail" for f in factors):
            days += _DD_FAIL_OVERHEAD_DAYS
        return days

    @log_execution_time(logger)
    def dd_recommendation(self, score: float, risk: str) -> str:
        """Generate a recommendation from score and risk level.

        Args:
            score: Overall due diligence score (0-10).
            risk: Risk level ("low", "medium", "high", or "critical").

        Returns:
            Human-readable recommendation string.

        Raises:
            InvalidRangeError: If score is outside [0, 10].
        """
        if not 0 <= score <= 10:
            raise InvalidRangeError(f"Score must be between 0 and 10, got {score}")
        risk_lower = risk.lower()
        if risk_lower == "low":
            return (
                "Proceed with acquisition — due diligence risk is low "
                f"(score {score:.1f}/10)."
            )
        if risk_lower == "medium":
            return (
                "Proceed with caution — address medium-risk findings "
                f"(score {score:.1f}/10) before closing."
            )
        if risk_lower == "high":
            return (
                "High risk — renegotiate terms or require remediation "
                f"(score {score:.1f}/10) before proceeding."
            )
        return (
            "Do not proceed — critical due diligence failures detected "
            f"(score {score:.1f}/10)."
        )

    @log_execution_time(logger)
    def generate_dd_report(self, factors: list[DDFactor]) -> DDResult:
        """Generate a complete due diligence report.

        Args:
            factors: Factors to include in the report.

        Returns:
            A DDResult with score, risk level, recommendation, and timeline.
        """
        score = self.overall_score(factors)
        risk = self.risk_level(score)
        report = DDResult(
            factors=list(factors),
            overall_score=score,
            risk_level=risk,
            recommendation=self.dd_recommendation(score, risk),
            timeline_days=self.dd_timeline(factors),
        )
        self._reports.append(report)
        return report
