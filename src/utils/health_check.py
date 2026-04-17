"""
Health Check and Monitoring System
Monitors agent and tool health, detects degradation
"""

import logging
from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import json

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class ToolHealthMetrics:
    """Health metrics for a single tool"""
    tool_name: str
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    timeout_calls: int = 0
    avg_response_time_ms: float = 0.0
    min_response_time_ms: float = float('inf')
    max_response_time_ms: float = 0.0
    last_failure_time: datetime = None
    consecutive_failures: int = 0
    error_rate: float = 0.0
    status: HealthStatus = HealthStatus.UNKNOWN
    last_checked: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'tool_name': self.tool_name,
            'total_calls': self.total_calls,
            'successful_calls': self.successful_calls,
            'failed_calls': self.failed_calls,
            'timeout_calls': self.timeout_calls,
            'success_rate': self.success_rate,
            'error_rate': self.error_rate,
            'avg_response_time_ms': round(self.avg_response_time_ms, 2),
            'status': self.status.value,
            'consecutive_failures': self.consecutive_failures,
            'last_failure': self.last_failure_time.isoformat() if self.last_failure_time else None
        }
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_calls == 0:
            return 0.0
        return (self.successful_calls / self.total_calls) * 100
    
    def is_degraded(self) -> bool:
        """Check if tool is degraded"""
        # Degraded if >20% error rate or >3 consecutive failures
        return self.error_rate > 20 or self.consecutive_failures > 3
    
    def is_critical(self) -> bool:
        """Check if tool is in critical state"""
        # Critical if >50% error rate or >5 consecutive failures
        return self.error_rate > 50 or self.consecutive_failures > 5


@dataclass
class AgentHealthMetrics:
    """Overall health metrics for the agent"""
    total_tickets_processed: int = 0
    successful_resolutions: int = 0
    failed_resolutions: int = 0
    escalated_tickets: int = 0
    avg_confidence: float = 0.0
    avg_processing_time_ms: float = 0.0
    uptime_seconds: float = 0.0
    start_time: datetime = field(default_factory=datetime.now)
    tool_metrics: Dict[str, ToolHealthMetrics] = field(default_factory=dict)
    status: HealthStatus = HealthStatus.HEALTHY
    last_checked: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_tickets': self.total_tickets_processed,
            'successful_resolutions': self.successful_resolutions,
            'failed_resolutions': self.failed_resolutions,
            'escalated_tickets': self.escalated_tickets,
            'success_rate': self.success_rate,
            'avg_confidence': round(self.avg_confidence, 3),
            'avg_processing_time_ms': round(self.avg_processing_time_ms, 2),
            'uptime_seconds': round(self.uptime_seconds, 2),
            'status': self.status.value,
            'tools': {name: metrics.to_dict() for name, metrics in self.tool_metrics.items()}
        }
    
    @property
    def success_rate(self) -> float:
        """Calculate overall success rate"""
        if self.total_tickets_processed == 0:
            return 0.0
        return (self.successful_resolutions / self.total_tickets_processed) * 100


