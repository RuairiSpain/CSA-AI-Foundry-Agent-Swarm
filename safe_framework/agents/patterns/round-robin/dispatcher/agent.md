# Round-Robin Dispatcher

## Overview
Dispatches incoming requests to workers in a round-robin fashion, returning a worker index to balance load evenly across the worker pool.

## Contract

### Inputs
- request (object): Incoming request payload with data field

### Outputs
- dispatch_output (object): Contains worker_index (0-based) for routing

## Usage

```python
from agents.round_robin_dispatcher import Agent

agent = Agent()
result = await agent.invoke({"data": {"task": "process"}})
# Returns: {"worker_index": 0}
```

## Use Cases
- Distribute load evenly across a pool of workers
- Implement stateless round-robin scheduling

## Dependencies
- (See requirements.txt)

## Limitations
- Stateless: index is derived from request metadata

## Related Agents
- Round-Robin Worker

---

**Status:** Production Ready
**Version:** 1.0
**Framework:** SAFE 1.0
