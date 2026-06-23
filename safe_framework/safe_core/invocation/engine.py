"""Route invocation engine"""

import uuid
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime, timezone

from ..config import config
from ..tracing import get_correlation_id

class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"

@dataclass
class ExecutionRequest:
    route_name: str
    route_version: str
    input_data: Dict[str, Any]
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: str = field(default_factory=get_correlation_id)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    timeout_seconds: int = field(default_factory=lambda: config.execution_timeout_seconds)

@dataclass
class ExecutionResult:
    request_id: str
    route_name: str
    route_version: str
    status: ExecutionStatus
    correlation_id: str = ""
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0
    errors: List[str] = field(default_factory=list)
    retry_count: int = 0
    
    @property
    def is_successful(self) -> bool:
        return self.status == ExecutionStatus.SUCCESS

class RouteInvocationEngine:
    def __init__(self):
        self.pending_requests: Dict[str, ExecutionRequest] = {}
        self.completed_results: List[ExecutionResult] = []
        self.execution_queue: List[ExecutionRequest] = []
    
    async def create_execution_request(
        self, route_name: str, route_version: str,
        input_data: Dict[str, Any], timeout_seconds: int = -1,
    ) -> ExecutionRequest:
        request = ExecutionRequest(
            route_name=route_name,
            route_version=route_version,
            input_data=input_data,
            timeout_seconds=timeout_seconds if timeout_seconds >= 0 else config.execution_timeout_seconds,
        )
        self.pending_requests[request.request_id] = request
        self.execution_queue.append(request)
        return request
    
    async def dequeue_request(self) -> Optional[ExecutionRequest]:
        if self.execution_queue:
            return self.execution_queue.pop(0)
        return None
    
    async def save_result(self, result: ExecutionResult) -> None:
        self.completed_results.append(result)
        if result.request_id in self.pending_requests:
            del self.pending_requests[result.request_id]
    
    async def get_result(self, request_id: str) -> Optional[ExecutionResult]:
        return next((r for r in self.completed_results if r.request_id == request_id), None)

