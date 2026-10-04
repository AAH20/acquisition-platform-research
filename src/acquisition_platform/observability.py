"""Observability utilities for the acquisition platform.

Provides centralized logging, execution-time decorators, metrics collection,
and health checks for all modules.
"""

from __future__ import annotations

import functools
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, TypeVar

# ---------------------------------------------------------------------------
# Logger factory
# ---------------------------------------------------------------------------

_DEFAULT_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_configured = False


def _ensure_configured() -> None:
    """Configure the root logger once with a standard format."""
    global _configured
    if not _configured:
        logging.basicConfig(
            level=logging.INFO,
            format=_DEFAULT_FORMAT,
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a named logger, configuring the root logger on first call.

    Args:
        name: Logger name (typically ``__name__``).

    Returns:
        A configured :class:`logging.Logger` instance.
    """
    _ensure_configured()
    return logging.getLogger(name)


# ---------------------------------------------------------------------------
# Decorators
# ---------------------------------------------------------------------------

F = TypeVar("F", bound=Callable[..., Any])


def log_execution_time(
    logger: logging.Logger | None = None,
    level: int = logging.DEBUG,
    threshold_ms: float | None = None,
) -> Callable[[F], F]:
    """Decorator that logs the execution time of the wrapped function.

    Args:
        logger: Logger to use. If ``None``, a logger named after the
            function's module is created automatically.
        level: Logging level for the timing message.
        threshold_ms: If set, only log when execution exceeds this
            many milliseconds.

    Returns:
        The decorator.
    """

    def decorator(func: F) -> F:
        _logger = logger if logger is not None else get_logger(func.__module__)

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                elapsed_ms = (time.perf_counter() - start) * 1000
                if threshold_ms is None or elapsed_ms >= threshold_ms:
                    _logger.log(
                        level,
                        "%s executed in %.3f ms",
                        func.__qualname__,
                        elapsed_ms,
                    )

        return wrapper  # type: ignore[return-value]

    return decorator


def log_module_call(
    logger: logging.Logger | None = None,
    level: int = logging.DEBUG,
) -> Callable[[F], F]:
    """Decorator that logs entry and exit of the wrapped function.

    Args:
        logger: Logger to use. If ``None``, a logger named after the
            function's module is created automatically.
        level: Logging level for the call message.

    Returns:
        The decorator.
    """

    def decorator(func: F) -> F:
        _logger = logger if logger is not None else get_logger(func.__module__)

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            _logger.log(level, "CALL %s", func.__qualname__)
            try:
                result = func(*args, **kwargs)
            except Exception:
                _logger.log(level, "RAISED %s", func.__qualname__)
                raise
            _logger.log(level, "RETURN %s", func.__qualname__)
            return result

        return wrapper  # type: ignore[return-value]

    return decorator


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


@dataclass
class MetricsCollector:
    """Collects counters, gauges, and timers.

    Thread-unsafe by design — intended for single-threaded or
    externally-synchronized use.
    """

    counters: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    gauges: dict[str, float] = field(default_factory=dict)
    timers: dict[str, list[float]] = field(default_factory=lambda: defaultdict(list))

    def increment(self, name: str, value: int = 1) -> None:
        """Increment a counter by ``value`` (default 1)."""
        self.counters[name] += value

    def decrement(self, name: str, value: int = 1) -> None:
        """Decrement a counter by ``value`` (default 1)."""
        self.counters[name] -= value

    def gauge(self, name: str, value: float) -> None:
        """Set a gauge to ``value``."""
        self.gauges[name] = value

    def timer(self, name: str, value_ms: float) -> None:
        """Record a timer observation in milliseconds."""
        self.timers[name].append(value_ms)

    def timeit(self, name: str) -> "_TimerContext":
        """Return a context manager that records its duration as a timer.

        Example::

            with metrics.timeit("my_operation"):
                do_work()
        """
        return _TimerContext(self, name)

    def get_counter(self, name: str) -> int:
        """Return the current value of a counter (0 if not set)."""
        return self.counters.get(name, 0)

    def get_gauge(self, name: str) -> float | None:
        """Return the current value of a gauge, or ``None`` if not set."""
        return self.gauges.get(name)

    def get_timer_stats(self, name: str) -> dict[str, float]:
        """Return count, min, max, mean, total for a timer.

        Returns an empty dict if the timer has no observations.
        """
        values = self.timers.get(name, [])
        if not values:
            return {}
        return {
            "count": float(len(values)),
            "min": min(values),
            "max": max(values),
            "mean": sum(values) / len(values),
            "total": sum(values),
        }

    def reset(self) -> None:
        """Reset all counters, gauges, and timers."""
        self.counters.clear()
        self.gauges.clear()
        self.timers.clear()

    def snapshot(self) -> dict[str, Any]:
        """Return a snapshot of all metrics as a plain dict."""
        return {
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "timers": {
                name: self.get_timer_stats(name) for name in self.timers
            },
        }


class _TimerContext:
    """Context manager returned by :meth:`MetricsCollector.timeit`."""

    def __init__(self, collector: MetricsCollector, name: str) -> None:
        self._collector = collector
        self._name = name
        self._start: float | None = None

    def __enter__(self) -> _TimerContext:
        self._start = time.perf_counter()
        return self

    def __exit__(self, *exc: Any) -> None:
        if self._start is not None:
            elapsed_ms = (time.perf_counter() - self._start) * 1000
            self._collector.timer(self._name, elapsed_ms)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@dataclass
class HealthCheck:
    """Simple health check registry.

    Each check is a zero-argument callable that returns ``True`` if the
    component is healthy. :meth:`check_all` runs every registered check
    and returns a summary dict.
    """

    _checks: dict[str, Callable[[], bool]] = field(default_factory=dict)

    def register(self, name: str, check: Callable[[], bool]) -> None:
        """Register a health check.

        Args:
            name: Human-readable name for the check.
            check: Zero-argument callable returning ``True`` if healthy.
        """
        self._checks[name] = check

    def unregister(self, name: str) -> None:
        """Remove a previously registered check."""
        self._checks.pop(name, None)

    def check_all(self) -> dict[str, Any]:
        """Run all registered checks and return a summary.

        Returns:
            Dict with ``status`` (``"healthy"`` or ``"unhealthy"``),
            ``checks`` (per-check ``{name: {"healthy": bool}}``),
            and ``timestamp``.
        """
        results: dict[str, dict[str, bool]] = {}
        all_healthy = True
        for name, check in self._checks.items():
            try:
                healthy = check()
            except Exception:
                healthy = False
            results[name] = {"healthy": healthy}
            if not healthy:
                all_healthy = False
        return {
            "status": "healthy" if all_healthy else "unhealthy",
            "checks": results,
            "timestamp": time.time(),
        }

    def is_healthy(self) -> bool:
        """Return ``True`` only if all registered checks pass."""
        return bool(self.check_all()["status"] == "healthy")
