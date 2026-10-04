# Wave 2: Data Export & Import Implementation

## Summary

Added comprehensive data export and import capabilities to the acquisition platform, following TDD (tests first, then implementation).

## What Was Done

### 1. Created `src/acquisition_platform/data_io.py`

New module with 7 functions:

| Function | Description |
|----------|-------------|
| `export_to_json(data, path)` | Serialize any JSON-serializable object to a file |
| `import_from_json(path)` | Deserialize JSON from a file |
| `export_to_csv(data, path)` | Export list of dicts to CSV (union of keys as header) |
| `import_from_csv(path)` | Import CSV as list of dicts |
| `export_to_yaml(data, path)` | Serialize to YAML format |
| `import_from_yaml(path)` | Deserialize YAML from a file |
| `validate_schema(data, schema)` | Validate dict against a type schema |

All functions raise `FileNotFoundError` for missing inputs and `OSError` for unwritable paths.

### 2. Added Export/Import Methods to Key Modules

- **EntityResolver**: `export_clusters(clusters, path)`, `import_entities(path)`
- **BuyerSellerMatcher**: `export_matches(matches, path)`, `import_buyers_sellers(path)`
- **ValuationEngine**: `export_valuations(valuations, path)`, `import_financials(path)`

All methods use the `data_io` module internally and leverage the existing `SerializableMixin` for dataclass serialization.

### 3. Created `tests/test_data_io.py`

33 tests covering:
- JSON export/import roundtrip (dict, list, nested structures)
- CSV export/import (roundtrip, empty list, type checking)
- YAML export/import (roundtrip, nested structures)
- Schema validation (valid data, missing fields, wrong types, extra fields)
- Invalid file handling (nonexistent files, corrupted JSON/YAML, invalid paths)
- EntityResolver export/import roundtrip
- BuyerSellerMatcher export/import roundtrip
- ValuationEngine export/import roundtrip

## Test Results

### data_io tests: **33/33 passed**

```
tests/test_data_io.py .................................  [100%]
============================== 33 passed in 0.35s ==============================
```

### Full suite: **564 passed, 19 failed, 15 errors**

All 33 data_io tests pass. The 19 failures + 15 errors are **pre-existing** in other test files:
- `test_batch.py` — 11 failures (batch processing)
- `test_caching.py` — 3 failures (cache hit/miss)
- `test_security.py` — 2 failures (input sanitizer)
- `test_type_safety.py` — 1 failure (mypy compliance)
- `test_valuation.py` — 1 failure (DCF caching)
- `test_benchmarks.py` — 15 errors (benchmark fixture issues)
- `test_property_based.py` — collection error (hypothesis API change)

None of these failures are related to the data_io changes.

## Files Created/Modified

| File | Action |
|------|--------|
| `src/acquisition_platform/data_io.py` | **Created** — 7 export/import/validation functions |
| `src/acquisition_platform/entity_resolution.py` | **Modified** — added `export_clusters`, `import_entities` |
| `src/acquisition_platform/matching.py` | **Modified** — added `export_matches`, `import_buyers_sellers` |
| `src/acquisition_platform/valuation.py` | **Modified** — added `export_valuations`, `import_financials` |
| `tests/test_data_io.py` | **Created** — 33 tests |

## Dependencies

- `pyyaml` was already available in the test venv (installed via pip during development)
- No other new dependencies required

## Design Decisions

- **CSV export**: Uses union of all dict keys as header; missing keys written as empty strings
- **Schema validation**: Extra fields in data are allowed (only schema-specified fields are checked)
- **Error handling**: All import functions raise `FileNotFoundError` for missing files; export functions raise `OSError` for unwritable paths
- **Serialization**: Leverages existing `SerializableMixin.to_dict()`/`from_dict()` for dataclass conversion
