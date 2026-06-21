# Guide: Debugging Agents with Azure AI Foundry

This guide covers the tools and techniques for debugging SAFE Framework agents and routes using Azure AI Foundry's built-in debugger, OpenTelemetry traces, and local debugging patterns.

---

## Debugging Layers

| Layer | Tool | When to Use |
|---|---|---|
| Local step-through | Python debugger + pytest | Agent contract issues, logic bugs in route code |
| Route trace inspection | SAFE Framework trace output | Multi-agent flow issues, agent contract mismatches |
| LLM call inspection | Azure AI Foundry Tracing UI | Prompt quality, token usage, LLM response quality |
| Production monitoring | Application Insights | Latency spikes, error rates, cost anomalies |
| Agent playground | Foundry Agent Testing UI | Interactive testing of individual agents |
| End-to-end replay | Foundry Evaluation harness | Regression testing with recorded inputs |

---

## 1. Local Debugging with Pytest

Run the SAFE Framework test suite to validate agent contracts and route logic:

```bash
cd safe_framework
pytest tests/ -v

# Run tests for a specific pattern
pytest tests/test_patterns.py::test_rag_pattern -v

# Run with coverage
pytest tests/ --cov=safe_core --cov-report=html
```

### Writing a Debug Test for Your Route

```python
# tests/test_contract_review.py
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from routes.contract_review.route import ContractReviewRoute

@pytest.fixture
def mock_kernel():
    kernel = MagicMock()
    return kernel

@pytest.fixture
def route_with_mocked_agents(mock_kernel):
    route = ContractReviewRoute(kernel=mock_kernel)

    # Mock each agent with a controlled response
    route.retriever = AsyncMock(return_value={
        "chunks": [{"content": "Section 3.1: Payment terms are net-30..."}],
        "sources": [{"title": "Supplier Agreement v2", "url": "..."}],
    })
    route.reranker = AsyncMock(return_value={
        "top_chunks": [{"content": "Section 3.1: Payment terms are net-30..."}],
    })
    route.rag_generator = AsyncMock(return_value={
        "assessment": "Risk: MEDIUM. Payment terms are standard but clause 7 is ambiguous.",
    })
    route.evaluator = AsyncMock(return_value={
        "quality_score": 0.9,
        "feedback": "Assessment is thorough and well-cited.",
    })
    route.guard = AsyncMock(return_value={
        "passed": True,
        "reason": None,
    })
    route.report_formatter = AsyncMock(return_value={
        "formatted_report": "## Contract Risk Report\n...",
        "risk_level": "MEDIUM",
        "recommendations": ["Clarify clause 7 with supplier"],
    })
    return route

@pytest.mark.asyncio
async def test_happy_path(route_with_mocked_agents):
    result = await route_with_mocked_agents.invoke({
        "contract_id": "TEST-001",
        "contract_text": "This agreement is between Contoso and the Supplier...",
    })
    assert result["status"] == "approved"
    assert result["risk_level"] == "MEDIUM"
    assert "Contract Risk Report" in result["report"]

@pytest.mark.asyncio
async def test_guard_blocks_high_risk(route_with_mocked_agents):
    route_with_mocked_agents.guard = AsyncMock(return_value={
        "passed": False,
        "reason": "Contract contains jurisdiction clause incompatible with EU GDPR",
        "escalate_to": "legal-team",
    })
    result = await route_with_mocked_agents.invoke({
        "contract_id": "TEST-002",
        "contract_text": "...",
    })
    assert result["status"] == "blocked"
    assert result["escalate_to"] == "legal-team"
```

---

## 2. Route Trace Inspection

SAFE Framework's execution engine logs a structured trace for every route invocation. Enable verbose trace output:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("safe_framework").setLevel(logging.DEBUG)
```

Example trace output:

```
[contract-review] Gate-Guard: validating request
[contract-review] Gate-Guard: PASSED (validation_ms=142)
[contract-review] RAG: retrieving (query="payment terms risk compliance...")
[contract-review] RAG.retriever: 8 chunks retrieved (retrieval_ms=2341)
[contract-review] RAG.reranker: top-5 selected (rerank_ms=318)
[contract-review] RAG.generator: draft assessment (generation_ms=4210, tokens_in=1850, tokens_out=480)
[contract-review] EO iteration 1: score=0.72 (below threshold 0.85)
[contract-review] EO.optimizer: refining prompt (optimizer_ms=1820)
[contract-review] EO iteration 2: score=0.89 (threshold met) ✓
[contract-review] Gate-Guard: compliance check PASSED
[contract-review] Report formatted (format_ms=2100)
[contract-review] COMPLETE — total_ms=11234, cost_usd=$0.045
```

### Reading the Trace

| Log Field | Meaning |
|---|---|
| `[route-name]` | Which route is executing |
| Pattern label (`RAG:`, `EO:`) | Which pattern step is running |
| `_ms=` suffix | Duration in milliseconds for that step |
| `tokens_in=` / `tokens_out=` | LLM token counts for this call |
| `score=` | Evaluator quality score |
| `PASSED` / `FAILED` | Gate/validator decision |

---

## 3. Azure AI Foundry Tracing UI

The Foundry UI provides a visual trace viewer for LLM calls. To connect:

### Enable Tracing

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter

# Wire up Application Insights tracing
provider = TracerProvider()
provider.add_span_processor(
    BatchSpanProcessor(
        AzureMonitorTraceExporter(
            connection_string=os.environ["APPLICATIONINSIGHTS_CONNECTION_STRING"]
        )
    )
)
trace.set_tracer_provider(provider)
```

