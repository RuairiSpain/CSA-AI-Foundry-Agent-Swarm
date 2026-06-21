# Diamond Merger

## Overview
Merges left and right branch results into a unified final output, completing the diamond pattern.

## Contract

### Inputs
- merge_input (object): Contains left_result and right_result from parallel processors

### Outputs
- merged_output (object): Combined result from both branches

## Usage

```python
from agents.diamond_merger import Agent

agent = Agent()
result = await agent.invoke({"left_result": {"processed": "A'"}, "right_result": {"processed": "B'"}})
# Returns: {"result": {"combined": "A'+B'"}}
```

## Use Cases
- Combine dual-path processing results
- Final stage in diamond pattern

## Dependencies
- (See requirements.txt)

## Limitations
- Requires both left and right branch results

## Related Agents
- Diamond Splitter
- Left Processor
- Right Processor

---

**Status:** Production Ready
**Version:** 1.0
**Framework:** SAFE 1.0
