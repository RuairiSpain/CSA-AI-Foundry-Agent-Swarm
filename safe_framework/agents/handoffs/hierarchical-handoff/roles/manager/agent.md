## Overview

The **manager** in `hierarchical-handoff` sits at the root (or an intermediate node) of the delegation tree. It decomposes the incoming task into subtasks, dispatches each subtask to a `worker_*` sub-agent, and aggregates results. Workers can themselves be managers in deeper hierarchies, up to `max_depth`.

## Pattern Diagram

```mermaid
sequenceDiagram
    participant Caller
    participant Manager as manager
    participant W0 as worker_0
    participant W1 as worker_1

    Caller->>Manager: invoke(task)
    Note over Manager: Decomposes task into subtasks
    Manager->>W0: subtask A
    W0-->>Manager: result A
    Manager->>W1: subtask B
    W1-->>Manager: result B
    Note over Manager: Aggregates results
    Manager-->>Caller: {"result": "A + B aggregated"}
```

## Contract Specification

**Inputs**

| Field | Type   | Required | Description                        |
|-------|--------|----------|------------------------------------|
| task  | string | yes      | Task to decompose and delegate     |

**Outputs**

| Field  | Type   | Required | Description                         |
|--------|--------|----------|-------------------------------------|
| result | string | yes      | Aggregated result from all workers  |

## Azure Tools

| Tool       | Purpose                                           |
|------------|---------------------------------------------------|
| iq-foundry | Task decomposition context and worker capability  |

## Usage

The manager is registered with all `worker_*` agents as ConnectedAgentTools. The manager's LLM decides at runtime which workers to invoke and in what order based on the task decomposition.
