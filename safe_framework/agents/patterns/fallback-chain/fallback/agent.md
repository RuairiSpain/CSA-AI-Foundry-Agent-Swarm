# Fallback Agent

## Overview
An alternative agent in a fallback-chain route, activated when the primary agent or an earlier fallback agent fails.

## Contract

### Inputs
- request (object): Request payload with data field

### Outputs
- result (object): Fallback processed result

## Usage

```python
from agents.fallback_agent import Agent

agent = Agent()
result = await agent.invoke({"data": {"task": "process"}})
# Returns: {"result": {"status": "done"}}
```

## Use Cases
- Alternative processing when primary fails
- Part of a fallback chain for resilience

## Dependencies
- (See requirements.txt)

## Limitations
- May also fail, triggering the next fallback in the chain

## Related Agents
- Primary Agent

---

**Status:** Production Ready
**Version:** 1.0
**Framework:** SAFE 1.0
