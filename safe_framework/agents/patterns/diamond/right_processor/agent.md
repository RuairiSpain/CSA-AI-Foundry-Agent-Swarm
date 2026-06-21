# Right Processor

## Overview
Processes the right branch of a diamond pattern route, running in parallel with the Left Processor.

## Contract

### Inputs
- right_input (object): Right branch data from the splitter

### Outputs
- right_result (object): Processed right branch result

## Usage

```python
from agents.right_processor import Agent

agent = Agent()
result = await agent.invoke({"data": {"half": "B"}})
# Returns: {"result": {"processed": "B'"}}
```

## Use Cases
- Right-path processing in diamond pattern
- Parallel processing alongside left processor

## Dependencies
- (See requirements.txt)

## Limitations
- Processes only the right branch input

## Related Agents
- Diamond Splitter
- Left Processor
- Diamond Merger

---

**Status:** Production Ready
**Version:** 1.0
**Framework:** SAFE 1.0
