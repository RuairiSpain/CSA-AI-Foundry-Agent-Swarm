# Diamond Splitter

## Overview
Splits the input request into left and right branches for parallel processing in the diamond pattern.

## Contract

### Inputs
- request (object): Input request with data payload

### Outputs
- split_output (object): Contains left and right branch inputs

## Usage

```python
from agents.diamond_splitter import Agent

agent = Agent()
result = await agent.invoke({"data": {"payload": "..."}})
# Returns: {"left": {"half": "A"}, "right": {"half": "B"}}
```

## Use Cases
- Bifurcate input for dual-path parallel processing
- Entry point in diamond pattern

## Dependencies
- (See requirements.txt)

## Limitations
- Splitting strategy is domain-specific

## Related Agents
- Left Processor
- Right Processor
- Diamond Merger

---

**Status:** Production Ready
**Version:** 1.0
**Framework:** SAFE 1.0
