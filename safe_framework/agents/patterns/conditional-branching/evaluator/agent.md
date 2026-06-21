# Condition Evaluator

## Overview
Evaluates incoming requests and determines which branch agent should handle them by returning the appropriate branch key.

## Contract

### Inputs
- request (object): Request payload with data field

### Outputs
- eval_output (object): Contains branch key (condition_field) for routing

## Usage

```python
from agents.condition_evaluator import Agent

agent = Agent()
result = await agent.invoke({"data": {"type": "urgent"}})
# Returns: {"branch": "branch_0"}
```

## Use Cases
- Route requests to the appropriate conditional branch
- Dynamic branching based on request content

## Dependencies
- (See requirements.txt)

## Limitations
- Returned branch key must match an available branch agent

## Related Agents
- Branch Agent

---

**Status:** Production Ready
**Version:** 1.0
**Framework:** SAFE 1.0
