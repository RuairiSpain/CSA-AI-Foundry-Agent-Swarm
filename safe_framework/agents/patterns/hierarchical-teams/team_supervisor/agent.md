# Team Supervisor

## Overview
Leads a team to complete an assigned sub-task as part of a hierarchical multi-team workflow.

## Contract

### Inputs
- sub_request (object): Sub-task assigned by the coordinator

### Outputs
- team_result (object): The team's completed result

## Usage

```python
from agents.team_supervisor import Agent

agent = Agent()
result = await agent.invoke({"data": {"subtask": "analyse segment A"}})
# Returns: {"result": {"analysis": "..."}}
```

## Use Cases
- Lead a team through a sub-task
- Mid-level orchestration in hierarchical pattern

## Dependencies
- (See requirements.txt)

## Limitations
- Scope limited to assigned sub-task

## Related Agents
- Team Coordinator
- Team Results Aggregator

---

**Status:** Production Ready
**Version:** 1.0
**Framework:** SAFE 1.0
