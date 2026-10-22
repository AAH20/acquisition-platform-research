"""Genetic algorithm framework for hyperparameter optimization.

This module provides a simple genetic algorithm engine for optimizing
hyperparameters in acquisition platform models. It uses tournament
selection, uniform crossover, and Gaussian mutation to evolve a population
of candidate solutions toward better fitness over multiple generations.

The framework also includes a Benchmark evaluation system for comparing
model performance against target metrics.
"""

from __future__ import annotations

import math
import random
import statistics
import time
from dataclasses import dataclass, field
from typing import Callable, Sequence, Tuple

from acquisition_platform.evaluation import hypervolume_2d
from acquisition_platform.exceptions import InvalidRangeError, ValidationError
from acquisition_platform.serialization import SerializableMixin


@dataclass
class EvaluationResult(SerializableMixin):
    """Result of evaluating a model against a benchmark target."""

    passed: bool
    gap: float
    suggestion: str


@dataclass
class Benchmark(SerializableMixin):
    """A benchmark target for evaluating model performance."""

    name: str
    target: float

    def evaluate(self, actual: float) -> EvaluationResult:
        """Evaluate actual performance against the target.

        Args:
            actual: The actual performance metric value.

        Returns:
            EvaluationResult with pass/fail status, gap, and suggestion.
        """
        passed = actual >= self.target
        gap = round(self.target - actual, 10)
        if not passed:
            suggestion = f"Improve {self.name} by {gap:.2f}"
        else:
            suggestion = "Maintain current performance"
        return EvaluationResult(passed=passed, gap=gap, suggestion=suggestion)


@dataclass
class EvolutionResult(SerializableMixin):
    """Result of running the genetic algorithm evolution."""

    best_fitness: float
    generation_count: int
    population_size: int
    diversity: float
    offspring_count: int
    converged: bool
    worst_fitness: float


class EvolutionEngine:
    """Genetic algorithm engine for hyperparameter optimization.

    Evolves a population of candidate solutions using selection, crossover,
    and mutation to maximize a fitness function over multiple generations.
    """

    def __init__(
        self,
        population_size: int = 50,
        generations: int = 20,
        mutation_rate: float = 0.1,
        elitism: int = 2,
    ) -> None:
        """Initialize the evolution engine.

        Args:
            population_size: Number of individuals in each generation.
            generations: Maximum number of generations to evolve.
            mutation_rate: Probability of mutating each gene.
            elitism: Number of top individuals preserved unchanged.
        """
        if population_size <= 0:
            raise ValidationError(
                f"population_size must be positive, got {population_size}"
            )
        if generations <= 0:
            raise ValidationError(f"generations must be positive, got {generations}")
        if mutation_rate < 0 or mutation_rate > 1:
            raise InvalidRangeError(
                f"mutation_rate must be in [0, 1], got {mutation_rate}"
            )
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.elitism = elitism

    def evolve(
        self,
        fitness_fn: Callable[[float], float],
        gene_range: Tuple[float, float],
    ) -> EvolutionResult:
        """Run the genetic algorithm to optimize fitness_fn.

        Args:
            fitness_fn: Function that takes a gene value and returns fitness.
            gene_range: (min, max) tuple defining the search space.

        Returns:
            EvolutionResult with metrics from the evolution run.
        """
        low, high = gene_range

        # Initialize random population
        population = [random.uniform(low, high) for _ in range(self.population_size)]

        offspring_count = 0
        prev_best = float("-inf")
        stagnant_generations = 0
        converged = False

        for generation in range(self.generations):
            # Evaluate fitness for all individuals
            fitness_scores = [fitness_fn(gene) for gene in population]

            # Track best and worst
            current_best = max(fitness_scores)
            current_worst = min(fitness_scores)

            # Check convergence: improvement < 0.001 for 5 consecutive generations
            # Only check after minimum generations to allow exploration
            improvement = current_best - prev_best
            if improvement < 0.001:
                stagnant_generations += 1
            else:
                stagnant_generations = 0

            if stagnant_generations >= 5 and generation >= 10:
                converged = True
                generation_count = generation + 1
                break

            prev_best = current_best

            # Select top performers (elitism)
            sorted_indices = sorted(
                range(len(population)), key=lambda i: fitness_scores[i], reverse=True
            )
            elite_genes = [population[i] for i in sorted_indices[: self.elitism]]

            # Create new population via crossover and mutation
            new_population = list(elite_genes)

            while len(new_population) < self.population_size:
                # Tournament selection: pick 2 random, take the better
                idx1, idx2 = random.sample(range(len(population)), 2)
                parent1 = population[idx1] if fitness_scores[idx1] > fitness_scores[idx2] else population[idx2]

                idx3, idx4 = random.sample(range(len(population)), 2)
                parent2 = population[idx3] if fitness_scores[idx3] > fitness_scores[idx4] else population[idx4]

                # Uniform crossover: average of parents
                child = (parent1 + parent2) / 2.0
                offspring_count += 1

                # Gaussian mutation
                if random.random() < self.mutation_rate:
                    mutation_scale = (high - low) * 0.1
                    child += random.gauss(0, mutation_scale)

                # Clamp to gene range
                child = max(low, min(high, child))
                new_population.append(child)

            population = new_population
        else:
            generation_count = self.generations

        # Final fitness evaluation
        final_fitness = [fitness_fn(gene) for gene in population]
        best_fitness = max(final_fitness)
        worst_fitness = min(final_fitness)

        # Diversity as standard deviation of fitness values
        if len(final_fitness) > 1:
            diversity = statistics.stdev(final_fitness)
        else:
            diversity = 0.0

        return EvolutionResult(
            best_fitness=best_fitness,
            generation_count=generation_count,
            population_size=self.population_size,
            diversity=diversity,
            offspring_count=offspring_count,
            converged=converged,
            worst_fitness=worst_fitness,
        )


