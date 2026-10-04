# Wave 2 — Security Analysis Report

**Scope:** `acquisition-platform-research/src/acquisition_platform/` (8 modules) + `optional-skills/research/osint-investigation/scripts/entity_resolution.py`
**Date:** 2026-10-04
**Analyst:** Wave 1 Security Research Agent

---

## Executive Summary

The acquisition platform codebase is a **pure-computation library** with no I/O, no database, no network calls, and no external service integration. This dramatically reduces the attack surface. No hardcoded secrets, no SQL injection vectors, no path traversal risks, and no rate-limiting concerns were found. The primary security considerations are **input validation robustness** and **algorithmic complexity DoS** in the fraud detection and entity resolution modules.

---

## 1. Hardcoded Secrets / Credentials

**Status: ✅ CLEAN**

| Check | Result |
|---|---|
| `password`, `secret`, `token`, `api_key`, `credential`, `apikey`, `access_key` in source | **0 matches** |
| `.env` files in project | None present |
| Hardcoded connection strings | None |
| Private keys or certificates | None |

The codebase contains no authentication logic, no API clients, and no credential management. All modules are pure computational functions operating on in-memory data structures.

---

## 2. Input Validation in Public Methods

**Status: ⚠️ MODERATE CONCERNS**

### 2.1 `fraud_detection.py` — `FraudDetector.score()`

| Issue | Severity | Detail |
|---|---|---|
| No type validation on `signals` | Low | If a non-list is passed, `if not signals` catches `None`/empty but not non-iterables (would raise `TypeError`) |
| No range validation on `FraudSignal.value` | Medium | Values outside `[0.0, 1.0]` are accepted. A value of `2.0` produces `fraud_value = -1.0`, which can skew scores negatively. A value of `-5.0` produces `fraud_value = 6.0`, inflating scores. |
| No validation on `signal.name` | Low | Arbitrary strings accepted; unknown names get `DEFAULT_WEIGHT = 0.1` — graceful but could mask bugs |
| Empty list handling | ✅ Good | Returns `FraudScore(score=0.0, risk_level="low", confidence=0.0)` with explanation |

### 2.2 `fraud_detection.py` — `FraudDetector.analyze_graph()`

| Issue | Severity | Detail |
|---|---|---|
| No validation on `graph` structure | Medium | `graph.get("nodes", [])` and `graph.get("edges", [])` — if `graph` is `None`, raises `AttributeError`. If `nodes` is not iterable, raises `TypeError`. |
| No validation on edge tuples | Medium | Edges are unpacked as `for src, dst in edges` — a malformed edge (e.g., single element) raises `ValueError` |
| No node type validation | Low | Nodes are used as dict keys; unhashable types (lists, dicts) would raise `TypeError` |
| Duplicate edges | ✅ Handled | `adjacency[src].add(dst)` — set semantics handle duplicates |
| Self-loops | ✅ Harmless | `adjacency[node].add(node)` — doesn't create false cycle detection |

### 2.3 `entity_resolution.py` — `EntityResolver.resolve()`

| Issue | Severity | Detail |
|---|---|---|
| No validation on `entities` | Medium | If `entities` is `None`, `if not entities` catches it. If non-list iterable, may work but undocumented. |
| No validation on entity dict structure | Medium | `e.get("name", "")` — if `e` is not a dict, raises `AttributeError`. If `name` is not a string, `_normalize()` may fail. |
| No validation on `threshold` | Medium | `threshold` is stored but not validated. A negative threshold matches everything; a threshold > 1.0 matches nothing. |
| Empty entity list | ✅ Good | Returns `[]` |
| Missing `name` key | ✅ Good | Defaults to `""` via `.get("name", "")` |
| Missing `domain` key | ✅ Good | Defaults to `""` via `.get("domain", "")` |

### 2.4 `dynamic_pricing.py` — `PricingEngine.recommend_price()`

