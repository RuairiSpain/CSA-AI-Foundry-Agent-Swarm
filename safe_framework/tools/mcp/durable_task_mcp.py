"""
safe-durable-task MCP server
Wraps the Azure Durable Functions HTTP Management API so agents can checkpoint,
suspend, and resume long-running orchestrations without direct HTTP calls.

Required environment variables:
  DURABLE_TASK_ENDPOINT — Function App base URL, e.g. https://<app>.azurewebsites.net
  DURABLE_TASK_KEY      — Function App host key (from portal → Function Keys)

Mount via tools/catalog.yaml → id: safe-durable-task
"""

from __future__ import annotations

import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP
from safe_core.tracing import correlation_headers

mcp = FastMCP("safe-durable-task")

_BASE_URL = os.environ.get("DURABLE_TASK_ENDPOINT", "").rstrip("/")
_KEY = os.environ.get("DURABLE_TASK_KEY", "")
_MGMT = f"{_BASE_URL}/runtime/webhooks/durabletask"
_DEFAULT_TIMEOUT = float(os.environ.get("DURABLE_TASK_TIMEOUT_SECONDS", "30"))


def _validate_env() -> None:
    missing = [v for v in ("DURABLE_TASK_ENDPOINT", "DURABLE_TASK_KEY") if not os.environ.get(v)]
    if missing:
        raise RuntimeError(
            f"Missing required environment variable(s): {', '.join(missing)}."
        )


def _headers() -> dict[str, str]:
    return {
        "x-functions-key": _KEY,
        "Content-Type": "application/json",
        **correlation_headers(),
    }


@mcp.tool()
async def durable_start(
    function_name: str,
    instance_id: str = "",
    input: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Start a new Durable Functions orchestration instance.

    Args:
        function_name: Name of the orchestrator function to start.
        instance_id: Optional custom instance ID (auto-generated if blank).
        input: JSON payload to pass to the orchestration on start.
    """
    url = f"{_MGMT}/orchestrators/{function_name}"
    if instance_id:
        url += f"/{instance_id}"
    async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
        resp = await client.post(url, json=input or {}, headers=_headers())
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
async def durable_checkpoint(instance_id: str) -> dict[str, Any]:
    """Get the full state checkpoint of an orchestration — status, input, output, history.

    Args:
        instance_id: The orchestration instance ID returned by durable_start.
    """
    url = f"{_MGMT}/instances/{instance_id}?showHistory=true&showHistoryOutput=true"
    async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
        resp = await client.get(url, headers=_headers())
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
async def durable_suspend(instance_id: str, reason: str = "") -> dict[str, str]:
    """Suspend a running orchestration, preserving its current state.

    Args:
        instance_id: The orchestration instance ID.
        reason: Human-readable reason for suspension (logged in history).
    """
    url = f"{_MGMT}/instances/{instance_id}/suspend"
    async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
        resp = await client.post(url, json={"reason": reason}, headers=_headers())
        resp.raise_for_status()
        return {"status": "suspended", "instance_id": instance_id}


@mcp.tool()
async def durable_resume(instance_id: str, reason: str = "") -> dict[str, str]:
    """Resume a suspended orchestration from its last checkpoint.

    Args:
        instance_id: The orchestration instance ID.
        reason: Human-readable reason for resumption (logged in history).
    """
    url = f"{_MGMT}/instances/{instance_id}/resume"
    async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
        resp = await client.post(url, json={"reason": reason}, headers=_headers())
        resp.raise_for_status()
        return {"status": "resumed", "instance_id": instance_id}


@mcp.tool()
async def durable_get_status(instance_id: str) -> dict[str, Any]:
    """Get the current runtime status of an orchestration.

    Returns runtimeStatus: Running | Pending | Suspended | Completed | Failed | Terminated.

    Args:
        instance_id: The orchestration instance ID.
    """
    url = f"{_MGMT}/instances/{instance_id}"
    async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
        resp = await client.get(url, headers=_headers())
        resp.raise_for_status()
        data = resp.json()
        return {
            "instance_id": instance_id,
            "runtime_status": data.get("runtimeStatus"),
            "created_time": data.get("createdTime"),
            "last_updated_time": data.get("lastUpdatedTime"),
            "output": data.get("output"),
        }


if __name__ == "__main__":
    mcp.run()
