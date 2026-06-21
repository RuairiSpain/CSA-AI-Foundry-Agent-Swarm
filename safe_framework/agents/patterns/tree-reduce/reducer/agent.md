# Tree Reducer

## Overview
Performs pairwise combination of two inputs at each level of a tree-reduce route, progressively combining results until a single final output remains.

## Contract

### Inputs
- reduce_input (object): Contains left and right inputs to combine

### Outputs
- reduce_output (object): Combined reduction result with result field

## Usage

```python
from agents.tree_reducer import Agent

agent = Agent()
result = await agent.invoke({"left": {"result": "A"}, "right": {"result": "B"}})
# Returns: {"result": {"combined": "A+B"}}
```

## Use Cases
- Pairwise combination in tree-reduce pattern
- Intermediate and final reduction steps

## Dependencies
- (See requirements.txt)

## Limitations
- Combines exactly two inputs at a time

## Related Agents
- Tree Leaf Agent

---

**Status:** Production Ready
**Version:** 1.0
**Framework:** SAFE 1.0
