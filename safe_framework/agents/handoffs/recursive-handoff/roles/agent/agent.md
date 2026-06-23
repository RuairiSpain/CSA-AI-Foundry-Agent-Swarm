# Agent — Recursive Handoff

## Overview

The **agent** role in `recursive-handoff` is a self-similar agent connected to another instance of itself via ConnectedAgentTool. It processes the task directly if it determines no further breakdown is needed, or delegates a sub-problem to its connected sibling. Recursion is bounded by `max_depth`.

Ideal for tasks that are structurally self-similar: recursive document decomposition, tree traversal, divide-and-conquer reasoning, or hierarchical summarisation.

## Pattern Diagram

```mermaid
sequenceDiagram
    participant Caller
    participant A0 as agent (depth=0)
    participant A1 as agent (depth=1, connected)
    participant A2 as agent (depth=2, connected)

    Caller->>A0: invoke(task, depth=0)
    Note over A0: Decides to recurse
    A0->>A1: invoke(sub-task, depth=1)
    Note over A1: Decides to recurse
    A1->>A2: invoke(sub-sub-task, depth=2)
    Note over A2: Base case — solves directly
    A2-->>A1: sub-result
    A1-->>A0: merged result
    A0-->>Caller: {"result": "...", "depth": 0}
```

## Contract Specification

**Inputs**

| Field | Type   | Required | Description                          |
|-------|--------|----------|--------------------------------------|
| task  | string | yes      | Task or sub-task (may recurse)       |

**Outputs**

| Field  | Type   | Required | Description                          |
|--------|--------|----------|--------------------------------------|
| result | string | yes      | Result (self-solved or bubbled up)   |

## Azure Tools

| Tool       | Purpose                                        |
|------------|------------------------------------------------|
| iq-foundry | Knowledge retrieval for self-similar reasoning |

## Usage

Only one `agent` role is registered per `recursive-handoff` definition. The generated code connects the agent to a deployed instance of itself in Azure AI Foundry. Set `max_depth` conservatively (≤ 5) to avoid excessive token usage.
