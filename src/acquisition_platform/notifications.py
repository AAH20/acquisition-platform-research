"""Notification system for the acquisition platform.

Provides a lightweight, extensible notification framework with severity
levels, delivery channels, and convenience helpers for platform events
(fraud alerts, matching, portfolio optimization, evolution convergence).
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional


class NotificationType(Enum):
    """Classification of notification purpose."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class NotificationChannel(Enum):
    """Delivery channel for notifications."""

    CONSOLE = "console"
    EMAIL = "email"
    WEBHOOK = "webhook"


@dataclass
class Notification:
    """A single notification record.

    Attributes:
        id: Unique identifier for the notification.
        type: Classification (info, warning, error, critical).
        message: Human-readable notification text.
        severity: Numeric severity (1=low .. 4=critical).
        timestamp: ISO-8601 timestamp string.
        channel: Delivery channel (defaults to CONSOLE).
        metadata: Optional extra context.
    """

    id: str
    type: NotificationType
    message: str
    severity: int
    timestamp: str
    channel: NotificationChannel = NotificationChannel.CONSOLE
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Notification id must not be empty")
        if not self.message:
            raise ValueError("Notification message must not be empty")
        if self.severity < 1 or self.severity > 4:
            raise ValueError("Severity must be between 1 and 4")


class NotificationHandler:
    """Handles dispatching and recording of notifications.

    Maintains an in-memory history of all sent notifications and supports
    batch delivery. Channel-specific sinks (console, email, webhook) can be
    registered via the ``sinks`` mapping.
    """

    def __init__(self) -> None:
        self._history: list[Notification] = []
        self._sinks: dict[NotificationChannel, Callable[[Notification], None]] = {}

    def register_sink(
        self,
        channel: NotificationChannel,
        sink: Callable[[Notification], None],
    ) -> None:
        """Register a delivery sink for a channel."""
        self._sinks[channel] = sink

    def send(self, notification: Notification) -> None:
        """Send a single notification through its channel sink.

        Args:
            notification: The notification to dispatch.

        Raises:
            ValueError: If the notification is None.
        """
        if notification is None:
            raise ValueError("Notification must not be None")
        sink = self._sinks.get(notification.channel)
        if sink is not None:
            sink(notification)
        self._history.append(notification)

    def send_batch(self, notifications: list[Notification]) -> list[Notification]:
        """Send multiple notifications in order.

        Args:
            notifications: Notifications to dispatch.

        Returns:
            The list of notifications that were sent.
        """
        sent: list[Notification] = []
        for notification in notifications:
            self.send(notification)
            sent.append(notification)
        return sent

    def get_history(self) -> list[Notification]:
        """Return a copy of the notification history."""
        return list(self._history)

    def clear_history(self) -> None:
        """Clear all recorded notification history."""
        self._history.clear()


def _now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _make_notification(
    ntype: NotificationType,
    message: str,
    severity: int,
    metadata: Optional[dict[str, Any]] = None,
) -> Notification:
    """Build a Notification with a generated id and current timestamp."""
    return Notification(
        id=str(uuid.uuid4()),
        type=ntype,
        message=message,
        severity=severity,
        timestamp=_now_iso(),
        metadata=metadata or {},
    )


def notify_high_fraud_risk(
    handler: NotificationHandler,
    entity_id: str,
    score: float,
) -> Notification:
    """Send a CRITICAL notification about a high fraud risk entity.

    Args:
        handler: The handler to dispatch through.
        entity_id: Identifier of the flagged entity.
        score: Fraud risk score in [0, 1].

    Returns:
        The dispatched notification.
    """
    notification = _make_notification(
        NotificationType.CRITICAL,
        f"High fraud risk detected for entity {entity_id} (score={score:.2f})",
        severity=4,
        metadata={"entity_id": entity_id, "score": score},
    )
    handler.send(notification)
    return notification


def notify_match_found(
    handler: NotificationHandler,
    buyer_id: str,
    seller_id: str,
    score: float,
) -> Notification:
    """Send an INFO notification about a buyer-seller match.

    Args:
        handler: The handler to dispatch through.
        buyer_id: Identifier of the buyer.
        seller_id: Identifier of the seller.
        score: Match confidence score in [0, 1].

    Returns:
        The dispatched notification.
    """
    notification = _make_notification(
        NotificationType.INFO,
        f"Match found between buyer {buyer_id} and seller {seller_id} (score={score:.2f})",
        severity=1,
        metadata={"buyer_id": buyer_id, "seller_id": seller_id, "score": score},
    )
    handler.send(notification)
    return notification


def notify_portfolio_optimized(
    handler: NotificationHandler,
    expected_return: float,
    sharpe_ratio: float,
) -> Notification:
    """Send an INFO notification about portfolio optimization results.

    Args:
        handler: The handler to dispatch through.
        expected_return: Expected portfolio return.
        sharpe_ratio: Achieved Sharpe ratio.

    Returns:
        The dispatched notification.
    """
    notification = _make_notification(
        NotificationType.INFO,
        f"Portfolio optimized: expected return={expected_return:.2f}, "
        f"Sharpe ratio={sharpe_ratio:.2f}",
        severity=1,
        metadata={"expected_return": expected_return, "sharpe_ratio": sharpe_ratio},
    )
    handler.send(notification)
    return notification


def notify_evolution_converged(
    handler: NotificationHandler,
    best_fitness: float,
    generations: int,
) -> Notification:
    """Send an INFO notification about evolution convergence.

    Args:
        handler: The handler to dispatch through.
        best_fitness: Best fitness achieved.
        generations: Number of generations run.

    Returns:
        The dispatched notification.
    """
    notification = _make_notification(
        NotificationType.INFO,
        f"Evolution converged after {generations} generations "
        f"(best fitness={best_fitness:.2f})",
        severity=1,
        metadata={"best_fitness": best_fitness, "generations": generations},
    )
    handler.send(notification)
    return notification
