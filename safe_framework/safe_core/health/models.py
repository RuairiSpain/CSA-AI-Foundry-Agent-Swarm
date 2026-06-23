"""Health monitoring data models"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime, timezone

from ..config import config

class RouteHealthStatus(str, Enum):
    """Route health status flags"""
    READY = "ready"
    WARN_SLOW = "warn-slow"
    WARN_FAILING = "warn-failing"
    WARN_COST = "warn-cost"
    OFFLINE = "offline"
    FROZEN = "frozen"

class AlertSeverity(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

@dataclass
class HealthMetric:
    """Single health metric"""
    name: str
    value: float
    unit: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    threshold: Optional[float] = None
    
    def is_threshold_exceeded(self) -> bool:
        """Check if metric exceeds threshold"""
        if self.threshold is None:
            return False
        return self.value > self.threshold

@dataclass
class RouteHealth:
    """Complete health snapshot for a route"""
    route_name: str
    route_version: str
    status: RouteHealthStatus
    
    # Metrics
    execution_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    avg_execution_time_ms: float = 0.0
    p95_execution_time_ms: float = 0.0
    p99_execution_time_ms: float = 0.0
    
    # Cost metrics
    estimated_monthly_cost_usd: float = 0.0
    tokens_used: int = 0
    
    # Status tracking
    consecutive_failures: int = 0
    consecutive_slow_executions: int = 0
    
    # Thresholds (override via SAFE_HEALTH_FAILURE_THRESHOLD, SAFE_HEALTH_SLOW_THRESHOLD_MS, SAFE_HEALTH_COST_THRESHOLD_USD)
    failure_threshold: int = field(default_factory=lambda: config.health_failure_threshold)
    slow_execution_threshold_ms: float = field(default_factory=lambda: config.health_slow_threshold_ms)
    cost_threshold_usd: float = field(default_factory=lambda: config.health_cost_threshold_usd)
    
    # Metadata
    last_check: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_deployed: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.execution_count == 0:
            return 100.0
        return (self.success_count / self.execution_count) * 100.0
    
    def update_status(self) -> None:
        """Update health status based on metrics"""
        # Check for offline (no executions in last hour)
        if self.execution_count == 0:
            self.status = RouteHealthStatus.OFFLINE
            return
        
        # Check for frozen (no recent executions but was previously working)
        if (datetime.now(timezone.utc) - self.last_check).total_seconds() > config.health_frozen_threshold_seconds:
            self.status = RouteHealthStatus.FROZEN
            return
        
        # Two-strike rule: require 2 consecutive threshold breaches
        issues = []
        
        # Check failure rate
        if self.consecutive_failures >= self.failure_threshold:
            issues.append("warn-failing")
        
        # Check execution time
        if self.consecutive_slow_executions >= self.failure_threshold:
            issues.append("warn-slow")
        
        # Check cost
        if self.estimated_monthly_cost_usd > self.cost_threshold_usd:
            issues.append("warn-cost")
        
        # Set status based on issues
        if "warn-failing" in issues:
            self.status = RouteHealthStatus.WARN_FAILING
        elif "warn-slow" in issues:
            self.status = RouteHealthStatus.WARN_SLOW
        elif "warn-cost" in issues:
            self.status = RouteHealthStatus.WARN_COST
        else:
            self.status = RouteHealthStatus.READY

@dataclass
class HealthAlert:
    """Health alert notification"""
    route_name: str
    severity: AlertSeverity
    message: str
    metric_name: str
    current_value: float
    threshold: float
    suggested_action: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    alert_id: str = field(default_factory=lambda: str(datetime.now(timezone.utc).timestamp()))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "alert_id": self.alert_id,
            "route_name": self.route_name,
            "severity": self.severity.value,
            "message": self.message,
            "metric": self.metric_name,
            "current_value": self.current_value,
            "threshold": self.threshold,
            "action": self.suggested_action,
            "timestamp": self.timestamp.isoformat(),
        }

