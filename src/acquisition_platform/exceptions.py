"""Custom exceptions for the acquisition platform.

This module defines the exception hierarchy used across all modules
for consistent error handling and input validation.
"""


class AcquisitionPlatformError(Exception):
    """Base exception for all acquisition platform errors.

    All custom exceptions inherit from this class, allowing callers
    to catch all platform-specific errors with a single except clause.
    """

    pass


class ValidationError(AcquisitionPlatformError, ValueError):
    """Raised when input validation fails.

    This exception is raised when a method receives invalid input
    that does not meet the documented constraints (e.g., negative
    values where positive are required, values outside valid ranges).
    """

    pass


class DivisionByZeroError(AcquisitionPlatformError, ZeroDivisionError):
    """Raised when a division by zero would occur.

    This exception is raised in edge cases like DCF valuation where
    the discount rate equals the terminal growth rate, causing a
    division by zero in the Gordon Growth Model formula.
    """

    pass


class EmptyInputError(AcquisitionPlatformError, ValueError):
    """Raised when an empty collection is provided where non-empty is required.

    This exception is raised when a method requires at least one
    element in a collection but receives an empty list.
    """

    pass


class InvalidRangeError(AcquisitionPlatformError, ValueError):
    """Raised when a value is outside the valid range.

    This exception is raised when a numeric value falls outside
    its documented valid range (e.g., a probability outside [0, 1]).
    """

    pass