| Issue | Severity | Detail |
|---|---|---|
| No range validation on `demand_level` / `competition_level` | Medium | Docstring says "normalized in [0, 1]" but no enforcement. Values outside range produce extreme multipliers. |
| No validation on `market_condition` | ✅ Good | Uses `.get(market_condition, 1.0)` — unknown values default to neutral multiplier |
| No validation on `base_value` | Low | Negative values produce negative prices — mathematically valid but semantically questionable |

### 2.5 `matching.py` — `BuyerSellerMatcher.match()`

| Issue | Severity | Detail |
|---|---|---|
| No validation on buyer/seller lists | Low | Empty lists return `[]` — handled |
| No validation on `budget` / `asking_price` | Medium | Negative budgets: `_compute_score` returns `0.0` for `budget <= 0` — handled. Negative asking prices: produce scores > 1.0, clamped to 1.0 — handled. |
| No validation on preference/attribute dicts | Low | `.get("category")` returns `None` for missing keys — `None != None` is `False`, so two entities with no category match — **potential bug** |

### 2.6 `valuation.py` — All methods

| Issue | Severity | Detail |
|---|---|---|
| No validation on numeric inputs | Medium | `dcf_valuation`: `discount_rate == terminal_growth` causes `ZeroDivisionError`. Negative `years` produces empty loop (returns 0 value). |
| No validation on `years` | Medium | `range(1, years + 1)` — `years=0` returns value=0; negative `years` also returns value=0 (loop doesn't execute) |

### 2.7 `search_ranking.py` — `SearchRanker.rank()`

| Issue | Severity | Detail |
|---|---|---|
| No validation on `query` | Low | `query` is accepted but **never used** in scoring — dead parameter |
| No validation on `listings` | Low | Empty list returns `[]` — handled |
| No validation on `Listing.relevance` | Medium | Negative relevance produces negative scores; no clamping |

### 2.8 `portfolio_optimizer.py` — `PortfolioOptimizer.optimize()`

| Issue | Severity | Detail |
|---|---|---|
| No validation on `risk_tolerance` | Medium | Docstring says "0-1" but no enforcement. Negative values invert the risk adjustment. |
| No validation on `budget` | Low | Negative budget: `affordable` list is empty, returns empty `Portfolio` — handled |
| Division by zero | ✅ Good | `asset.risk + 0.01` prevents division by zero |

### 2.9 `evolution.py` — `EvolutionEngine.evolve()`

| Issue | Severity | Detail |
|---|---|---|
| No validation on `fitness_fn` | Medium | If `fitness_fn` is not callable, raises `TypeError` at first evaluation |
| No validation on `gene_range` | Medium | If `low > high`, `random.uniform` still works but produces inverted range; clamping still works |
| No validation on constructor params | Low | `population_size=0` causes division by zero in tournament selection (`random.sample(range(0), 2)` raises `ValueError`) |

---

## 3. SQL Injection Risks

**Status: ✅ NO RISK**

The codebase contains **zero database interaction**. No SQL queries, no ORM usage, no database drivers imported. All data is processed in-memory using Python data structures.

---

## 4. Path Traversal Risks

**Status: ✅ NO RISK (in acquisition-platform)**

The `acquisition_platform` source modules contain **no file I/O operations**. No `open()`, `Path()`, `os.path`, `shutil`, or any filesystem access.

**Note:** The `optional-skills/research/osint-investigation/scripts/entity_resolution.py` does use `open()` for CSV reading/writing, but:
- Paths are provided via CLI arguments (not user-supplied at runtime)
- No path sanitization is performed, but the script is a standalone CLI tool, not a web service
- Risk is minimal in the intended usage context

---

## 5. Rate Limiting for API Methods

**Status: ✅ NOT APPLICABLE**

The codebase is a **library, not a service**. There are no HTTP endpoints, no API routes, no network listeners. All methods are synchronous Python function calls. Rate limiting would be the responsibility of any application that wraps these modules in an API.

**Consideration for future API wrapping:** If these modules are exposed via REST/gRPC, the following methods should have rate limits:
- `FraudDetector.analyze_graph()` — O(n³) complexity, could be abused for DoS
- `EntityResolver.resolve()` — O(n²) within blocks, could be abused with large inputs
- `BuyerSellerMatcher.match()` — O(n*m) pair generation

---

## 6. Fraud Detection Edge Case Security

### 6.1 Algorithmic Complexity DoS

| Method | Complexity | Risk |
|---|---|---|
| `score()` | O(n) where n = len(signals) | **Low** — linear, safe |
| `analyze_graph()` | O(n³) for 3-cycle detection, O(n⁴) for 4-cycle detection | **HIGH** — a graph with 10,000 nodes would require ~10¹² operations |
| `_has_cycle_of_length_3_or_4()` | O(n × d²) where d = max degree | **Medium** — depends on graph density |

**Recommendation:** Add a node/edge count limit before graph analysis:
```python
MAX_GRAPH_NODES = 1000
MAX_GRAPH_EDGES = 5000
```

### 6.2 Edge Cases

| Edge Case | Behavior | Security Impact |
|---|---|---|
| `signals=None` | `AttributeError` | DoS via unhandled exception |
| `signals` contains non-FraudSignal objects | `AttributeError` on `.name`/`.value` | DoS via unhandled exception |
| `FraudSignal.value = float('nan')` | `fraud_value = 1.0 - nan = nan`; `max(0.0, min(1.0, nan))` = `nan` | **Score poisoning** — NaN propagates |
| `FraudSignal.value = float('inf')` | `fraud_value = -inf`; clamped to 0.0 | Score manipulation |
| `graph=None` | `AttributeError` | DoS |
| `graph` with 1 node, no edges | Returns `has_ring=False` | ✅ Correct |
| `graph` with 2 nodes, 1 edge | Returns `has_ring=False` | ✅ Correct |
| `graph` with self-loop `("a","a")` | `adjacency["a"].add("a")` — doesn't create false positive | ✅ Correct |
| Very large `nodes` list with duplicate entries | `adjacency` dict deduplicates; `node_set` deduplicates | ✅ Correct but wasteful |
| `edges` referencing unknown nodes | `if src in adjacency and dst in adjacency` — silently ignored | ✅ Correct |

### 6.3 Scoring Manipulation

The `score()` method uses `max(0.0, min(1.0, score))` for clamping, which is good. However:
- NaN values bypass clamping (`min(1.0, nan)` returns `nan` in Python)
- The confidence calculation `1.0 - (missing / TOTAL_EXPECTED_SIGNALS)` can go negative if `len(signals) > TOTAL_EXPECTED_SIGNALS` (3), but `missing = max(0, ...)` prevents this — ✅ correct

---

## 7. Entity Resolution Malicious Input Handling

### 7.1 Input Validation Gaps

| Input | Validation | Risk |
|---|---|---|
| `entities` list | Only `if not entities` check | Medium — non-list iterables may cause issues |
| Entity dict structure | No schema validation | Medium — non-dict elements cause `AttributeError` |
| `name` field type | No type check | Medium — non-string names may cause `TypeError` in `_normalize()` |
| `domain` field type | No type check | Low — only used for equality comparison |
| `threshold` | No range validation | Medium — negative threshold matches all pairs |
| Very large input | No size limit | **HIGH** — O(n²) within blocks |

### 7.2 Algorithmic Complexity

| Scenario | Complexity | Risk |
|---|---|---|
| All entities share first 3 chars | O(n²) comparisons | **HIGH** — 10,000 entities → 50M comparisons |
| Entities with empty names | Blocked (empty string key) | ✅ Handled |
| Entities with very long names | `_jaro_winkler` is O(len²) | Medium — 10KB names → 100M char comparisons |
| Unicode names | `re.sub(r"[^\w\s]", "", ...)` — `\w` matches Unicode | ✅ Correct |
| Null bytes in names | No sanitization | Low — Python handles null bytes in strings |

### 7.3 Blocking Key Collision

The blocking strategy uses `norm[:3]` (first 3 characters). An attacker could craft entities with names sharing the same first 3 characters to force O(n²) comparisons:

```python
# Adversarial input: 10,000 entities all starting with "aaa"
entities = [{"name": f"aaa_{i}", "domain": ""} for i in range(10000)]
# All fall into block "aaa" → 50,000,000 comparisons
```

**Recommendation:** Add a maximum input size limit and consider secondary blocking keys.

### 7.4 `_jaro_winkler` Edge Cases

| Edge Case | Behavior |
|---|---|
| Both strings empty | Returns `0.0` (early return) — ✅ |
| One string empty | Returns `0.0` — ✅ |
| Identical strings | Returns `1.0` — ✅ |
| `match_window = 0` (short strings) | Only exact position matches — ✅ |
| Very long strings | O(len²) time and O(len) space — Medium risk |

---

## 8. Additional Security Observations

### 8.1 No Dangerous Patterns Found

| Pattern | Found |
|---|---|
| `eval()` / `exec()` | ❌ No |
| `__import__()` | ❌ No |
| `compile()` | ❌ No |
| `pickle` / `marshal` | ❌ No |
| `subprocess` / `os.system` | ❌ No |
| `shell=True` | ❌ No |
| `yaml.load` (unsafe) | ❌ No |
| `assert` in production code | ❌ No |

### 8.2 Dependency Security

The project has no `requirements.txt` or `pyproject.toml` dependencies in the source directory. The `.venv-test` directory contains only `pip` internals. No third-party dependencies to audit.

### 8.3 Information Disclosure

No logging of sensitive data, no debug endpoints, no stack trace exposure. The codebase is a library, so information disclosure would depend on the calling application.

---

## 9. Recommendations Summary

| Priority | Recommendation | Module |
|---|---|---|
| **HIGH** | Add input size limits to `analyze_graph()` and `resolve()` | `fraud_detection.py`, `entity_resolution.py` |
| **HIGH** | Validate `FraudSignal.value` is in `[0.0, 1.0]` | `fraud_detection.py` |
| **HIGH** | Handle `NaN` / `Inf` in signal values | `fraud_detection.py` |
| **MEDIUM** | Validate `graph` is a dict with expected keys | `fraud_detection.py` |
| **MEDIUM** | Validate `entities` is a list of dicts | `entity_resolution.py` |
| **MEDIUM** | Validate `threshold` is in `[0.0, 1.0]` | `entity_resolution.py` |
| **MEDIUM** | Add `discount_rate != terminal_growth` check | `valuation.py` |
| **MEDIUM** | Validate `demand_level` / `competition_level` in `[0, 1]` | `dynamic_pricing.py` |
| **MEDIUM** | Validate `risk_tolerance` in `[0, 1]` | `portfolio_optimizer.py` |
| **LOW** | Add `population_size >= 2` check in constructor | `evolution.py` |
| **LOW** | Remove or use `query` parameter in `rank()` | `search_ranking.py` |
| **LOW** | Add `Listing.relevance` range validation | `search_ranking.py` |

---

## 10. Risk Matrix

| Threat | Likelihood | Impact | Overall |
|---|---|---|---|
| Algorithmic DoS via large graph | Medium | High | **High** |
| Algorithmic DoS via blocking collision | Medium | High | **High** |
| Input validation bypass | Medium | Medium | **Medium** |
| NaN/Inf score poisoning | Low | Medium | **Medium** |
| SQL injection | None | — | **None** |
| Path traversal | None | — | **None** |
| Hardcoded credentials | None | — | **None** |
| Remote code execution | None | — | **None** |

---

## Conclusion

The acquisition platform codebase is **fundamentally secure** due to its pure-computation nature. The absence of I/O, database, network, and dependency surface eliminates most common attack vectors. The primary security concerns are:

1. **Algorithmic complexity DoS** — `analyze_graph()` and `resolve()` can be abused with crafted inputs
2. **Input validation gaps** — numeric range validation is missing across multiple modules
3. **NaN/Inf handling** — special float values can bypass clamping logic

These are **defense-in-depth** concerns, not critical vulnerabilities. The codebase is safe for its intended use as a computational library. If wrapped in a service API, the recommendations above should be implemented as a security boundary.
