# Event Router

_Classifies the normalised event and selects the appropriate handler agent._

## Overview

The Event Router is the **router** role in the **event-driven** pattern — agents triggered by events (webhook, queue message, file upload) rather than direct calls. Enables reactive, asynchronous enterprise integrations.

## Pattern Diagram

```mermaid
flowchart LR
    classDef active fill:#0078D4,color:#fff,stroke:#005A9E
    EventSource([Event Source]) --> Listener
    Listener --> Router
    Router -- data event --> HandlerA[Data Handler]
    Router -- M365 event --> HandlerB[M365 Handler]
    Router -- knowledge event --> HandlerC[Knowledge Handler]
    HandlerA --> Output([Handled])
    HandlerB --> Output
    HandlerC --> Output
    class Router active
```

## Contract Specification

### Inputs
**event_type** (string, required): Normalised event type from listener  
**payload** (object, required): Event payload  


### Outputs
**handler_key** (string): Key of the handler agent to invoke  
**routing_reason** (string): Why this handler was selected  


## Azure Tools

| Tool ID | Display Name | Service | Purpose in this role |
|---|---|---|---|
| `iq-foundry` | Foundry IQ | Indexed org knowledge via Azure AI Search | Classify event type to determine the correct handler |


## Usage

```python
from safe_framework.safe_core.code_generator import RouteCodeGenerator
from safe_framework.safe_core.models import RouteDefinition, RoutePattern, Agent

route = RouteDefinition(
    name="my-route",
    pattern=RoutePattern.EVENT_DRIVEN,
    agents={"router": Agent(
        name="Router",
        category="test",
        version="1.0",
        input_schema={"type": "object", "properties": {}},
        output_schema={"type": "object", "properties": {}},
    )},
    description="Example route using this role",
)
generated = RouteCodeGenerator.generate(route)
```

## Use Cases

1. **Event classification**
2. **Priority routing**
3. **Multi-system event dispatch**


## Limitations

- Event deduplication must be implemented using `event_id` — Service Bus / Event Hub provides at-least-once delivery
- Handler must be idempotent

## Related Roles

- **Listener** normalises → **Router** dispatches → **Handler** processes
- See also: `checkpoint-resume` for long-running event handlers that need state persistence

---

**Status:** Production Ready  
**Version:** 1.0  
**Framework:** SAFE 1.0  
**Last Updated:** 2026-06-21
