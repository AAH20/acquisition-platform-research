"""Security module for the acquisition platform.

Provides rate limiting, input sanitization, audit logging, and security
configuration to protect the platform against abuse and ensure
accountability for sensitive operations.
"""

from __future__ import annotations

import math
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Callable


class RateLimitExceeded(Exception):
    """Raised when a rate limit is exceeded."""

    def __init__(self, key: str, retry_after: float) -> None:
        self.key = key
        self.retry_after = retry_after
        super().__init__(
            f"Rate limit exceeded for '{key}'. Retry after {retry_after:.1f}s."
        )


class RateLimiter:
    """Token-bucket rate limiter.

    Tracks request counts per key within a sliding time window.
    Each key is allowed up to ``max_requests`` within ``window_seconds``.
    """

    def __init__(self, max_requests: int = 100, window_seconds: float = 60.0) -> None:
        if max_requests <= 0:
            raise ValueError("max_requests must be positive")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, deque[float]] = defaultdict(deque)

    def is_allowed(self, key: str) -> bool:
        """Check if a request is allowed without raising.

        Returns True if the request is within the rate limit, False otherwise.
        """
        try:
            self.check(key)
            return True
        except RateLimitExceeded:
            return False

    def check(self, key: str) -> None:
        """Check rate limit and raise RateLimitExceeded if over limit.

        Args:
            key: The rate limit key (e.g., user ID, IP address).

        Raises:
            RateLimitExceeded: If the rate limit has been exceeded.
        """
        now = time.monotonic()
        window_start = now - self.window_seconds

        # Clean old entries
        req_deque = self._requests[key]
        while req_deque and req_deque[0] < window_start:
            req_deque.popleft()

        if len(req_deque) >= self.max_requests:
            retry_after = req_deque[0] + self.window_seconds - now
            raise RateLimitExceeded(key, max(0.0, retry_after))

        req_deque.append(now)

    def get_remaining(self, key: str) -> int:
        """Get remaining requests for a key within the current window."""
        now = time.monotonic()
        window_start = now - self.window_seconds

        req_deque = self._requests[key]
        while req_deque and req_deque[0] < window_start:
            req_deque.popleft()

        return max(0, self.max_requests - len(req_deque))

    def reset(self, key: str) -> None:
        """Reset rate limit for a specific key."""
        self._requests.pop(key, None)


class InputSanitizer:
    """Sanitizes user inputs to prevent injection and ensure data quality."""

    def __init__(self, max_length: int = 10000) -> None:
        self.max_length = max_length

    def sanitize_string(self, value: Any) -> str:
        """Sanitize a string value.

        - Converts to string if not already
        - Strips leading/trailing whitespace
        - Removes control characters (null bytes, newlines, etc.)
        - Truncates to max_length

        Args:
            value: The value to sanitize.

        Returns:
            Sanitized string.
        """
        if value is None:
            return ""
        result = str(value)
        # Remove control characters
        result = "".join(ch for ch in result if ch >= " " or ch == "\t")
        result = result.strip()
        if len(result) > self.max_length:
            result = result[: self.max_length]
        return result

    def sanitize_number(
        self,
        value: Any,
        min_val: float | None = None,
        max_val: float | None = None,
    ) -> float:
        """Sanitize a numeric value.

        - Converts to float
        - Replaces NaN/Inf with min_val (or 0)
        - Clamps to [min_val, max_val] if bounds provided

        Args:
            value: The value to sanitize.
            min_val: Minimum allowed value.
            max_val: Maximum allowed value.

        Returns:
            Sanitized float.
        """
        try:
            result = float(value)
        except (TypeError, ValueError):
            result = 0.0

        if math.isnan(result):
            result = min_val if min_val is not None else 0.0
        elif math.isinf(result):
            if result > 0:
                result = max_val if max_val is not None else result
            else:
                result = min_val if min_val is not None else result

        if min_val is not None and result < min_val:
            result = min_val
        if max_val is not None and result > max_val:
            result = max_val

        return result

    def sanitize_dict(
        self,
        data: dict[str, Any],
        max_depth: int = 5,
        _depth: int = 0,
    ) -> dict[str, Any]:
        """Recursively sanitize all values in a dict.

        - String values are sanitized via sanitize_string
        - Numeric values are clamped to [0, 1000000]
        - Nested dicts are recursively sanitized
        - Lists are sanitized element-wise

        Args:
            data: The dict to sanitize.
            max_depth: Maximum recursion depth for nested dicts.
            _depth: Current recursion depth (internal use).

        Returns:
            Sanitized dict.
        """
        if not isinstance(data, dict):
            return {}
        if _depth >= max_depth:
            return {}

        result: dict[str, Any] = {}
        for key, value in data.items():
            safe_key = self.sanitize_string(key)
            if isinstance(value, str):
                result[safe_key] = self.sanitize_string(value)
            elif isinstance(value, (int, float)):
                result[safe_key] = self.sanitize_number(value, min_val=0, max_val=1_000_000)
            elif isinstance(value, dict):
                result[safe_key] = self.sanitize_dict(value, max_depth, _depth + 1)
            elif isinstance(value, list):
                result[safe_key] = [
                    self.sanitize_string(v) if isinstance(v, str)
                    else self.sanitize_number(v, min_val=0, max_val=1_000_000) if isinstance(v, (int, float))
                    else v
                    for v in value
                ]
            else:
                result[safe_key] = value
        return result


