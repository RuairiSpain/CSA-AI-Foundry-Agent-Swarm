# Retry Worker

## Overview
Processes tasks in a retry-loop pattern. The worker is re-invoked up to max_retries times if the validator determines the output is insufficient.

## Contract

### Inputs
- request (object): Task request with data payload

### Outputs
- result (object): Task result

## Usage

```python
from agents.retry_worker import Agent

agent = Agent()
result = await agent.invoke({"data": {"task": "process"}})
# Returns: {"result": {"status": "done"}}
```

## Use Cases
- Idempotent task processing with retry support
- Worker in a retry-loop pattern

## Dependencies
- (See requirements.txt)

## Limitations
- Should produce idempotent output for safe retries

## Related Agents
- Result Validator

---

**Status:** Production Ready
**Version:** 1.0
**Framework:** SAFE 1.0
