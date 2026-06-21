# Expert Router

## Overview
Analyses incoming requests and assigns relevance weights to each domain expert, enabling selective invocation in the mixture-of-experts pattern.

## Contract

### Inputs
- request (object): The incoming request with data payload

### Outputs
- routing_output (object): expert_weights dict mapping expert keys to 0-1 weights

## Usage

```python
from agents.expert_router import Agent

agent = Agent()
result = await agent.invoke({"data": {"query": "finance question"}})
# Returns: {"expert_weights": {"expert_0": 0.9, "expert_1": 0.1}}
```

## Use Cases
- Route queries to domain experts by relevance
- Weighted expert selection for mixture-of-experts

## Dependencies
- (See requirements.txt)

## Limitations
- Weights are computed heuristically from request content

## Related Agents
- Domain Expert
- Expert Aggregator

---

**Status:** Production Ready
**Version:** 1.0
**Framework:** SAFE 1.0
