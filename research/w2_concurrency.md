# Wave 2: Concurrency & Thread Safety Analysis

**Scope:** `src/acquisition_platform/*.py` (9 files)
**Date:** 2026-10-04

---

## 1. Module-by-Module Analysis

### 1.1 `__init__.py`
- **Shared mutable state:** None
- **Global variables:** None
- **Side effects:** None (imports only)
- **Thread-safe:** Yes
- **Locking:** N/A
- **Risks:** None

### 1.2 `portfolio_optimizer.py`
- **Shared mutable state:** None. `PortfolioOptimizer` stores `budget` and `max_assets` as instance attributes, but they are set once in `__init__` and never mutated.
- **Global variables:** None
- **Side effects:** None
- **Thread-safe:** Yes — `optimize()` uses only local variables (`affordable`, `selected`, `scored`, `remaining_budget`, etc.)
- **Locking:** None needed
- **Risks:** None

### 1.3 `entity_resolution.py`
- **Shared mutable state:** `EntityResolver.comparison_count` — instance attribute mutated in `resolve()` (line 169: `self.comparison_count = 0`, line 188: `self.comparison_count += 1`)
- **Global variables:** None
- **Side effects:** `resolve()` mutates `self.comparison_count`
- **Thread-safe:** **NO** — if two threads share one `EntityResolver` instance and call `resolve()` concurrently, they race on `self.comparison_count` (read-modify-write on line 188 is not atomic)
- **Locking:** None
- **Risks:**
  - **Race condition on `comparison_count`**: Concurrent calls to `resolve()` will corrupt the counter. The `_UnionFind` object is created locally per call, so the union-find structure itself is safe.
  - **Mitigation:** Use a `threading.Lock` around the counter increment, or make `comparison_count` a local variable returned as part of the result, or use `itertools.count` with a lock.

### 1.4 `valuation.py`
- **Shared mutable state:** None. `ValuationEngine` has no instance attributes.
- **Global variables:** None
- **Side effects:** None — all methods are pure functions
- **Thread-safe:** Yes
- **Locking:** None needed
- **Risks:** None

### 1.5 `evolution.py`
- **Shared mutable state:** None on the instance. `EvolutionEngine` stores config (`population_size`, `generations`, `mutation_rate`, `elitism`) set once in `__init__`.
- **Global variables:** **`random` module global state** — `evolve()` calls `random.uniform()`, `random.sample()`, `random.random()`, `random.gauss()` which all use the module-level `Random` instance.
- **Side effects:** `evolve()` reads from the global `random` state (advances the PRNG sequence)
- **Thread-safe:** **Mostly yes, with caveats.** Python's `random` module uses an internal lock, so individual calls are atomic. However:
  - Concurrent calls will serialize on the `random` module lock, creating contention.
  - The sequence of random numbers becomes non-deterministic across threads (not a correctness bug, but a reproducibility concern).
- **Locking:** None in module; `random` module has internal lock
- **Risks:**
  - **PRNG contention:** High-concurrency scenarios will bottleneck on the `random` module lock.
  - **Reproducibility:** Cannot reproduce evolution results if threads run concurrently.
  - **Mitigation:** Use a per-instance `random.Random()` instance instead of the global `random` module.

### 1.6 `matching.py`
- **Shared mutable state:** None. `BuyerSellerMatcher` has no instance attributes.
- **Global variables:** None
- **Side effects:** None — `match()` uses only local variables
- **Thread-safe:** Yes
- **Locking:** None needed
- **Risks:** None

### 1.7 `dynamic_pricing.py`
- **Shared mutable state:** None. `PricingEngine` has no instance attributes.
- **Global variables:** None
- **Side effects:** None — `recommend_price()` is a pure function
- **Thread-safe:** Yes
- **Locking:** None needed
- **Risks:** None

### 1.8 `fraud_detection.py`
- **Shared mutable state:** `FraudDetector.WEIGHTS`, `FraudDetector.DEFAULT_WEIGHT`, `FraudDetector.TOTAL_EXPECTED_SIGNALS` — class-level constants shared across all instances. **Read-only** — never mutated after class definition.
- **Global variables:** None
- **Side effects:** None — `score()` and `analyze_graph()` use only local variables
- **Thread-safe:** Yes — class constants are immutable in practice (dict is never modified after definition)
- **Locking:** None needed
- **Risks:**
  - **Theoretical:** If any code mutated `WEIGHTS` at runtime, it would affect all instances. Currently no code does this, but there's no enforcement (e.g., `MappingProxyType` or frozen dataclass).
  - **Mitigation:** Use `types.MappingProxyType` to make `WEIGHTS` truly immutable.

