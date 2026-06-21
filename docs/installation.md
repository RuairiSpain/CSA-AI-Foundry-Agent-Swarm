# Installation Guide

## Prerequisites

| Requirement | Minimum Version | Notes |
|---|---|---|
| Python | 3.11 | 3.12+ recommended |
| pip | 23+ | |
| Azure subscription | — | Required for all IQ tools |
| Azure AI Foundry workspace | — | Required for agent execution |
| Azure Managed Identity | — | Required for tool authentication |

---

## Install from Source

SAFE Framework is not yet published to PyPI. Install directly from the repository.

```bash
# 1. Clone the repository
git clone https://github.com/ruairispain/csa-ai-foundry-agent-swarm.git
cd csa-ai-foundry-agent-swarm

# 2. Install the package (editable mode for development)
cd safe_framework
pip install -e .

# 3. Verify
safe --help
```

### Install with Dev Dependencies

For running tests, linting, and contributing:

```bash
pip install -e ".[dev]"
```

Dev dependencies include: `pytest`, `pytest-asyncio`, `pytest-cov`.

---

## Environment Variables

### Required (Core Framework)

```bash
# Azure AI Foundry endpoint and API key
export FOUNDRY_ENDPOINT="https://<workspace-name>.openai.azure.com/"
export FOUNDRY_API_KEY="<your-foundry-api-key>"
```

### Required for Custom MCP Servers

```bash
# safe-durable-task — Azure Durable Functions
export DURABLE_TASK_ENDPOINT="https://<function-app>.azurewebsites.net/runtime/webhooks/durabletask"
export DURABLE_TASK_KEY="<system-key>"
```

The `safe-model-router` and `safe-token-metrics` MCPs reuse `FOUNDRY_ENDPOINT` and `FOUNDRY_API_KEY`.

### Optional (Pattern-Specific)

| Variable | Used By | Description |
|---|---|---|
| `COSMOS_ENDPOINT` | memory-augmented pattern | Cosmos DB NoSQL endpoint |
| `COSMOS_KEY` | memory-augmented pattern | Cosmos DB primary key (or use MI) |
| `BING_API_KEY` | iq-web / web-query agent | Bing Search grounding API key |
| `AZURE_CLIENT_ID` | all MCP tools | Managed Identity client ID |
| `AZURE_TENANT_ID` | all MCP tools | Azure AD tenant ID |

---

## Using Managed Identity (Recommended for Production)

The IQ tools (`iq-foundry`, `iq-work`, `iq-fabric`, `iq-web`, `azure-cosmos-db`) all authenticate via Azure Managed Identity by default. Set up:

```bash
# Assign the Managed Identity roles needed (example for iq-foundry)
az role assignment create \
  --assignee <managed-identity-object-id> \
  --role "Azure AI Developer" \
  --scope /subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.CognitiveServices/accounts/<workspace>
```

See [Azure Requirements](azure-requirements.md) for the full list of RBAC roles.

---

## Verify the Installation

```bash
# Check CLI is accessible
safe --version

# Search the agent catalog
safe catalog

# List available tools
safe tool list
```

Expected output from `safe tool list`:

```
Tool Catalog
 id                  display name          category    version
 iq-foundry          Foundry IQ            azure-iq    1.0
 iq-work             Work IQ               azure-iq    1.0
 iq-fabric           Fabric IQ             azure-iq    1.0
 iq-web              Web IQ                azure-iq    1.0
 azure-cosmos-db     Azure Cosmos DB       azure       1.0
 safe-durable-task   SAFE Durable Task     safe-mcp    1.0
 safe-model-router   SAFE Model Router     safe-mcp    1.0
 safe-token-metrics  SAFE Token Metrics    safe-mcp    1.0
```

---

## Running the Custom MCP Servers

The three custom MCP servers ship as Python modules in `safe_framework/tools/mcp/`. They are loaded automatically when the corresponding tool is referenced in a route, but you can also start them standalone for debugging:

```bash
# Start the durable task MCP server on port 8001
python -m safe_framework.tools.mcp.durable_task_mcp --port 8001

# Start the model router MCP server on port 8002
python -m safe_framework.tools.mcp.model_router_mcp --port 8002

# Start the token metrics MCP server on port 8003
python -m safe_framework.tools.mcp.token_metrics_mcp --port 8003
```

---

## Updating

```bash
cd csa-ai-foundry-agent-swarm
git pull origin main
cd safe_framework
pip install -e .
```

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| `safe: command not found` | Package not installed or PATH issue | Run `pip install -e .` and check `pip show safe-framework` |
| `ModuleNotFoundError: safe_cli` | Installed from wrong directory | `cd safe_framework && pip install -e .` |
| `AuthenticationError` from MCP tools | Missing env vars | Check `FOUNDRY_ENDPOINT` and `FOUNDRY_API_KEY` are set |
| `ConnectionRefusedError` on MCP port | MCP server not started | Start the MCP server process; see above |
| Template render fails | Jinja2 not installed | `pip install jinja2` |

For additional help, see [FAQ and Troubleshooting](../SAFE-Complete-Phases-1-9/documentation/PHASE_3_FAQ_AND_TROUBLESHOOTING.md).
