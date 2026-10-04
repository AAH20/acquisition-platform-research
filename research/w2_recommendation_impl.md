# Wave 2: Recommendation Module Implementation

## Summary

Implemented `src/acquisition_platform/recommendation.py` — a hybrid recommendation engine combining collaborative filtering and content-based filtering with diversity-aware selection.

## Files Created/Modified

- **Created**: `src/acquisition_platform/recommendation.py` — full engine implementation
- **Created**: `tests/test_recommendation.py` — 14 tests covering all required scenarios

## Architecture

### Data Models (all `SerializableMixin`)
- `UserProfile`: user_id, preferences dict, history list
- `ItemProfile`: item_id, attributes dict, category
- `Recommendation`: item_id, score, reason
- `RecommendationResult`: recommendations list, diversity_score, coverage

### RecommendationEngine
- **Hybrid scoring**: `0.05 baseline + 0.55 * content_score + 0.40 * cf_score`
- **Content-based**: attribute match ratio between user preferences and item attributes
- **Collaborative filtering**: preference overlap with similar users (weighted Jaccard)
- **Diversity**: greedy selection penalizing over-represented categories (0.15 penalty per repeat)
- **Similarity metrics**: weighted overlap for user preferences, Jaccard for item attributes

## Test Results

```
tests/test_recommendation.py ..............  [100%]
14 passed

Full suite: 423 passed (excluding pre-existing broken test_auction_design.py)
```

## Key Design Decisions

1. **Baseline score (0.05)**: ensures every candidate has positive score, preventing zero-score recommendations
2. **Partial preference matching**: shared keys with different values get 0.3 weight (not 0), enabling discovery
3. **Diversity penalty**: 0.15 per category repeat in greedy selection, balancing relevance vs. variety
4. **History exclusion**: items in user history are filtered out before scoring

## Issues Encountered

- Pre-existing collection error in `tests/test_auction_design.py` (unrelated to this module)
- Initial cosine similarity was too strict for sparse preference dicts — replaced with weighted overlap
