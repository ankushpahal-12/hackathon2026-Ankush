"""
Utility modules for the support agent
Includes validation, error handling, health checking, and monitoring
"""

from .validation import SchemaValidator, ValidationError
from .dead_letter_queue import DeadLetterQueue, DeadLetterEntry
from .error_handling import (
    ErrorContext,
    ErrorCategory,
    ErrorSeverity,
    CircuitBreaker,
    RetryStrategy,
    ErrorRecoveryHandler
)
from .input_validation import InputValidator
from .health_check import HealthChecker, HealthStatus, ToolHealthMetrics, AgentHealthMetrics

__all__ = [
    # Validation
    'SchemaValidator',
    'ValidationError',
    'InputValidator',
    
    # Dead-letter queue
    'DeadLetterQueue',
    'DeadLetterEntry',
    
    # Error handling
    'ErrorContext',
    'ErrorCategory',
    'ErrorSeverity',
    'CircuitBreaker',
    'RetryStrategy',
    'ErrorRecoveryHandler',
    
    # Health checks
    'HealthChecker',
    'HealthStatus',
    'ToolHealthMetrics',
    'AgentHealthMetrics'
]
