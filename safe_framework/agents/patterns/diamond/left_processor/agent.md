# Left Processor

## Overview
Processes the left branch of a diamond pattern route, running in parallel with the Right Processor.

## Contract

### Inputs
- left_input (object): Left branch data from the splitter

### Outputs
- left_result (object): Processed left branch result

## Usage

```python
from agents.left_processor import Agent

agent = Agent()
result = await agent.invoke({"data": {"half": "A"}})
# Returns: {"result": {"processed": "A'"}}
```

## Use Cases
- Left-path processing in diamond pattern
- Parallel processing alongside right processor

## Dependencies
- (See requirements.txt)

## Limitations
- Processes only the left branch input

## Related Agents
- Diamond Splitter
- Right Processor
- Diamond Merger

---

**Status:** Production Ready
**Version:** 1.0
**Framework:** SAFE 1.0
