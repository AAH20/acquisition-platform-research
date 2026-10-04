# Module: `search_ranking.py`

## Purpose

Search ranking engine using submodular maximization with diversity and personalization factors.

## Responsibilities

- Rank listings by relevance, diversity, and personalization
- Deduplicate results by listing ID
- Apply diversity penalty for repeated categories
- Boost preferred categories based on user preferences

## Key Files

- [`src/acquisition_platform/search_ranking.py`](../../../src/acquisition_platform/search_ranking.py) — 103 lines

## Public API

### `Listing`

```python
@dataclass
class Listing:
    id: str
    title: str
    relevance: float
    category: str = ""
```

### `RankedListing`

```python
@dataclass
class RankedListing:
    id: str
    title: str
    score: float
    category: str
```

### `SearchRanker`

```python
class SearchRanker:
    def rank(self, query: str, listings: list[Listing],
             user_preferences: dict | None = None) -> list[RankedListing]
```

## Scoring Formula

```
score = relevance × diversity_factor × personalization_factor
```

| Factor | Value |
|--------|-------|
| Diversity (first category) | 1.0 |
| Diversity (subsequent) | 0.7 |
| Personalization (preferred) | 1.3 |
| Personalization (other) | 1.0 |

## Dependencies

- **Used by:** Recommendation system
- **Uses:** Nothing (standalone module)

## Tests

7 tests in [`tests/test_search_ranking.py`](../../../tests/test_search_ranking.py):
- Empty query, single listing, relevance ordering, diversity penalty, personalization, deduplication