class HealthChecker:
    """
    Monitors system health and detects degradation
    """
    
    def __init__(self):
        self.agent_metrics = AgentHealthMetrics()
        self.tool_checks = {}  # Custom health checks per tool
    
    def record_tool_call(self,
                        tool_name: str,
                        success: bool,
                        response_time_ms: float,
                        is_timeout: bool = False,
                        error: Optional[str] = None):
        """Record a tool call result"""
        
        if tool_name not in self.agent_metrics.tool_metrics:
            self.agent_metrics.tool_metrics[tool_name] = ToolHealthMetrics(tool_name=tool_name)
        
        metrics = self.agent_metrics.tool_metrics[tool_name]
        
        # Update metrics
        metrics.total_calls += 1
        metrics.avg_response_time_ms = (
            (metrics.avg_response_time_ms * (metrics.total_calls - 1) + response_time_ms) /
            metrics.total_calls
        )
        metrics.min_response_time_ms = min(metrics.min_response_time_ms, response_time_ms)
        metrics.max_response_time_ms = max(metrics.max_response_time_ms, response_time_ms)
        
        if success:
            metrics.successful_calls += 1
            metrics.consecutive_failures = 0
        else:
            metrics.failed_calls += 1
            metrics.consecutive_failures += 1
            metrics.last_failure_time = datetime.now()
        
        if is_timeout:
            metrics.timeout_calls += 1
        
        # Update error rate
        metrics.error_rate = (metrics.failed_calls / metrics.total_calls) * 100 if metrics.total_calls > 0 else 0
        
        # Update status
        if metrics.is_critical():
            metrics.status = HealthStatus.CRITICAL
        elif metrics.is_degraded():
            metrics.status = HealthStatus.DEGRADED
        else:
            metrics.status = HealthStatus.HEALTHY
        
        metrics.last_checked = datetime.now()
        
        # Log if degradation detected
        if metrics.status != HealthStatus.HEALTHY:
            logger.warning(
                f"Tool {tool_name} status: {metrics.status.value} "
                f"(error_rate: {metrics.error_rate:.1f}%, failures: {metrics.consecutive_failures})"
            )
    
    def record_ticket_resolution(self,
                                success: bool,
                                confidence: float,
                                processing_time_ms: float,
                                escalated: bool = False):
        """Record a ticket resolution"""
        
        self.agent_metrics.total_tickets_processed += 1
        
        if success:
            self.agent_metrics.successful_resolutions += 1
        else:
            self.agent_metrics.failed_resolutions += 1
        
        if escalated:
            self.agent_metrics.escalated_tickets += 1
        
        # Update averages
        total = self.agent_metrics.total_tickets_processed
        prev_avg_conf = self.agent_metrics.avg_confidence
        self.agent_metrics.avg_confidence = (
            (prev_avg_conf * (total - 1) + confidence) / total
        )
        
        prev_avg_time = self.agent_metrics.avg_processing_time_ms
        self.agent_metrics.avg_processing_time_ms = (
            (prev_avg_time * (total - 1) + processing_time_ms) / total
        )
        
        # Update uptime
        self.agent_metrics.uptime_seconds = (
            datetime.now() - self.agent_metrics.start_time
        ).total_seconds()
        
        # Determine overall health
        success_rate = self.agent_metrics.success_rate
        if success_rate < 50:
            self.agent_metrics.status = HealthStatus.CRITICAL
        elif success_rate < 75:
            self.agent_metrics.status = HealthStatus.DEGRADED
        else:
            self.agent_metrics.status = HealthStatus.HEALTHY
        
        self.agent_metrics.last_checked = datetime.now()
    
    def get_health_report(self) -> Dict[str, Any]:
        """Get complete health report"""
        
        # Check for critical tools
        critical_tools = [
            name for name, metrics in self.agent_metrics.tool_metrics.items()
            if metrics.status == HealthStatus.CRITICAL
        ]
        
        # Recommendations
        recommendations = []
        if self.agent_metrics.status == HealthStatus.CRITICAL:
            recommendations.append("URGENT: Agent in critical state - investigate immediately")
        
        for tool_name in critical_tools:
            recommendations.append(f"Tool {tool_name} requires immediate attention")
        
        return {
            'overall_status': self.agent_metrics.status.value,
            'agent_metrics': self.agent_metrics.to_dict(),
            'critical_tools': critical_tools,
            'recommendations': recommendations,
            'timestamp': datetime.now().isoformat()
        }
    
    def should_circuit_break_tool(self, tool_name: str) -> bool:
        """Determine if tool should be circuit broken"""
        if tool_name not in self.agent_metrics.tool_metrics:
            return False
        
        metrics = self.agent_metrics.tool_metrics[tool_name]
        
        # Circuit break if critical or too many consecutive failures
        return metrics.status == HealthStatus.CRITICAL or metrics.consecutive_failures >= 5
