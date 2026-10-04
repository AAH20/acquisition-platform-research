# Wave 2 Research: Auction Design Module Gap Analysis

**Date:** 2026-10-04
**Focus:** Identify what `auction_design.py` should export based on Wave 1 research and existing codebase patterns

---

## 1. Gap Summary

The README references an "Auction Designer" component in the architecture diagram (line 110: `AUCTION["Auction Designer<br/>#P-hard"]`) and "Auction Design" in the data flow diagram (line 247: `AUC[Auction Design]`), but **no `auction_design.py` module exists** in `src/acquisition_platform/`.

### Current Module Inventory

| Module | Status | NP-Hard Problem |
|--------|--------|-----------------|
| `matching.py` | ✅ Exists | GAP (Generalized Assignment Problem) |
| `valuation.py` | ✅ Exists | PPAD-hard |
| `fraud_detection.py` | ✅ Exists | Dense Subgraph |
| `portfolio_optimizer.py` | ✅ Exists | MIQP |
| `dynamic_pricing.py` | ✅ Exists | Stackelberg (Σ₂ᵖ-complete) |
| `entity_resolution.py` | ✅ Exists | O(n²) |
| `search_ranking.py` | ✅ Exists | Submodular Max |
| `evolution.py` | ✅ Exists | GA Framework |
| **`auction_design.py`** | **❌ Missing** | **#P-hard** |

### Cross-Platform Bottleneck Mapping

From the README's bottleneck table, auction design maps to:
- **Bottleneck #6:** Information Asymmetry (High severity, all platforms, NP-hard via mechanism design)
- **Bottleneck #4:** NDA Harvesting (High severity, Acquire.com + Flippa)

---

## 2. Research Foundation

Two Wave 1 research documents provide the theoretical basis:

### 2.1 `w1_auction_design.md` — Key Findings

| Section | Finding | Implementation Implication |
|---------|---------|---------------------------|
| Auction Types | English ≈ Vickrey; Dutch ≈ FPSBA; combinatorial auctions extend to multi-item | Need format abstraction |
| Theory | Revenue equivalence holds under standard conditions; breaks with risk aversion, interdependent values | Need reserve price optimization |
| Mechanism Design | Vickrey is dominant-strategy IC; GSP dominates in practice due to O(n log n) vs O(nk) | Need GSP and Vickrey implementations |
| Efficiency | Budget constraints cause inefficiency; PoA bounds via LP duality | Need budget-constrained bidding |
| Fraud | Shill bidding, non-delivery, misrepresentation; platform + regulatory countermeasures | Need shill detection integration |
| Bottlenecks | Cataloging throughput is #1 growth constraint; multi-party coordination is labor-intensive | Need multi-party synchronization |
| NP-Hard Problems | Optimal multi-item auction is NP-hard even for single budget-additive bidder | Need approximation algorithms |

### 2.2 `w1_auction_theory.md` — Key Findings

| Section | Finding | Implementation Implication |
|---------|---------|---------------------------|
| Auction Theory | Revenue equivalence: all efficient auctions yield same expected revenue | Need revenue equivalence validation |
| Mechanism Design | Vickrey auction achieves dominant-strategy IC; Myerson's optimal auction maximizes revenue | Need Myerson optimal auction |
| Efficiency | Optimal reserve price increases revenue ≤13% but doubles net profit | Need reserve price optimizer |
| Bidding Strategies | Sniping and squatting are equilibrium strategies in online auctions | Need sniping detection |
| Fraud/Collusion | Shill Score and CSBD algorithms detect collusive shill bidding | Need shill score integration |
| Bottlenecks | Cataloging throughput caps solo operators at 1 sale/week | Need cataloging automation |
| Optimization | ML + ILP solves optimal ordering in sequential auctions | Need sequential auction optimizer |
| NP-Hard Problems | Winner determination is NP-hard; optimal mechanism design is NP-hard | Need WDP solver |
| Machine Learning | LLMs replicate human bidding behavior; MLHCA reduces efficiency loss 10× | Need ML-powered auction design |
| Market Design | "Horses for courses" — design must match context; collusion prevention paramount | Need context-aware design |

