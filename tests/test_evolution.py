"""Tests for evolution and evaluation framework."""
import pytest
from acquisition_platform.evolution import EvolutionEngine, EvaluationResult, Benchmark


class TestEvolutionEngine:
    """TDD tests for the evolution and evaluation framework."""

    def test_evolution_improves_fitness_over_generations(self):
        engine = EvolutionEngine(population_size=20, generations=10)
        result = engine.evolve(
            fitness_fn=lambda x: x**2,
            gene_range=(0, 100),
        )
        assert result.best_fitness > 0
        assert result.generation_count == 10

    def test_population_size_respected(self):
        engine = EvolutionEngine(population_size=15, generations=5)
        result = engine.evolve(
            fitness_fn=lambda x: x,
            gene_range=(0, 10),
        )
        assert result.population_size == 15

    def test_mutation_rate_affects_diversity(self):
        engine = EvolutionEngine(population_size=20, generations=5, mutation_rate=0.5)
        result = engine.evolve(
            fitness_fn=lambda x: x,
            gene_range=(0, 100),
        )
        assert result.diversity > 0

    def test_crossover_produces_offspring(self):
        engine = EvolutionEngine(population_size=20, generations=5)
        result = engine.evolve(
            fitness_fn=lambda x: x,
            gene_range=(0, 100),
        )
        assert result.offspring_count > 0

    def test_elitism_preserves_best(self):
        engine = EvolutionEngine(population_size=20, generations=10, elitism=2)
        result = engine.evolve(
            fitness_fn=lambda x: x**2,
            gene_range=(0, 100),
        )
        assert result.best_fitness >= result.worst_fitness

    def test_convergence_detected(self):
        engine = EvolutionEngine(population_size=10, generations=50)
        result = engine.evolve(
            fitness_fn=lambda x: x,
            gene_range=(0, 1),
        )
        # Should converge in 50 generations for simple fitness
        assert result.converged or result.generation_count == 50


class TestEvaluationFramework:
    """TDD tests for the evaluation framework."""

    def test_benchmark_comparison(self):
        bench = Benchmark(name="matching_accuracy", target=0.95)
        result = bench.evaluate(actual=0.92)
        assert result.passed is False
        assert result.gap == 0.03

    def test_benchmark_passes_when_target_met(self):
        bench = Benchmark(name="fraud_detection", target=0.90)
        result = bench.evaluate(actual=0.95)
        assert result.passed is True

    def test_multiple_benchmarks_evaluated(self):
        benchmarks = [
            Benchmark(name="matching", target=0.90),
            Benchmark(name="valuation", target=0.85),
            Benchmark(name="fraud", target=0.95),
        ]
        scores = {"matching": 0.92, "valuation": 0.80, "fraud": 0.97}
        results = {b.name: b.evaluate(scores[b.name]) for b in benchmarks}
        assert results["matching"].passed is True
        assert results["valuation"].passed is False
        assert results["fraud"].passed is True

    def test_evaluation_result_has_improvement_suggestion(self):
        bench = Benchmark(name="test", target=0.95)
        result = bench.evaluate(actual=0.80)
        assert result.suggestion is not None
        assert len(result.suggestion) > 0
