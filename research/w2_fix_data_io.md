# Wave 2 Fix: test_data_io.py

## Summary

Fixed 9 failing tests in `tests/test_data_io.py` by adding 6 missing methods to 3 source modules.

## Changes

### `src/acquisition_platform/entity_resolution.py`
- Added `export_clusters(clusters, path)` — serializes `EntityCluster` objects to JSON
- Added `import_entities(path)` — deserializes entity list from JSON

### `src/acquisition_platform/matching.py`
- Added `export_matches(matches, path)` — serializes `Match` objects to JSON
- Added `import_buyers_sellers(path)` — deserializes buyers/sellers from JSON, returns `(list[Buyer], list[Seller])`

### `src/acquisition_platform/valuation.py`
- Added `export_valuations(results, path)` — serializes `ValuationResult` objects to JSON
- Added `import_financials(path)` — deserializes financial parameters from JSON

## Results

- `tests/test_data_io.py`: **33 passed** (was 24 passed, 9 failed)
- Full suite: **all passing**
