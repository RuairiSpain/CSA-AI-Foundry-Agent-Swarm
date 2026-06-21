# Task Planner

_Produces an explicit step-by-step execution plan with dependencies before any work begins._

## Overview

The Task Planner is the **planner** role in the **planning** pattern — where an explicit plan is produced before any execution begins, reducing errors on complex multi-step business processes.

## Pattern Diagram

```mermaid
flowchart LR
    classDef active fill:#0078D4,color:#fff,stroke:#005A9E
    Input([Goal]) --> Planner
    Planner --> Executor
    Executor --> Step1[Step 1]
    Executor --> Step2[Step N]
    Step1 --> Reviewer
    Step2 --> Reviewer
    Reviewer --> Output([Reviewed Result])
    class Planner active
```

## Contract Specification

### Inputs
**goal** (string, required): High-level goal to plan  
**constraints** (object, optional): Deadline, budget, resource constraints  


### Outputs
**steps** (array): Ordered list of steps with IDs and dependencies  
**plan_id** (string): Plan identifier  
**estimated_duration_minutes** (integer): Estimated total duration  


## Azure Tools

| Tool ID | Display Name | Service | Purpose in this role |
|---|---|---|---|
| `iq-foundry` | Foundry IQ | Indexed org knowledge via Azure AI Search | Retrieve past plans and templates for similar goals |
| `iq-work` | Work IQ | M365 signals — meetings, chats, emails, documents | Understand org workflows, team capacity, and past execution history |

## Use Cases

1. **RFP response planning**
2. **Project timeline generation**
3. **Incident response plan**


## Limitations

- Plan quality determines execution quality — validate planner output on critical workflows
- Executor steps run sequentially; use `fan-out-fan-in` for parallelisable steps

## Related Roles

- **Planner** → **Executor** → **Reviewer** is the plan-execute-review chain

---

**Status:** Production Ready  
**Version:** 1.0  
**Framework:** SAFE 1.0  
**Last Updated:** 2026-06-21
