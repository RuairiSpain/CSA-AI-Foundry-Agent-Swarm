"""Execution engine with timeout enforcement and exponential-backoff retry."""

import asyncio
import random
from typing import Any, Callable, Dict, Optional
from datetime import datetime, timezone
from ..invocation.engine import ExecutionResult, ExecutionStatus
from ..config import config as _global_config


class RetryPolicy:
    def __init__(
        self,
        max_retries: int | None = None,
        base_backoff_seconds: float | None = None,
        jitter: bool = True,
    ):
        self.max_retries = max_retries if max_retries is not None else _global_config.execution_max_retries
        self.base_backoff_seconds = (
            base_backoff_seconds if base_backoff_seconds is not None
            else _global_config.execution_base_backoff_seconds
        )
        self.jitter = jitter

    def backoff_for(self, attempt: int) -> float:
        """Return the sleep duration for *attempt* (0-indexed) with optional jitter."""
        delay = self.base_backoff_seconds * (2 ** attempt)
        if self.jitter:
            delay *= (0.5 + random.random())
        return delay


class ExecutionEngine:
    def __init__(self, retry_policy: Optional[RetryPolicy] = None):
        self.retry_policy = retry_policy or RetryPolicy()

    async def execute_route(
        self,
        result: ExecutionResult,
        route_callable: Callable,
        timeout_seconds: float = 60.0,
    ) -> ExecutionResult:
        """Execute *route_callable* with a hard timeout.

        Sets ExecutionStatus.TIMEOUT when the callable exceeds *timeout_seconds*
        instead of blocking indefinitely.
        """
        try:
            result.status = ExecutionStatus.RUNNING
            start = datetime.now(timezone.utc)

            result.output_data = await asyncio.wait_for(
                route_callable(result.input_data),
                timeout=timeout_seconds,
            )
            result.status = ExecutionStatus.SUCCESS

            elapsed = (datetime.now(timezone.utc) - start).total_seconds() * 1000
            result.execution_time_ms = elapsed

        except asyncio.TimeoutError:
            result.errors.append(f"Route timed out after {timeout_seconds}s")
            result.status = ExecutionStatus.TIMEOUT

        except Exception as e:
            result.errors.append(str(e))
            result.status = ExecutionStatus.FAILED

        return result

    async def execute_with_retry(
        self,
        result: ExecutionResult,
        route_callable: Callable,
        timeout_seconds: float = 60.0,
    ) -> ExecutionResult:
        """Retry *route_callable* up to max_retries times with exponential backoff + jitter."""
        for attempt in range(self.retry_policy.max_retries):
            result = await self.execute_route(result, route_callable, timeout_seconds)

            if result.is_successful:
                return result

            result.retry_count = attempt + 1

            if attempt < self.retry_policy.max_retries - 1:
                delay = self.retry_policy.backoff_for(attempt)
                await asyncio.sleep(delay)

        return result
