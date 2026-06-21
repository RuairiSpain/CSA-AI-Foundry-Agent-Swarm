# Tree Leaf Agent

## Overview
Processes input at the leaf level of a tree-reduce route. Multiple leaf agents run in parallel; their results are progressively combined by pairwise reduction.

## Contract

### Inputs
- request (object): Input request with data payload

### Outputs
- leaf_result (object): Leaf-level processing result for reduction

## Usage

```python
from agents.tree_leaf_agent import Agent

agent = Agent()
result = await agent.invoke({"data": {"segment": "part A"}})
# Returns: {"result": {"processed": "..."}}
```

## Use Cases
- Initial parallel processing in tree-reduce
- Leaf node in reduction tree

## Dependencies
- (See requirements.txt)

## Limitations
- Produces intermediate results; not a final output by itself

## Related Agents
- Tree Reducer

---

**Status:** Production Ready
**Version:** 1.0
**Framework:** SAFE 1.0
