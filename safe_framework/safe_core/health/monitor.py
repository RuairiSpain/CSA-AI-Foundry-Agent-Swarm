"""Health monitoring engine for routes"""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from .models import (
    RouteHealth,
    RouteHealthStatus,
    HealthAlert,
    AlertSeverity,
)
from .storage.base import IRouteHealthStore

class HealthMonitor:
    """Monitors route health and generates alerts"""
    
    def __init__(self, storage: IRouteHealthStore):
        self.storage = storage
        self.monitored_routes: Dict[str, RouteHealth] = {}
        self.alert_history: List[HealthAlert] = []
    
    async def register_route(self, route_name: str, version: str) -> None:
        """Register a route for monitoring"""
        health = RouteHealth(
            route_name=route_name,
            route_version=version,
            status=RouteHealthStatus.READY,
        )
        
        key = f"{route_name}:{version}"
        self.monitored_routes[key] = health
        await self.storage.save_route_health(health)
    
    async def record_execution(
        self,
        route_name: str,
        version: str,
        success: bool,
        execution_time_ms: float,
        tokens_used: int = 0,
        estimated_cost_usd: float = 0.0,
    ) -> None:
        """Record a route execution"""
        key = f"{route_name}:{version}"
        
        if key not in self.monitored_routes:
            await self.register_route(route_name, version)
        
        health = self.monitored_routes[key]
        
        # Update counts
        health.execution_count += 1
        
        if success:
            health.success_count += 1
            health.consecutive_failures = 0
        else:
            health.failure_count += 1
            health.consecutive_failures += 1
        
        # Update timing
        if health.execution_count == 1:
            health.avg_execution_time_ms = execution_time_ms
            health.p95_execution_time_ms = execution_time_ms
            health.p99_execution_time_ms = execution_time_ms
        else:
            # Simple running average (production: use proper quantile algo)
            health.avg_execution_time_ms = (
                (health.avg_execution_time_ms * (health.execution_count - 1) + execution_time_ms)
                / health.execution_count
            )
        
        # Update slow execution counter
        if execution_time_ms > health.slow_execution_threshold_ms:
            health.consecutive_slow_executions += 1
        else:
            health.consecutive_slow_executions = 0
        
        # Update cost metrics
        health.tokens_used += tokens_used
        health.estimated_monthly_cost_usd += estimated_cost_usd
        
        # Update timestamp
        health.last_check = datetime.now(timezone.utc)
        
        # Update status
        health.update_status()
        
        # Save to storage
        await self.storage.save_route_health(health)
        
        # Check for alerts
        await self._check_and_alert(health)
    
    async def _check_and_alert(self, health: RouteHealth) -> None:
        """Check health and generate alerts if needed"""
        
        # Alert on high failure rate
        if health.status == RouteHealthStatus.WARN_FAILING:
            alert = HealthAlert(
                route_name=health.route_name,
                severity=AlertSeverity.CRITICAL,
                message=f"Route {health.route_name} has {health.consecutive_failures} consecutive failures",
                metric_name="failure_rate",
                current_value=100 - health.success_rate,
                threshold=50.0,
                suggested_action="Review recent executions and check route logs"
            )
            await self.storage.save_alert(alert)
            self.alert_history.append(alert)
        
        # Alert on slow execution
        if health.status == RouteHealthStatus.WARN_SLOW:
            alert = HealthAlert(
                route_name=health.route_name,
                severity=AlertSeverity.WARNING,
                message=f"Route {health.route_name} executions are slow ({health.avg_execution_time_ms:.0f}ms avg)",
                metric_name="execution_time",
                current_value=health.avg_execution_time_ms,
                threshold=health.slow_execution_threshold_ms,
                suggested_action="Check agent performance and optimize prompts"
            )
            await self.storage.save_alert(alert)
            self.alert_history.append(alert)
        
        # Alert on high cost
        if health.status == RouteHealthStatus.WARN_COST:
            alert = HealthAlert(
                route_name=health.route_name,
                severity=AlertSeverity.WARNING,
                message=f"Route {health.route_name} estimated cost exceeds threshold (${health.estimated_monthly_cost_usd:.2f})",
                metric_name="monthly_cost",
                current_value=health.estimated_monthly_cost_usd,
                threshold=health.cost_threshold_usd,
                suggested_action="Review agent usage and consider caching or batch processing"
            )
            await self.storage.save_alert(alert)
            self.alert_history.append(alert)
    
    async def get_health_dashboard(self) -> Dict[str, Any]:
        """Get overall health dashboard"""
        all_routes = await self.storage.list_all_routes()
        
        dashboard = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_routes": len(all_routes),
            "routes_by_status": {},
            "recent_alerts": [],
        }
        
        # Collect status counts
        for route in all_routes:
            version = self.monitored_routes.get(f"{route}:v1.0", RouteHealth("", "", RouteHealthStatus.OFFLINE)).route_version
            health = await self.storage.get_route_health(route, version)
            
            if health:
                status = health.status.value
                if status not in dashboard["routes_by_status"]:
                    dashboard["routes_by_status"][status] = []
                dashboard["routes_by_status"][status].append(route)
        
        # Recent alerts
        recent_alerts = await self.storage.get_alerts(limit=10)
        dashboard["recent_alerts"] = [a.to_dict() for a in recent_alerts]
        
        return dashboard
    
    async def freeze_route(self, route_name: str, version: str) -> bool:
        """Manually freeze a route"""
        key = f"{route_name}:{version}"
        
        if key not in self.monitored_routes:
            return False
        
        health = self.monitored_routes[key]
        health.status = RouteHealthStatus.FROZEN
        
        await self.storage.save_route_health(health)
        
        alert = HealthAlert(
            route_name=route_name,
            severity=AlertSeverity.CRITICAL,
            message=f"Route {route_name} has been manually frozen",
            metric_name="status",
            current_value=1.0,
            threshold=1.0,
            suggested_action="Investigate and unfreeze when ready"
        )
        await self.storage.save_alert(alert)
        
        return True
    
    async def unfreeze_route(self, route_name: str, version: str) -> bool:
        """Unfreeze a route"""
        key = f"{route_name}:{version}"
        
        if key not in self.monitored_routes:
            return False
        
        health = self.monitored_routes[key]
        health.status = RouteHealthStatus.READY
        
        await self.storage.save_route_health(health)
        
        return True

