# Getting Started

## Prerequisites

- Python 3.10+
- pip
- git

## Installation

```bash
# Clone the repository
git clone https://github.com/AAH20/acquisition-platform-research.git
cd acquisition-platform-research

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install with dev dependencies
pip install -e ".[dev]"
```

## First Run

```bash
# Run all tests (62 tests across 8 modules)
pytest tests/ -v

# Expected output: 62 passed
```

## Common Workflows

### Match Buyers to Sellers

```python
from acquisition_platform import Buyer, Seller, BuyerSellerMatcher

matcher = BuyerSellerMatcher()
matches = matcher.match(
    [Buyer(id="b1", budget=100000, preferences={"category": "saas"})],
    [Seller(id="s1", asking_price=80000, attributes={"category": "saas"})],
)
```

### Value a Business

```python
from acquisition_platform import ValuationEngine

engine = ValuationEngine()
result = engine.ensemble_valuation(
    free_cash_flow=100000, revenue=500000,
    growth_rate=0.05, discount_rate=0.10,
    terminal_growth=0.02, revenue_multiple=3.2, years=5,
)
```

### Detect Fraud

```python
from acquisition_platform import FraudDetector, FraudSignal

detector = FraudDetector()
score = detector.score([
    FraudSignal(name="identity_verified", value=0.9),
    FraudSignal(name="financial_consistency", value=0.85),
])
```

### Optimize Portfolio

```python
from acquisition_platform import Asset, PortfolioOptimizer

optimizer = PortfolioOptimizer(budget=1000000, max_assets=3)
portfolio = optimizer.optimize([
    Asset(id="a1", cost=400000, expected_return=0.12, risk=0.15, sector="saas"),
], risk_tolerance=0.5)
```

### Get Pricing Recommendation

```python
from acquisition_platform import PricingEngine

engine = PricingEngine()
rec = engine.recommend_price(
    base_value=100000, demand_level=0.7,
    competition_level=0.5, market_condition="bull",
)
```

### Resolve Entities

```python
from acquisition_platform import EntityResolver

resolver = EntityResolver(threshold=0.85)
clusters = resolver.resolve([
    {"id": "e1", "name": "Acme Corp", "domain": "acme.com"},
    {"id": "e2", "name": "Acme Corporation", "domain": "acme.com"},
])
```

### Rank Search Results

```python
from acquisition_platform import Listing, SearchRanker

ranker = SearchRanker()
results = ranker.rank("saas", [
    Listing(id="l1", title="SaaS A", relevance=0.9, category="saas"),
])
```

### Run Evolution

```python
from acquisition_platform import EvolutionEngine, Benchmark

engine = EvolutionEngine(population_size=50, generations=20)
result = engine.evolve(fitness_fn=lambda x: x**2, gene_range=(0, 100))

bench = Benchmark(name="matching_accuracy", target=0.90)
eval_result = bench.evaluate(actual=0.92)
```

## Configuration

- `pyproject.toml` — Project metadata, dependencies, tool config
- No environment variables required for core functionality
- Optional: `pytest` configuration in `pyproject.toml`

## Where to Go Next

- Architecture: [architecture.md](architecture.md)
- Module reference: [README.md](../README.md#module-reference)
- API reference: [README.md](../README.md#api-reference)
