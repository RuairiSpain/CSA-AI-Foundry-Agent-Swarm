# SAFE Framework Documentation

**SAFE** (Semantic Agent Framework for Enterprises) — an orchestration layer for Azure AI Foundry agent swarms.

---

## Start Here

| Document | Description |
|---|---|
| [Getting Started](getting-started.md) | What SAFE is, core concepts, 5-minute quickstart |
| [Installation Guide](installation.md) | Full install, environment variables, verification |
| [Azure Requirements](azure-requirements.md) | Mandatory and optional Azure services, RBAC roles, env vars |
| [Command Cheat Sheet](command-cheatsheet.md) | All `safe` CLI commands in one table |
| [Command Reference](command-reference.md) | Full CLI reference with flags, examples, and exit codes |
| [Patterns Overview](patterns-overview.md) | All 27 orchestration patterns with file links and decision guide |

---

## Workflow Guides

| Guide | Patterns Used | Complexity |
|---|---|---|
| [Simple Workflow: Policy Q&A](guides/01-simple-workflow.md) | `rag` | Beginner |
| [Business Workflow: Contract Review](guides/02-business-workflow.md) | `rag`, `evaluator-optimizer`, `gate-guard` | Intermediate |
| [Complex Workflow: Employee Onboarding](guides/03-complex-workflow.md) | 6 patterns + 3 standalone agents | Advanced |

---

## Reference Guides

| Guide | Description |
|---|---|
| [Standalone Agents](guides/04-standalone-agents.md) | All 12 standalone agents: file links, tools, MCPs, IQ API integration |
| [MCP Catalog](guides/05-mcp-catalog.md) | Private project MCPs, Azure IQ tools, public Microsoft MCP catalog |
| [Foundry Catalog](guides/06-foundry-catalog.md) | Publishing agents, routes, and tools to Azure AI Foundry |
| [Models, RAG & Governance](guides/07-models-rag-governance.md) | Deploying models, AI Search indexing, approval workflows |

---

## Tool Development Guides

| Guide | Description |
|---|---|
| [Purview Security Summary Tool](guides/08-purview-tool.md) | Custom MCP for Microsoft Purview sensitivity and compliance data |
| [OTL Analytics Tool](guides/09-otl-analytics-tool.md) | Custom MCP for OpenTelemetry metrics from Log Analytics |

---

## Operations

| Guide | Description |
|---|---|
| [Debugging Agents](guides/10-debug-agents.md) | Foundry Tracing UI, local debugging, common issues and fixes |
| [Agent Channels](guides/11-agent-channels.md) | M365 Copilot, Copilot Studio, VS Code Copilot, Teams |
| [Testing & Observability](guides/12-testing-observability.md) | Test suite, health monitoring, dashboards, key metrics |
| [Governance & Audit](guides/13-governance-audit.md) | Approval workflows, policies, audit trail, cost budgets |
| [Security & Compliance](guides/14-security-compliance.md) | Input validation, Managed Identity, data residency, GDPR |
| [Deployment & CI/CD](guides/15-deployment-cicd.md) | Docker, Azure Container Apps, AKS, GitHub Actions |

---

## Contributing

| Guide | Description |
|---|---|
| [Contributing](guides/16-contributing.md) | Adding patterns, agents, MCP tools; code style; PR process |

---

## Agent File Index

### Standalone Agents

| Agent | agent.yaml | agent.md |
|---|---|---|
| document-writer | [yaml](../safe_framework/agents/standalone/document-writer/agent.yaml) | [md](../safe_framework/agents/standalone/document-writer/agent.md) |
| empty-agent | [yaml](../safe_framework/agents/standalone/empty-agent/agent.yaml) | [md](../safe_framework/agents/standalone/empty-agent/agent.md) |
| presenter-code | [yaml](../safe_framework/agents/standalone/presenter-code/agent.yaml) | [md](../safe_framework/agents/standalone/presenter-code/agent.md) |
| presenter-html | [yaml](../safe_framework/agents/standalone/presenter-html/agent.yaml) | [md](../safe_framework/agents/standalone/presenter-html/agent.md) |
| presenter-markdown | [yaml](../safe_framework/agents/standalone/presenter-markdown/agent.yaml) | [md](../safe_framework/agents/standalone/presenter-markdown/agent.md) |
| presenter-word | [yaml](../safe_framework/agents/standalone/presenter-word/agent.yaml) | [md](../safe_framework/agents/standalone/presenter-word/agent.md) |
| rag-query | [yaml](../safe_framework/agents/standalone/rag-query/agent.yaml) | [md](../safe_framework/agents/standalone/rag-query/agent.md) |
| researcher | [yaml](../safe_framework/agents/standalone/researcher/agent.yaml) | [md](../safe_framework/agents/standalone/researcher/agent.md) |
| reviewer | [yaml](../safe_framework/agents/standalone/reviewer/agent.yaml) | [md](../safe_framework/agents/standalone/reviewer/agent.md) |
| semantic-search | [yaml](../safe_framework/agents/standalone/semantic-search/agent.yaml) | [md](../safe_framework/agents/standalone/semantic-search/agent.md) |
| summarizer | [yaml](../safe_framework/agents/standalone/summarizer/agent.yaml) | [md](../safe_framework/agents/standalone/summarizer/agent.md) |
| web-query | [yaml](../safe_framework/agents/standalone/web-query/agent.yaml) | [md](../safe_framework/agents/standalone/web-query/agent.md) |

### Pattern Roles

See [Patterns Overview](patterns-overview.md) for per-pattern links to all role files.

---

## Historical Phase Documentation

The `SAFE-Complete-Phases-1-9/documentation/` directory contains the original phase-by-phase delivery documents (Phases 1–9). These are preserved as implementation history but the guides above supersede them as the primary reference.
