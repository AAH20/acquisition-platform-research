"""Monitoring module — metrics collection, alerting, health checks, SLA tracking.

Provides the Monitoring class for collecting metrics, generating alerts,
tracking performance and SLA compliance, detecting anomalies, and producing
dashboard data and monitoring reports.
"""

from __future__ import annotations

import statistics
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class Metric:
    """A single collected metric data point."""

    name: str
    value: float
    timestamp: str
    labels: dict[str, Any] = field(default_factory=dict)


@dataclass
class Alert:
    """A monitoring alert."""

    alert_id: str
    severity: str
    message: str
    timestamp: str
    acknowledged: bool = False


@dataclass
class MonitoringResult:
    """Aggregated result of a monitoring cycle."""

    metrics: list[Metric] = field(default_factory=list)
    alerts: list[Alert] = field(default_factory=list)
    health_status: str = "unknown"
    sla_compliance: float = 0.0


# ---------------------------------------------------------------------------
# Monitoring class
# ---------------------------------------------------------------------------


class Monitoring:
    """Core monitoring engine for the acquisition platform."""

    def __init__(self) -> None:
        self.metrics: list[Metric] = []
        self.alerts: list[Alert] = []

    # -- Metric collection ---------------------------------------------------

    def collect_metric(
        self,
        name: str,
        value: float,
        labels: dict[str, Any] | None = None,
    ) -> Metric:
        """Collect and store a metric data point.

        Args:
            name: Metric name (e.g. ``"cpu_usage"``).
            value: Numeric value.
            labels: Optional key-value labels.

        Returns:
            The created :class:`Metric`.
        """
        metric = Metric(
            name=name,
            value=float(value),
            timestamp=datetime.now(timezone.utc).isoformat(),
            labels=labels or {},
        )
        self.metrics.append(metric)
        return metric

    # -- Alerting ------------------------------------------------------------

    def generate_alert(self, severity: str, message: str) -> Alert:
        """Generate and store an alert.

        Args:
            severity: Alert severity (``"critical"``, ``"warning"``, ``"info"``).
            message: Human-readable alert message.

        Returns:
            The created :class:`Alert`.
        """
        alert = Alert(
            alert_id=str(uuid.uuid4()),
            severity=severity,
            message=message,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self.alerts.append(alert)
        return alert

    # -- Health --------------------------------------------------------------

    def health_check(self) -> str:
        """Assess overall system health.

        Returns:
            One of ``"healthy"``, ``"degraded"``, ``"unhealthy"``, ``"unknown"``.
        """
        if not self.metrics and not self.alerts:
            return "unknown"

        critical_count = sum(1 for a in self.alerts if a.severity == "critical")
        warning_count = sum(1 for a in self.alerts if a.severity == "warning")

        if critical_count > 0:
            return "unhealthy"
        if warning_count > 0:
            return "degraded"
        return "healthy"

    # -- Performance tracking -------------------------------------------------

    def track_performance(self, metric_name: str, threshold: float) -> bool:
        """Check whether the latest value for a metric is within threshold.

        Args:
            metric_name: Name of the metric to check.
            threshold: Maximum acceptable value.

        Returns:
            ``True`` if the latest value is within threshold, ``False`` otherwise.
        """
        matching = [m for m in self.metrics if m.name == metric_name]
        if not matching:
            return False
        return matching[-1].value <= threshold

    # -- Anomaly detection ---------------------------------------------------

    def detect_anomalies(self, metrics: list[Metric]) -> list[Metric]:
        """Detect anomalous metrics using z-score.

        A metric is anomalous if its z-score exceeds 2.0 relative to all
        metrics sharing the same name.

        Args:
            metrics: List of metrics to analyze.

        Returns:
            List of anomalous metrics.
        """
        if not metrics:
            return []

        # Group by metric name
        by_name: dict[str, list[Metric]] = {}
        for m in metrics:
            by_name.setdefault(m.name, []).append(m)

        anomalies: list[Metric] = []
        for group in by_name.values():
            if len(group) < 2:
                continue
            values = [m.value for m in group]
            mean = statistics.mean(values)
            stdev = statistics.stdev(values) if len(values) > 1 else 0.0
            if stdev == 0.0:
                continue
            for m in group:
                z_score = abs(m.value - mean) / stdev
                if z_score > 2.0:
                    anomalies.append(m)

        return anomalies

    # -- SLA tracking --------------------------------------------------------

    def track_sla(self, metric_name: str, target: float) -> float:
        """Calculate SLA compliance percentage for a metric.

        Compliance is ``min(100, (value / target) * 100)``.

        Args:
            metric_name: Name of the metric.
            target: Target value (e.g. 99.9 for 99.9% uptime).

        Returns:
            SLA compliance percentage (0.0–100.0), or 0.0 if metric not found.
        """
        matching = [m for m in self.metrics if m.name == metric_name]
        if not matching:
            return 0.0
        value = matching[-1].value
        if target <= 0:
            return 0.0
        return min(100.0, (value / target) * 100.0)

    # -- Dashboard -----------------------------------------------------------

    def generate_dashboard_data(self) -> dict[str, Any]:
        """Generate a summary dict suitable for dashboard rendering.

        Returns:
            Dictionary with metric/alert counts, health, and SLA compliance.
        """
        return {
            "total_metrics": len(self.metrics),
            "total_alerts": len(self.alerts),
            "health": self.health_check(),
            "sla_compliance": self._overall_sla_compliance(),
        }

    # -- Alert management ----------------------------------------------------

    def manage_alerts(self, alerts: list[Alert]) -> list[Alert]:
        """Process and manage a list of alerts.

        Acknowledges critical alerts and returns the managed list.

        Args:
            alerts: Alerts to manage.

        Returns:
            The managed alerts (critical ones acknowledged).
        """
        managed: list[Alert] = []
        for alert in alerts:
            if alert.severity == "critical" and not alert.acknowledged:
                alert.acknowledged = True
            managed.append(alert)
        return managed

    # -- Reporting -----------------------------------------------------------

    def generate_monitoring_report(self) -> MonitoringResult:
        """Generate a full monitoring report.

        Returns:
            A :class:`MonitoringResult` with current metrics, alerts,
            health status, and SLA compliance.
        """
        return MonitoringResult(
            metrics=list(self.metrics),
            alerts=list(self.alerts),
            health_status=self.health_check(),
            sla_compliance=self._overall_sla_compliance(),
        )

    # -- Internal helpers ----------------------------------------------------

    def _overall_sla_compliance(self) -> float:
        """Compute average SLA compliance across all tracked metrics."""
        if not self.metrics:
            return 0.0
        by_name: dict[str, list[Metric]] = {}
        for m in self.metrics:
            by_name.setdefault(m.name, []).append(m)
        # Use the latest value per metric name with a default target of 100
        compliances = []
        for name, group in by_name.items():
            latest = group[-1].value
            target = 100.0
            if target > 0:
                compliances.append(min(100.0, (latest / target) * 100.0))
        if not compliances:
            return 0.0
        return round(sum(compliances) / len(compliances), 2)
