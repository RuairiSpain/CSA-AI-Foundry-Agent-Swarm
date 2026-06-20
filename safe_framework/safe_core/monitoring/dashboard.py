"""Production dashboard"""
from typing import Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"

@dataclass
class RouteMetrics:
    route_name: str
    status: HealthStatus
    execution_count: int = 0
    success_rate: float = 0.0
    avg_execution_time_ms: float = 0.0
    error_count: int = 0

class ProductionDashboard:
    def __init__(self):
        self.routes: Dict[str, RouteMetrics] = {}
    
    async def register_route(self, route_name: str) -> None:
        self.routes[route_name] = RouteMetrics(
            route_name=route_name, status=HealthStatus.HEALTHY
        )
    
    async def update_route_metrics(
        self, route_name: str, count: int, rate: float, time: float, errors: int
    ) -> None:
        if route_name in self.routes:
            r = self.routes[route_name]
            r.execution_count = count
            r.success_rate = rate
            r.avg_execution_time_ms = time
            r.error_count = errors
            r.status = HealthStatus.CRITICAL if errors > 0 else HealthStatus.HEALTHY
