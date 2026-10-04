"""Tests for security module — rate limiting, input sanitization, audit logging."""
import time
import pytest
from acquisition_platform.security import (
    RateLimiter,
    InputSanitizer,
    AuditLogger,
    SecurityConfig,
    RateLimitExceeded,
)


# ---------------------------------------------------------------------------
# RateLimiter tests
# ---------------------------------------------------------------------------


class TestRateLimiter:
    """Tests for the RateLimiter class."""

    def test_allows_requests_within_limit(self):
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        assert limiter.is_allowed("user1") is True
        assert limiter.is_allowed("user1") is True
        assert limiter.is_allowed("user1") is True

    def test_blocks_requests_over_limit(self):
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        limiter.is_allowed("user1")
        limiter.is_allowed("user1")
        assert limiter.is_allowed("user1") is False

    def test_rate_limit_exceeded_raises(self):
        limiter = RateLimiter(max_requests=1, window_seconds=60)
        limiter.is_allowed("user1")
        with pytest.raises(RateLimitExceeded):
            limiter.check("user1")

    def test_different_keys_independent(self):
        limiter = RateLimiter(max_requests=1, window_seconds=60)
        assert limiter.is_allowed("user1") is True
        assert limiter.is_allowed("user2") is True
        assert limiter.is_allowed("user1") is False

    def test_window_expires_allows_again(self):
        limiter = RateLimiter(max_requests=1, window_seconds=0.05)
        assert limiter.is_allowed("user1") is True
        assert limiter.is_allowed("user1") is False
        time.sleep(0.06)
        assert limiter.is_allowed("user1") is True

    def test_get_remaining(self):
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        assert limiter.get_remaining("user1") == 3
        limiter.is_allowed("user1")
        assert limiter.get_remaining("user1") == 2
        limiter.is_allowed("user1")
        limiter.is_allowed("user1")
        assert limiter.get_remaining("user1") == 0

    def test_reset(self):
        limiter = RateLimiter(max_requests=1, window_seconds=60)
        limiter.is_allowed("user1")
        assert limiter.is_allowed("user1") is False
        limiter.reset("user1")
        assert limiter.is_allowed("user1") is True

    def test_invalid_params_raise(self):
        with pytest.raises(ValueError):
            RateLimiter(max_requests=0, window_seconds=60)
        with pytest.raises(ValueError):
            RateLimiter(max_requests=1, window_seconds=0)


# ---------------------------------------------------------------------------
# InputSanitizer tests
# ---------------------------------------------------------------------------


class TestInputSanitizer:
    """Tests for the InputSanitizer class."""

    def test_sanitize_string_strips_whitespace(self):
        sanitizer = InputSanitizer()
        assert sanitizer.sanitize_string("  hello  ") == "hello"

    def test_sanitize_string_removes_control_chars(self):
        sanitizer = InputSanitizer()
        assert sanitizer.sanitize_string("hello\x00world") == "helloworld"
        assert sanitizer.sanitize_string("hello\nworld") == "helloworld"

    def test_sanitize_string_truncates_long_strings(self):
        sanitizer = InputSanitizer(max_length=10)
        result = sanitizer.sanitize_string("a" * 100)
        assert len(result) == 10

    def test_sanitize_string_handles_non_string(self):
        sanitizer = InputSanitizer()
        assert sanitizer.sanitize_string(123) == "123"
        assert sanitizer.sanitize_string(None) == ""

    def test_sanitize_number_clamps_to_range(self):
        sanitizer = InputSanitizer()
        assert sanitizer.sanitize_number(5, min_val=0, max_val=10) == 5
        assert sanitizer.sanitize_number(-5, min_val=0, max_val=10) == 0
        assert sanitizer.sanitize_number(15, min_val=0, max_val=10) == 10

    def test_sanitize_number_handles_nan_inf(self):
        sanitizer = InputSanitizer()
        assert sanitizer.sanitize_number(float("nan"), min_val=0, max_val=10) == 0
        assert sanitizer.sanitize_number(float("inf"), min_val=0, max_val=10) == 10
        assert sanitizer.sanitize_number(float("-inf"), min_val=0, max_val=10) == 0

    def test_sanitize_number_no_bounds(self):
        sanitizer = InputSanitizer()
        assert sanitizer.sanitize_number(42.0) == 42.0

    def test_sanitize_dict_sanitizes_values(self):
        sanitizer = InputSanitizer()
        data = {"name": "  hello  ", "count": 15, "nested": {"value": "  world  "}}
        result = sanitizer.sanitize_dict(data)
        assert result["name"] == "hello"
        assert result["count"] == 15.0  # within default max
        assert result["nested"]["value"] == "world"

    def test_sanitize_dict_handles_non_dict(self):
        sanitizer = InputSanitizer()
        assert sanitizer.sanitize_dict("not a dict") == {}
        assert sanitizer.sanitize_dict(None) == {}


