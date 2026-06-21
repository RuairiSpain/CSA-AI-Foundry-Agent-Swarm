# Getting Started with SAFE Framework

**SAFE** (Semantic Agent Framework for Enterprises) is the orchestration layer for Azure AI Foundry agent swarms. It gives Cloud Solution Architects a pattern library, a code generator, a tool catalog, and a CLI to build, validate, and deploy multi-agent workflows on Azure.

---

## What You Get

| Capability | Description |
|---|---|
| 27 orchestration patterns | From simple sequential pipelines to complex human-in-the-loop workflows |
| 12 standalone agents | Ready-to-use agents for research, summarisation, RAG, document writing, and more |
| 8 MCP tool integrations | Azure IQ Suite, Cosmos DB, Durable Tasks, Model Router, Token Metrics |
| Code generator | Jinja2-based templates generate production-ready Python route code |
| `safe` CLI | Interactive route builder, catalog search, and tool management |
| Governance layer | Approval workflows, audit trail, cost controls, health monitoring |

---

## Five-Minute Quickstart

### 1. Install

```bash
git clone https://github.com/ruairispain/csa-ai-foundry-agent-swarm.git
cd csa-ai-foundry-agent-swarm/safe_framework
pip install -e .
```

### 2. Set Required Environment Variables

```bash
export FOUNDRY_ENDPOINT="https://<your-workspace>.openai.azure.com/"
export FOUNDRY_API_KEY="<your-api-key>"
```

For a full list of environment variables see [Azure Requirements](azure-requirements.md).

### 3. Verify the Installation

```bash
safe --help
```

Expected output:

```
Usage: safe [OPTIONS] COMMAND [ARGS]...

  SAFE — Semantic Agent Framework for Enterprises

Options:
  --help  Show this message and exit.

Commands:
  catalog  Search the agent catalog.
  route    Interactive route writer.
  tool     Manage MCP tools in the catalog.
```

### 4. Search the Agent Catalog

```bash
safe catalog researcher
```

### 5. Create Your First Route (Interactive)

```bash
safe route
```

The interactive route writer guides you through selecting a pattern, choosing agents, and generating executable Python code.

---

## Core Concepts

### Routes
A **route** is a named, versioned workflow that wires two or more agents together using an orchestration pattern. Routes are defined as `RouteDefinition` objects and can be generated from the CLI or written in Python.

### Patterns
A **pattern** defines how agents are arranged and how data flows between them. SAFE ships with 27 patterns. See [Patterns Overview](patterns-overview.md).

### Agents
Each agent has a **contract** (typed inputs and outputs defined in `agent.yaml`) and a **prompt** (`prompt.txt`). Agents are composed into routes — they do not call each other directly.

### Tools (MCP)
Agents are wired to external services via **MCP tools** — Azure IQ Suite, Cosmos DB, and custom SAFE tools. The tool catalog lives in `safe_framework/tools/catalog.yaml`. See [MCP Catalog Guide](guides/05-mcp-catalog.md).

---

## Repository Layout

```
safe_framework/
├── safe_cli/          CLI entry point (safe command)
├── safe_core/         Runtime: models, validator, code generator, interview
│   ├── audit/         Immutable audit trail
│   ├── governance/    Approval policies and workflows
│   ├── health/        Agent health monitoring
│   ├── execution/     Route execution engine
│   └── ...
├── agents/
│   ├── patterns/      27 orchestration patterns (role-based agent.yaml + agent.md)
│   └── standalone/    12 single-purpose agents
├── tools/
│   ├── catalog.yaml   Tool registry
│   └── mcp/           Custom MCP server implementations
pyproject.toml
```

---

## Next Steps

| I want to… | Go to |
|---|---|
| Install in detail with Azure setup | [Installation Guide](installation.md) |
| Understand Azure resource requirements | [Azure Requirements](azure-requirements.md) |
| See every CLI command | [Command Reference](command-reference.md) |
| Learn about patterns | [Patterns Overview](patterns-overview.md) |
| Build my first workflow | [Guide: Simple Workflow](guides/01-simple-workflow.md) |
| Build a business solution | [Guide: Business Workflow](guides/02-business-workflow.md) |
| Build a complex enterprise solution | [Guide: Complex Workflow](guides/03-complex-workflow.md) |
