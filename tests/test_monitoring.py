"""Tests for monitoring module — metrics, alerts, health, SLA, anomalies."""
import pytest

from acquisition_platform.monitoring import (
    Alert,
    Metric,
    Monitoring,
    MonitoringResult,
)


# ---------------------------------------------------------------------------
# Test: Metric dataclass
# ---------------------------------------------------------------------------


class TestMetric:
    """Tests for the Metric dataclass."""

    def test_metric_creation(self):
        m = Metric(name="cpu", value=75.0, timestamp="2026-10-05T10:00:00", labels={"host": "a"})
        assert m.name == "cpu"
        assert m.value == 75.0
        assert m.timestamp == "2026-10-05T10:00:00"
        assert m.labels == {"host": "a"}

    def test_metric_default_labels(self):
        m = Metric(name="mem", value=50.0, timestamp="t")
        assert m.labels == {}


# ---------------------------------------------------------------------------
# Test: Alert dataclass
# ---------------------------------------------------------------------------


class TestAlert:
    """Tests for the Alert dataclass."""

    def test_alert_creation(self):
        a = Alert(alert_id="a1", severity="critical", message="down", timestamp="t", acknowledged=False)
        assert a.alert_id == "a1"
        assert a.severity == "critical"
        assert a.message == "down"
        assert a.acknowledged is False

    def test_alert_default_acknowledged(self):
        a = Alert(alert_id="a2", severity="info", message="ok", timestamp="t")
        assert a.acknowledged is False


# ---------------------------------------------------------------------------
# Test: MonitoringResult dataclass
# ---------------------------------------------------------------------------


class TestMonitoringResult:
    """Tests for the MonitoringResult dataclass."""

    def test_result_creation(self):
        m = Metric(name="x", value=1.0, timestamp="t")
        a = Alert(alert_id="a", severity="low", message="m", timestamp="t")
        r = MonitoringResult(metrics=[m], alerts=[a], health_status="healthy", sla_compliance=99.5)
        assert r.metrics == [m]
        assert r.alerts == [a]
        assert r.health_status == "healthy"
        assert r.sla_compliance == 99.5

    def test_result_defaults(self):
        r = MonitoringResult()
        assert r.metrics == []
        assert r.alerts == []
        assert r.health_status == "unknown"
        assert r.sla_compliance == 0.0


# ---------------------------------------------------------------------------
# Test: collect_metric
# ---------------------------------------------------------------------------


class TestCollectMetric:
    """Tests for Monitoring.collect_metric."""

    def test_metric_collection(self):
        mon = Monitoring()
        m = mon.collect_metric("cpu_usage", 82.5, {"host": "web-1"})
        assert isinstance(m, Metric)
        assert m.name == "cpu_usage"
        assert m.value == 82.5
        assert m.labels == {"host": "web-1"}
        assert m.timestamp  # non-empty

    def test_collect_stores_metric(self):
        mon = Monitoring()
        mon.collect_metric("disk", 60.0)
        assert len(mon.metrics) == 1

    def test_collect_multiple(self):
        mon = Monitoring()
        mon.collect_metric("a", 1.0)
        mon.collect_metric("b", 2.0)
        assert len(mon.metrics) == 2


# ---------------------------------------------------------------------------
# Test: generate_alert
# ---------------------------------------------------------------------------


class TestGenerateAlert:
    """Tests for Monitoring.generate_alert."""

    def test_alert_generation(self):
        mon = Monitoring()
        a = mon.generate_alert("warning", "high load")
        assert isinstance(a, Alert)
        assert a.severity == "warning"
        assert a.message == "high load"
        assert a.acknowledged is False
        assert a.alert_id  # non-empty

    def test_alert_stored(self):
        mon = Monitoring()
        mon.generate_alert("critical", "disk full")
        assert len(mon.alerts) == 1

    def test_unique_alert_ids(self):
        mon = Monitoring()
        a1 = mon.generate_alert("info", "m1")
        a2 = mon.generate_alert("info", "m2")
        assert a1.alert_id != a2.alert_id


# ---------------------------------------------------------------------------
# Test: empty_metrics
# ---------------------------------------------------------------------------


class TestEmptyMetrics:
    """Tests for behavior with no metrics collected."""

    def test_empty_metrics_returns_defaults(self):
        mon = Monitoring()
        assert mon.metrics == []
        assert mon.alerts == []
        assert mon.health_check() == "unknown"
        assert mon.generate_dashboard_data() == {
            "total_metrics": 0,
            "total_alerts": 0,
            "health": "unknown",
            "sla_compliance": 0.0,
        }

    def test_empty_metrics_report(self):
        mon = Monitoring()
        result = mon.generate_monitoring_report()
        assert isinstance(result, MonitoringResult)
        assert result.metrics == []
        assert result.alerts == []
        assert result.health_status == "unknown"
        assert result.sla_compliance == 0.0


# ---------------------------------------------------------------------------
# Test: health_check
# ---------------------------------------------------------------------------