---

## 3. Required Exports for `auction_design.py`

Based on the research and the patterns established by existing modules (dataclass results + engine class + clear docstrings), the module should export:

### 3.1 Data Types (Dataclasses)

| Type | Fields | Purpose |
|------|--------|---------|
| `Bid` | `bidder_id: str, amount: float, timestamp: float, is_shill: bool = False` | Represents a single bid in the auction |
| `AuctionConfig` | `format: str, reserve_price: float, min_increment: float, duration_seconds: int, item_count: int = 1` | Configuration for the auction format |
| `AuctionResult` | `winner_id: str, winning_bid: float, second_highest_bid: float, revenue: float, efficiency: float, is_efficient: bool` | Result of running the auction |
| `Bidder` | `id: str, valuation: float, budget: float, risk_aversion: float = 0.0` | Represents a bidder with private valuation |
| `ShillScore` | `bidder_id: str, score: float, risk_level: str, confidence: float` | Shill bidding detection result |
| `ReservePriceRecommendation` | `optimal_reserve: float, expected_revenue: float, confidence: float` | Optimal reserve price result |

### 3.2 Engine Class

| Class | Methods | Purpose |
|-------|---------|---------|
| `AuctionDesigner` | `design_auction(config, bidders) -> AuctionResult` | Main auction design engine |
| | `optimize_reserve_price(valuations, distribution) -> ReservePriceRecommendation` | Myerson optimal reserve price |
| | `detect_shill_bidding(bids, history) -> list[ShillScore]` | Shill bidding detection |
| | `estimate_revenue(config, bidders) -> float` | Revenue estimation |
| | `select_format(context) -> str` | Format selection based on context |

### 3.3 Key Functions

| Function | Signature | Purpose |
|----------|-----------|---------|
| `vickrey_auction` | `(bids: list[Bid]) -> AuctionResult` | Second-price sealed-bid implementation |
| `gsp_auction` | `(bids: list[Bid], qualities: list[float]) -> AuctionResult` | Generalized second-price for multi-slot |
| `myerson_optimal` | `(valuations: list[float], distribution: str) -> float` | Myerson's optimal reserve price |
| `winner_determination` | `(bids: list[Bid], items: int) -> list[Bid]` | NP-hard winner determination (approximation) |
| `shill_score` | `(bid_history: list[Bid]) -> float` | Trevathan-style shill score |

---

## 4. Integration Points

### 4.1 Internal Module Dependencies

```
auction_design.py should integrate with:
├── fraud_detection.py  → ShillScore, FraudDetector for bid screening
├── valuation.py        → ValuationEngine for reserve price estimation
├── matching.py         → BuyerSellerMatcher for bidder-seller matching
└── evolution.py        → EvolutionEngine for hyperparameter optimization
```

### 4.2 External Research Integration

| Research Finding | Integration Point |
|-----------------|-------------------|
| Shill Score (Trevathan 2018) | Use `FraudDetector` from `fraud_detection.py` |
| Myerson's Optimal Auction | Use `ValuationEngine` from `valuation.py` for distribution estimation |
| GSP vs VCG complexity | Implement both, benchmark with `EvolutionEngine` |
| ML-powered combinatorial auctions | Future: integrate with ML layer |

---

## 5. Complexity Classification

| Problem | Complexity | Approach |
|---------|-----------|----------|
| Winner Determination (combinatorial) | NP-hard | Approximation + heuristics |
| Optimal Mechanism Design | #P-hard | Myerson's formula (single-item) |
| Shill Detection | Polynomial | Graph-based + scoring |
| Reserve Price Optimization | Polynomial | Closed-form (regular distributions) |
| Revenue Equivalence Validation | Polynomial | Simulation-based |

---

## 6. Recommended Implementation Priority

### Phase 1: Core Auction Engine (Week 1)
1. Implement `Bid`, `AuctionConfig`, `AuctionResult` dataclasses
2. Implement `AuctionDesigner.design_auction()` with Vickrey and English formats
3. Implement `vickrey_auction()` and `gsp_auction()` functions
4. Write tests (target: 8-10 tests matching existing module pattern)

