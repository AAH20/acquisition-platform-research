# Wave 2: auction_design Module Implementation

## Summary

Implemented `src/acquisition_platform/auction_design.py` with full TDD coverage.

## What Was Done

### Tests Created
- `tests/test_auction_design.py` — 13 tests covering all required scenarios:
  - Vickrey (second-price sealed-bid)
  - GSP (generalized second-price)
  - English (ascending-price)
  - Dutch (descending-price)
  - Reserve price enforcement (including all-bids-below-reserve edge case)
  - Shill bidding detection (positive and negative cases)
  - Revenue estimation (with and without reserve)
  - Auction format selection
  - Empty bids
  - Single bid

### Module Implementation
- `Bid` dataclass: `bidder_id: str`, `amount: float`
- `AuctionConfig` dataclass: `format: str`, `reserve_price: float`, `min_increment: float`
- `AuctionResult` dataclass: `winner_id: Optional[str]`, `winning_bid: float`, `revenue: float`, `format: str`
- `AuctionDesigner` class with methods:
  - `design_auction(bids, config) -> AuctionResult` — runs auction, filters below-reserve bids, computes winner and revenue per format
  - `optimize_reserve_price(bids) -> float` — median-based heuristic
  - `detect_shill_bidding(bids) -> list[str]` — flags bids within 5% of max (excluding max itself)
  - `estimate_revenue(bids, config) -> float` — point estimate based on format
  - `select_format(num_bidders, item_value) -> str` — English for many bidders/high value, Dutch for few/low, Vickrey otherwise

### Design Decisions
- All dataclasses inherit `SerializableMixin` for JSON serialization consistency with the rest of the codebase
- `ValidationError` raised for unknown auction formats
- Single-bid Vickrey/GSP pays reserve price (no second bid to use)
- Shill detection uses 5% threshold below max bid

## Test Results

```
tests/test_auction_design.py .............  [100%]  13 passed
Full suite: 436 passed, 1 warning in 1.09s
```

## Files Created/Modified

- `tests/test_auction_design.py` (new)
- `src/acquisition_platform/auction_design.py` (new)
- `research/w2_auction_design_impl.md` (this file)
