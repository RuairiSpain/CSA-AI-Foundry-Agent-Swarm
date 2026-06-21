# Primary Agent

## Overview
The primary agent in a fallback-chain route. Attempted first; if it raises an exception the chain moves to the next fallback agent.

## Contract

### Inputs
- request (object): Request payload with data field

### Outputs
- result (object): Processed result

## Usage

```python
from agents.primary_agent import Agent

agent = Agent()
result = await agent.invoke({"data": {"task": "process"}})
# Returns: {"result": {"status": "done"}}
```

## Use Cases
- First attempt in a fallback chain
- Primary processing path

## Dependencies
- (See requirements.txt)

## Limitations
- May fail, which triggers the fallback chain

## Related Agents
- Fallback Agent

---

**Status:** Production Ready
**Version:** 1.0
**Framework:** SAFE 1.0
