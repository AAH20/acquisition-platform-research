# Wave 3: Risk Assessment Module Implementation

## Summary

Implemented the risk assessment module with TDD (tests first, then implementation).

## Files Created/Modified

- **Created**: `src/acquisition_platform/risk_assessment.py` — full module implementation
- **Created**: `tests/test_risk_assessment.py` — 10 tests covering all required scenarios

## Implementation Details

### Data Classes
- `RiskFactor`: name, score (0-10), weight (0-1), category
- `RiskAssessment`: factors list, total_score, risk_level, mitigations list

### RiskAssessor Class Methods
| Method | Description |
|--------|-------------|
| `assess_risk(name, score, weight, category)` | Creates validated RiskFactor |
| `total_score(factors)` | Weighted sum of factor scores; 0.0 for empty list |
| `risk_level(score)` | Classifies: low (<3), medium (<6), high (<8), critical (≥8) |
| `geographic_risk(country, region)` | Country risk table + region modifier, capped at 10 |
| `technology_risk(trl, complexity)` | TRL 1-9 inverted + complexity, weighted 60/40 |
| `financial_risk(leverage, liquidity)` | Leverage 60% + inverse liquidity 40% |
| `hr_risk(key_person_dependency, turnover)` | 50/50 weighted combination |
| `generate_mitigations(factors)` | Category-aware strategies for factors scoring ≥6 |
| `generate_report(factors)` | Full RiskAssessment with score, level, mitigations |
| `portfolio_risk(assessments)` | Aggregates multiple assessments into portfolio view |

### Validation
- Empty names/categories → `ValidationError`
- Out-of-range scores/weights/inputs → `InvalidRangeError`
- All scores clamped to [0, 10]

## Test Results

```
tests/test_risk_assessment.py ..........  [100%]
10 passed
```

Full suite: **874 passed, 1 failed** (pre-existing mypy failure in `swf_matching.py` and `post_merger.py`, unrelated to this module). Module is mypy-clean.
