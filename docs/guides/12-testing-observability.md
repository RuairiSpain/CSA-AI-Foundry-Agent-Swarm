# Guide: Testing and Observability

---

## Testing

### Running the Test Suite

```bash
cd safe_framework
pytest tests/ -v                         # All tests
pytest tests/test_patterns.py -v         # Pattern tests only
pytest tests/ -k "rag" -v               # Filter by name
pytest tests/ --cov=safe_core -v        # With coverage
```

### Test Structure

```
safe_framework/tests/
├── test_patterns.py       Pattern contract validation tests
├── test_validator.py      RouteValidator tests
├── test_code_generator.py Code generation tests
├── test_agent_catalog.py  Catalog loader tests
└── fixtures/              Sample route definitions and agent contracts
```

### Writing Route Tests

```python
# tests/test_my_route.py
import pytest
from unittest.mock import AsyncMock
from safe_framework.safe_core.models import RouteDefinition, RoutePattern

@pytest.mark.asyncio
async def test_route_validates():
    from safe_framework.safe_core.validator import RouteValidator
    route = RouteDefinition(
        name="my-route",
        pattern=RoutePattern.RAG,
        agents={...},
    )
    errors = RouteValidator().validate(route)
    assert not errors, f"Validation errors: {errors}"

@pytest.mark.asyncio
async def test_route_generates_code():
    from safe_framework.safe_core.code_generator import RouteCodeGenerator
    route = RouteDefinition(...)
    generated = RouteCodeGenerator().generate(route)
    assert "class MyRouteRoute" in generated.route_code
    assert "async def invoke" in generated.route_code
```

### Loading Test Data

Each pattern's `test_data.json` contains sample inputs and expected output schemas:

```python
import json

with open("routes/contract-review/test_data.json") as f:
    test_data = json.load(f)

# test_data structure:
# {
#   "sample_inputs": [...],
#   "expected_output_schema": {...},
#   "edge_cases": [...]
# }

for sample in test_data["sample_inputs"]:
    result = await route.invoke(sample)
    assert result["status"] in ("approved", "blocked", "rejected")
```

---

## Observability

### Application Insights Integration

```python
# Wire up at application start
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter

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

### Health Monitoring

```python
from safe_framework.safe_core.health.monitor import HealthMonitor

monitor = HealthMonitor()
monitor.register_route(
    route_name="contract-review",
    sla_latency_p95_seconds=60.0,
    error_rate_threshold=0.05,
)

# Check health
status = await monitor.get_status("contract-review")
# status.health: "healthy" | "degraded" | "critical"
```

### Dashboard

```python
from safe_framework.safe_core.monitoring.dashboard import Dashboard

dashboard = Dashboard()
report = await dashboard.generate(
    routes=["contract-review", "policy-qa"],
    period_hours=24,
)
print(report.summary)
```

### Key Metrics to Monitor

| Metric | Healthy Range | Alert Threshold |
|---|---|---|
| P95 latency | < 30s | > 60s |
| Error rate | < 1% | > 5% |
| Cost per run | < $0.10 | > $1.00 |
| Token usage | per baseline | > 2× baseline |
| Human gate wait | < 4h | > 24h |
| Evaluator iterations | 1–2 | = MAX (threshold never met) |
