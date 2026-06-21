"""Phase 7 tests"""

import pytest
import asyncio
from safe_core.invocation.engine import (
    RouteInvocationEngine, ExecutionRequest, ExecutionResult, ExecutionStatus
)
from safe_core.execution.executor import ExecutionEngine, RetryPolicy
from safe_core.results.tracker import ResultTracker

class TestInvocationEngine:
    @pytest.mark.asyncio
    async def test_create_request(self):
        engine = RouteInvocationEngine()
        request = await engine.create_execution_request(
            "test-route", "v1.0", {"data": "test"}
        )
        assert request.route_name == "test-route"
        assert request.input_data == {"data": "test"}
    
    @pytest.mark.asyncio
    async def test_dequeue_request(self):
        engine = RouteInvocationEngine()
        request = await engine.create_execution_request(
            "test-route", "v1.0", {}
        )
        dequeued = await engine.dequeue_request()
        assert dequeued.request_id == request.request_id
    
    @pytest.mark.asyncio
    async def test_save_and_retrieve_result(self):
        engine = RouteInvocationEngine()
        result = ExecutionResult(
            request_id="req-001",
            route_name="test-route",
            route_version="v1.0",
            status=ExecutionStatus.SUCCESS,
            output_data={"result": "ok"},
        )
        await engine.save_result(result)
        retrieved = await engine.get_result("req-001")
        assert retrieved.request_id == "req-001"

class TestExecutionEngine:
    @pytest.mark.asyncio
    async def test_successful_execution(self):
        engine = ExecutionEngine()
        result = ExecutionResult(
            request_id="req-001",
            route_name="test",
            route_version="v1.0",
            status=ExecutionStatus.PENDING,
            input_data={"test": True},
        )
        
        async def mock_route(data):
            return {"status": "ok"}
        
        result = await engine.execute_route(result, mock_route)
        assert result.is_successful
        assert result.execution_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_retry_on_failure(self):
        engine = ExecutionEngine(RetryPolicy(max_retries=3))
        result = ExecutionResult(
            request_id="req-001",
            route_name="test",
            route_version="v1.0",
            status=ExecutionStatus.PENDING,
            input_data={},
        )
        
        call_count = [0]
        
        async def failing_route(data):
            call_count[0] += 1
            if call_count[0] < 3:
                raise Exception("Temporary failure")
            return {"status": "ok"}
        
        result = await engine.execute_with_retry(result, failing_route)
        assert result.retry_count >= 1

class TestResultTracker:
    @pytest.mark.asyncio
    async def test_track_result(self):
        tracker = ResultTracker()
        result = ExecutionResult(
            request_id="req-001",
            route_name="test",
            route_version="v1.0",
            status=ExecutionStatus.SUCCESS,
        )
        await tracker.track_result(result)
        stats = await tracker.get_route_stats("test", "v1.0")
        assert stats["total_executions"] == 1

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

