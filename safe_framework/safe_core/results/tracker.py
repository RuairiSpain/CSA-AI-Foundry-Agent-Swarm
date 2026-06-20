"""Result tracking and history"""

from typing import Dict, List, Optional
from ..invocation.engine import ExecutionResult, ExecutionStatus
from datetime import datetime

class ResultTracker:
    def __init__(self):
        self.results: Dict[str, ExecutionResult] = {}
        self.route_history: Dict[str, List[ExecutionResult]] = {}
    
    async def track_result(self, result: ExecutionResult) -> None:
        self.results[result.request_id] = result
        
        key = f"{result.route_name}:{result.route_version}"
        if key not in self.route_history:
            self.route_history[key] = []
        self.route_history[key].append(result)
    
    async def get_route_stats(self, route_name: str, version: str):
        key = f"{route_name}:{version}"
        history = self.route_history.get(key, [])
        
        if not history:
            return None
        
        successful = [r for r in history if r.is_successful]
        failed = [r for r in history if not r.is_successful]
        
        avg_time = sum(r.execution_time_ms for r in history) / len(history) if history else 0
        
        return {
            "total_executions": len(history),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(history) * 100 if history else 0,
            "avg_execution_time_ms": avg_time,
        }

