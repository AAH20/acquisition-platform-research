"""Tests for observability module — logging, metrics, and health checks."""

import logging
import time

import pytest

from acquisition_platform.observability import (
    HealthCheck,
    MetricsCollector,
    get_logger,
    log_execution_time,
    log_module_call,
)


# ---------------------------------------------------------------------------
# Test: get_logger
# ---------------------------------------------------------------------------


class TestGetLogger:
    """Tests for the get_logger factory function."""

    def test_returns_logger(self):
        logger = get_logger("test.module")
        assert isinstance(logger, logging.Logger)

    def test_logger_has_name(self):
        logger = get_logger("my.test.logger")
        assert logger.name == "my.test.logger"

    def test_same_name_returns_same_logger(self):
        """Loggers with the same name should be the same object."""
        logger1 = get_logger("duplicate.test")
        logger2 = get_logger("duplicate.test")
        assert logger1 is logger2

    def test_logger_effective_level(self):
        logger = get_logger("level.test")
        assert logger.level == logging.NOTSET  # inherits from root

    def test_multiple_loggers_independent(self):
        log1 = get_logger("indep.1")
        log2 = get_logger("indep.2")
        assert log1 is not log2
        assert log1.name != log2.name


# ---------------------------------------------------------------------------
# Test: log_execution_time decorator
# ---------------------------------------------------------------------------


class TestLogExecutionTime:
    """Tests for the log_execution_time decorator."""

    def test_decorator_preserves_return_value(self):
        @log_execution_time()
        def add(a, b):
            return a + b

        assert add(2, 3) == 5

    def test_decorator_preserves_function_name(self):
        @log_execution_time()
        def my_function():
            return 42

        assert my_function.__name__ == "my_function"

    def test_decorator_logs_message(self, caplog):
        logger = logging.getLogger("test.execution_time")

        @log_execution_time(logger=logger)
        def slow_function():
            time.sleep(0.01)
            return "done"

        with caplog.at_level(logging.DEBUG, logger="test.execution_time"):
            result = slow_function()

        assert result == "done"
        assert any("slow_function" in record.message for record in caplog.records)
        assert any("executed in" in record.message for record in caplog.records)

    def test_decorator_with_threshold(self, caplog):
        logger = logging.getLogger("test.threshold")

        @log_execution_time(logger=logger, threshold_ms=1000.0)
        def fast_function():
            return "quick"

        with caplog.at_level(logging.DEBUG, logger="test.threshold"):
            result = fast_function()

        assert result == "quick"
        # Should NOT log because execution was under threshold
        assert not any("fast_function" in record.message for record in caplog.records)

    def test_decorator_logs_when_threshold_exceeded(self, caplog):
        logger = logging.getLogger("test.threshold_exceeded")

        @log_execution_time(logger=logger, threshold_ms=0.0)
        def any_function():
            return "done"

        with caplog.at_level(logging.DEBUG, logger="test.threshold_exceeded"):
            any_function()

        assert any("any_function" in record.message for record in caplog.records)

    def test_decorator_with_exception(self, caplog):
        logger = logging.getLogger("test.exception")

        @log_execution_time(logger=logger)
        def failing_function():
            raise ValueError("boom")

        with caplog.at_level(logging.DEBUG, logger="test.exception"):
            with pytest.raises(ValueError, match="boom"):
                failing_function()

        # Should still log the execution time
        assert any("failing_function" in record.message for record in caplog.records)

    def test_decorator_with_custom_level(self, caplog):
        logger = logging.getLogger("test.custom_level")

        @log_execution_time(logger=logger, level=logging.WARNING)
        def warn_function():
            return "done"

        with caplog.at_level(logging.WARNING, logger="test.custom_level"):
            warn_function()

        assert any(
            record.levelno == logging.WARNING for record in caplog.records
        )


# ---------------------------------------------------------------------------
# Test: log_module_call decorator
# ---------------------------------------------------------------------------


