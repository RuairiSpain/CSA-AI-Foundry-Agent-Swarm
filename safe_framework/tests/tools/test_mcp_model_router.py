"""
Unit tests for the safe-model-router MCP server.

Uses respx to mock the Azure AI Foundry chat completions endpoint.
The cost-estimation logic is pure Python and needs no mock.
"""

import os
import pytest
import respx
import httpx

os.environ.setdefault("FOUNDRY_ENDPOINT", "https://test-hub.openai.azure.com")
os.environ.setdefault("FOUNDRY_API_KEY", "test-api-key")
os.environ.setdefault("MODEL_ROUTER_DEPLOYMENT", "model-router")

from tools.mcp.model_router_mcp import (
    model_router_chat,
    model_router_estimate_cost,
    ROUTING_POLICIES,
)

COMPLETIONS_URL = (
    "https://test-hub.openai.azure.com/openai/deployments/model-router"
    "/chat/completions?api-version=2025-01-01-preview"
)

MOCK_RESPONSE = {
    "choices": [{"message": {"content": "Hello from mock model"}}],
    "model": "gpt-4o-mini",
    "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
}


# ---------------------------------------------------------------------------
# model_router_chat
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@respx.mock
async def test_chat_balanced_policy_succeeds():
    respx.post(COMPLETIONS_URL).mock(return_value=httpx.Response(200, json=MOCK_RESPONSE))
    result = await model_router_chat([{"role": "user", "content": "hi"}], policy="Balanced")
    assert result["content"] == "Hello from mock model"
    assert result["model_used"] == "gpt-4o-mini"
    assert result["policy"] == "Balanced"


@pytest.mark.asyncio
@respx.mock
async def test_chat_quality_policy():
    respx.post(COMPLETIONS_URL).mock(return_value=httpx.Response(200, json=MOCK_RESPONSE))
    result = await model_router_chat([{"role": "user", "content": "hi"}], policy="Quality")
    assert result["policy"] == "Quality"


@pytest.mark.asyncio
@respx.mock
async def test_chat_cost_policy():
    respx.post(COMPLETIONS_URL).mock(return_value=httpx.Response(200, json=MOCK_RESPONSE))
    result = await model_router_chat([{"role": "user", "content": "hi"}], policy="Cost")
    assert result["policy"] == "Cost"


@pytest.mark.asyncio
async def test_chat_invalid_policy_raises():
    with pytest.raises(ValueError, match="policy must be one of"):
        await model_router_chat([{"role": "user", "content": "hi"}], policy="Invalid")


@pytest.mark.asyncio
@respx.mock
async def test_chat_usage_included_in_response():
    respx.post(COMPLETIONS_URL).mock(return_value=httpx.Response(200, json=MOCK_RESPONSE))
    result = await model_router_chat([{"role": "user", "content": "test"}])
    assert "usage" in result
    assert result["usage"]["total_tokens"] == 15


@pytest.mark.asyncio
@respx.mock
async def test_chat_extra_params_passed():
    route = respx.post(COMPLETIONS_URL).mock(return_value=httpx.Response(200, json=MOCK_RESPONSE))
    await model_router_chat(
        [{"role": "user", "content": "hi"}],
        extra={"stream": False},
    )
    assert route.called
    request_body = httpx.Request("POST", COMPLETIONS_URL, content=route.calls[0].request.content)
    import json
    body = json.loads(route.calls[0].request.content)
    assert body.get("stream") is False


# ---------------------------------------------------------------------------
# model_router_estimate_cost (pure logic — no HTTP call)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_estimate_cost_balanced_1000_tokens():
    result = await model_router_estimate_cost(1000, policy="Balanced")
    assert result["policy"] == "Balanced"
    assert result["prompt_tokens"] == 1000
    assert result["likely_model"] == "gpt-4o-mini"
    assert result["estimated_input_cost_usd"] == pytest.approx(0.00015, rel=1e-3)


@pytest.mark.asyncio
async def test_estimate_cost_quality_policy():
    result = await model_router_estimate_cost(500, policy="Quality")
    assert result["likely_model"] == "gpt-4o"
    assert result["estimated_input_cost_usd"] > 0


@pytest.mark.asyncio
async def test_estimate_cost_cost_policy_cheapest():
    balanced = await model_router_estimate_cost(1000, policy="Balanced")
    cost = await model_router_estimate_cost(1000, policy="Cost")
    quality = await model_router_estimate_cost(1000, policy="Quality")
    assert cost["estimated_input_cost_usd"] <= balanced["estimated_input_cost_usd"]
    assert balanced["estimated_input_cost_usd"] <= quality["estimated_input_cost_usd"]


@pytest.mark.asyncio
async def test_estimate_cost_invalid_policy_raises():
    with pytest.raises(ValueError):
        await model_router_estimate_cost(100, policy="NotAPolicy")


@pytest.mark.asyncio
async def test_estimate_cost_response_has_note():
    result = await model_router_estimate_cost(100)
    assert "note" in result


@pytest.mark.parametrize("policy", ROUTING_POLICIES)
@pytest.mark.asyncio
async def test_estimate_cost_all_valid_policies(policy):
    result = await model_router_estimate_cost(100, policy=policy)
    assert result["policy"] == policy
    assert result["estimated_input_cost_usd"] >= 0
