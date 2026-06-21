# Round-Robin Worker

## Overview
Processes tasks assigned by the Round-Robin Dispatcher. Multiple instances of this agent form a worker pool for load distribution.

## Contract

### Inputs
- request (object): The task payload to process

### Outputs
- result (object): The processed result

## Usage

```python
from agents.round_robin_worker import Agent

agent = Agent()
result = await agent.invoke({"data": {"task": "process"}})
# Returns: {"result": {"status": "done"}}
```

## Use Cases
- Parallel task processing in a round-robin pool
- Load-balanced workload distribution

## Dependencies
- (See requirements.txt)

## Limitations
- Processes one request at a time per instance

## Related Agents
- Round-Robin Dispatcher

---

**Status:** Production Ready
**Version:** 1.0
**Framework:** SAFE 1.0
