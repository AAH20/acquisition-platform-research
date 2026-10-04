# Wave 2: Evolution Framework Enhancement Gaps

**File analyzed:** `src/acquisition_platform/evolution.py` (194 lines)
**Tests:** `tests/test_evolution.py` (90 lines)
**Package exports:** `src/acquisition_platform/__init__.py`

---

## 1. Multi-Objective Optimization

**Status: NOT SUPPORTED**

The `evolve()` method accepts a single scalar fitness function:

```python
def evolve(self, fitness_fn: Callable[[float], float], gene_range: Tuple[float, float]) -> EvolutionResult:
```

- No Pareto front tracking
- No multi-objective trade-off handling
- No weighted sum or epsilon-constraint methods
- No support for conflicting objectives (e.g., maximize accuracy vs. minimize latency)
- The `Benchmark` class evaluates a single metric at a time; no composite scoring

**Gap:** Real acquisition platforms need to optimize multiple competing objectives simultaneously (e.g., matching accuracy + fraud detection + valuation speed). The current engine can only optimize one scalar at a time.

---

## 2. Constraint Handling

**Status: NOT SUPPORTED (beyond simple bounds)**

The only constraint mechanism is clamping to `gene_range`:

```python
child = max(low, min(high, child))
```

Missing:
- **Hard constraints** (feasibility requirements): e.g., "total portfolio risk < 0.3"
- **Soft constraints** (penalty functions): e.g., "prefer solutions with latency < 100ms"
- **Repair operators** for infeasible offspring
- **Constraint violation tracking** in `EvolutionResult`
- **Feasibility-preserving crossover/mutation**

**Gap:** Portfolio optimization, pricing, and matching all have complex constraints (budget caps, regulatory limits, business rules) that cannot be expressed as simple gene bounds.

---

## 3. Adaptive Mutation Rates

**Status: NOT SUPPORTED**

Mutation rate is fixed at initialization:

```python
self.mutation_rate = mutation_rate  # default 0.1, never changes
```

Missing:
- Diversity-based adaptation (increase mutation when population converges)
- Fitness-based adaptation (decrease mutation near optimum)
- Generation-based annealing (decay over time)
- Per-gene mutation rates
- Adaptive mutation scale (currently fixed at `(high - low) * 0.1`)

**Gap:** Fixed mutation rates cause premature convergence (too high) or slow convergence (too low). Adaptive rates are standard in modern GA implementations.

---

## 4. Selection Strategies

**Status: ONLY TOURNAMENT (size 2)**

The only selection mechanism is binary tournament:

```python
idx1, idx2 = random.sample(range(len(population)), 2)
parent1 = population[idx1] if fitness_scores[idx1] > fitness_scores[idx2] else population[idx2]
```

Missing:
- **Roulette wheel / fitness proportionate selection**
- **Rank-based selection** (more robust to fitness scaling)
- **Boltzmann selection** (temperature-controlled exploration)
- **Configurable tournament size** (currently hardcoded to 2)
- **Stochastic universal sampling**

**Gap:** Binary tournament has low selection pressure. Different problems need different selection strategies for optimal convergence.

---

## 5. Additional GA Improvements Needed

### 5.1 Single-Dimensional Chromosomes Only
The engine optimizes a single `float` gene. Real hyperparameter tuning needs **multi-dimensional chromosomes** (vectors of mixed types: continuous, discrete, categorical).

```python
# Current: fitness_fn takes a single float
fitness_fn: Callable[[float], float]

# Needed: fitness_fn takes a vector
fitness_fn: Callable[[List[float]], float]
```

### 5.2 No Crossover Strategy Selection
Only arithmetic mean crossover is implemented:
```python
child = (parent1 + parent2) / 2.0
```
Missing: single-point crossover, uniform crossover, blend crossover (BLX-alpha), simulated binary crossover (SBX).

### 5.3 No Migration / Island Model
Single population only. No support for:
- Multiple subpopulations with periodic migration
- Parallel evaluation across islands
- Speciation / niching for multimodal optimization

### 5.4 No Checkpointing / Resume
Evolution state cannot be saved and resumed. Long-running optimizations lose all progress on interruption.

### 5.5 No History / Logging
`EvolutionResult` only returns final metrics. No generation-by-generation history of:
- Best fitness per generation
- Population diversity over time
- Mutation/crossover statistics

### 5.6 No Parallel Fitness Evaluation
Fitness evaluation is sequential:
```python
fitness_scores = [fitness_fn(gene) for gene in population]
```
For expensive fitness functions (e.g., model training), parallel evaluation is essential.

### 5.7 No Early Stopping Criteria
Only stagnation-based convergence (5 generations without >0.001 improvement). Missing:
- Target fitness threshold
- Maximum time budget
- Maximum fitness evaluations
- Custom convergence callbacks

### 5.8 No Discrete / Categorical Gene Support
All genes are continuous floats. No support for:
- Integer/discrete parameters
- Categorical choices (e.g., optimizer type: "adam", "sgd", "rmsprop")
- Boolean flags
- Permutation-based encoding (e.g., for scheduling)

### 5.9 No Co-Evolution
No support for:
- Competitive co-evolution (predator-prey)
- Cooperative co-evolution (species collaboration)
- Co-adaptation between modules

---

## 6. Multi-Module Optimization

**Status: NOT SUPPORTED**

The `EvolutionEngine` optimizes a single scalar function with no awareness of the platform's modules:

- No mechanism to optimize across `matching`, `valuation`, `fraud_detection`, `portfolio_optimizer`, `dynamic_pricing`, `entity_resolution`, `search_ranking` simultaneously
- No inter-module dependency modeling
- No composite fitness aggregation across modules
- No module-specific gene encoding

**Gap:** The acquisition platform has 7+ modules with interdependent parameters. Optimizing each in isolation misses cross-module synergies (e.g., entity resolution quality affects matching accuracy).

---

## Summary of Enhancement Priorities

| Priority | Enhancement | Impact | Effort |
|----------|-------------|--------|--------|
| P0 | Multi-dimensional chromosomes | Unblocks all real hyperparameter tuning | Medium |
| P0 | Multi-objective optimization | Enables real-world trade-off analysis | High |
| P1 | Constraint handling | Required for portfolio/pricing constraints | Medium |
| P1 | Adaptive mutation rates | Prevents premature convergence | Low |
| P1 | Configurable selection strategies | Improves convergence across problems | Low |
| P2 | Parallel fitness evaluation | Enables expensive fitness functions | Medium |
| P2 | History / logging | Debugging and analysis | Low |
| P2 | Checkpointing / resume | Long-running optimizations | Medium |
| P3 | Categorical/discrete genes | Broader problem coverage | Medium |
| P3 | Island model / migration | Multimodal optimization | High |
| P3 | Multi-module coordination | Cross-module synergy | High |
| P3 | Co-evolution | Advanced scenarios | High |

---

## Conclusion

The current `EvolutionEngine` is a **minimal proof-of-concept GA** suitable only for single-objective, single-dimensional, unconstrained optimization. It lacks virtually all features expected of a production-grade evolutionary computation framework. The most critical gaps are:

1. **Multi-dimensional chromosomes** — without this, the engine cannot optimize real hyperparameter vectors
2. **Multi-objective support** — without this, real-world trade-offs cannot be modeled
3. **Constraint handling** — without this, portfolio and pricing constraints cannot be enforced

These three gaps should be addressed before any other enhancements.
