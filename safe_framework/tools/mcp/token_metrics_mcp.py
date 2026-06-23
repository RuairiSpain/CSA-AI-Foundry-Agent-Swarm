"""
safe-token-metrics MCP server
Wraps the Azure AI Foundry Token Metrics API for granular per-request cost
attribution and budget enforcement across agent workflows.

Required environment variables:
  FOUNDRY_ENDPOINT   — Azure AI Foundry project endpoint
  FOUNDRY_API_KEY    — API key from Azure AI Foundry project settings
  TOKEN_BUDGET_USD   — Optional daily budget cap in USD (default: no limit)

Mount via tools/catalog.yaml → id: safe-token-metrics
"""

from __future__ import annotations

import os
from datetime import date, timedelta
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP
from safe_core.tracing import correlation_headers

mcp = FastMCP("safe-token-metrics")

_ENDPOINT = os.environ.get("FOUNDRY_ENDPOINT", "").rstrip("/")
_API_KEY = os.environ.get("FOUNDRY_API_KEY", "")
_BUDGET_USD = float(os.environ.get("TOKEN_BUDGET_USD", "0"))
_API_VERSION = "2025-01-01-preview"


def _headers() -> dict[str, str]:
    return {
        "api-key": _API_KEY,
        "Content-Type": "application/json",
        **correlation_headers(),
    }


@mcp.tool()
async def token_metrics_get_usage(
    start_date: str = "",
    end_date: str = "",
    request_id: str = "",
    model: str = "",
) -> dict[str, Any]:
    """Get token usage breakdown for a time period or specific request.

    Args:
        start_date: ISO date string (YYYY-MM-DD). Defaults to today.
        end_date: ISO date string (YYYY-MM-DD). Defaults to today.
        request_id: Filter to a single request ID (optional).
        model: Filter to a specific model name (optional).
    """
    today = date.today().isoformat()
    params: dict[str, str] = {
        "api-version": _API_VERSION,
        "startDate": start_date or today,
        "endDate": end_date or today,
    }
    if request_id:
        params["requestId"] = request_id
    if model:
        params["model"] = model

    url = f"{_ENDPOINT}/metrics/tokens"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, headers=_headers())
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
async def token_metrics_get_cost(
    start_date: str = "",
    end_date: str = "",
    group_by: str = "model",
) -> dict[str, Any]:
    """Get cost breakdown by model, agent, or operation for a time period.

    Args:
        start_date: ISO date string (YYYY-MM-DD). Defaults to today.
        end_date: ISO date string (YYYY-MM-DD). Defaults to today.
        group_by: Dimension to group by — "model", "agent", or "operation".
    """
    today = date.today().isoformat()
    params = {
        "api-version": _API_VERSION,
        "startDate": start_date or today,
        "endDate": end_date or today,
        "groupBy": group_by,
    }

    url = f"{_ENDPOINT}/metrics/costs"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, headers=_headers())
        resp.raise_for_status()
        data = resp.json()

    return {"group_by": group_by, "costs": data}


@mcp.tool()
async def token_metrics_get_budget(period_days: int = 1) -> dict[str, Any]:
    """Get current budget utilization and remaining allowance.

    Compares actual spend (from Token Metrics API) against TOKEN_BUDGET_USD env var.
    Returns remaining budget and a warning flag when over 80% consumed.

    Args:
        period_days: Number of days to look back for spend calculation (default: 1 = today).
    """
    end = date.today()
    start = end - timedelta(days=period_days - 1)

    params = {
        "api-version": _API_VERSION,
        "startDate": start.isoformat(),
        "endDate": end.isoformat(),
        "groupBy": "model",
    }

    url = f"{_ENDPOINT}/metrics/costs"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, headers=_headers())
        resp.raise_for_status()
        data = resp.json()

    # Sum total cost across all groups
    total_cost = sum(
        float(entry.get("totalCost", 0))
        for entry in (data if isinstance(data, list) else data.get("costs", []))
    )

    result: dict[str, Any] = {
        "period_days": period_days,
        "total_cost_usd": round(total_cost, 4),
        "budget_configured": _BUDGET_USD > 0,
    }

    if _BUDGET_USD > 0:
        utilization = total_cost / _BUDGET_USD
        result["budget_usd"] = _BUDGET_USD
        result["remaining_usd"] = round(_BUDGET_USD - total_cost, 4)
        result["utilization_pct"] = round(utilization * 100, 1)
        result["budget_warning"] = utilization >= 0.8

    return result


if __name__ == "__main__":
    mcp.run()
