# Team Coordinator

## Overview
Orchestrates the hierarchical-teams pattern by decomposing top-level requests into sub-tasks and assigning each to a team supervisor.

## Contract

### Inputs
- request (object): Top-level request with data payload

### Outputs
- coordinator_output (object): team_assignments mapping team keys to sub-requests

## Usage

```python
from agents.team_coordinator import Agent

agent = Agent()
result = await agent.invoke({"data": {"project": "analysis"}})
# Returns: {"team_assignments": {"team_0": {...}, "team_1": {...}}}
```

## Use Cases
- Decompose complex tasks across parallel teams
- Top-level orchestration in hierarchical pattern

## Dependencies
- (See requirements.txt)

## Limitations
- Decomposition strategy is task-specific

## Related Agents
- Team Supervisor
- Team Results Aggregator

---

**Status:** Production Ready
**Version:** 1.0
**Framework:** SAFE 1.0