class TestHealthCheck:
    """Tests for Monitoring.health_check."""

    def test_health_checked(self):
        mon = Monitoring()
        status = mon.health_check()
        assert isinstance(status, str)
        assert status in ("healthy", "degraded", "unhealthy", "unknown")

    def test_health_with_critical_alerts(self):
        mon = Monitoring()
        mon.generate_alert("critical", "down")
        status = mon.health_check()
        assert status in ("unhealthy", "degraded")

    def test_health_healthy_when_no_alerts(self):
        mon = Monitoring()
        mon.collect_metric("cpu", 30.0)
        assert mon.health_check() == "healthy"


# ---------------------------------------------------------------------------
# Test: track_performance
# ---------------------------------------------------------------------------


class TestTrackPerformance:
    """Tests for Monitoring.track_performance."""

    def test_performance_tracked(self):
        mon = Monitoring()
        mon.collect_metric("latency", 120.0)
        result = mon.track_performance("latency", threshold=200.0)
        assert result is True

    def test_performance_breach(self):
        mon = Monitoring()
        mon.collect_metric("latency", 350.0)
        result = mon.track_performance("latency", threshold=200.0)
        assert result is False

    def test_performance_no_metric(self):
        mon = Monitoring()
        result = mon.track_performance("missing", threshold=100.0)
        assert result is False


# ---------------------------------------------------------------------------
# Test: detect_anomalies
# ---------------------------------------------------------------------------


class TestDetectAnomalies:
    """Tests for Monitoring.detect_anomalies."""

    def test_anomaly_detection(self):
        mon = Monitoring()
        for i in range(10):
            mon.collect_metric("cpu", 50.0)
        mon.collect_metric("cpu", 500.0)  # anomaly
        anomalies = mon.detect_anomalies(mon.metrics)
        assert len(anomalies) >= 1
        assert any(m.value == 500.0 for m in anomalies)

    def test_no_anomalies(self):
        mon = Monitoring()
        for _ in range(5):
            mon.collect_metric("cpu", 50.0)
        anomalies = mon.detect_anomalies(mon.metrics)
        assert anomalies == []

    def test_empty_metrics_no_anomalies(self):
        mon = Monitoring()
        assert mon.detect_anomalies([]) == []


# ---------------------------------------------------------------------------
# Test: track_sla
# ---------------------------------------------------------------------------


class TestTrackSla:
    """Tests for Monitoring.track_sla."""

    def test_sla_tracked(self):
        mon = Monitoring()
        mon.collect_metric("uptime", 99.9)
        compliance = mon.track_sla("uptime", target=99.0)
        assert isinstance(compliance, float)
        assert compliance >= 99.0

    def test_sla_breach(self):
        mon = Monitoring()
        mon.collect_metric("uptime", 95.0)
        compliance = mon.track_sla("uptime", target=99.0)
        assert compliance < 99.0

    def test_sla_no_metric(self):
        mon = Monitoring()
        compliance = mon.track_sla("missing", target=99.0)
        assert compliance == 0.0


# ---------------------------------------------------------------------------
# Test: generate_dashboard_data
# ---------------------------------------------------------------------------


class TestDashboardData:
    """Tests for Monitoring.generate_dashboard_data."""

    def test_dashboard_data(self):
        mon = Monitoring()
        mon.collect_metric("cpu", 70.0)
        mon.generate_alert("warning", "high cpu")
        data = mon.generate_dashboard_data()
        assert isinstance(data, dict)
        assert data["total_metrics"] == 1
        assert data["total_alerts"] == 1
        assert "health" in data
        assert "sla_compliance" in data

    def test_dashboard_empty(self):
        mon = Monitoring()
        data = mon.generate_dashboard_data()
        assert data["total_metrics"] == 0
        assert data["total_alerts"] == 0


# ---------------------------------------------------------------------------
# Test: manage_alerts
# ---------------------------------------------------------------------------


class TestManageAlerts:
    """Tests for Monitoring.manage_alerts."""

    def test_alerts_managed(self):
        mon = Monitoring()
        a1 = mon.generate_alert("critical", "down")
        a2 = mon.generate_alert("info", "ok")
        managed = mon.manage_alerts(mon.alerts)
        assert isinstance(managed, list)
        assert len(managed) == 2
        assert all(isinstance(a, Alert) for a in managed)

    def test_manage_empty(self):
        mon = Monitoring()
        assert mon.manage_alerts([]) == []

    def test_manage_acknowledges_critical(self):
        mon = Monitoring()
        a = mon.generate_alert("critical", "down")
        managed = mon.manage_alerts([a])
        # Critical alerts should be flagged/acknowledged
        assert len(managed) == 1


# ---------------------------------------------------------------------------
# Test: generate_monitoring_report
# ---------------------------------------------------------------------------


class TestMonitoringReport:
    """Tests for Monitoring.generate_monitoring_report."""

    def test_report_generated(self):
        mon = Monitoring()
        mon.collect_metric("cpu", 65.0)
        mon.generate_alert("warning", "high cpu")
        result = mon.generate_monitoring_report()
        assert isinstance(result, MonitoringResult)
        assert len(result.metrics) == 1
        assert len(result.alerts) == 1
        assert result.health_status in ("healthy", "degraded", "unhealthy")
        assert isinstance(result.sla_compliance, float)

    def test_report_empty(self):
        mon = Monitoring()
        result = mon.generate_monitoring_report()
        assert result.metrics == []
        assert result.alerts == []
        assert result.health_status == "unknown"
        assert result.sla_compliance == 0.0
