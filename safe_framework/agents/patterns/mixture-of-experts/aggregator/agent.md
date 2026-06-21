# Expert Aggregator

## Overview
Combines the weighted outputs from multiple domain experts into a single coherent final answer in the mixture-of-experts pattern.

## Contract

### Inputs
- expert_outputs (array): List of {expert, output, weight} objects from invoked experts

### Outputs
- final_output (object): Combined expert result

## Usage

```python
from agents.expert_aggregator import Agent

agent = Agent()
result = await agent.invoke({"expert_outputs": [{"expert": "e0", "output": {}, "weight": 0.9}]})
# Returns: {"result": {"answer": "..."}}
```

## Use Cases
- Combine weighted expert opinions
- Final aggregation in mixture-of-experts route

## Dependencies
- (See requirements.txt)

## Limitations
- Requires at least one valid expert output

## Related Agents
- Expert Router
- Domain Expert

---

**Status:** Production Ready
**Version:** 1.0
**Framework:** SAFE 1.0
