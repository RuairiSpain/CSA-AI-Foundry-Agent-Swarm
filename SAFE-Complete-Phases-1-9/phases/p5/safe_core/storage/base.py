"""Abstract storage interface for route health"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from ..health_models import RouteHealth, HealthAlert

class IRouteHealthStore(ABC):
    """Abstract interface for route health storage"""
    
    @abstractmethod
    async def save_route_health(self, health: RouteHealth) -> bool:
        """Save route health snapshot"""
        pass
    
    @abstractmethod
    async def get_route_health(self, route_name: str, version: str) -> Optional[RouteHealth]:
        """Get current health for a route"""
        pass
    
    @abstractmethod
    async def get_route_health_history(
        self, 
        route_name: str, 
        version: str,
        hours: int = 24
    ) -> List[RouteHealth]:
        """Get health history for a route"""
        pass
    
    @abstractmethod
    async def save_alert(self, alert: HealthAlert) -> bool:
        """Save health alert"""
        pass
    
    @abstractmethod
    async def get_alerts(
        self,
        route_name: Optional[str] = None,
        limit: int = 100
    ) -> List[HealthAlert]:
        """Get recent alerts"""
        pass
    
    @abstractmethod
    async def list_all_routes(self) -> List[str]:
        """List all monitored routes"""
        pass
    
    @abstractmethod
    async def delete_route(self, route_name: str, version: str) -> bool:
        """Delete route from monitoring"""
        pass

