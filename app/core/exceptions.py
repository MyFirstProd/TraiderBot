class AppError(Exception):
    """Base application exception."""


class UnauthorizedError(AppError):
    """Authentication or authorization failure."""


class ValidationError(AppError):
    """Business rule validation failure."""


class ExternalServiceError(AppError):
    """External dependency failure."""


class CircuitBreakerOpenError(AppError):
    """Trading is blocked by circuit breaker."""
