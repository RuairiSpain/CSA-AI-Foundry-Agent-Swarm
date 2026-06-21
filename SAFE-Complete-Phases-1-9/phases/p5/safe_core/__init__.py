"""
SAFE Framework Phase 5: Health Registry
Route monitoring, metrics collection, and auto-detection
"""

__version__ = "1.0.0"
__author__ = "Microsoft CSA Team"

from .health_models import (
    RouteHealthStatus,
    HealthMetric,
    RouteHealth,
    HealthAlert,
)
from .health_monitor import HealthMonitor
from .storage.base import IRouteHealthStore
from .storage.semantic_kernel_store import SemanticKernelRouteHealthStore

__all__ = [
    "RouteHealthStatus",
    "HealthMetric",
    "RouteHealth",
    "HealthAlert",
    "HealthMonitor",
    "IRouteHealthStore",
    "SemanticKernelRouteHealthStore",
]
