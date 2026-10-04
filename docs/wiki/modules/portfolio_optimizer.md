# Module: `portfolio_optimizer.py`

## Purpose

Greedy MIQP (Mixed Integer Quadratic Program) solver for acquisition portfolio optimization with risk-adjusted return scoring and diversification bonuses.

## Responsibilities

- Select optimal portfolio of acquisition targets within budget
- Respect cardinality constraints (max number of assets)
- Apply diversification bonuses for sector diversity
- Compute portfolio expected return and Sharpe ratio

## Key Files

- [`src/acquisition_platform/portfolio_optimizer.py`](../../../src/acquisition_platform/portfolio_optimizer.py) — 119 lines

## Public API

### `Asset`

```python
@dataclass
class Asset:
    id: str
    cost: float
    expected_return: float
    risk: float
    sector: str = ""
```

### `Portfolio`

```python
@dataclass
class Portfolio:
    assets: list[Asset]
    expected_return: float
    sharpe_ratio: float
```

### `PortfolioOptimizer`

```python
class PortfolioOptimizer:
    def __init__(self, budget: float, max_assets: int = 10) -> None
    def optimize(self, assets: list[Asset], risk_tolerance: float) -> Portfolio
```

## Algorithm

1. **Filter** assets within budget
2. **Score** each asset: `(expected_return / (risk + 0.01)) * (1 + risk_tolerance)`
3. **Sort** by score descending
4. **Greedy selection** with diversification bonus (1.5× for new sector, 1.0× for existing)
5. **Compute metrics:** weighted expected return, Sharpe ratio

**Complexity:** O(n log n) greedy selection vs O(C(n,K)) exhaustive search.

## Dependencies

- **Used by:** Evolution framework
- **Uses:** Valuation engine (for expected returns)

## Tests

7 tests in [`tests/test_portfolio_optimizer.py`](../../../tests/test_portfolio_optimizer.py):
- Empty portfolio, single asset, budget constraint, risk tolerance, cardinality, diversification, Sharpe ratio
