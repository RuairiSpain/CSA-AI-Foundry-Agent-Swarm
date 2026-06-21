# Team Results Aggregator

## Overview
Combines and synthesises results from all team supervisors into a single unified final output in the hierarchical-teams pattern.

## Contract

### Inputs
- team_results (object): Dict mapping team_key to each team's result

### Outputs
- final_output (object): Combined result from all teams

## Usage

```python
from agents.team_results_aggregator import Agent

agent = Agent()
result = await agent.invoke({"team_results": {"team_0": {"result": "..."}, "team_1": {"result": "..."}}})
# Returns: {"result": {"combined": "..."}}
```

## Use Cases
- Combine results from multiple teams
- Final synthesis in hierarchical-teams route

## Dependencies
- (See requirements.txt)

## Limitations
- Requires at least one team result

## Related Agents
- Team Coordinator
- Team Supervisor

---

**Status:** Production Ready
**Version:** 1.0
**Framework:** SAFE 1.0