# ---------------------------------------------------------------------------
# AuditLogger tests
# ---------------------------------------------------------------------------


class TestAuditLogger:
    """Tests for the AuditLogger class."""

    def test_log_access_creates_entry(self):
        logger = AuditLogger()
        logger.log_access("user1", "resource1", "read")
        trail = logger.get_audit_trail("user1")
        assert len(trail) == 1
        assert trail[0]["user"] == "user1"
        assert trail[0]["resource"] == "resource1"
        assert trail[0]["action"] == "read"

    def test_log_action_creates_entry(self):
        logger = AuditLogger()
        logger.log_action("user1", "delete", {"target": "resource1"})
        trail = logger.get_audit_trail("user1")
        assert len(trail) == 1
        assert trail[0]["action"] == "delete"
        assert trail[0]["details"] == {"target": "resource1"}

    def test_get_audit_trail_filters_by_user(self):
        logger = AuditLogger()
        logger.log_access("user1", "r1", "read")
        logger.log_access("user2", "r2", "read")
        trail = logger.get_audit_trail("user1")
        assert len(trail) == 1
        assert trail[0]["user"] == "user1"

    def test_get_audit_trail_empty_for_unknown_user(self):
        logger = AuditLogger()
        logger.log_access("user1", "r1", "read")
        trail = logger.get_audit_trail("unknown")
        assert trail == []

    def test_audit_trail_has_timestamp(self):
        logger = AuditLogger()
        logger.log_access("user1", "r1", "read")
        trail = logger.get_audit_trail("user1")
        assert "timestamp" in trail[0]

    def test_clear_audit_trail(self):
        logger = AuditLogger()
        logger.log_access("user1", "r1", "read")
        logger.clear()
        assert logger.get_audit_trail("user1") == []

    def test_max_entries_limits_trail(self):
        logger = AuditLogger(max_entries=3)
        for i in range(5):
            logger.log_access("user1", f"r{i}", "read")
        trail = logger.get_audit_trail("user1")
        assert len(trail) == 3


# ---------------------------------------------------------------------------
# SecurityConfig tests
# ---------------------------------------------------------------------------


class TestSecurityConfig:
    """Tests for the SecurityConfig dataclass."""

    def test_default_config(self):
        config = SecurityConfig()
        assert config.rate_limit is not None
        assert isinstance(config.rate_limit, RateLimiter)
        assert config.audit_enabled is True
        assert config.sanitize_enabled is True

    def test_custom_config(self):
        limiter = RateLimiter(max_requests=100, window_seconds=300)
        config = SecurityConfig(
            rate_limit=limiter,
            audit_enabled=False,
            sanitize_enabled=False,
        )
        assert config.rate_limit is limiter
        assert config.audit_enabled is False
        assert config.sanitize_enabled is False

    def test_config_with_custom_rate_limiter(self):
        limiter = RateLimiter(max_requests=5, window_seconds=10)
        config = SecurityConfig(rate_limit=limiter)
        assert config.rate_limit.max_requests == 5
        assert config.rate_limit.window_seconds == 10


# ---------------------------------------------------------------------------
# Integration: Rate limiting with modules
# ---------------------------------------------------------------------------


class TestRateLimitExceeded:
    """Test that rate limit exceeded is properly detected."""

    def test_rate_limiter_check_raises(self):
        limiter = RateLimiter(max_requests=1, window_seconds=60)
        limiter.check("user1")  # first call OK
        with pytest.raises(RateLimitExceeded):
            limiter.check("user1")  # second call raises

    def test_rate_limiter_is_allowed_does_not_raise(self):
        limiter = RateLimiter(max_requests=1, window_seconds=60)
        assert limiter.is_allowed("user1") is True
        assert limiter.is_allowed("user1") is False  # no exception

    def test_rate_limiter_reset_allows_again(self):
        limiter = RateLimiter(max_requests=1, window_seconds=60)
        limiter.check("user1")
        limiter.reset("user1")
        limiter.check("user1")  # should not raise