### 1.9 `search_ranking.py`
- **Shared mutable state:** None. `SearchRanker` has no instance attributes.
- **Global variables:** None
- **Side effects:** None — `rank()` uses only local variables
- **Thread-safe:** Yes
- **Locking:** None needed
- **Risks:** None

---

## 2. Summary Table

| Module | Shared Mutable State | Global Vars | Side Effects | Thread-Safe | Locking | Risk Level |
|---|---|---|---|---|---|---|
| `__init__.py` | None | None | None | ✅ Yes | N/A | None |
| `portfolio_optimizer.py` | None | None | None | ✅ Yes | None | None |
| `entity_resolution.py` | `comparison_count` (instance) | None | Mutates `self.comparison_count` | ❌ **No** | None | **Medium** |
| `valuation.py` | None | None | None | ✅ Yes | None | None |
| `evolution.py` | None (instance) | `random` module state | Advances global PRNG | ⚠️ Mostly | `random` internal | **Low-Medium** |
| `matching.py` | None | None | None | ✅ Yes | None | None |
| `dynamic_pricing.py` | None | None | None | ✅ Yes | None | None |
| `fraud_detection.py` | Class constants (read-only) | None | None | ✅ Yes | None | **Low** |
| `search_ranking.py` | None | None | None | ✅ Yes | None | None |

---

## 3. Concurrency Risks (Ranked)

### Risk 1: `EntityResolver.comparison_count` Race Condition (Medium)
- **File:** `entity_resolution.py:169,188`
- **Issue:** `self.comparison_count += 1` is a non-atomic read-modify-write. Two threads calling `resolve()` on the same instance will lose increments.
- **Impact:** Incorrect comparison count (cosmetic/diagnostic only — does not affect clustering correctness).
- **Fix:** Use `threading.Lock`, or return count as part of result, or use `itertools.count` with lock.

### Risk 2: `random` Module Contention in `EvolutionEngine` (Low-Medium)
- **File:** `evolution.py:111,152,155,163,165`
- **Issue:** Global `random` module state is shared across all threads. Python's `random` has an internal lock, so no data corruption, but concurrent access serializes and makes results non-reproducible.
- **Impact:** Performance bottleneck under high concurrency; non-deterministic evolution results.
- **Fix:** Create a per-instance `random.Random()` in `__init__` and use it throughout `evolve()`.

### Risk 3: `FraudDetector.WEIGHTS` Mutable Class Constant (Low)
- **File:** `fraud_detection.py:42-48`
- **Issue:** `WEIGHTS` is a plain dict on the class. Nothing currently mutates it, but nothing prevents it either.
- **Impact:** If any code path mutates `WEIGHTS`, it affects all `FraudDetector` instances process-wide.
- **Fix:** Wrap with `types.MappingProxyType` to enforce immutability.

---

## 4. Locking Mechanisms

**None found.** No module uses `threading.Lock`, `threading.RLock`, `threading.Semaphore`, `threading.Event`, or any other synchronization primitive.

---

## 5. Global Variables

| Module | Global Variable | Mutable? | Thread-Safe? |
|---|---|---|---|
| `evolution.py` | `random` module state | Yes (PRNG advances) | Yes (internal lock) |
| `fraud_detection.py` | `FraudDetector.WEIGHTS` (class var) | No (read-only) | Yes |
| `fraud_detection.py` | `FraudDetector.DEFAULT_WEIGHT` (class var) | No | Yes |
| `fraud_detection.py` | `FraudDetector.TOTAL_EXPECTED_SIGNALS` (class var) | No | Yes |

No module-level mutable global variables exist in any file.

---

## 6. Side Effects

| Module | Side Effect | Thread-Safe? |
|---|---|---|
| `entity_resolution.py` | Mutates `self.comparison_count` | ❌ No (race condition) |
| `evolution.py` | Advances global `random` PRNG state | ⚠️ Yes (with lock contention) |
| All others | None | ✅ Yes |

No file I/O, network calls, print statements, or other I/O side effects found in any module.

---

## 7. Recommendations

1. **`entity_resolution.py`:** Add a `threading.Lock` to `EntityResolver` and acquire it around `comparison_count` updates, or refactor to avoid shared mutable state entirely.
2. **`evolution.py`:** Replace global `random` with a per-instance `random.Random()` to eliminate contention and improve reproducibility.
3. **`fraud_detection.py`:** Make `WEIGHTS` immutable with `types.MappingProxyType` to prevent accidental mutation.
4. **General:** Consider adding a note to module docstrings about thread-safety guarantees for each class.