### View Traces in Foundry

1. Open [Azure AI Foundry](https://ai.azure.com) → your workspace
2. Navigate to **Tracing** in the left sidebar
3. Filter by `safe.route.name` to find your route's traces
4. Click a trace to expand individual agent spans
5. Each span shows: prompt, completion, tokens, latency, model

### Inspecting Prompts and Completions

In the trace viewer, each agent invocation span shows:
- **System prompt** (from `prompt.txt`)
- **User message** (the agent's input after contract mapping)
- **Assistant response** (raw LLM output before schema parsing)
- **Token counts** (input, output, total)
- **Model deployment** used

Use this to diagnose:
- **Hallucinations** — LLM responded but ignored context
- **Schema mismatch** — LLM output doesn't match agent's output contract
- **Prompt leakage** — sensitive context inadvertently included
- **Token overflow** — input too long, context truncated

---

## 4. Agent Playground (Foundry UI)

Test individual agents interactively before wiring them into a route:

1. Open Azure AI Foundry → **Agents** tab
2. Select your published agent
3. Click **Try in Playground**
4. Send test messages using sample payloads from `test_data.json`

The playground shows real-time responses with token counts and a trace link.

### Local Playground with FastAPI

For agents not yet published to Foundry, run a local playground:

```python
# tools/playground.py
import asyncio
import json
from fastapi import FastAPI
from pydantic import BaseModel
from semantic_kernel import Kernel

app = FastAPI(title="SAFE Agent Playground")

class InvokeRequest(BaseModel):
    agent_name: str
    payload: dict

@app.post("/invoke")
async def invoke_agent(request: InvokeRequest):
    from safe_framework.safe_core.agent_catalog import AgentCatalog
    catalog = AgentCatalog()
    agent_def = catalog.get_agent(request.agent_name)

    # Simplified invocation for debugging
    kernel = Kernel()
    # ... configure kernel ...

    result = await kernel.invoke_prompt(
        prompt=json.dumps(request.payload),
        settings=None,
    )
    return {"result": str(result)}

# Run: uvicorn tools.playground:app --reload
```

---

## 5. Common Issues and Fixes

### Agent Output Doesn't Match Output Contract

**Symptom:** `ValidationError: field 'assessment' is required`

**Debug:**
```python
from safe_framework.safe_core.validator import RouteValidator
errors = RouteValidator().validate(my_route)
for e in errors:
    print(f"{e.error_type}: {e.message}")
    # Output: contract_mismatch: Agent 'reviewer' output missing field 'assessment'
```

**Fix:** Update the agent's system prompt to always return the required JSON fields, or add an output parser step.

---

### LLM Ignores Context (Hallucinating)

**Symptom:** Agent answers confidently but ignores retrieved chunks.

**Debug:** In Foundry Tracing, check the user message sent to the LLM. If retrieved chunks are not in the prompt, the retriever result is not being passed correctly.

**Fix:** Check the data flow between `retriever → reranker → generator`. Ensure `context` is serialised to the generator's input.

---

### Human Gate Never Resumes

**Symptom:** Workflow stuck in `suspended` state indefinitely.

**Debug:**
```python
from safe_framework.tools.mcp.durable_task_mcp import durable_get_status
status = await durable_get_status(instance_id="workflow-abc123")
print(status)  # Should show "suspended" with pending event name
```

**Fix:** Check that the approval notification was sent successfully. Manually resume for testing:
```python
from safe_framework.tools.mcp.durable_task_mcp import durable_resume
await durable_resume(
    instance_id="workflow-abc123",
    event_name="HumanApproval",
    event_data={"decision": "approved", "approver": "manager@company.com"},
)
```

---

### Evaluator Never Reaches Quality Threshold

**Symptom:** Log shows `Quality threshold not reached after 4 iterations`.

**Debug:** Lower `QUALITY_THRESHOLD` temporarily to `0.7` to see if the evaluator is scoring at all. Check evaluator agent prompt — ensure it returns `quality_score` as a float 0–1.

---

### Tool Authentication Fails

**Symptom:** `AuthenticationError: DefaultAzureCredential failed to retrieve a token`

**Debug:**
```bash
az account show           # Verify you are logged in
az account get-access-token --resource https://cognitiveservices.azure.com/
```

**Fix for local dev:** Set `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`, or run `az login`.

---

## 6. Debug Checklist

Before escalating a bug, work through this checklist:

- [ ] Run `safe route` validation — does the route pass contract checks?
- [ ] Check logs at `DEBUG` level — is every agent invoke logged?
- [ ] Find the trace in Foundry Tracing — does the failing span show the correct prompt?
- [ ] Check token counts — is context being truncated?
- [ ] Run the failing step in isolation using the Agent Playground
- [ ] Check environment variables are set (`FOUNDRY_ENDPOINT`, `FOUNDRY_API_KEY`, etc.)
- [ ] Check MCP server is running if using `safe-durable-task`, `safe-model-router`, or `safe-token-metrics`
- [ ] Verify the agent's output matches its declared output contract schema
