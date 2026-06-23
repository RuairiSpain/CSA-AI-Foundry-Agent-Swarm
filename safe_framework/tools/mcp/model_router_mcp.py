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

import asyncio
import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP
from safe_core.tracing import correlation_headers

mcp = FastMCP("safe-model-router")

_ENDPOINT = os.environ.get("FOUNDRY_ENDPOINT", "").rstrip("/")
_API_KEY = os.environ.get("FOUNDRY_API_KEY", "")
_API_VERSION = "2025-01-01-preview"
_DEFAULT_TIMEOUT = float(os.environ.get("MODEL_ROUTER_TIMEOUT_SECONDS", "30"))

# Foundry Model Router deployment name (configured in your Foundry project)
_ROUTER_DEPLOYMENT = os.environ.get("MODEL_ROUTER_DEPLOYMENT", "model-router")

# Policy names supported by Azure AI Foundry Model Router
ROUTING_POLICIES = ("Quality", "Cost", "Balanced")

_MAX_RETRIES = 3
_RETRY_STATUSES = {429, 503}


def _headers() -> dict[str, str]:
    return {
        "api-key": _API_KEY,
        "Content-Type": "application/json",
        **correlation_headers(),
    }


def _validate_env() -> None:
    """Raise RuntimeError if required env vars are missing."""
    missing = [v for v in ("FOUNDRY_ENDPOINT", "FOUNDRY_API_KEY") if not os.environ.get(v)]
    if missing:
        raise RuntimeError(
            f"Missing required environment variable(s): {', '.join(missing)}. "
            "Set them before calling model-router tools."
        )


async def _post_with_retry(url: str, body: dict, headers: dict) -> dict:
    """POST with retry on 429/503 using exponential backoff."""
    async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
        for attempt in range(_MAX_RETRIES):
            resp = await client.post(url, json=body, headers=headers)
            if resp.status_code not in _RETRY_STATUSES:
                resp.raise_for_status()
                return resp.json()
            if attempt < _MAX_RETRIES - 1:
                await asyncio.sleep(2 ** attempt)
        resp.raise_for_status()
        return resp.json()


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
    _validate_env()

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
    req_headers = {**_headers(), "x-model-router-policy": policy}

    data = await _post_with_retry(url, body, req_headers)

    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError(
            f"No choices in model-router response (content filtered or empty). "
            f"Raw response: {data}"
        )
    content = choices[0].get("message", {}).get("content", "")

    return {
        "content": content,
        "model_used": data.get("model"),
        "policy": policy,
        "usage": data.get("usage"),
    }


@mcp.tool()
async def model_router_estimate_cost(
    prompt_tokens: int,
    output_tokens: int = 0,
    policy: str = "Balanced",
) -> dict[str, Any]:
    """Estimate the token cost for a request under a given routing policy.

    Uses indicative static rates. For live actuals, call safe-token-metrics
    (token_metrics_get_cost). Both prompt (input) and completion (output) tokens
    are included in the estimate.

    Args:
        prompt_tokens: Estimated number of prompt/input tokens.
        output_tokens: Estimated number of completion/output tokens (default 0).
        policy: Routing policy — "Quality", "Cost", or "Balanced".
    """
    if policy not in ROUTING_POLICIES:
        raise ValueError(f"policy must be one of {ROUTING_POLICIES}")

    # Model tier → typical token rates (USD per 1K tokens, input/output)
    _TIER_RATES: dict[str, dict[str, float]] = {
        "Quality":  {"model": "gpt-4o",        "input_per_1k": 0.005, "output_per_1k": 0.015},
        "Balanced": {"model": "gpt-4o-mini",   "input_per_1k": 0.00015, "output_per_1k": 0.0006},
        "Cost":     {"model": "phi-4-mini",    "input_per_1k": 0.0001, "output_per_1k": 0.0004},
    }

    tier = _TIER_RATES[policy]
    input_cost = (prompt_tokens / 1000) * tier["input_per_1k"]
    output_cost = (output_tokens / 1000) * tier["output_per_1k"]
    total_cost = input_cost + output_cost

    return {
        "policy": policy,
        "likely_model": tier["model"],
        "prompt_tokens": prompt_tokens,
        "output_tokens": output_tokens,
        "estimated_input_cost_usd": round(input_cost, 6),
        "estimated_output_cost_usd": round(output_cost, 6),
        "estimated_total_cost_usd": round(total_cost, 6),
        "input_rate_per_1k_usd": tier["input_per_1k"],
        "output_rate_per_1k_usd": tier["output_per_1k"],
        "note": "Rates are indicative defaults. Use safe-token-metrics for live actuals.",
    }


if __name__ == "__main__":
    mcp.run()
