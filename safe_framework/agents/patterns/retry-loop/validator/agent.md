# Result Validator

## Overview
Validates worker output quality in a retry-loop pattern, returning a "valid" boolean to control whether the route retries.

## Contract

### Inputs
- validation_input (object): Contains result (worker output) and attempt (0-based count)

### Outputs
- validation_output (object): Contains valid (boolean) flag

## Usage

```python
from agents.result_validator import Agent

agent = Agent()
result = await agent.invoke({"result": {"status": "done"}, "attempt": 0})
# Returns: {"valid": true}
```

## Use Cases
- Quality gate for retry decisions
- Validate worker output in retry-loop pattern

## Dependencies
- (See requirements.txt)

## Limitations
- Validation criteria are domain-specific

## Related Agents
- Retry Worker

---

**Status:** Production Ready
**Version:** 1.0
**Framework:** SAFE 1.0
