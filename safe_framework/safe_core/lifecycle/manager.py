"""Route lifecycle management for Agent 365 integration"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from ..governance.models import RouteLifecycleState

class RouteLifecycleManager:
    """Manages route lifecycle states and transitions"""
    
    def __init__(self):
        self.routes: Dict[str, Dict[str, Any]] = {}
    
    async def create_route_entry(self, route_name: str, version: str) -> None:
        """Create new route lifecycle entry"""
        key = f"{route_name}:{version}"
        
        self.routes[key] = {
            "name": route_name,
            "version": version,
            "state": RouteLifecycleState.DRAFT,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "deployed_at": None,
            "retired_at": None,
            "state_history": [
                {
                    "state": RouteLifecycleState.DRAFT,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "actor": "system",
                    "reason": "Route created",
                }
            ],
        }
    
    async def transition_state(
        self,
        route_name: str,
        version: str,
        new_state: RouteLifecycleState,
        actor: str = "system",
        reason: str = "",
    ) -> bool:
        """Transition route to new state"""
        key = f"{route_name}:{version}"
        
        if key not in self.routes:
            return False
        
        route = self.routes[key]
        current_state = route["state"]
        
        # Validate state transition
        if not self._is_valid_transition(current_state, new_state):
            return False
        
        # Update state
        route["state"] = new_state
        route["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Track state history
        route["state_history"].append({
            "state": new_state,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": actor,
            "reason": reason,
        })
        
        # Update special timestamps
        if new_state == RouteLifecycleState.DEPLOYED:
            route["deployed_at"] = datetime.now(timezone.utc).isoformat()
        elif new_state in [RouteLifecycleState.ARCHIVED, RouteLifecycleState.DISABLED]:
            route["retired_at"] = datetime.now(timezone.utc).isoformat()
        
        return True
    
    def _is_valid_transition(
        self,
        current: RouteLifecycleState,
        target: RouteLifecycleState,
    ) -> bool:
        """Check if state transition is valid"""
        
        # Valid transitions
        valid_transitions = {
            RouteLifecycleState.DRAFT: [
                RouteLifecycleState.PENDING_APPROVAL,
                RouteLifecycleState.ARCHIVED,
            ],
            RouteLifecycleState.PENDING_APPROVAL: [
                RouteLifecycleState.APPROVED,
                RouteLifecycleState.REJECTED,
            ],
            RouteLifecycleState.APPROVED: [
                RouteLifecycleState.DEPLOYED,
                RouteLifecycleState.DISABLED,
            ],
            RouteLifecycleState.DEPLOYED: [
                RouteLifecycleState.ACTIVE,
                RouteLifecycleState.DISABLED,
            ],
            RouteLifecycleState.ACTIVE: [
                RouteLifecycleState.SUSPENDED,
                RouteLifecycleState.DISABLED,
                RouteLifecycleState.ARCHIVED,
            ],
            RouteLifecycleState.SUSPENDED: [
                RouteLifecycleState.ACTIVE,
                RouteLifecycleState.DISABLED,
            ],
            RouteLifecycleState.DISABLED: [
                RouteLifecycleState.ARCHIVED,
            ],
            RouteLifecycleState.ARCHIVED: [],  # Terminal state
        }
        
        return target in valid_transitions.get(current, [])
    
    async def get_route_state(self, route_name: str, version: str) -> Optional[RouteLifecycleState]:
        """Get current route state"""
        key = f"{route_name}:{version}"
        
        if key not in self.routes:
            return None
        
        return self.routes[key]["state"]
    
    async def get_route_history(self, route_name: str, version: str) -> Optional[List[Dict[str, Any]]]:
        """Get route state change history"""
        key = f"{route_name}:{version}"
        
        if key not in self.routes:
            return None
        
        return self.routes[key]["state_history"]
    
    async def list_routes_by_state(self, state: RouteLifecycleState) -> List[str]:
        """List all routes in a given state"""
        return [
            key for key, route in self.routes.items()
            if route["state"] == state
        ]

