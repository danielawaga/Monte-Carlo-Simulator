"""Custom exceptions for the simulator."""


class MonteCarloError(Exception):
    """Base exception for business errors."""


class ValidationError(MonteCarloError):
    """Raised when model or simulation input is invalid."""
