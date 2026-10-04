# Module: `fraud_detection.py`

## Purpose

Detects fraudulent listings using weighted signal scoring and graph-based fraud ring detection.

## Responsibilities

- Score listings based on identity verification, financial consistency, and traffic authenticity
- Detect fraud rings through cycle detection in relationship graphs
- Provide risk levels (low/medium/high) with confidence scores

## Key Files

- [`src/acquisition_platform/fraud_detection.py`](../../../src/acquisition_platform/fraud_detection.py) — 172 lines

## Public API

### `FraudSignal`

```python
@dataclass
class FraudSignal:
    name: str
    value: float
```

### `FraudScore`

```python
@dataclass
class FraudScore:
    score: float
    risk_level: str
    confidence: float
    explanations: list[str]
```

### `FraudDetector`

```python
class FraudDetector:
    WEIGHTS: dict[str, float] = {
        "identity_verified": 0.3,
        "financial_consistency": 0.3,
        "traffic_authenticity": 0.2,
    }
    DEFAULT_WEIGHT: float = 0.1
    TOTAL_EXPECTED_SIGNALS: int = 3

    def score(self, signals: list[FraudSignal]) -> FraudScore
    def analyze_graph(self, graph: dict) -> GraphAnalysis
```

## Scoring

- **Weighted average** of inverted signal values (high signal = low fraud risk)
- **Risk levels:** score < 0.3 = low, 0.3-0.7 = medium, > 0.7 = high
- **Confidence:** `1 - (missing_signals / 3)`

## Graph Analysis

Detects 3-cycles and 4-cycles in relationship graphs. If a ring is found:
- `has_ring = True`
- `risk_score = 0.8`
- `risk_level = "high"`

## Dependencies

- **Used by:** Matching, recommendation system
- **Uses:** Nothing (standalone module)

## Tests

7 tests in [`tests/test_fraud_detection.py`](../../../tests/test_fraud_detection.py):
- Clean/suspicious/mixed signals, explanations, missing signals, graph rings, real-time performance
