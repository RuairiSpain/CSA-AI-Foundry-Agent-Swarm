"""Tests for correlation ID propagation across the agent pipeline (issue #14)."""

import json
import io
import pytest

from safe_core.tracing import (
    set_correlation_id,
    get_correlation_id,
    new_correlation_id,
    correlation_headers,
    StructuredLogger,
)
from safe_core.invocation.engine import ExecutionRequest, ExecutionResult, ExecutionStatus
from safe_core.audit.logger import AuditLogger, AuditEventType


class TestCorrelationIDContext:
    def test_default_is_empty(self):
        set_correlation_id("")
        assert get_correlation_id() == ""

    def test_set_and_get(self):
        set_correlation_id("test-cid-123")
        assert get_correlation_id() == "test-cid-123"

    def test_new_generates_uuid(self):
        cid = new_correlation_id()
        assert len(cid) == 36  # UUID4 canonical form
        assert get_correlation_id() == cid

    def test_correlation_headers_when_set(self):
        set_correlation_id("abc-456")
        hdrs = correlation_headers()
        assert hdrs == {"x-correlation-id": "abc-456"}

    def test_correlation_headers_when_empty(self):
        set_correlation_id("")
        assert correlation_headers() == {}


class TestExecutionRequestCorrelationID:
    def test_request_captures_active_correlation_id(self):
        set_correlation_id("req-cid-789")
        req = ExecutionRequest(
            route_name="test-route",
            route_version="v1.0",
            input_data={},
        )
        assert req.correlation_id == "req-cid-789"

    def test_request_has_empty_cid_when_not_set(self):
        set_correlation_id("")
        req = ExecutionRequest(
            route_name="test-route",
            route_version="v1.0",
            input_data={},
        )
        assert req.correlation_id == ""

    def test_result_accepts_correlation_id(self):
        result = ExecutionResult(
            request_id="req-001",
            route_name="test-route",
            route_version="v1.0",
            status=ExecutionStatus.SUCCESS,
            correlation_id="result-cid-xyz",
        )
        assert result.correlation_id == "result-cid-xyz"

    def test_result_defaults_correlation_id_to_empty(self):
        result = ExecutionResult(
            request_id="req-001",
            route_name="test-route",
            route_version="v1.0",
            status=ExecutionStatus.SUCCESS,
        )
        assert result.correlation_id == ""


class TestAuditEventCorrelationID:
    @pytest.mark.asyncio
    async def test_log_event_stores_correlation_id(self):
        logger = AuditLogger()
        event_id = await logger.log_event(
            event_type=AuditEventType.ROUTE_CREATED,
            actor="user@example.com",
            resource="my-route",
            resource_id="route-001",
            details={"version": "v1.0"},
            correlation_id="audit-cid-abc",
        )
        event = await logger.get_event(event_id)
        assert event is not None
        assert event.correlation_id == "audit-cid-abc"

    @pytest.mark.asyncio
    async def test_to_dict_includes_correlation_id(self):
        logger = AuditLogger()
        event_id = await logger.log_event(
            event_type=AuditEventType.ROUTE_DEPLOYED,
            actor="system",
            resource="my-route",
            resource_id="route-002",
            details={},
            correlation_id="dict-cid-xyz",
        )
        event = await logger.get_event(event_id)
        d = event.to_dict()
        assert d["correlation_id"] == "dict-cid-xyz"

    @pytest.mark.asyncio
    async def test_correlation_id_defaults_to_empty(self):
        logger = AuditLogger()
        event_id = await logger.log_event(
            event_type=AuditEventType.ROUTE_CREATED,
            actor="system",
            resource="my-route",
            resource_id="route-003",
            details={},
        )
        event = await logger.get_event(event_id)
        assert event.correlation_id == ""


class TestStructuredLogger:
    def _capture(self, fn, *args, **kwargs):
        buf = io.StringIO()
        import sys
        old_stderr = sys.stderr
        sys.stderr = buf
        try:
            fn(*args, **kwargs)
        finally:
            sys.stderr = old_stderr
        return json.loads(buf.getvalue().strip())

    def test_agent_invoked_includes_correlation_id(self):
        set_correlation_id("log-cid-111")
        log = StructuredLogger(route_name="fan-out")
        entry = self._capture(log.agent_invoked, "mapper_1", elapsed_ms=5.0)
        assert entry["correlation_id"] == "log-cid-111"
        assert entry["route_name"] == "fan-out"
        assert entry["stage"] == "mapper_1"
        assert entry["event"] == "agent_invoked"
        assert entry["elapsed_ms"] == 5.0

    def test_agent_failed_includes_error(self):
        set_correlation_id("log-cid-222")
        log = StructuredLogger(route_name="pipeline")
        entry = self._capture(log.agent_failed, "stage_2", error="timeout", elapsed_ms=3000.0)
        assert entry["event"] == "agent_failed"
        assert entry["error"] == "timeout"
        assert entry["correlation_id"] == "log-cid-222"

    def test_route_completed_event(self):
        set_correlation_id("log-cid-333")
        log = StructuredLogger(route_name="my-route")
        entry = self._capture(log.route_completed, elapsed_ms=120.0)
        assert entry["event"] == "route_completed"
        assert entry["elapsed_ms"] == 120.0

    def test_same_cid_across_multiple_events(self):
        cid = new_correlation_id()
        log = StructuredLogger(route_name="test")
        entries = [
            self._capture(log.route_started),
            self._capture(log.agent_invoked, "step_1"),
            self._capture(log.agent_succeeded, "step_1", elapsed_ms=10.0),
            self._capture(log.route_completed, elapsed_ms=50.0),
        ]
        assert all(e["correlation_id"] == cid for e in entries)
