# Wave 2 Research: Due Diligence Module Gap Analysis

**Date:** 2026-10-04
**Focus:** Missing `due_diligence.py` module — gap between README architecture and actual codebase
**Method:** Codebase grep, README analysis, research document review, architecture diagram inspection

---

## 1. Gap Summary

The `due_diligence.py` module is **referenced in the README and architecture diagrams but does not exist** in the codebase. This is a critical gap because:

- The README's system architecture diagram includes `DD["Due Diligence<br/>Job Shop"]` as a core optimization engine component
- The module interactions diagram shows `DD[Due Diligence]` feeding into `EVO[Evolution Engine]`
- The `__init__.py` docstring explicitly mentions "due diligence scheduling" as one of the solved NP-hard problems
- The NP-hard problems table lists "Deal Timeline (3-6 months)" as "Yes (job shop)" but maps it to `evolution.py` instead of a dedicated `due_diligence.py`
- The research document `w1_due_diligence_automation.md` exists and provides domain context

**Verdict:** The module was designed and referenced but never implemented.

---

## 2. Grep Evidence

### 2.1 Source Code Search
```bash
grep -r 'due_diligence' src/
# Result: No matches found
```

### 2.2 Import Search
```bash
grep -r 'import.*due_diligence\|from.*due_diligence' .
# Result: No matches found
```

### 2.3 Documentation References
```bash
grep -r 'due_diligence\|DueDiligence\|JobShop\|job_shop' . --include="*.py" --include="*.md" --include="*.mmd"
# Results:
# - docs/ARCHITECTURE.md: "Yes (job shop scheduling)"
# - README.md: "Yes (job shop)" → evolution.py
# - research/w1_quiet_light.md: "This is a job shop scheduling problem, which is NP-hard"
# - research/w1_cross_border_ma.md: "NP-hard — equivalent to job-shop scheduling with precedence constraints"
```

---

## 3. NP-Hard Problem: Job Shop Scheduling

### 3.1 Problem Definition

**Job Shop Scheduling (JSS)** is a classical NP-hard combinatorial optimization problem where:
- A set of **jobs** must be processed on a set of **machines** (resources)
- Each job consists of a sequence of **operations**, each requiring a specific machine for a given duration
- Each machine can process only one operation at a time
- The objective is to minimize **makespan** (total completion time) or other scheduling metrics

### 3.2 Mapping to Due Diligence

In the acquisition platform context:

