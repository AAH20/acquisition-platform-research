# Wave 2 — CLI Entry Point Implementation

**Date:** 2026-10-04
**Agent:** Wave 2 Implementation Agent — CLI entry point
**Project:** `acquisition-platform-research`

---

## Outcome

Implemented a full argparse-based CLI for the acquisition platform, exposed both as
`python -m acquisition_platform` and as the installed `acquisition-platform` console
script. TDD was followed: the test file was written first (RED), then the
implementation (GREEN), then ruff-cleanup.

**Isolated verification: 92 passed** (62 original module tests + 30 new CLI tests).

---

## Files Created / Modified

| File | Status | Notes |
|------|--------|-------|
| `src/acquisition_platform/__main__.py` | **created** | Full CLI: parser, handlers, JSON I/O, config store |
| `tests/test_cli.py` | **created** | 30 TDD tests (valid input, error handling, help) |
| `pyproject.toml` | **modified** | Added `[project.scripts]` entry |

### pyproject.toml change

```toml
[project.scripts]
acquisition-platform = "acquisition_platform.__main__:main"
```

Verified: `pip install -e .` creates the `acquisition-platform` executable and it runs.

---

## Commands Implemented

All ten required commands are wired to the existing solver modules:

| Command | Solver | Input |
|---------|--------|-------|
| `acq match --buyers-file --sellers-file` | `BuyerSellerMatcher` | JSON files |
| `acq value --fcf --revenue --growth --discount --terminal-growth --multiple --years` | `ValuationEngine` | flags |
| `acq fraud-check --signals` | `FraudDetector` | inline JSON |
| `acq optimize --budget --max-assets --assets-file` | `PortfolioOptimizer` | JSON file |
| `acq price --base-value --demand --competition --market` | `PricingEngine` | flags |
| `acq resolve --entities-file` | `EntityResolver` | JSON file |
| `acq rank --query --listings-file` | `SearchRanker` | JSON file |
| `acq evolve --fitness-fn --gene-range` | `EvolutionEngine` | flags |
| `acq benchmark --name --target --actual` | `Benchmark` | flags |
| `acq config show` / `acq config set <key> <value>` | built-in config store | flags |

### Design decisions

- **JSON to stdout always.** Every command emits a stable JSON object so results
  compose in shell pipelines and CI. `sort_keys=True` for deterministic output.
- **Exit codes:** `0` success, `1` handled error (message prefixed `error:` on stderr),
  `2` argparse usage error.
- **`value` dispatch:** `--fcf` alone → DCF; `--revenue` + `--multiple` alone → Comps;
  all together → Ensemble. Partial combinations raise a clear `error:`.
- **`fraud-check --signals`** accepts a JSON array of `[name, value]` pairs or
  `{name, value}` objects.
- **`evolve --fitness-fn`** compiles a Python expression in `x` with a restricted
  namespace (math funcs + abs/min/max, `__builtins__` disabled), raising a handled
  error on bad syntax/eval. `--seed` gives reproducible runs.
- **Config store:** `DEFAULT_CONFIG` schema, deep-merged with a JSON file at
  `--config`, `$ACQ_CONFIG`, or `~/.acq/config.json`. `config set` rejects unknown
  dotted keys.
- **`--market`** validated in the handler (not argparse `choices`) so invalid values
  return exit code 1 with an `error:` message, consistent with other input errors.

---

## Test Coverage (`tests/test_cli.py`, 30 tests)

- **Help output:** top-level lists all commands; subcommand help; no-command → exit 2.
- **Valid input:** one or more tests per command, asserting parsed JSON fields.
- **Error handling:** missing files, invalid JSON, bad signal shape, invalid market,
  bad fitness expression, inverted gene range, unknown config key, missing
  `--fcf` argument combinations.
- **Config round-trip:** `config set` then `config show` reflects the new value.

---

## Verification

```
# Isolated clean HEAD baseline + my two new files:
$ python -m pytest tests/ -q
92 passed in 0.31s

# Entry point install + run:
$ pip install -e .
$ acquisition-platform benchmark --name test --target 1.0 --actual 1.5   # exit 0, JSON out

# python -m:
$ python -m acquisition_platform --help          # exit 0
$ python -m acquisition_platform value --fcf 100000 --growth 0.05 \
    --discount 0.10 --terminal-growth 0.02 --years 5
{"confidence": 0.7, "method": "DCF", "value": 1446211.89, ...}

# Lint:
$ ruff check src/acquisition_platform/__main__.py tests/test_cli.py
All checks passed!
```

---

## Issue: Concurrent-Agent Interference (not my footprint)

The **shared working tree is being edited concurrently by other Wave 2 agents**, so the
live `tests/` directory is not runnable as a whole right now. Observed transient breakage
introduced by other agents while I worked:

- `tests/test_type_safety.py` — syntax error (`ranker rank(...)`) → collection error.
- `tests/test_serialization.py` — collection error.
- `tests/test_config.py` — imports `acquisition_platform.config` (not yet implemented).
- `tests/test_validation.py` — 30+ failures expecting a not-yet-landed validation layer.
- `src/acquisition_platform/valuation.py` — `@lru_cache` missing import, then fixed.
- `src/acquisition_platform/fraud_detection.py` — stray import mid-file → SyntaxError.
- `src/acquisition_platform/matching.py` — optimization refactor broke 1 matching test.

**None of these files were created or modified by this task.** My exact footprint is:
`src/acquisition_platform/__main__.py` (new), `tests/test_cli.py` (new),
`pyproject.toml` (scripts entry only).

To verify my work without the moving target, I extracted the clean `HEAD` baseline
(`git archive HEAD` → `/tmp/acq_baseline`), copied in only my two new files, and ran the
full suite there: **92 passed**. That is the authoritative result for this task.

The baseline at `HEAD` before any Wave 2 edits was 62 passing; my additions bring it to
92 passing with zero regressions.

---

## Follow-ups (owned by other agents)

- Resolve the live-tree syntax/import errors in `fraud_detection.py`, `valuation.py`.
- Land the validation layer so `test_validation.py` passes, or mark it xfail until then.
- Fix the `test_type_safety.py` syntax error and the `test_config.py` missing module
  (the latter depends on a `config` module that the CLI's config store currently
  implements internally in `__main__.py`).

*End of report.*
