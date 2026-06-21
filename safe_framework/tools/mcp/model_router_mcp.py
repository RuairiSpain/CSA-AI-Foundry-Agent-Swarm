"""
safe-model-router MCP server
Wraps the Azure AI Foundry Model Router REST API so agents can route LLM calls
to the optimal model tier (Quality / Cost / Balanced) and estimate cost before routing.

Required environment variables:
  FOUNDRY_ENDPOINT — Azure AI Foundry project endpoint, e.g. https://<hub>.openai.azure.com
  FOUNDRY_API_KEY  — API key from Azure AI Foundry project settings

Mount via tools/catalog.yaml → id: safe-model-router
"""

from __future__ import annotations

import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("safe-model-router")

_ENDPOINT = os.environ.get("FOUNDRY_ENDPOINT", "").rstrip("/")
_API_KEY = os.environ.get("FOUNDRY_API_KEY", "")
_API_VERSION = "2025-01-01-preview"

# Foundry Model Router deployment name (configured in your Foundry project)
_ROUTER_DEPLOYMENT = os.environ.get("MODEL_ROUTER_DEPLOYMENT", "model-router")

# Policy names supported by Azure AI Foundry Model Router
ROUTING_POLICIES = ("Quality", "Cost", "Balanced")


def _headers() -> dict[str, str]:
    return {"api-key": _API_KEY, "Content-Type": "application/json"}


@mcp.tool()
async def model_router_chat(
    messages: list[dict[str, str]],
    policy: str = "Balanced",
    max_tokens: int = 1024,
    temperature: float = 0.7,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Route a chat completion to the optimal model tier via Foundry Model Router.

    The router automatically selects the best model (e.g. Phi-4-mini for simple tasks,
    GPT-4o for complex ones) according to the chosen policy.

    Args:
        messages: OpenAI-format message list, e.g. [{"role":"user","content":"..."}].
        policy: Routing policy — "Quality", "Cost", or "Balanced" (default).
        max_tokens: Maximum tokens in the completion.
        temperature: Sampling temperature (0.0–2.0).
        extra: Additional OpenAI-compatible parameters to pass through.
    """
    if policy not in ROUTING_POLICIES:
        raise ValueError(f"policy must be one of {ROUTING_POLICIES}")

    url = (
        f"{_ENDPOINT}/openai/deployments/{_ROUTER_DEPLOYMENT}"
        f"/chat/completions?api-version={_API_VERSION}"
    )
    body: dict[str, Any] = {
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        **(extra or {}),
    }
    headers = {**_headers(), "x-model-router-policy": policy}

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(url, json=body, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    return {
        "content": data["choices"][0]["message"]["content"],
        "model_used": data.get("model"),
        "policy": policy,
        "usage": data.get("usage"),
    }


@mcp.tool()
async def model_router_estimate_cost(
    prompt_tokens: int,
    policy: str = "Balanced",
) -> dict[str, Any]:
    """Estimate the token cost for a request under a given routing policy.

    Queries the Foundry Token Metrics API to look up current per-token rates
    for the model tier the router would select, without making an actual completion.

    Args:
        prompt_tokens: Estimated number of prompt tokens in the request.
        policy: Routing policy — "Quality", "Cost", or "Balanced".
    """
    if policy not in ROUTING_POLICIES:
        raise ValueError(f"policy must be one of {ROUTING_POLICIES}")

    # Model tier → typical token rates (USD per 1K tokens, input/output)
    # These are approximate defaults; token_metrics_get_cost provides live actuals.
    _TIER_RATES: dict[str, dict[str, float]] = {
        "Quality":  {"model": "gpt-4o",        "input_per_1k": 0.005, "output_per_1k": 0.015},
        "Balanced": {"model": "gpt-4o-mini",   "input_per_1k": 0.00015, "output_per_1k": 0.0006},
        "Cost":     {"model": "phi-4-mini",    "input_per_1k": 0.0001, "output_per_1k": 0.0004},
    }

    tier = _TIER_RATES[policy]
    estimated_cost = (prompt_tokens / 1000) * tier["input_per_1k"]

    return {
        "policy": policy,
        "likely_model": tier["model"],
        "prompt_tokens": prompt_tokens,
        "estimated_input_cost_usd": round(estimated_cost, 6),
        "input_rate_per_1k_usd": tier["input_per_1k"],
        "output_rate_per_1k_usd": tier["output_per_1k"],
        "note": "Rates are indicative defaults. Use safe-token-metrics for live actuals.",
    }


if __name__ == "__main__":
    mcp.run()