# ---------------------------------------------------------------------------
# Alpha evolution: multi-gene, multi-objective, constraint-aware
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ParamSpec:
    """Definition of one evolvable gene.

    Args:
        name: Gene name exposed to the evaluation function.
        low: Lower bound (inclusive).
        high: Upper bound (inclusive).
        kind: One of ``"float"``, ``"int"`` or ``"log"``. Log genes are sampled
            logarithmically between two strictly positive bounds.
    """

    name: str
    low: float
    high: float
    kind: str = "float"

    def __post_init__(self) -> None:
        if not self.name:
            raise ValidationError("ParamSpec name cannot be empty")
        if self.high <= self.low:
            raise InvalidRangeError(
                f"ParamSpec '{self.name}' requires high > low, got [{self.low}, {self.high}]"
            )
        if self.kind not in {"float", "int", "log"}:
            raise ValidationError(
                f"ParamSpec '{self.name}' has unknown kind '{self.kind}'"
            )
        if self.kind == "log" and self.low <= 0:
            raise InvalidRangeError(
                f"ParamSpec '{self.name}' log bounds must be positive"
            )

    def decode(self, value: float) -> float:
        """Clamp a raw gene value to this spec's bounds."""
        clamped = max(self.low, min(self.high, value))
        if self.kind == "int":
            return float(round(clamped))
        return clamped

    def sample(self, generator: random.Random) -> float:
        """Draw a value uniformly over the gene's effective range."""
        if self.kind == "log":
            sampled = math.exp(
                generator.uniform(math.log(self.low), math.log(self.high))
            )
        else:
            sampled = generator.uniform(self.low, self.high)
        return self.decode(sampled)


@dataclass(frozen=True)
class Objective:
    """A single optimisation objective.

    Args:
        name: Key returned by the evaluation function.
        maximize: Direction of improvement.
        weight: Relative weight in the scalar fitness summary.
        target: Optional acceptance threshold, recorded for gating.
    """

    name: str
    maximize: bool = True
    weight: float = 1.0
    target: float | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ValidationError("Objective name cannot be empty")
        if self.weight <= 0:
            raise InvalidRangeError(
                f"Objective '{self.name}' weight must be positive, got {self.weight}"
            )


@dataclass(frozen=True)
class Constraint:
    """A hard constraint expressed as a violation function.

    ``fn`` must return a value <= 0 when the solution is feasible. Positive
    values are treated as the magnitude of the violation.
    """

    name: str
    fn: Callable[[dict[str, float]], float]
    penalty: float = 1.0

    def __post_init__(self) -> None:
        if not self.name:
            raise ValidationError("Constraint name cannot be empty")
        if self.penalty < 0:
            raise InvalidRangeError(
                f"Constraint '{self.name}' penalty must be non-negative"
            )

    def violation(self, params: dict[str, float]) -> float:
        """Return the non-negative constraint violation."""
        return max(0.0, float(self.fn(params)))


