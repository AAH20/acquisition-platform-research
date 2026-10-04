# Wave 2: pyproject.toml Update Summary

## Changes Made

### 1. Fixed build backend
- **Before:** `setuptools.backends._legacy:_Backend` (invalid, causes `BackendUnavailable`)
- **After:** `setuptools.build_meta` (standard PEP 517 backend)

### 2. Added `[project.scripts]`
```toml
[project.scripts]
acquisition-platform = "acquisition_platform.__main__:main"
```
Entry point for the CLI defined in `src/acquisition_platform/__main__.py`.

### 3. Added dev dependencies
- `pytest-benchmark>=4.0,<5` — benchmark test support
- `hypothesis>=6.0,<7` — property-based testing

### 4. Verified existing config
- `[tool.pytest.ini_options]` — correct (`testpaths`, `pythonpath`, `addopts`)
- `[tool.mypy]` — strict mode already present (`strict = true`, `warn_return_any`, `warn_unused_configs`)

## Verification

### `pip install -e '.[dev]'`
- **Status:** SUCCESS
- Installed: `acquisition-platform-0.1.0`, `py-cpuinfo-9.0.0`, `pytest-benchmark-4.0.0`
- All dev dependencies resolved and installed cleanly.

### `python -m pytest tests/ -q --tb=no`
- **Status:** 335 tests collected, 3 collection errors (pre-existing)
- **Errors:** Missing source modules `acquisition_platform.auction_design` and `acquisition_platform.due_diligence` — these are source code gaps, not pyproject.toml issues.
- **Affected test files:** `test_auction_design.py`, `test_cli.py`, `test_due_diligence.py`
- **Root cause:** `src/acquisition_platform/__init__.py` imports from modules that don't exist yet.

## Files Modified
- `pyproject.toml` — build backend fix, `[project.scripts]`, dev dependencies

## Issues Encountered
1. **Invalid build backend** — `setuptools.backends._legacy:_Backend` is not a valid setuptools backend. Fixed to `setuptools.build_meta`.
2. **Pre-existing test collection errors** — 3 test files fail to import due to missing source modules. Not caused by pyproject.toml changes.
