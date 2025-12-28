"""
Custom exceptions and error handling for the Emotional Companion Bot.
Provides structured error handling with proper logging and user-friendly messages.
"""

import logging
from typing import Optional, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)

class BotErrorCode(Enum):
    """Error codes for different types of failures."""
    CONFIG_ERROR = "config_error"
    API_ERROR = "api_error"
    DATABASE_ERROR = "database_error"
    MEMORY_ERROR = "memory_error"
    VALIDATION_ERROR = "validation_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    PERMISSION_ERROR = "permission_error"
    NETWORK_ERROR = "network_error"
    UNKNOWN_ERROR = "unknown_error"

class BotException(Exception):
    """Base exception class for bot errors."""

    def __init__(
        self,
        message: str,
        error_code: BotErrorCode = BotErrorCode.UNKNOWN_ERROR,
        user_message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        should_retry: bool = False
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.user_message = user_message or self._get_default_user_message()
        self.details = details or {}
        self.should_retry = should_retry

        # Log the error
        self._log_error()

    def _log_error(self):
        """Log the error with appropriate level."""
        log_message = f"{self.error_code.value}: {self.message}"
        if self.details:
            log_message += f" | Details: {self.details}"

        if self.error_code in [BotErrorCode.API_ERROR, BotErrorCode.NETWORK_ERROR]:
            logger.warning(log_message)
        else:
            logger.error(log_message)

    def _get_default_user_message(self) -> str:
        """Get default user-friendly message based on error code."""
        defaults = {
            BotErrorCode.CONFIG_ERROR: "Error de configuración del bot.",
            BotErrorCode.API_ERROR: "Error al comunicarme con el servicio de IA.",
            BotErrorCode.DATABASE_ERROR: "Error en la base de datos.",
            BotErrorCode.MEMORY_ERROR: "Error en el sistema de memoria.",
            BotErrorCode.VALIDATION_ERROR: "Los datos proporcionados no son válidos.",
            BotErrorCode.RATE_LIMIT_ERROR: "Demasiadas solicitudes. Inténtalo en unos momentos.",
            BotErrorCode.PERMISSION_ERROR: "No tienes permisos para esta acción.",
            BotErrorCode.NETWORK_ERROR: "Error de conexión. Verifica tu internet.",
            BotErrorCode.UNKNOWN_ERROR: "Ha ocurrido un error inesperado."
        }
        return defaults.get(self.error_code, "Ha ocurrido un error.")

class ConfigurationError(BotException):
    """Raised when there's a configuration issue."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            error_code=BotErrorCode.CONFIG_ERROR,
            **kwargs
        )

class APIError(BotException):
    """Raised when there's an API communication issue."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            error_code=BotErrorCode.API_ERROR,
            should_retry=True,
            **kwargs
        )

class DatabaseError(BotException):
    """Raised when there's a database operation issue."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            error_code=BotErrorCode.DATABASE_ERROR,
            **kwargs
        )

class MemoryError(BotException):
    """Raised when there's a memory system issue."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            error_code=BotErrorCode.MEMORY_ERROR,
            **kwargs
        )

class ValidationError(BotException):
    """Raised when input validation fails."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            error_code=BotErrorCode.VALIDATION_ERROR,
            **kwargs
        )

class RateLimitError(BotException):
    """Raised when rate limits are exceeded."""

    def __init__(self, message: str = "Rate limit exceeded", **kwargs):
        super().__init__(
            message,
            error_code=BotErrorCode.RATE_LIMIT_ERROR,
            user_message="Has enviado demasiados mensajes. Espera un momento antes de continuar.",
            **kwargs
        )

class PermissionError(BotException):
    """Raised when user doesn't have required permissions."""

    def __init__(self, message: str = "Insufficient permissions", **kwargs):
        super().__init__(
            message,
            error_code=BotErrorCode.PERMISSION_ERROR,
            user_message="No tienes permisos para realizar esta acción.",
            **kwargs
        )

def handle_bot_error(error: Exception, context: str = "") -> str:
    """
    Handle bot errors and return user-friendly messages.

    Args:
        error: The exception that occurred
        context: Additional context about where the error occurred

    Returns:
        User-friendly error message
    """
    if isinstance(error, BotException):
        return error.user_message

    # Handle unexpected errors
    logger.error(f"Unexpected error in {context}: {error}")
    return "Ha ocurrido un error inesperado. Inténtalo de nuevo en unos momentos."

def with_error_handling(operation_name: str):
    """
    Decorator for functions that need error handling.

    Args:
        operation_name: Name of the operation for logging
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except BotException as e:
                logger.warning(f"Bot error in {operation_name}: {e.message}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error in {operation_name}: {e}")
                raise BotException(
                    f"Error in {operation_name}: {str(e)}",
                    error_code=BotErrorCode.UNKNOWN_ERROR,
                    details={"operation": operation_name, "original_error": str(e)}
                )
        return wrapper
    return decorator

# Export all exceptions
__all__ = [
    'BotErrorCode',
    'BotException',
    'ConfigurationError',
    'APIError',
    'DatabaseError',
    'MemoryError',
    'ValidationError',
    'RateLimitError',
    'PermissionError',
    'handle_bot_error',
    'with_error_handling'
]
