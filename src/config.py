"""
Agent Configuration Management
Centralized configuration for production deployment
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class RetryConfig:
    """Retry strategy configuration"""
    max_retries: int = 2
    base_delay_seconds: float = 0.1
    max_delay_seconds: float = 10.0
    exponential_base: float = 2.0


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 3
    recovery_timeout_seconds: int = 30
    enabled: bool = True


@dataclass
class TimeoutConfig:
    """Timeout configuration for tool calls"""
    default_timeout_seconds: int = 5
    get_customer_timeout_seconds: int = 5
    get_order_timeout_seconds: int = 5
    check_refund_timeout_seconds: int = 5
    issue_refund_timeout_seconds: int = 5
    send_reply_timeout_seconds: int = 5


@dataclass
class HealthCheckConfig:
    """Health check configuration"""
    enabled: bool = True
    check_interval_seconds: int = 60
    degradation_threshold_percent: float = 20.0
    critical_threshold_percent: float = 50.0


@dataclass
class LLMConfig:
    """LLM configuration"""
    enabled: bool = True
    use_gemini: bool = True
    use_openai: bool = True
    timeout_seconds: int = 10
    max_retries: int = 1


@dataclass
class LoggingConfig:
    """Logging configuration"""
    log_level: str = "INFO"
    log_file: str = "agent.log"
    audit_log_file: str = "output/audit_log.json"
    deadletter_log_file: str = "output/dead_letter_queue.json"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


@dataclass
class ConcurrencyConfig:
    """Concurrency configuration"""
    max_concurrent_tickets: int = 20
    max_concurrent_tools_per_ticket: int = 1  # Sequential tool execution per ticket
    thread_pool_size: int = 4


@dataclass
class AgentConfig:
    """Complete agent configuration"""
    retry: RetryConfig
    circuit_breaker: CircuitBreakerConfig
    timeout: TimeoutConfig
    health_check: HealthCheckConfig
    llm: LLMConfig
    logging: LoggingConfig
    concurrency: ConcurrencyConfig
    
    @classmethod
    def load_from_env(cls) -> 'AgentConfig':
        """Load configuration from environment variables"""
        
        return cls(
            retry=RetryConfig(
                max_retries=int(os.getenv('RETRY_MAX_RETRIES', '2')),
                base_delay_seconds=float(os.getenv('RETRY_BASE_DELAY', '0.1')),
                max_delay_seconds=float(os.getenv('RETRY_MAX_DELAY', '10.0'))
            ),
            circuit_breaker=CircuitBreakerConfig(
                failure_threshold=int(os.getenv('CB_FAILURE_THRESHOLD', '3')),
                recovery_timeout_seconds=int(os.getenv('CB_RECOVERY_TIMEOUT', '30')),
                enabled=os.getenv('CB_ENABLED', 'true').lower() == 'true'
            ),
            timeout=TimeoutConfig(
                default_timeout_seconds=int(os.getenv('TIMEOUT_DEFAULT', '5')),
                get_customer_timeout_seconds=int(os.getenv('TIMEOUT_GET_CUSTOMER', '5')),
                get_order_timeout_seconds=int(os.getenv('TIMEOUT_GET_ORDER', '5')),
                check_refund_timeout_seconds=int(os.getenv('TIMEOUT_CHECK_REFUND', '5')),
                issue_refund_timeout_seconds=int(os.getenv('TIMEOUT_ISSUE_REFUND', '5')),
                send_reply_timeout_seconds=int(os.getenv('TIMEOUT_SEND_REPLY', '5'))
            ),
            health_check=HealthCheckConfig(
                enabled=os.getenv('HC_ENABLED', 'true').lower() == 'true',
                check_interval_seconds=int(os.getenv('HC_INTERVAL', '60')),
                degradation_threshold_percent=float(os.getenv('HC_DEGRADE_THRESHOLD', '20.0')),
                critical_threshold_percent=float(os.getenv('HC_CRITICAL_THRESHOLD', '50.0'))
            ),
            llm=LLMConfig(
                enabled=os.getenv('LLM_ENABLED', 'true').lower() == 'true',
                use_gemini=os.getenv('LLM_USE_GEMINI', 'true').lower() == 'true',
                use_openai=os.getenv('LLM_USE_OPENAI', 'true').lower() == 'true',
                timeout_seconds=int(os.getenv('LLM_TIMEOUT', '10'))
            ),
            logging=LoggingConfig(
                log_level=os.getenv('LOG_LEVEL', 'INFO'),
                log_file=os.getenv('LOG_FILE', 'agent.log'),
                audit_log_file=os.getenv('AUDIT_LOG_FILE', 'output/audit_log.json'),
                deadletter_log_file=os.getenv('DL_LOG_FILE', 'output/dead_letter_queue.json')
            ),
            concurrency=ConcurrencyConfig(
                max_concurrent_tickets=int(os.getenv('MAX_CONCURRENT_TICKETS', '20')),
                max_concurrent_tools_per_ticket=int(os.getenv('MAX_CONCURRENT_TOOLS', '1')),
                thread_pool_size=int(os.getenv('THREAD_POOL_SIZE', '4'))
            )
        )
    
    @classmethod
    def load_from_file(cls, config_file: str) -> 'AgentConfig':
        """Load configuration from JSON file"""
        
        if not os.path.exists(config_file):
            logger.warning(f"Config file not found: {config_file}, using defaults")
            return cls.get_defaults()
        
        try:
            with open(config_file, 'r') as f:
                config_dict = json.load(f)
            
            return cls(
                retry=RetryConfig(**config_dict.get('retry', {})),
                circuit_breaker=CircuitBreakerConfig(**config_dict.get('circuit_breaker', {})),
                timeout=TimeoutConfig(**config_dict.get('timeout', {})),
                health_check=HealthCheckConfig(**config_dict.get('health_check', {})),
                llm=LLMConfig(**config_dict.get('llm', {})),
                logging=LoggingConfig(**config_dict.get('logging', {})),
                concurrency=ConcurrencyConfig(**config_dict.get('concurrency', {}))
            )
        except Exception as e:
            logger.error(f"Error loading config file: {e}, using defaults")
            return cls.get_defaults()
    
    @classmethod
    def get_defaults(cls) -> 'AgentConfig':
        """Get default configuration"""
        return cls(
            retry=RetryConfig(),
            circuit_breaker=CircuitBreakerConfig(),
            timeout=TimeoutConfig(),
            health_check=HealthCheckConfig(),
            llm=LLMConfig(),
            logging=LoggingConfig(),
            concurrency=ConcurrencyConfig()
        )
    
    def save_to_file(self, filepath: str):
        """Save configuration to JSON file"""
        config_dict = {
            'retry': {
                'max_retries': self.retry.max_retries,
                'base_delay_seconds': self.retry.base_delay_seconds,
                'max_delay_seconds': self.retry.max_delay_seconds,
                'exponential_base': self.retry.exponential_base
            },
            'circuit_breaker': {
                'failure_threshold': self.circuit_breaker.failure_threshold,
                'recovery_timeout_seconds': self.circuit_breaker.recovery_timeout_seconds,
                'enabled': self.circuit_breaker.enabled
            },
            'timeout': {
                'default_timeout_seconds': self.timeout.default_timeout_seconds,
                'get_customer_timeout_seconds': self.timeout.get_customer_timeout_seconds,
                'get_order_timeout_seconds': self.timeout.get_order_timeout_seconds,
                'check_refund_timeout_seconds': self.timeout.check_refund_timeout_seconds,
                'issue_refund_timeout_seconds': self.timeout.issue_refund_timeout_seconds,
                'send_reply_timeout_seconds': self.timeout.send_reply_timeout_seconds
            },
            'health_check': {
                'enabled': self.health_check.enabled,
                'check_interval_seconds': self.health_check.check_interval_seconds,
                'degradation_threshold_percent': self.health_check.degradation_threshold_percent,
                'critical_threshold_percent': self.health_check.critical_threshold_percent
            },
            'llm': {
                'enabled': self.llm.enabled,
                'use_gemini': self.llm.use_gemini,
                'use_openai': self.llm.use_openai,
                'timeout_seconds': self.llm.timeout_seconds,
                'max_retries': self.llm.max_retries
            },
            'logging': {
                'log_level': self.logging.log_level,
                'log_file': self.logging.log_file,
                'audit_log_file': self.logging.audit_log_file,
                'deadletter_log_file': self.logging.deadletter_log_file
            },
            'concurrency': {
                'max_concurrent_tickets': self.concurrency.max_concurrent_tickets,
                'max_concurrent_tools_per_ticket': self.concurrency.max_concurrent_tools_per_ticket,
                'thread_pool_size': self.concurrency.thread_pool_size
            }
        }
        
        os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(config_dict, f, indent=2)
        
        logger.info(f"Configuration saved to {filepath}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'retry': {
                'max_retries': self.retry.max_retries,
                'base_delay_seconds': self.retry.base_delay_seconds,
                'max_delay_seconds': self.retry.max_delay_seconds
            },
            'circuit_breaker': {
                'enabled': self.circuit_breaker.enabled,
                'failure_threshold': self.circuit_breaker.failure_threshold,
                'recovery_timeout_seconds': self.circuit_breaker.recovery_timeout_seconds
            },
            'timeouts': {
                'default': self.timeout.default_timeout_seconds
            },
            'health_check': {
                'enabled': self.health_check.enabled
            },
            'llm': {
                'enabled': self.llm.enabled
            },
            'concurrency': {
                'max_concurrent_tickets': self.concurrency.max_concurrent_tickets
            }
        }


# Default instance
_default_config: Optional[AgentConfig] = None


def get_config() -> AgentConfig:
    """Get configuration instance (singleton)"""
    global _default_config
    
    if _default_config is None:
        # Try loading from file first, then environment
        if os.path.exists('config.json'):
            _default_config = AgentConfig.load_from_file('config.json')
        else:
            _default_config = AgentConfig.load_from_env()
    
    return _default_config


def reset_config():
    """Reset configuration (for testing)"""
    global _default_config
    _default_config = None
