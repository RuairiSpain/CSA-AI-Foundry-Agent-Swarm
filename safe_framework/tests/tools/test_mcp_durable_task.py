"""
Unit tests for the safe-durable-task MCP server.

Uses respx to mock Azure Durable Functions HTTP Management API calls so no
real Azure connection is required.
"""

import os
import pytest
import respx
import httpx

os.environ.setdefault("DURABLE_TASK_ENDPOINT", "https://test-app.azurewebsites.net")
os.environ.setdefault("DURABLE_TASK_KEY", "test-key")

# Import the MCP functions after env vars are set
from tools.mcp.durable_task_mcp import (
    durable_start,
    durable_checkpoint,
    durable_suspend,
    durable_resume,
    durable_get_status,
)

BASE = "https://test-app.azurewebsites.net/runtime/webhooks/durabletask"


@pytest.mark.asyncio
@respx.mock
async def test_durable_start_returns_instance_id():
    respx.post(f"{BASE}/orchestrators/MyOrchestrator").mock(
        return_value=httpx.Response(
            202,
            json={"id": "inst-001", "statusQueryGetUri": "https://test-app.azurewebsites.net/..."},
        )
    )
    # No instance_id → URL stays as .../orchestrators/MyOrchestrator
    result = await durable_start("MyOrchestrator", input={"key": "value"})
    assert result["id"] == "inst-001"


@pytest.mark.asyncio
@respx.mock
async def test_durable_start_with_custom_instance_id():
    respx.post(f"{BASE}/orchestrators/Fn/my-custom-id").mock(
        return_value=httpx.Response(202, json={"id": "my-custom-id"})
    )
    result = await durable_start("Fn", "my-custom-id", {})
    assert "id" in result


@pytest.mark.asyncio
@respx.mock
async def test_durable_checkpoint_returns_history():
    respx.get(
        f"{BASE}/instances/inst-001?showHistory=true&showHistoryOutput=true"
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "instanceId": "inst-001",
                "runtimeStatus": "Running",
                "input": {"topic": "test"},
                "historyEvents": [{"EventType": "ExecutionStarted"}],
            },
        )
    )
    result = await durable_checkpoint("inst-001")
    assert result["runtimeStatus"] == "Running"


@pytest.mark.asyncio
@respx.mock
async def test_durable_suspend_returns_suspended_status():
    respx.post(f"{BASE}/instances/inst-001/suspend").mock(
        return_value=httpx.Response(202, json={})
    )
    result = await durable_suspend("inst-001", "Manual pause")
    assert result["status"] == "suspended"
    assert result["instance_id"] == "inst-001"


@pytest.mark.asyncio
@respx.mock
async def test_durable_resume_returns_resumed_status():
    respx.post(f"{BASE}/instances/inst-001/resume").mock(
        return_value=httpx.Response(202, json={})
    )
    result = await durable_resume("inst-001", "Resuming after review")
    assert result["status"] == "resumed"
    assert result["instance_id"] == "inst-001"


@pytest.mark.asyncio
@respx.mock
async def test_durable_get_status_returns_runtime_fields():
    respx.get(f"{BASE}/instances/inst-001").mock(
        return_value=httpx.Response(
            200,
            json={
                "runtimeStatus": "Completed",
                "createdTime": "2026-01-01T00:00:00Z",
                "lastUpdatedTime": "2026-01-01T00:01:00Z",
                "output": {"result": "done"},
            },
        )
    )
    result = await durable_get_status("inst-001")
    assert result["runtime_status"] == "Completed"
    assert result["instance_id"] == "inst-001"
    assert result["output"] == {"result": "done"}


@pytest.mark.asyncio
@respx.mock
async def test_durable_get_status_running():
    respx.get(f"{BASE}/instances/inst-002").mock(
        return_value=httpx.Response(
            200,
            json={"runtimeStatus": "Running", "createdTime": None, "lastUpdatedTime": None, "output": None},
        )
    )
    result = await durable_get_status("inst-002")
    assert result["runtime_status"] == "Running"
    assert result["output"] is None


@pytest.mark.asyncio
@respx.mock
async def test_durable_start_no_instance_id():
    """When no instance_id given, URL should not include the trailing ID segment."""
    route = respx.post(f"{BASE}/orchestrators/NoIdFn").mock(
        return_value=httpx.Response(202, json={"id": "auto-gen-id"})
    )
    result = await durable_start("NoIdFn")
    assert route.called
