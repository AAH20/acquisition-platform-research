# Module: `entity_resolution.py`

## Purpose

Entity resolution (deduplication) using Jaro-Winkler similarity with union-find clustering and blocking for scalable performance.

## Responsibilities

- Normalize entity names (lowercase, strip punctuation)
- Block entities by first 3 characters of normalized name
- Compare pairs using Jaro-Winkler similarity + domain match bonus
- Cluster similar entities using union-find
- Select canonical name (most frequent, first wins ties)

## Key Files

- [`src/acquisition_platform/entity_resolution.py`](../../../src/acquisition_platform/entity_resolution.py) — 226 lines

## Public API

### `EntityCluster`

```python
@dataclass
class EntityCluster:
    entities: list[dict]
    canonical_name: str
```

### `EntityResolver`

```python
class EntityResolver:
    def __init__(self, threshold: float = 0.85) -> None
    def resolve(self, entities: list[dict]) -> list[EntityCluster]
    comparison_count: int  # number of pairwise comparisons made
```

## Algorithm

1. **Normalize** — Lowercase, strip punctuation
2. **Block** — Group by first 3 characters of normalized name
3. **Compare** — Jaro-Winkler similarity + 0.2 domain match bonus
4. **Cluster** — Union-find with path compression
5. **Canonical name** — Most frequent name (first wins ties)

**Complexity:** O(n²) worst case, O(Σ block_size²) with blocking.

## Jaro-Winkler

Implemented from scratch:
- **Jaro similarity** — Based on matching characters and transpositions
- **Winkler adjustment** — Prefix bonus: `jw = jaro + prefix_len * 0.1 * (1 - jaro)`
- **Domain bonus** — +0.2 if domains match (capped at 1.0)

## Dependencies

- **Used by:** All modules (entity deduplication)
- **Uses:** Nothing (standalone module)

## Tests

8 tests in [`tests/test_entity_resolution.py`](../../../tests/test_entity_resolution.py):
- Empty input, single entity, exact match, different entities, fuzzy match, domain boost, canonical name, blocking efficiency