### Phase 2: Optimization (Week 2)
5. Implement `optimize_reserve_price()` using Myerson's formula
6. Implement `myerson_optimal()` for regular distributions
7. Implement `estimate_revenue()` with Monte Carlo simulation
8. Write tests (target: 6-8 tests)

### Phase 3: Fraud Integration (Week 3)
9. Implement `detect_shill_bidding()` using `FraudDetector`
10. Implement `shill_score()` using Trevathan-style scoring
11. Integrate with existing `fraud_detection.py` module
12. Write tests (target: 6-8 tests)

### Phase 4: Advanced Features (Week 4)
13. Implement `winner_determination()` for combinatorial auctions
14. Implement `select_format()` for context-aware format selection
15. Integrate with `evolution.py` for hyperparameter optimization
16. Write tests (target: 6-8 tests)

---

## 7. Test Plan

Following the existing test pattern (see `test_dynamic_pricing.py`):

```python
# tests/test_auction_design.py

class TestAuctionDesigner:
    """TDD tests for the auction design engine."""

    def test_vickrey_auction_basic(self):
        """Second-price auction: winner pays second-highest bid."""
        # Test Vickrey mechanism

    def test_english_auction_ascending(self):
        """English auction: price rises until one bidder remains."""
        # Test English format

    def test_reserve_price_optimization(self):
        """Myerson optimal reserve price maximizes revenue."""
        # Test reserve price formula

    def test_shill_detection(self):
        """Shill bidding detection identifies suspicious patterns."""
        # Test shill score

    def test_revenue_equivalence(self):
        """Revenue equivalence holds under standard conditions."""
        # Test RET

    def test_budget_constrained_bidding(self):
        """Budget constraints affect bidding strategy."""
        # Test budget handling

    def test_gsp_auction(self):
        """GSP auction for multi-slot allocation."""
        # Test GSP mechanism

    def test_winner_determination(self):
        """Winner determination in combinatorial auctions."""
        # Test WDP approximation
```

---

## 8. Conclusion

The `auction_design.py` module is a **critical gap** in the acquisition platform research codebase. It is referenced in the README architecture but has no implementation. The module should:

1. **Export 6 dataclasses** for auction configuration, results, and fraud detection
2. **Export 1 engine class** (`AuctionDesigner`) with 5 core methods
3. **Export 5 functions** for specific auction mechanisms and optimizations
4. **Integrate with 4 existing modules** (fraud_detection, valuation, matching, evolution)
5. **Follow the established pattern** of dataclass results + engine class + comprehensive tests
6. **Target 26-32 tests** matching the existing test coverage (62 tests / 8 modules ≈ 8 tests per module)

The implementation should prioritize the Vickrey auction (dominant-strategy IC) and GSP auction (practical efficiency) as the two most important formats, with Myerson's optimal reserve price as the key optimization feature.

---

## Citations

1. Vickrey, W. (1961). "Counterspeculation, Auctions, and Competitive Sealed Tenders." *Journal of Finance*, 16(1), 8–37.
2. Myerson, R. B. (1981). "Optimal Auction Design." *Mathematics of Operations Research*, 6(1), 58–73.
3. Krishna, V. (2010). *Auction Theory* (2nd ed.). Academic Press.
4. Milgrom, P. R. (2004). *Putting Auction Theory to Work*. Cambridge University Press.
5. Dobzinski, S., Lavi, R., & Nisan, N. (2011). "The Complexity of Optimal Mechanism Design." *arXiv:1211.1703*.
6. Varian, H. R., & Edelman, B. (2007). "Google's AdWords Auction." *American Economic Review*.
7. Trevathan, J. (2018). "Detecting Collusive Shill Bidding in Commercial Online Auctions." *doi.org/10.1007/s10614-022-10326-7*.
8. Klemperer, P. (2003). "Auction Theory: A Guide to the Literature." *Journal of Economic Surveys*.
9. Bulow, J., & Klemperer, P. (1996). "Auctions vs. Negotiations." *American Economic Review*.
10. Groenwegen, P. (2017). "Squatting, Sniping, and Online Strategy." Yale University.
