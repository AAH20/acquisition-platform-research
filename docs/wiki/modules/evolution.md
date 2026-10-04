# Module: `evolution.py`

## Purpose

Genetic algorithm framework for hyperparameter optimization with benchmark evaluation.

## Responsibilities

- Evolve a population of candidate solutions using selection, crossover, and mutation
- Track fitness, diversity, offspring count, and convergence
- Evaluate model performance against benchmark targets
- Provide improvement suggestions for failed benchmarks

## Key Files

- [`src/acquisition_platform/evolution.py`](../../../src/acquisition_platform/evolution.py) — 194 lines

## Public API

### `Benchmark`

```python
@dataclass
class Benchmark:
    name: str
    target: float
    def evaluate(self, actual: float) -> EvaluationResult
```

### `EvaluationResult`

```python
@dataclass
class EvaluationResult:
    passed: bool
    gap: float
    suggestion: str
```

### `EvolutionEngine`

```python
class EvolutionEngine:
    def __init__(self, population_size: int = 50, generations: int = 20,
                 mutation_rate: float = 0.1, elitism: int = 2) -> None
    def evolve(self, fitness_fn: Callable[[float], float],
               gene_range: Tuple[float, float]) -> EvolutionResult
```

### `EvolutionResult`

```python
@dataclass
class EvolutionResult:
    best_fitness: float
    generation_count: int
    population_size: int
    diversity: float
    offspring_count: int
    converged: bool
    worst_fitness: float
```

## GA Operators

| Operator | Implementation |
|----------|---------------|
| Selection | Tournament (pick 2 random, take better) |
| Crossover | Uniform (average of parents) |
| Mutation | Gaussian (scale = 10% of range) |
| Elitism | Top N preserved unchanged |
| Convergence | Improvement < 0.001 for 5 generations (min 10 generations) |

## Dependencies

- **Used by:** All modules (hyperparameter optimization)
- **Uses:** Nothing (standalone module)

## Tests

10 tests in [`tests/test_evolution.py`](../../../tests/test_evolution.py):
- Fitness improvement, population size, mutation diversity, crossover offspring, elitism, convergence, benchmark comparison/pass/fail, suggestions