class AuditLogger:
    """Audit logger for tracking sensitive operations.

    Maintains an in-memory audit trail of all logged actions,
    queryable by user.
    """

    def __init__(self, max_entries: int = 10000) -> None:
        self.max_entries = max_entries
        self._trail: list[dict[str, Any]] = []

    def log_access(self, user: str, resource: str, action: str) -> None:
        """Log an access event.

        Args:
            user: The user performing the action.
            resource: The resource being accessed.
            action: The action performed (e.g., "read", "write").
        """
        self._append({
            "timestamp": time.time(),
            "user": user,
            "resource": resource,
            "action": action,
            "details": {},
        })

    def log_action(self, user: str, action: str, details: dict[str, Any] | None = None) -> None:
        """Log a general action.

        Args:
            user: The user performing the action.
            action: The action name (e.g., "delete", "modify").
            details: Optional dict with additional context.
        """
        self._append({
            "timestamp": time.time(),
            "user": user,
            "resource": "",
            "action": action,
            "details": details or {},
        })

    def get_audit_trail(self, user: str | None = None) -> list[dict[str, Any]]:
        """Get audit trail entries.

        Args:
            user: If provided, filter entries by this user.

        Returns:
            List of audit trail entries.
        """
        if user is None:
            return list(self._trail)
        return [entry for entry in self._trail if entry["user"] == user]

    def clear(self) -> None:
        """Clear all audit trail entries."""
        self._trail.clear()

    def _append(self, entry: dict[str, Any]) -> None:
        """Append an entry, maintaining max_entries limit."""
        self._trail.append(entry)
        if len(self._trail) > self.max_entries:
            self._trail = self._trail[-self.max_entries :]


@dataclass
class SecurityConfig:
    """Security configuration for the acquisition platform.

    Attributes:
        rate_limit: RateLimiter instance for request throttling.
        audit_enabled: Whether audit logging is active.
        sanitize_enabled: Whether input sanitization is active.
    """

    rate_limit: RateLimiter = field(
        default_factory=lambda: RateLimiter(max_requests=100, window_seconds=60)
    )
    audit_enabled: bool = True
    sanitize_enabled: bool = True


# ---------------------------------------------------------------------------
# Security decorator for public methods
# ---------------------------------------------------------------------------

_default_rate_limiter = RateLimiter(max_requests=100, window_seconds=60)
_default_audit_logger = AuditLogger()
_default_sanitizer = InputSanitizer()


def secure_method(
    rate_limiter: RateLimiter | None = None,
    audit_logger: AuditLogger | None = None,
    sanitizer: InputSanitizer | None = None,
    user_key: str = "user_id",
    action: str | None = None,
) -> Callable[..., Any]:
    """Decorator that adds rate limiting, input sanitization, and audit logging.

    Args:
        rate_limiter: RateLimiter instance (uses default if None).
        audit_logger: AuditLogger instance (uses default if None).
        sanitizer: InputSanitizer instance (uses default if None).
        user_key: The kwarg name to use as the rate limit key.
        action: Action name for audit logging (defaults to function name).

    Returns:
        Decorated function with security checks.
    """
    import functools

    rl = rate_limiter or _default_rate_limiter
    al = audit_logger or _default_audit_logger
    sc = sanitizer or _default_sanitizer

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Rate limiting
            key = kwargs.get(user_key, "default")
            rl.check(key)

            # Input sanitization for string arguments
            if sc is not None:
                new_kwargs: dict[str, Any] = {}
                for k, v in kwargs.items():
                    if isinstance(v, str):
                        new_kwargs[k] = sc.sanitize_string(v)
                    elif isinstance(v, dict):
                        new_kwargs[k] = sc.sanitize_dict(v)
                    else:
                        new_kwargs[k] = v
                kwargs = new_kwargs

            # Audit logging
            if al is not None:
                al.log_action(
                    user=key,
                    action=action or func.__name__,
                    details={"args_count": len(args), "kwargs_keys": list(kwargs.keys())},
                )

            return func(*args, **kwargs)

        return wrapper

    return decorator