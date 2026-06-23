"""Tests for execution engine timeout enforcement and exponential backoff."""
import asyncio
import pytest
from safe_core.execution.executor import ExecutionEngine, RetryPolicy
from safe_core.invocation.engine import ExecutionResult, ExecutionStatus


def _result():
    return ExecutionResult(
        request_id="req-1", route_name="test", route_version="v1",
        status=ExecutionStatus.PENDING, input_data={"x": 1},
    )


async def _success(data):
    return {"out": "ok"}


async def _fail(data):
    raise RuntimeError("deliberate failure")


async def _slow(data):
    await asyncio.sleep(10)
    return {"out": "never"}


class TestTimeout:
    @pytest.mark.asyncio
    async def test_successful_callable_returns_success(self):
        engine = ExecutionEngine()
        result = await engine.execute_route(_result(), _success, timeout_seconds=5.0)
        assert result.status == ExecutionStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_hung_callable_returns_timeout(self):
        engine = ExecutionEngine()
        result = await engine.execute_route(_result(), _slow, timeout_seconds=0.1)
        assert result.status == ExecutionStatus.TIMEOUT
        assert any("timed out" in e for e in result.errors)

    @pytest.mark.asyncio
    async def test_failing_callable_returns_failed(self):
        engine = ExecutionEngine()
        result = await engine.execute_route(_result(), _fail, timeout_seconds=5.0)
        assert result.status == ExecutionStatus.FAILED
        assert any("deliberate failure" in e for e in result.errors)


class TestRetryWithBackoff:
    @pytest.mark.asyncio
    async def test_succeeds_on_first_attempt(self):
        engine = ExecutionEngine(RetryPolicy(max_retries=3, base_backoff_seconds=0.01, jitter=False))
        result = await engine.execute_with_retry(_result(), _success, timeout_seconds=5.0)
        assert result.status == ExecutionStatus.SUCCESS
        assert result.retry_count == 0

    @pytest.mark.asyncio
    async def test_exhausts_retries_and_returns_failed(self):
        engine = ExecutionEngine(RetryPolicy(max_retries=3, base_backoff_seconds=0.01, jitter=False))
        result = await engine.execute_with_retry(_result(), _fail, timeout_seconds=5.0)
        assert result.status == ExecutionStatus.FAILED
        assert result.retry_count == 3

    @pytest.mark.asyncio
    async def test_backoff_grows_exponentially(self):
        policy = RetryPolicy(max_retries=3, base_backoff_seconds=1.0, jitter=False)
        assert policy.backoff_for(0) == 1.0
        assert policy.backoff_for(1) == 2.0
        assert policy.backoff_for(2) == 4.0

    @pytest.mark.asyncio
    async def test_jitter_varies_backoff(self):
        policy = RetryPolicy(max_retries=3, base_backoff_seconds=1.0, jitter=True)
        delays = {policy.backoff_for(0) for _ in range(20)}
        assert len(delays) > 1