class TestLogModuleCall:
    """Tests for the log_module_call decorator."""

    def test_logs_call_and_return(self, caplog):
        logger = logging.getLogger("test.module_call")

        @log_module_call(logger=logger)
        def my_func(x):
            return x * 2

        with caplog.at_level(logging.DEBUG, logger="test.module_call"):
            result = my_func(5)

        assert result == 10
        messages = [record.message for record in caplog.records]
        assert any("CALL" in m and "my_func" in m for m in messages)
        assert any("RETURN" in m and "my_func" in m for m in messages)

    def test_logs_raised_on_exception(self, caplog):
        logger = logging.getLogger("test.module_call_exc")

        @log_module_call(logger=logger)
        def fail_func():
            raise RuntimeError("fail")

        with caplog.at_level(logging.DEBUG, logger="test.module_call_exc"):
            with pytest.raises(RuntimeError):
                fail_func()

        messages = [record.message for record in caplog.records]
        assert any("CALL" in m for m in messages)
        assert any("RAISED" in m for m in messages)
        assert not any("RETURN" in m for m in messages)

    def test_preserves_function_metadata(self):
        @log_module_call()
        def documented():
            """This is a docstring."""
            return 1

        assert documented.__name__ == "documented"
        assert documented.__doc__ == "This is a docstring."


# ---------------------------------------------------------------------------
# Test: MetricsCollector
# ---------------------------------------------------------------------------


class TestMetricsCollector:
    """Tests for the MetricsCollector class."""

    def test_increment_counter(self):
        m = MetricsCollector()
        m.increment("requests")
        assert m.get_counter("requests") == 1

    def test_increment_counter_by_value(self):
        m = MetricsCollector()
        m.increment("requests", 5)
        assert m.get_counter("requests") == 5

    def test_increment_counter_multiple_times(self):
        m = MetricsCollector()
        m.increment("requests")
        m.increment("requests")
        m.increment("requests")
        assert m.get_counter("requests") == 3

    def test_decrement_counter(self):
        m = MetricsCollector()
        m.increment("active", 10)
        m.decrement("active", 3)
        assert m.get_counter("active") == 7

    def test_get_counter_default(self):
        m = MetricsCollector()
        assert m.get_counter("nonexistent") == 0

    def test_set_gauge(self):
        m = MetricsCollector()
        m.gauge("cpu_usage", 75.5)
        assert m.get_gauge("cpu_usage") == 75.5

    def test_get_gauge_default(self):
        m = MetricsCollector()
        assert m.get_gauge("nonexistent") is None

    def test_update_gauge(self):
        m = MetricsCollector()
        m.gauge("memory", 50.0)
        m.gauge("memory", 80.0)
        assert m.get_gauge("memory") == 80.0

    def test_record_timer(self):
        m = MetricsCollector()
        m.timer("latency", 100.0)
        m.timer("latency", 200.0)
        m.timer("latency", 300.0)

        stats = m.get_timer_stats("latency")
        assert stats["count"] == 3.0
        assert stats["min"] == 100.0
        assert stats["max"] == 300.0
        assert stats["mean"] == 200.0
        assert stats["total"] == 600.0

    def test_timer_stats_empty(self):
        m = MetricsCollector()
        assert m.get_timer_stats("nonexistent") == {}

    def test_timeit_context_manager(self):
        m = MetricsCollector()
        with m.timeit("operation"):
            time.sleep(0.01)

        stats = m.get_timer_stats("operation")
        assert stats["count"] == 1.0
        assert stats["min"] >= 0.0

    def test_timeit_records_duration(self):
        m = MetricsCollector()
        with m.timeit("sleep"):
            time.sleep(0.05)

        stats = m.get_timer_stats("sleep")
        assert stats["min"] >= 40.0  # at least 40ms

    def test_reset(self):
        m = MetricsCollector()
        m.increment("counter")
        m.gauge("gauge", 42.0)
        m.timer("timer", 100.0)

        m.reset()

        assert m.get_counter("counter") == 0
        assert m.get_gauge("gauge") is None
        assert m.get_timer_stats("timer") == {}

    def test_snapshot(self):
        m = MetricsCollector()
        m.increment("requests", 5)
        m.gauge("cpu", 50.0)
        m.timer("latency", 100.0)

        snap = m.snapshot()
        assert snap["counters"]["requests"] == 5
        assert snap["gauges"]["cpu"] == 50.0
        assert "latency" in snap["timers"]
        assert snap["timers"]["latency"]["count"] == 1.0