| JSS Concept | Due Diligence Equivalent |
|-------------|-------------------------|
| Job | Due diligence workstream (legal, financial, commercial, tax, operational) |
| Machine | Reviewer/team with specific expertise (legal team, financial analysts, etc.) |
| Operation | Individual task within a workstream (contract review, UCC search, financial analysis) |
| Processing time | Estimated hours/days for each task |
| Precedence constraints | Task dependencies (can't review contracts before NDA is signed) |
| Makespan | Total deal timeline (currently 3-6 months) |

### 3.3 Complexity

- **Decision version:** NP-complete
- **Optimization version:** NP-hard
- **Dynamic version** (new deals arrive, timelines shift): Even harder — referenced in `w1_quiet_light.md`
- **Cross-border variant:** "NP-hard — equivalent to job-shop scheduling with precedence constraints" (`w1_cross_border_ma.md`)

### 3.4 Why It Matters

The README identifies "Deal Timeline (3-6 months)" as bottleneck #3 with **High** severity across **all 8 platforms**. Current solutions are manual; the architecture calls for constraint programming or heuristic optimization.

---

## 4. Required Exports for `due_diligence.py`

Based on the pattern established by existing modules (`matching.py`, `fraud_detection.py`, `portfolio_optimizer.py`) and the architecture diagrams, the module should export:

### 4.1 Data Classes

```python
@dataclass
class DueDiligenceTask:
    """Represents a single due diligence task/operation."""
    id: str
    name: str
    workstream: str  # legal, financial, commercial, tax, operational
    estimated_duration: float  # hours
    required_expertise: str  # skill/domain required
    dependencies: list[str]  # task IDs that must complete first
    priority: int  # 1-5 scale
    deadline: float | None  # absolute deadline if applicable

@dataclass
class DueDiligenceSchedule:
    """Represents a complete due diligence schedule."""
    tasks: list[DueDiligenceTask]
    assignments: dict[str, tuple[str, float, float]]  # task_id → (reviewer_id, start_time, end_time)
    makespan: float
    feasibility: bool
    confidence: float

@dataclass
class Reviewer:
    """Represents a reviewer/resource in the due diligence team."""
    id: str
    name: str
    expertise: list[str]
    availability: float  # hours per day
    cost_per_hour: float
```

### 4.2 Solver Class

```python
class DueDiligenceScheduler:
    """Job shop scheduling solver for due diligence optimization.
    
    Solves the NP-hard job shop scheduling problem using heuristic
    optimization (e.g., genetic algorithm, simulated annealing, or
    constraint programming) to minimize makespan while respecting
    precedence constraints and resource availability.
    """
    
    def __init__(self, algorithm: str = "genetic", time_limit: float = 60.0):
        ...
    
    def schedule(
        self,
        tasks: list[DueDiligenceTask],
        reviewers: list[Reviewer],
    ) -> DueDiligenceSchedule:
        """Generate an optimal or near-optimal schedule.
        
        Args:
            tasks: List of due diligence tasks with dependencies.
            reviewers: List of available reviewers with expertise.
            
        Returns:
            DueDiligenceSchedule with assignments and metadata.
        """
        ...
    
    def add_task(self, task: DueDiligenceTask) -> None:
        """Add a task dynamically (for dynamic job shop)."""
        ...
    
    def reschedule(self, task_id: str, new_constraints: dict) -> DueDiligenceSchedule:
        """Reschedule when constraints change (dynamic variant)."""
        ...
```

### 4.3 Package-Level Exports

The `__init__.py` should be updated to include:

```python
from acquisition_platform.due_diligence import (
    DueDiligenceTask,
    DueDiligenceSchedule,
    Reviewer,
    DueDiligenceScheduler,
)
```

---

## 5. Integration Points

### 5.1 Module Interactions (from README diagram)

```
DD[Due Diligence] --> EVO[Evolution Engine]
```

The due diligence scheduler feeds schedule quality metrics into the evolution framework for hyperparameter optimization.

### 5.2 Data Flow

1. **Input:** Due diligence task lists from VDR/document analysis
2. **Processing:** Job shop scheduler assigns tasks to reviewers
3. **Output:** Optimized schedule with minimized makespan
4. **Evolution:** Schedule fitness feeds into GA for continuous improvement

### 5.3 Cross-Border Extension

The `w1_cross_border_ma.md` research notes that cross-border deals add:
- Multiple regulatory clocks (each jurisdiction has its own timeline)
- Precedence constraints (some filings are prerequisites for others)
- Multi-objective optimization (minimize time, cost, and risk simultaneously)

---

## 6. Implementation Recommendations

### 6.1 Algorithm Choice

| Algorithm | Pros | Cons | Fit |
|-----------|------|------|-----|
| Genetic Algorithm | Flexible, handles constraints, already used in `evolution.py` | May not find global optimum | **Recommended** — reuses existing GA infrastructure |
| Simulated Annealing | Good for dynamic rescheduling | Slower for large instances | Good for `reschedule()` method |
| Constraint Programming | Optimal for small instances | Doesn't scale well | Not recommended for production |
| Greedy Heuristic | Fast, simple | Poor solution quality | Good for baseline comparison |

### 6.2 Testing Strategy

Following the project's TDD approach and 62-test baseline:

```python
# tests/test_due_diligence.py
# Expected: 7-10 tests covering:
# - Basic scheduling with no dependencies
# - Precedence constraint handling
# - Resource conflict resolution
# - Dynamic task addition
# - Rescheduling on constraint change
# - Cross-border multi-jurisdiction scenario
# - Edge cases (empty task list, single reviewer, etc.)
```

### 6.3 Performance Targets

Based on README benchmarks:

| Metric | Target | Current |
|--------|--------|---------|
| Schedule Optimality | Within 15% of lower bound | N/A |
| Computation Time | < 60s for 100 tasks | N/A |
| Makespan Reduction | 30-50% vs. manual scheduling | N/A |

---

## 7. Research Citations

1. **Job Shop Scheduling NP-hardness:** `w1_quiet_light.md` — "This is a job shop scheduling problem, which is NP-hard"
2. **Cross-border complexity:** `w1_cross_border_ma.md` — "NP-hard — equivalent to job-shop scheduling with precedence constraints"
3. **Due diligence bottlenecks:** `w1_due_diligence_automation.md` — Section 7 (Bottlenecks)
4. **Optimization principles:** `w1_due_diligence_automation.md` — Section 9 (Optimization)
5. **NP-hard problems in DD:** `w1_due_diligence_automation.md` — Section 10 (NP-Hard Problems)

---

## 8. Conclusion

The `due_diligence.py` module is a **designed but unimplemented** component. The gap is well-documented:

- ✅ Architecture diagrams include it
- ✅ NP-hard problem classification identifies it (Job Shop Scheduling)
- ✅ Research document provides domain context
- ✅ Module interactions diagram shows data flow
- ❌ Source code does not exist
- ❌ No imports from other modules
- ❌ No tests exist
- ❌ Not exported from `__init__.py`

**Priority:** High — the module addresses bottleneck #3 (Deal Timeline) affecting all 8 platforms and is a core component of the optimization engine architecture.

**Estimated effort:** 1 implementation agent (TDD: RED-GREEN-REFACTOR), ~200-300 lines of code, 7-10 tests, following the pattern established by `matching.py` and `fraud_detection.py`.
