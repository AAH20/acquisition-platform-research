# Wave 2: Notification System Implementation

## Summary

Implemented a lightweight, extensible notification system for the acquisition platform following TDD (tests first, then implementation).

## Files Created

### `src/acquisition_platform/notifications.py`
- **NotificationType** enum: INFO, WARNING, ERROR, CRITICAL
- **NotificationChannel** enum: CONSOLE, EMAIL, WEBHOOK
- **Notification** dataclass: id, type, message, severity (1-4), timestamp, channel, metadata — with `__post_init__` validation
- **NotificationHandler** class:
  - `send(notification) -> None` — dispatches via registered channel sink and records to history
  - `send_batch(notifications) -> list[Notification]` — sends multiple in order, returns sent list
  - `get_history() -> list[Notification]` — returns copy of history
  - `clear_history() -> None` — clears all history
  - `register_sink(channel, sink)` — extensible channel delivery
- **Convenience helpers** (each returns the dispatched Notification):
  - `notify_high_fraud_risk(handler, entity_id, score)` → CRITICAL, severity 4
  - `notify_match_found(handler, buyer_id, seller_id, score)` → INFO, severity 1
  - `notify_portfolio_optimized(handler, expected_return, sharpe_ratio)` → INFO, severity 1
  - `notify_evolution_converged(handler, best_fitness, generations)` → INFO, severity 1

### `tests/test_notifications.py`
18 tests across 7 test classes:
- **TestNotificationCreation** (4): field assignment, enum values, equality
- **TestNotificationSending** (3): single send, batch send, empty batch
- **TestNotificationHistory** (3): get history, clear history, accumulation
- **TestHighFraudNotification** (2): message content (entity ID + score), severity ≥ 3
- **TestMatchFoundNotification** (2): message content (buyer/seller/score), type is INFO
- **TestPortfolioNotification** (2): message content (return + Sharpe), keyword check
- **TestEvolutionNotification** (2): message content (fitness + generations), keyword check

## Test Results

```
tests/test_notifications.py ..................  [100%]
18 passed, 1 warning in 0.26s
```

### Full Suite
```
478 passed, 3 failed, 1 warning in 1.76s
```
- All 18 new notification tests pass.
- 3 pre-existing failures in `tests/test_caching.py` (TestCacheHitMiss, TestCacheClearing) — unrelated to this change; these tests existed before and do not involve the notification system.

## Design Decisions

- **Severity scale 1–4**: 1=INFO, 2=WARNING, 3=ERROR, 4=CRITICAL, validated in `__post_init__`.
- **Extensible sinks**: `register_sink()` allows plugging in email/webhook/console delivery without modifying the handler.
- **UUID + UTC timestamps**: notifications are self-identifying and timezone-safe.
- **Metadata dict**: each convenience helper attaches structured context (entity_id, score, etc.) for downstream consumers.
- **No external dependencies**: pure stdlib implementation.
