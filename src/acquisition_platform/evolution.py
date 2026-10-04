"""Genetic algorithm framework for hyperparameter optimization.

This module provides a simple genetic algorithm engine for optimizing
hyperparameters in acquisition platform models. It uses tournament
selection, uniform crossover, and Gaussian mutation to evolve a population
of candidate solutions toward better fitness over multiple generations.

The framework also includes a Benchmark evaluation system for comparing
model performance against target metrics.
"""

from __future__ import annotations

import random
import statistics
from dataclasses import dataclass
from typing import Callable, Tuple

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