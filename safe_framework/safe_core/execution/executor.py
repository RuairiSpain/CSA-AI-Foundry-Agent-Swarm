"""Execution engine with retry logic and error handling"""

from typing import Dict, Any, Optional
from datetime import datetime
from ..invocation.engine import ExecutionResult, ExecutionStatus
import asyncio

class RetryPolicy:
    def __init__(self, max_retries: int = 3, backoff_seconds: int = 2):
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds

class ExecutionEngine:
    def __init__(self, retry_policy: Optional[RetryPolicy] = None):
        self.retry_policy = retry_policy or RetryPolicy()
        self.executing: Dict[str, bool] = {}
    
    async def execute_route(
        self, result: ExecutionResult, route_callable
    ) -> ExecutionResult:
        try:
            result.status = ExecutionStatus.RUNNING
            start = datetime.now()
            
            # Simulate execution
            result.output_data = await route_callable(result.input_data)
            result.status = ExecutionStatus.SUCCESS
            
            elapsed = (datetime.now() - start).total_seconds() * 1000
            result.execution_time_ms = elapsed
            
        except Exception as e:
            result.errors.append(str(e))
            result.status = ExecutionStatus.FAILED
        
        return result
    
    async def execute_with_retry(
        self, result: ExecutionResult, route_callable
    ) -> ExecutionResult:
        for attempt in range(self.retry_policy.max_retries):
            result = await self.execute_route(result, route_callable)
            
            if result.is_successful:
                return result
            
            result.retry_count = attempt + 1
            
            if attempt < self.retry_policy.max_retries - 1:
                await asyncio.sleep(self.retry_policy.backoff_seconds)
        
        return result

