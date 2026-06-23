# CSA Customer Call Copilot (C3 Copilot)

An AI-powered assistant for Cloud Solution Architects (CSAs) that listens to customer conversations and delivers real-time guidance, discovery prompts, and solution recommendations.

---

## Overview

C3 Copilot is an Azure AI Foundry-based multi-agent system designed to assist CSAs during live customer interactions (Teams calls, workshops, or transcript-driven sessions). It transforms conversation streams into actionable intelligence:

- Suggested open-ended discovery questions
- Solution architectures and Azure opportunities
- Risk identification (security, cost, governance, reliability)
- Executive-ready talk tracks and next-step recommendations

---

## Architecture

```
Audio Input (Teams / Mic / Transcript)
        ↓
Azure Speech SDK (optional)
        ↓
Listener Agent (WebSocket / MCP)
        ↓
AI Foundry Endpoint
        ↓
Enterprise Agent Swarm
        ↓
Guidance Cards + Talk Tracks
```

**Core concept:** Copilot UX → MCP Server → AI Foundry (multi-agent reasoning)

---

## Repository Structure

```
safe_framework/              # SAFE code-generation framework (main package)
  safe_core/                 # Validators, code generator, patterns, runtime modules
    audit/                   # Immutable audit trail
    execution/               # Execution engine with retry logic
    governance/              # Approval gates and policy engine
    health/                  # Health checks and monitoring
    invocation/              # Route invocation engine
    lifecycle/               # Route registration and promotion
    monitoring/              # Dashboard and metrics aggregation
    release/                 # Release manager with governance gate
    results/                 # Result tracking
    security/                # Input validation, PII detection, injection blocking
    templates/               # Jinja2 templates for code generation
  agents/                    # Agent catalog and pattern templates
  tools/                     # MCP servers and tool catalog
    mcp/                     # Custom MCP servers (durable-task, model-router, token-metrics)
  tests/                     # pytest test suite
  pyproject.toml
SAFE-Complete-Phases-1-9/    # Phase-by-phase design documentation
docs/                        # Additional guides and references
.github/
  workflows/
    coverage.yml             # PR coverage reporting
    freeze-check.yml         # Dependency freeze validation
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Azure AI Foundry project with model deployments configured
- (Optional) Azure Durable Functions app for long-running orchestrations

### Install

```bash
cd safe_framework
pip install -e ".[dev]"
```

### Configure

Copy and fill in the environment variables:

```bash
cp .env.example .env
# edit .env with your Azure endpoint, API key, and approver emails
```

### CLI commands

```bash
safe catalog [query]          # search available agents
safe route                    # interactive route creation wizard
safe chain                    # interactive multi-pattern chain wizard
safe chain list               # list saved chains
safe chain validate <name>    # validate field mappings
safe chain generate <name>    # regenerate chain.py from saved YAML
safe tool list                # list all MCP tools
safe tool info <id>           # show full catalog entry
```

### Run tests

```bash
cd safe_framework
pytest tests/                 # full suite
pytest tests/ -m safe_md      # agent.md section + token budget checks
pytest tests/ -m project_md   # engineer project MD under routes/
python -m coverage run --source=safe_core -m pytest tests/ -q
python -m coverage report --show-missing
```

---

## Core Components

### Listener Agent

Ingests conversation data and generates live guidance via:

- WebSocket streaming (`/listener/ws`)
- MCP tools (JSON-RPC)

Outputs per interaction: key insight, suggested question, solution hint, critical gap, structured extracted facts.

### MCP Server (Integration Layer)

Implements the Model Context Protocol: `initialize`, `tools/list`, `tools/call`, `resources/*`, `prompts/*`.

Enables integration with Copilot in VS Code, Copilot in GitHub, and custom clients.

### Enterprise Agent Swarm

```
Planner → Specialists → Principal Review → Verifier → Diagram Lint → Report
```

Specialist agents cover: security & network architecture, reliability, FinOps, data governance, DevSecOps, threat modelling, diagnostics, and report writing.

### Topic-Aware Intelligence

Dynamically classifies conversations and adapts behaviour across topics (security, architecture, FinOps, observability, data/AI, delivery) and modes (consultative, technical, executive).

---

## Guidance Cards

Each interaction produces a structured response:

```json
{
  "key_insight": "...",
  "suggested_question": "...",
  "solution_hint": "...",
  "critical_gap": "...",
  "_card": {
    "schema": "csa.card.security_compliance.v1",
    "sections": { "risk": "...", "controls": "...", "ask": "...", "next_step": "..." }
  }
}
```

---

## MCP Tools

Available via JSON-RPC:

| Tool | Description |
|------|-------------|
| `swarm.run` | Run the full enterprise agent swarm |
| `foundry.ask` | Direct Foundry model query |
| `debug.triage` | Diagnostic triage |
| `security.review` | Security review pass |
| `report.generate` | Generate final report |
| `diagram.lint` | Validate and fix Mermaid diagrams |
| `listener.start` / `listener.ingest` / `listener.state` | Listener lifecycle |

---

## Enterprise Design Principles

Every output enforces: identity & access (RBAC / Entra ID), networking (VNet, Private Link), observability (logging, tracing, evals), cost controls (routing, caching, quotas), resilience (HA/DR, RTO/RPO), governance & compliance, and security threat modelling.

---

## Limitations

- No direct real-time Teams audio capture (requires specific APIs)
- Requires transcript or audio-to-text input
- Azure Foundry models must be configured via environment variables (see `.env.example`)

---

## Author

Cloud Solution Architecture — Cloud & AI, Microsoft
