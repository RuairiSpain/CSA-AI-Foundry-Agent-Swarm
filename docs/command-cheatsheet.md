# Command Cheat Sheet

Quick reference for every `safe` CLI command. For full flag descriptions and examples see [Command Reference](command-reference.md).

---

## Global

| Command | Description |
|---|---|
| `safe --help` | Show top-level help |
| `safe --version` | Show installed version |

---

## Catalog Commands

| Command | Description |
|---|---|
| `safe catalog` | List all agents in the catalog |
| `safe catalog <query>` | Search catalog by name, category, or keyword |

---

## Route Commands

| Command | Description |
|---|---|
| `safe route` | Launch interactive route writer |

---

## Tool Commands

| Command | Description |
|---|---|
| `safe tool list` | List all tools in the tool catalog |
| `safe tool list --category azure-iq` | Filter tools by category |
| `safe tool list --project` | Show only project-level tool overrides |
| `safe tool info <tool-id>` | Show full catalog entry for a tool |
| `safe tool rename <old-id> <new-id>` | Rename a tool in the local project catalog |
| `safe tool fork <tool-id> <project>` | Fork a catalog tool for project-level customisation |

---

## Common Workflows (Shell Sequences)

```bash
# Search for a research agent and see its full spec
safe catalog researcher

# Find all tools in the azure-iq category
safe tool list --category azure-iq

# Inspect the iq-foundry tool
safe tool info iq-foundry

# Rename a cloned tool for your project
safe tool fork iq-foundry my-project
safe tool rename iq-foundry iq-foundry-my-project

# Launch the interactive route writer to build a new route
safe route
```

---

## Tool IDs Quick Reference

| Tool ID | Display Name | Category |
|---|---|---|
| `iq-foundry` | Foundry IQ | azure-iq |
| `iq-work` | Work IQ | azure-iq |
| `iq-fabric` | Fabric IQ | azure-iq |
| `iq-web` | Web IQ | azure-iq |
| `azure-cosmos-db` | Azure Cosmos DB | azure |
| `safe-durable-task` | SAFE Durable Task | safe-mcp |
| `safe-model-router` | SAFE Model Router | safe-mcp |
| `safe-token-metrics` | SAFE Token Metrics | safe-mcp |

---

## Pattern Names Quick Reference

| Pattern | Use When |
|---|---|
| `sequential-pipeline` | Linear chain, each step depends on previous |
| `fan-out-fan-in` | Parallel workers, then aggregate |
| `map-reduce` | Batch processing large datasets |
| `supervisor-manager` | Runtime routing decisions |
| `round-robin` | Load-balanced identical workers |
| `mixture-of-experts` | Expert selection by router |
| `hierarchical-teams` | Nested team structures |
| `fallback-chain` | Primary → fallback on failure |
| `retry-loop` | Retry until validation passes |
| `diamond` | Parallel paths converging |
| `conditional-branching` | Dynamic branching on conditions |
| `tree-reduce` | Hierarchical reduction |
| `evaluator-optimizer` | Iterative quality improvement |
| `human-in-the-loop` | Human approval gate |
| `reflection` | Self-critique and refinement |
| `orchestrator-workers` | Dynamic task decomposition |
| `rag` | Retrieval-augmented generation |
| `planning` | Plan → execute → review |
| `gate-guard` | Policy check before processing |
| `self-consistency` | Consensus from multiple runs |
| `debate` | Deliberation and synthesis |
| `agent-as-a-tool` | Sub-agents callable as tools |
| `memory-augmented` | Persistent memory across invocations |
| `event-driven` | React to incoming events |
| `checkpoint-resume` | Durable long-running workflows |
| `budget-aware-routing` | Cost-constrained model selection |
| `adaptive-routing` | Performance-based routing |