@dataclass
class Alpha:
    """One candidate solution in the evolving population."""

    vector: tuple[float, ...]
    params: dict[str, float]
    objectives: dict[str, float]
    fitness: float
    rank: int = 0
    crowding: float = 0.0
    violations: dict[str, float] = field(default_factory=dict)
    generation: int = 0
    alpha_id: str = ""

    @property
    def total_violation(self) -> float:
        """Sum of all constraint violations; zero means feasible."""
        return sum(self.violations.values())

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serialisable representation."""
        return {
            "alpha_id": self.alpha_id,
            "generation": self.generation,
            "params": dict(self.params),
            "objectives": dict(self.objectives),
            "fitness": self.fitness,
            "rank": self.rank,
            "crowding": self.crowding,
            "violations": dict(self.violations),
        }


@dataclass
class EvolutionConfig:
    """Configuration for :class:`AlphaEvolver`."""

    population_size: int = 48
    generations: int = 40
    mutation_rate: float = 0.2
    mutation_sigma: float = 0.2
    crossover_rate: float = 0.9
    crossover_alpha: float = 0.5
    elitism: int = 2
    tournament_size: int = 3
    seed: int = 0
    adaptive_mutation: bool = True
    patience: int = 12
    archive_size: int = 64
    reference_point: tuple[float, ...] | None = None

    def __post_init__(self) -> None:
        if self.population_size < 2:
            raise InvalidRangeError("population_size must be at least 2")
        if self.generations < 1:
            raise InvalidRangeError("generations must be at least 1")
        if not 0.0 <= self.mutation_rate <= 1.0:
            raise InvalidRangeError("mutation_rate must be in [0, 1]")
        if not 0.0 < self.mutation_sigma <= 1.0:
            raise InvalidRangeError("mutation_sigma must be in (0, 1]")
        if not 0.0 <= self.crossover_rate <= 1.0:
            raise InvalidRangeError("crossover_rate must be in [0, 1]")
        if self.crossover_alpha < 0.0:
            raise InvalidRangeError("crossover_alpha must be non-negative")
        if self.elitism < 0 or self.elitism >= self.population_size:
            raise InvalidRangeError("elitism must be in [0, population_size)")
        if self.tournament_size < 2:
            raise InvalidRangeError("tournament_size must be at least 2")
        if self.patience < 1:
            raise InvalidRangeError("patience must be at least 1")
        if self.archive_size < 1:
            raise InvalidRangeError("archive_size must be at least 1")
        if self.reference_point is not None and len(self.reference_point) != 2:
            raise InvalidRangeError(
                "reference_point must have exactly 2 values for hypervolume"
            )


@dataclass
class EvolutionReport:
    """Outcome of an alpha evolution run."""

    best: Alpha
    pareto_front: list[Alpha]
    generations_run: int
    evaluations: int
    baseline_fitness: float
    best_fitness: float
    improvement_pct: float
    converged: bool
    convergence_generation: int | None
    fitness_history: list[float]
    diversity_history: list[float]
    seed: int
    elapsed_seconds: float
    hypervolume: float | None = None

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serialisable representation."""
        return {
            "best": self.best.to_dict(),
            "pareto_front": [alpha.to_dict() for alpha in self.pareto_front],
            "generations_run": self.generations_run,
            "evaluations": self.evaluations,
            "baseline_fitness": self.baseline_fitness,
            "best_fitness": self.best_fitness,
            "improvement_pct": self.improvement_pct,
            "converged": self.converged,
            "convergence_generation": self.convergence_generation,
            "fitness_history": list(self.fitness_history),
            "diversity_history": list(self.diversity_history),
            "seed": self.seed,
            "elapsed_seconds": self.elapsed_seconds,
            "hypervolume": self.hypervolume,
        }


