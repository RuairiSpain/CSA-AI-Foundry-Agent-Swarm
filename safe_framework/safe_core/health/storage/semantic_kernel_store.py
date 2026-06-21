"""Semantic Kernel implementation of route health storage"""

import json
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from .base import IRouteHealthStore
from ..models import RouteHealth, HealthAlert, RouteHealthStatus

class SemanticKernelRouteHealthStore(IRouteHealthStore):
    """
    Semantic Kernel-based health storage (MVP implementation)
    Uses in-memory store with JSON serialization
    Production: Replace with Cosmos DB
    """
    
    def __init__(self):
        self.health_snapshots: Dict[str, List[RouteHealth]] = {}
        self.alerts: List[HealthAlert] = []
        self.routes: Dict[str, str] = {}  # route_name -> version
    
    async def save_route_health(self, health: RouteHealth) -> bool:
        """Save route health snapshot"""
        try:
            key = f"{health.route_name}:{health.route_version}"
            
            if key not in self.health_snapshots:
                self.health_snapshots[key] = []
            
            self.health_snapshots[key].append(health)
            self.routes[health.route_name] = health.route_version
            
            # Keep only last 1000 snapshots per route
            if len(self.health_snapshots[key]) > 1000:
                self.health_snapshots[key] = self.health_snapshots[key][-1000:]
            
            return True
        except Exception as e:
            print(f"Error saving health: {e}")
            return False
    
    async def get_route_health(self, route_name: str, version: str) -> Optional[RouteHealth]:
        """Get current health for a route"""
        try:
            key = f"{route_name}:{version}"
            snapshots = self.health_snapshots.get(key, [])
            
            if not snapshots:
                return None
            
            return snapshots[-1]  # Return latest snapshot
        except Exception as e:
            print(f"Error retrieving health: {e}")
            return None
    
    async def get_route_health_history(
        self,
        route_name: str,
        version: str,
        hours: int = 24
    ) -> List[RouteHealth]:
        """Get health history for a route"""
        try:
            key = f"{route_name}:{version}"
            snapshots = self.health_snapshots.get(key, [])
            
            # Filter by time window
            cutoff_time = datetime.now() - timedelta(hours=hours)
            return [s for s in snapshots if s.last_check >= cutoff_time]
        except Exception as e:
            print(f"Error retrieving history: {e}")
            return []
    
    async def save_alert(self, alert: HealthAlert) -> bool:
        """Save health alert"""
        try:
            self.alerts.append(alert)
            
            # Keep only last 10000 alerts
            if len(self.alerts) > 10000:
                self.alerts = self.alerts[-10000:]
            
            return True
        except Exception as e:
            print(f"Error saving alert: {e}")
            return False
    
    async def get_alerts(
        self,
        route_name: Optional[str] = None,
        limit: int = 100
    ) -> List[HealthAlert]:
        """Get recent alerts"""
        try:
            alerts = self.alerts
            
            if route_name:
                alerts = [a for a in alerts if a.route_name == route_name]
            
            # Return most recent
            return sorted(
                alerts[-limit:],
                key=lambda a: a.timestamp,
                reverse=True
            )
        except Exception as e:
            print(f"Error retrieving alerts: {e}")
            return []
    
    async def list_all_routes(self) -> List[str]:
        """List all monitored routes"""
        return list(self.routes.keys())
    
    async def delete_route(self, route_name: str, version: str) -> bool:
        """Delete route from monitoring"""
        try:
            key = f"{route_name}:{version}"
            
            if key in self.health_snapshots:
                del self.health_snapshots[key]
            
            if route_name in self.routes:
                del self.routes[route_name]
            
            return True
        except Exception as e:
            print(f"Error deleting route: {e}")
            return False

