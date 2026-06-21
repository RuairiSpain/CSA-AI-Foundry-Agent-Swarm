# Domain Expert

## Overview
Applies specialised domain knowledge to analyse requests and produce expert-level output as part of a mixture-of-experts route.

## Contract

### Inputs
- request (object): The request payload from the router

### Outputs
- expert_output (object): Expert analysis result

## Usage

```python
from agents.domain_expert import Agent

agent = Agent()
result = await agent.invoke({"data": {"query": "finance question"}})
# Returns: {"result": {"answer": "..."}}
```

## Use Cases
- Domain-specific analysis
- Specialised inference in mixture-of-experts

## Dependencies
- (See requirements.txt)

## Limitations
- Limited to its assigned domain of expertise

## Related Agents
- Expert Router
- Expert Aggregator

---

**Status:** Production Ready
**Version:** 1.0
**Framework:** SAFE 1.0
