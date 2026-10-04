"""Tests for notification system module."""
import pytest
from acquisition_platform.notifications import (
    Notification,
    NotificationType,
    NotificationChannel,
    NotificationHandler,
    notify_high_fraud_risk,
    notify_match_found,
    notify_portfolio_optimized,
    notify_evolution_converged,
)


class TestNotificationCreation:
    """Tests for Notification dataclass creation."""

    def test_create_notification_with_required_fields(self):
        n = Notification(
            id="n1",
            type=NotificationType.INFO,
            message="Test message",
            severity=1,
            timestamp="2024-01-01T00:00:00",
        )
        assert n.id == "n1"
        assert n.type == NotificationType.INFO
        assert n.message == "Test message"
        assert n.severity == 1
        assert n.timestamp == "2024-01-01T00:00:00"

    def test_notification_type_enum_values(self):
        assert NotificationType.INFO is not None
        assert NotificationType.WARNING is not None
        assert NotificationType.ERROR is not None
        assert NotificationType.CRITICAL is not None

    def test_notification_channel_enum_values(self):
        assert NotificationChannel.CONSOLE is not None
        assert NotificationChannel.EMAIL is not None
        assert NotificationChannel.WEBHOOK is not None

    def test_notification_equality(self):
        n1 = Notification(
            id="n1",
            type=NotificationType.INFO,
            message="msg",
            severity=1,
            timestamp="2024-01-01T00:00:00",
        )
        n2 = Notification(
            id="n1",
            type=NotificationType.INFO,
            message="msg",
            severity=1,
            timestamp="2024-01-01T00:00:00",
        )
        assert n1 == n2


class TestNotificationSending:
    """Tests for sending notifications."""

    def test_send_single_notification(self):
        handler = NotificationHandler()
        n = Notification(
            id="n1",
            type=NotificationType.INFO,
            message="Hello",
            severity=1,
            timestamp="2024-01-01T00:00:00",
        )
        handler.send(n)
        assert len(handler.get_history()) == 1

    def test_send_batch_notifications(self):
        handler = NotificationHandler()
        notifications = [
            Notification(
                id=f"n{i}",
                type=NotificationType.INFO,
                message=f"msg {i}",
                severity=1,
                timestamp="2024-01-01T00:00:00",
            )
            for i in range(3)
        ]
        results = handler.send_batch(notifications)
        assert len(results) == 3
        assert len(handler.get_history()) == 3

    def test_send_batch_empty_list(self):
        handler = NotificationHandler()
        results = handler.send_batch([])
        assert results == []


class TestNotificationHistory:
    """Tests for notification history management."""

    def test_get_history_returns_notifications(self):
        handler = NotificationHandler()
        n = Notification(
            id="n1",
            type=NotificationType.WARNING,
            message="warn",
            severity=2,
            timestamp="2024-01-01T00:00:00",
        )
        handler.send(n)
        history = handler.get_history()
        assert len(history) == 1
        assert history[0].message == "warn"

    def test_clear_history(self):
        handler = NotificationHandler()
        n = Notification(
            id="n1",
            type=NotificationType.INFO,
            message="msg",
            severity=1,
            timestamp="2024-01-01T00:00:00",
        )
        handler.send(n)
        assert len(handler.get_history()) == 1
        handler.clear_history()
        assert len(handler.get_history()) == 0

    def test_history_accumulates(self):
        handler = NotificationHandler()
        for i in range(3):
            handler.send(
                Notification(
                    id=f"n{i}",
                    type=NotificationType.INFO,
                    message=f"msg {i}",
                    severity=1,
                    timestamp="2024-01-01T00:00:00",
                )
            )
        assert len(handler.get_history()) == 3


class TestHighFraudNotification:
    """Tests for high fraud risk notification."""

    def test_notify_high_fraud_risk(self):
        handler = NotificationHandler()
        notify_high_fraud_risk(handler, "entity_123", 0.95)
        history = handler.get_history()
        assert len(history) == 1
        assert history[0].type == NotificationType.CRITICAL
        assert "entity_123" in history[0].message
        assert "0.95" in history[0].message

    def test_notify_high_fraud_risk_severity(self):
        handler = NotificationHandler()
        notify_high_fraud_risk(handler, "entity_456", 0.88)
        history = handler.get_history()
        assert history[0].severity >= 3


class TestMatchFoundNotification:
    """Tests for match found notification."""

    def test_notify_match_found(self):
        handler = NotificationHandler()
        notify_match_found(handler, "buyer_1", "seller_1", 0.92)
        history = handler.get_history()
        assert len(history) == 1
        assert history[0].type == NotificationType.INFO
        assert "buyer_1" in history[0].message
        assert "seller_1" in history[0].message
        assert "0.92" in history[0].message

    def test_notify_match_found_is_info(self):
        handler = NotificationHandler()
        notify_match_found(handler, "b", "s", 0.5)
        assert handler.get_history()[0].type == NotificationType.INFO


class TestPortfolioNotification:
    """Tests for portfolio optimization notification."""

    def test_notify_portfolio_optimized(self):
        handler = NotificationHandler()
        notify_portfolio_optimized(handler, 0.15, 1.8)
        history = handler.get_history()
        assert len(history) == 1
        assert history[0].type == NotificationType.INFO
        assert "0.15" in history[0].message
        assert "1.8" in history[0].message

    def test_notify_portfolio_optimized_message_content(self):
        handler = NotificationHandler()
        notify_portfolio_optimized(handler, 0.20, 2.0)
        msg = handler.get_history()[0].message
        assert "return" in msg.lower() or "sharpe" in msg.lower()


class TestEvolutionNotification:
    """Tests for evolution convergence notification."""

    def test_notify_evolution_converged(self):
        handler = NotificationHandler()
        notify_evolution_converged(handler, 0.95, 50)
        history = handler.get_history()
        assert len(history) == 1
        assert history[0].type == NotificationType.INFO
        assert "0.95" in history[0].message
        assert "50" in history[0].message

    def test_notify_evolution_converged_generations(self):
        handler = NotificationHandler()
        notify_evolution_converged(handler, 0.88, 100)
        msg = handler.get_history()[0].message
        assert "100" in msg
        assert "generations" in msg.lower() or "converged" in msg.lower()