# ---------------------------------------------------------------------------
# Test: HealthCheck
# ---------------------------------------------------------------------------


class TestHealthCheck:
    """Tests for the HealthCheck class."""

    def test_register_and_check(self):
        hc = HealthCheck()
        hc.register("database", lambda: True)
        result = hc.check_all()
        assert result["status"] == "healthy"
        assert result["checks"]["database"]["healthy"] is True

    def test_unhealthy_check(self):
        hc = HealthCheck()
        hc.register("database", lambda: False)
        result = hc.check_all()
        assert result["status"] == "unhealthy"
        assert result["checks"]["database"]["healthy"] is False

    def test_mixed_checks(self):
        hc = HealthCheck()
        hc.register("db", lambda: True)
        hc.register("cache", lambda: False)
        result = hc.check_all()
        assert result["status"] == "unhealthy"

    def test_check_with_exception(self):
        hc = HealthCheck()

        def bad_check():
            raise RuntimeError("connection failed")

        hc.register("failing", bad_check)
        result = hc.check_all()
        assert result["status"] == "unhealthy"
        assert result["checks"]["failing"]["healthy"] is False

    def test_is_healthy_true(self):
        hc = HealthCheck()
        hc.register("a", lambda: True)
        hc.register("b", lambda: True)
        assert hc.is_healthy() is True

    def test_is_healthy_false(self):
        hc = HealthCheck()
        hc.register("a", lambda: True)
        hc.register("b", lambda: False)
        assert hc.is_healthy() is False

    def test_unregister(self):
        hc = HealthCheck()
        hc.register("test", lambda: True)
        hc.unregister("test")
        result = hc.check_all()
        assert result["status"] == "healthy"
        assert "test" not in result["checks"]

    def test_check_all_has_timestamp(self):
        hc = HealthCheck()
        hc.register("x", lambda: True)
        result = hc.check_all()
        assert "timestamp" in result
        assert isinstance(result["timestamp"], float)

    def test_multiple_checks_all_healthy(self):
        hc = HealthCheck()
        for i in range(5):
            hc.register(f"service_{i}", lambda i=i: True)
        result = hc.check_all()
        assert result["status"] == "healthy"
        assert len(result["checks"]) == 5


# ---------------------------------------------------------------------------
# Test: Integration — decorators work together
# ---------------------------------------------------------------------------


class TestIntegration:
    """Integration tests combining multiple observability features."""

    def test_decorator_on_real_module(self):
        """Test that decorators work on actual platform modules."""
        from acquisition_platform.valuation import ValuationEngine

        engine = ValuationEngine()
        result = engine.comparable_valuation(metric=100.0, multiple=2.0)
        assert result.value == 200.0
        assert result.method == "Comps"

    def test_metrics_with_pipeline(self):
        """Test metrics collection during pipeline execution."""
        from acquisition_platform.orchestrator import AcquisitionPipeline, PipelineConfig

        m = MetricsCollector()
        pipeline = AcquisitionPipeline()
        entities = [
            {"id": "b1", "budget": 500_000, "preferences": {"category": "saas"}},
            {"id": "s1", "asking_price": 400_000, "attributes": {"category": "saas"}},
        ]

        with m.timeit("pipeline_run"):
            result = pipeline.run(entities, PipelineConfig())

        stats = m.get_timer_stats("pipeline_run")
        assert stats["count"] == 1.0
        assert stats["min"] >= 0.0
        assert result is not None

    def test_health_check_with_metrics(self):
        """Test health check that uses metrics collector."""
        m = MetricsCollector()
        m.increment("errors", 0)

        hc = HealthCheck()
        hc.register("no_errors", lambda: m.get_counter("errors") == 0)

        assert hc.is_healthy() is True

        m.increment("errors", 1)
        assert hc.is_healthy() is False
