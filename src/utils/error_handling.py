"""
Robust Error Handling and Recovery System
Provides fault tolerance, circuit breaking, and intelligent retry strategies
"""

import logging
import time
from enum import Enum
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Categorizes error severity for recovery decision-making"""
    CRITICAL = "critical"      # System failure, escalate immediately
    HIGH = "high"              # Tool failure, retry with backoff
    MEDIUM = "medium"          # Recoverable, safe to retry
    LOW = "low"                # Graceful degradation, fallback available
    TRANSIENT = "transient"    # Temporary (timeout), safe to retry


class ErrorCategory(Enum):
    """Categorizes error types for different handling strategies"""
    TIMEOUT = "timeout"
    MALFORMED_RESPONSE = "malformed_response"
    NOT_FOUND = "not_found"
    RATE_LIMIT = "rate_limit"
    SERVICE_UNAVAILABLE = "service_unavailable"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    """Rich error context for debugging and recovery"""
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    original_exception: Optional[Exception] = None
    tool_name: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    retry_count: int = 0
    is_recoverable: bool = True
    suggested_action: str = "retry"  # retry, escalate, skip, fallback
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'category': self.category.value,
            'severity': self.severity.value,
            'message': self.message,
            'tool_name': self.tool_name,
            'retry_count': self.retry_count,
            'is_recoverable': self.is_recoverable,
            'suggested_action': self.suggested_action,
            'timestamp': self.timestamp.isoformat()
        }


class CircuitBreaker:
    """
    Circuit breaker pattern for tool calls
    Prevents cascading failures when tools are degraded
    
    States:
    - CLOSED: Normal operation, calls go through
    - OPEN: Too many failures, calls blocked
    - HALF_OPEN: Testing if service recovered
    """
    
    def __init__(self, 
                 failure_threshold: int = 5,
                 recovery_timeout: int = 30,
                 expected_exception: type = Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function through circuit breaker"""
        
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
                logger.info(f"Circuit breaker HALF_OPEN - testing recovery")
            else:
                raise Exception(f"Circuit breaker OPEN - service unavailable (retry in {self._time_until_retry()}s)")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Reset on successful call"""
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            self.failure_count = 0
            logger.info(f"Circuit breaker CLOSED - service recovered")
        elif self.failure_count > 0:
            self.failure_count = 0
    
    def _on_failure(self):
        """Record failure and update state"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.error(f"Circuit breaker OPEN - {self.failure_count} failures detected")
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time passed for recovery test"""
        if not self.last_failure_time:
            return False
        return datetime.now() - self.last_failure_time >= timedelta(seconds=self.recovery_timeout)
    
    def _time_until_retry(self) -> int:
        """Seconds until circuit can attempt reset"""
        if not self.last_failure_time:
            return 0
        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return max(0, int(self.recovery_timeout - elapsed))
    
    def status(self) -> Dict[str, Any]:
        """Get circuit breaker status"""
        return {
            'state': self.state,
            'failure_count': self.failure_count,
            'threshold': self.failure_threshold,
            'last_failure': self.last_failure_time.isoformat() if self.last_failure_time else None,
            'time_until_retry': self._time_until_retry()
        }


class RetryStrategy:
    """
    Intelligent retry strategy with exponential backoff
    Adapts backoff based on error type
    """
    
    def __init__(self,
                 max_retries: int = 3,
                 base_delay: float = 0.1,
                 max_delay: float = 10.0,
                 exponential_base: float = 2.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
    
    def get_delay(self, retry_count: int, error_category: Optional[ErrorCategory] = None) -> float:
        """Calculate backoff delay based on retry count and error type"""
        
        # Rate limit errors get longer backoff
        if error_category == ErrorCategory.RATE_LIMIT:
            base_delay = self.base_delay * 5
        # Timeout errors get medium backoff
        elif error_category == ErrorCategory.TIMEOUT:
            base_delay = self.base_delay * 2
        else:
            base_delay = self.base_delay
        
        delay = base_delay * (self.exponential_base ** retry_count)
        return min(delay, self.max_delay)
    
    async def execute_with_retry(self,
                                 func: Callable,
                                 *args,
                                 on_retry: Optional[Callable] = None,
                                 **kwargs) -> Any:
        """Execute function with automatic retry"""
        
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    # Determine error category for intelligent backoff
                    category = self._categorize_error(e)
                    delay = self.get_delay(attempt, category)
                    
                    if on_retry:
                        on_retry(attempt + 1, self.max_retries, delay, category, str(e))
                    
                    await asyncio.sleep(delay) if asyncio.iscoroutinefunction(func) else time.sleep(delay)
        
        raise last_exception
    
    @staticmethod
    def _categorize_error(exception: Exception) -> ErrorCategory:
        """Infer error category from exception type"""
        exc_str = str(exception).lower()
        
        if 'timeout' in exc_str:
            return ErrorCategory.TIMEOUT
        elif 'malformed' in exc_str or 'invalid' in exc_str:
            return ErrorCategory.MALFORMED_RESPONSE
        elif 'not found' in exc_str or '404' in exc_str:
            return ErrorCategory.NOT_FOUND
        elif 'rate limit' in exc_str or '429' in exc_str:
            return ErrorCategory.RATE_LIMIT
        elif 'unavailable' in exc_str or '503' in exc_str:
            return ErrorCategory.SERVICE_UNAVAILABLE
        elif 'auth' in exc_str or '401' in exc_str or '403' in exc_str:
            return ErrorCategory.AUTHENTICATION
        else:
            return ErrorCategory.UNKNOWN


class ErrorRecoveryHandler:
    """
    Intelligent error recovery system
    Routes errors to appropriate recovery strategies
    """
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.retry_strategies: Dict[str, RetryStrategy] = {}
        self.error_history: List[ErrorContext] = []
    
    def get_circuit_breaker(self, tool_name: str) -> CircuitBreaker:
        """Get or create circuit breaker for tool"""
        if tool_name not in self.circuit_breakers:
            self.circuit_breakers[tool_name] = CircuitBreaker(
                failure_threshold=3,
                recovery_timeout=30
            )
        return self.circuit_breakers[tool_name]
    
    def get_retry_strategy(self, tool_name: str) -> RetryStrategy:
        """Get or create retry strategy for tool"""
        if tool_name not in self.retry_strategies:
            self.retry_strategies[tool_name] = RetryStrategy(
                max_retries=2,
                base_delay=0.1,
                max_delay=5.0
            )
        return self.retry_strategies[tool_name]
    
    def categorize_error(self, exception: Exception) -> ErrorContext:
        """Categorize exception into error context"""
        exc_str = str(exception).lower()
        
        # Determine category
        if 'timeout' in exc_str:
            category = ErrorCategory.TIMEOUT
            severity = ErrorSeverity.TRANSIENT
        elif 'malformed' in exc_str:
            category = ErrorCategory.MALFORMED_RESPONSE
            severity = ErrorSeverity.MEDIUM
        elif 'not found' in exc_str:
            category = ErrorCategory.NOT_FOUND
            severity = ErrorSeverity.MEDIUM
        elif 'rate limit' in exc_str:
            category = ErrorCategory.RATE_LIMIT
            severity = ErrorSeverity.HIGH
        elif 'unavailable' in exc_str:
            category = ErrorCategory.SERVICE_UNAVAILABLE
            severity = ErrorSeverity.HIGH
        elif 'validation' in exc_str:
            category = ErrorCategory.VALIDATION
            severity = ErrorSeverity.MEDIUM
        else:
            category = ErrorCategory.UNKNOWN
            severity = ErrorSeverity.MEDIUM
        
        context = ErrorContext(
            category=category,
            severity=severity,
            message=str(exception),
            original_exception=exception,
            is_recoverable=severity != ErrorSeverity.CRITICAL
        )
        
        self.error_history.append(context)
        return context
    
    def get_recovery_action(self, error_context: ErrorContext) -> str:
        """Determine best recovery action for error"""
        
        if error_context.severity == ErrorSeverity.CRITICAL:
            return "escalate"
        elif error_context.severity == ErrorSeverity.HIGH:
            if error_context.category in [ErrorCategory.RATE_LIMIT, ErrorCategory.SERVICE_UNAVAILABLE]:
                return "circuit_break"
            return "retry_aggressive"
        elif error_context.severity == ErrorSeverity.TRANSIENT:
            return "retry"
        elif error_context.severity == ErrorSeverity.MEDIUM:
            return "retry_cautious"
        else:
            return "fallback"
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of all errors encountered"""
        if not self.error_history:
            return {'total_errors': 0}
        
        by_category = {}
        by_severity = {}
        
        for error in self.error_history:
            cat = error.category.value
            sev = error.severity.value
            by_category[cat] = by_category.get(cat, 0) + 1
            by_severity[sev] = by_severity.get(sev, 0) + 1
        
        return {
            'total_errors': len(self.error_history),
            'by_category': by_category,
            'by_severity': by_severity,
            'circuit_breaker_status': {name: cb.status() for name, cb in self.circuit_breakers.items()},
            'recent_errors': [e.to_dict() for e in self.error_history[-5:]]
        }