class AlphaEvolver:
    """Multi-gene, multi-objective evolutionary optimiser.

    Implements NSGA-II selection (fast non-dominated sort plus crowding
    distance), blend crossover, per-gene Gaussian mutation with an adaptive
    step size, constraint domination, and a bounded Pareto archive.

    The evolver is deterministic for a fixed ``EvolutionConfig.seed``.
    """

    def __init__(
        self,
        space: Sequence[ParamSpec],
        objectives: Sequence[Objective],
        config: EvolutionConfig | None = None,
        constraints: Sequence[Constraint] | None = None,
    ) -> None:
        if not space:
            raise ValidationError("space must contain at least one ParamSpec")
        if not objectives:
            raise ValidationError("objectives must contain at least one Objective")

        self.space = tuple(space)
        self.objectives = tuple(objectives)
        self.constraints = tuple(constraints or ())
        self.config = config or EvolutionConfig()
        self._rng = random.Random(self.config.seed)
        self.mutation_sigma = self.config.mutation_sigma
        self.hall_of_fame: list[Alpha] = []
        self._evaluations = 0
        self._evaluate_fn: Callable[[dict[str, float]], dict[str, float]] | None = None

    # -- construction -----------------------------------------------------

    def _random_vector(self) -> tuple[float, ...]:
        return tuple(spec.sample(self._rng) for spec in self.space)

    def _midpoint_vector(self) -> tuple[float, ...]:
        return tuple(
            spec.decode((spec.low + spec.high) / 2.0) for spec in self.space
        )

    def _decode(self, vector: tuple[float, ...]) -> dict[str, float]:
        return {spec.name: spec.decode(value) for spec, value in zip(self.space, vector)}

    def _violations(self, params: dict[str, float]) -> dict[str, float]:
        violations: dict[str, float] = {}
        for constraint in self.constraints:
            amount = constraint.violation(params)
            if amount > 0.0:
                violations[constraint.name] = amount
        return violations

    def _fitness(
        self, objectives: dict[str, float], violations: dict[str, float]
    ) -> float:
        total_weight = sum(objective.weight for objective in self.objectives)
        weighted = 0.0
        for objective in self.objectives:
            value = objectives[objective.name]
            direction = 1.0 if objective.maximize else -1.0
            weighted += objective.weight * direction * value
        penalty = 0.0
        for constraint in self.constraints:
            penalty += constraint.penalty * violations.get(constraint.name, 0.0)
        return weighted / total_weight - penalty

    def _make_alpha(
        self, vector: tuple[float, ...], generation: int, index: int = 0
    ) -> Alpha:
        params = self._decode(vector)
        self._evaluations += 1
        objectives = self.evaluate(params)
        missing = [
            objective.name
            for objective in self.objectives
            if objective.name not in objectives
        ]
        if missing:
            raise ValidationError(f"evaluate() did not return objectives: {missing}")
        violations = self._violations(params)
        return Alpha(
            vector=vector,
            params=params,
            objectives={
                name: float(objectives[name]) for name in (o.name for o in self.objectives)
            },
            fitness=self._fitness(objectives, violations),
            violations=violations,
            generation=generation,
            alpha_id=f"a{generation:03d}-{index:04d}",
        )

    def evaluate(self, params: dict[str, float]) -> dict[str, float]:
        """Evaluate a parameter set using the callback bound by :meth:`evolve`."""
        if self._evaluate_fn is None:
            raise ValidationError("evaluate() is only available during evolve()")
        return self._evaluate_fn(params)

    # -- NSGA-II machinery ------------------------------------------------

    @staticmethod
    def _adjusted(alpha: Alpha, objective: Objective) -> float:
        value = alpha.objectives[objective.name]
        return value if objective.maximize else -value

    def _dominates(self, a: Alpha, b: Alpha) -> bool:
        if a.total_violation == 0.0 and b.total_violation > 0.0:
            return True
        if a.total_violation > 0.0 and b.total_violation == 0.0:
            return False
        if a.total_violation > 0.0 and b.total_violation > 0.0:
            return a.total_violation < b.total_violation

        not_worse = True
        strictly_better = False
        for objective in self.objectives:
            left = self._adjusted(a, objective)
            right = self._adjusted(b, objective)
            if left < right:
                not_worse = False
                break
            if left > right:
                strictly_better = True
        return not_worse and strictly_better

    def _fast_non_dominated_sort(self, population: Sequence[Alpha]) -> list[list[int]]:
        size = len(population)
        dominated_by: list[list[int]] = [[] for _ in range(size)]
        domination_count = [0] * size
        fronts: list[list[int]] = [[]]

        for p in range(size):
            for q in range(size):
                if p == q:
                    continue
                if self._dominates(population[p], population[q]):
                    dominated_by[p].append(q)
                elif self._dominates(population[q], population[p]):
                    domination_count[p] += 1
            if domination_count[p] == 0:
                fronts[0].append(p)

        index = 0
        while fronts[index]:
            next_front: list[int] = []
            for p in fronts[index]:
                for q in dominated_by[p]:
                    domination_count[q] -= 1
                    if domination_count[q] == 0:
                        next_front.append(q)
            index += 1
            fronts.append(next_front)
        return [front for front in fronts if front]

    def _assign_crowding(self, population: Sequence[Alpha], front: list[int]) -> None:
        for index in front:
            population[index].crowding = 0.0
        if len(front) <= 2:
            for index in front:
                population[index].crowding = float("inf")
            return

        for objective in self.objectives:
            ordered = sorted(
                front, key=lambda i: self._adjusted(population[i], objective)
            )
            population[ordered[0]].crowding = float("inf")
            population[ordered[-1]].crowding = float("inf")
            low = self._adjusted(population[ordered[0]], objective)
            high = self._adjusted(population[ordered[-1]], objective)
            span = high - low
            if span <= 0.0:
                continue
            for position in range(1, len(ordered) - 1):
                previous = self._adjusted(population[ordered[position - 1]], objective)
                following = self._adjusted(population[ordered[position + 1]], objective)
                population[ordered[position]].crowding += (following - previous) / span

    def _rank(self, population: Sequence[Alpha]) -> list[list[int]]:
        fronts = self._fast_non_dominated_sort(population)
        for rank, front in enumerate(fronts):
            for index in front:
                population[index].rank = rank
            self._assign_crowding(population, front)
        return fronts

    def _tournament(self, population: Sequence[Alpha]) -> Alpha:
        contenders = [
            population[self._rng.randrange(len(population))]
            for _ in range(self.config.tournament_size)
        ]
        return min(contenders, key=lambda a: (a.rank, -a.crowding, -a.fitness))

    def _blend(self, a: float, b: float, spec: ParamSpec) -> float:
        span = abs(a - b)
        low = min(a, b) - self.config.crossover_alpha * span
        high = max(a, b) + self.config.crossover_alpha * span
        return spec.decode(self._rng.uniform(low, high))

    def _mutate(self, value: float, spec: ParamSpec) -> float:
        if self._rng.random() >= self.config.mutation_rate:
            return value
        if spec.kind == "log":
            log_low = math.log(spec.low)
            log_high = math.log(spec.high)
            mutated = math.exp(
                math.log(max(value, spec.low))
                + self._rng.gauss(0.0, self.mutation_sigma * (log_high - log_low))
            )
        else:
            mutated = value + self._rng.gauss(
                0.0, self.mutation_sigma * (spec.high - spec.low)
            )
        return spec.decode(mutated)

    def _breed(self, parent_a: Alpha, parent_b: Alpha) -> tuple[float, ...]:
        if self._rng.random() < self.config.crossover_rate:
            child = tuple(
                self._blend(left, right, spec)
                for left, right, spec in zip(parent_a.vector, parent_b.vector, self.space)
            )
        else:
            child = parent_a.vector
        return tuple(
            self._mutate(value, spec) for value, spec in zip(child, self.space)
        )

    # -- archive -----------------------------------------------------------

    def _update_archive(self, population: Sequence[Alpha]) -> None:
        feasible = [alpha for alpha in population if alpha.total_violation == 0.0]
        combined: list[Alpha] = []
        seen: set[tuple[float, ...]] = set()
        for alpha in list(self.hall_of_fame) + feasible:
            key = tuple(round(value, 10) for value in alpha.params.values())
            if key in seen:
                continue
            seen.add(key)
            combined.append(alpha)
        if not combined:
            self.hall_of_fame = []
            return

        front = [
            alpha
            for alpha in combined
            if not any(
                self._dominates(other, alpha) for other in combined if other is not alpha
            )
        ]
        self._rank(front)
        front.sort(key=lambda a: (-a.crowding, -a.fitness))
        self.hall_of_fame = front[: self.config.archive_size]

    # -- public API --------------------------------------------------------

    def evolve(
        self,
        evaluate: Callable[[dict[str, float]], dict[str, float]],
        baseline_params: dict[str, float] | None = None,
    ) -> EvolutionReport:
        """Evolve a population against ``evaluate``.

        Args:
            evaluate: Maps parameters to a dict of objective values keyed by
                the names declared on the objectives.
            baseline_params: Reference solution used to compute improvement.
                Defaults to the midpoint of the search space.

        Returns:
            EvolutionReport with the best alpha, Pareto front and history.
        """
        started = time.perf_counter()
        self._evaluations = 0
        self.hall_of_fame = []
        self.mutation_sigma = self.config.mutation_sigma
        self._evaluate_fn = evaluate
        if baseline_params is not None:
            missing = [spec.name for spec in self.space if spec.name not in baseline_params]
            if missing:
                raise ValidationError(f"baseline_params missing genes: {missing}")
            baseline_vector = tuple(
                spec.decode(baseline_params[spec.name]) for spec in self.space
            )
        else:
            baseline_vector = self._midpoint_vector()
        baseline = self._make_alpha(baseline_vector, generation=0)
        baseline_fitness = baseline.fitness

        population = [
            self._make_alpha(self._random_vector(), generation=0, index=index)
            for index in range(self.config.population_size)
        ]
        population[0] = baseline
        self._rank(population)
        self._update_archive(population)

        best_fitness = max(alpha.fitness for alpha in population)
        fitness_history: list[float] = []
        diversity_history: list[float] = []
        stagnation = 0
        convergence_generation: int | None = None
        converged = False

        for generation in range(1, self.config.generations + 1):
            fronts = self._rank(population)
            elite_indices = [
                index for front in fronts for index in front
            ][: self.config.elitism]
            children: list[Alpha] = [
                population[index] for index in elite_indices
            ]

            while len(children) < self.config.population_size:
                parent_a = self._tournament(population)
                parent_b = self._tournament(population)
                vector = self._breed(parent_a, parent_b)
                children.append(
                    self._make_alpha(vector, generation=generation, index=len(children))
                )

            combined = list(population) + children
            combined_fronts = self._rank(combined)

            next_population: list[Alpha] = []
            for front in combined_fronts:
                if len(next_population) + len(front) <= self.config.population_size:
                    next_population.extend(combined[index] for index in front)
                else:
                    remaining = self.config.population_size - len(next_population)
                    ordered = sorted(
                        front, key=lambda index: -combined[index].crowding
                    )
                    next_population.extend(
                        combined[index] for index in ordered[:remaining]
                    )
                    break

            population = next_population
            self._rank(population)
            self._update_archive(population)

            generation_best = max(alpha.fitness for alpha in population)
            fitness_history.append(generation_best)
            diversity_history.append(
                statistics.pstdev([alpha.fitness for alpha in population])
                if len(population) > 1
                else 0.0
            )

            if generation_best > best_fitness + 1e-12:
                best_fitness = generation_best
                stagnation = 0
                if self.config.adaptive_mutation:
                    self.mutation_sigma = max(0.02, self.mutation_sigma * 0.95)
            else:
                stagnation += 1
                if self.config.adaptive_mutation:
                    self.mutation_sigma = min(
                        self.config.mutation_sigma, self.mutation_sigma * 1.25
                    )
                if stagnation >= self.config.patience and generation >= 10:
                    converged = True
                    convergence_generation = generation
                    break

        best = max(population, key=lambda alpha: alpha.fitness)
        if abs(baseline_fitness) > 1e-12:
            improvement = (best.fitness - baseline_fitness) / abs(baseline_fitness) * 100.0
        else:
            improvement = 100.0 if best.fitness > baseline_fitness else 0.0

        hypervolume = None
        if self.config.reference_point is not None and len(self.objectives) == 2:
            hypervolume = hypervolume_2d(
                [
                    tuple(
                        alpha.objectives[objective.name]
                        if objective.maximize
                        else -alpha.objectives[objective.name]
                        for objective in self.objectives
                    )
                    for alpha in self.hall_of_fame
                ],
                self.config.reference_point,
            )

        return EvolutionReport(
            best=best,
            pareto_front=list(self.hall_of_fame),
            generations_run=len(fitness_history),
            evaluations=self._evaluations,
            baseline_fitness=baseline_fitness,
            best_fitness=best.fitness,
            improvement_pct=improvement,
            converged=converged,
            convergence_generation=convergence_generation,
            fitness_history=fitness_history,
            diversity_history=diversity_history,
            seed=self.config.seed,
            elapsed_seconds=time.perf_counter() - started,
            hypervolume=hypervolume,
        )