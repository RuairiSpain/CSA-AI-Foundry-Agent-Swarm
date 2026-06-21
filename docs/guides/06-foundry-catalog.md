# Guide: Adding Components to the Azure AI Foundry Catalog

This guide shows how to publish SAFE Framework agents, routes, and tools to the Azure AI Foundry agent catalog so they are discoverable and reusable across your engineering organisation.

---

## What Can Be Published

| Component | Foundry Catalog Type | What It Enables |
|---|---|---|
| Standalone agent | Agent definition | Engineers deploy and invoke the agent from Foundry UI or SDK |
| Pattern route | Agent workflow | Reusable multi-agent workflow available in Foundry |
| MCP tool | Connected tool | Tool available to any Foundry agent across the org |
| System prompt / persona | Prompt asset | Versioned prompt reuse |
| Fine-tuned model | Model deployment | Custom model available to all routes |

---

## Prerequisites

- Azure AI Foundry workspace (with Contributor access)
- Azure CLI logged in: `az login`
- Foundry Python SDK: `pip install azure-ai-foundry`
- Your agent tested and working locally

---

## Step 1: Structure Your Agent Package

Before publishing, ensure your agent directory is complete:

```
safe_framework/agents/standalone/my-agent/
├── agent.yaml        Contract, metadata, tools
├── agent.md          Documentation (required for catalog)
├── prompt.txt        System prompt (optional but recommended)
└── requirements.txt  Python dependencies
```

The `agent.yaml` must include the `documentation` block:

```yaml
# agent.yaml
name: My Custom Agent
version: 1.0
category: research
description: |
  Short description shown in the Foundry catalog.

contract:
  inputs:
    - name: query
      type: string
      required: true
      description: The question or task to process

  outputs:
    - name: result
      type: string
      required: true
      description: The agent's answer

metadata:
  author: "Azure CSA Team"
  tags:
    - research
    - enterprise
  sla_latency_p95_seconds: 30.0
  max_cost_per_run: 0.50

documentation:
  readme: agent.md
  examples:
    - input: {"query": "What is our cloud spend trend?"}
      output: {"result": "Azure spend increased 12% in Q2 driven by VM scale-out..."}

tools:
  - id: iq-foundry
    purpose: "Search enterprise knowledge base"
```

---

## Step 2: Publish an Agent to the Foundry Catalog

### Using the Azure AI Foundry Python SDK

```python
from azure.ai.foundry import AIFoundryClient
from azure.identity import DefaultAzureCredential
import yaml, pathlib

client = AIFoundryClient(
    endpoint=os.environ["FOUNDRY_ENDPOINT"],
    credential=DefaultAzureCredential(),
)

agent_dir = pathlib.Path("safe_framework/agents/standalone/my-agent")

# Load agent definition
with open(agent_dir / "agent.yaml") as f:
    agent_def = yaml.safe_load(f)

with open(agent_dir / "agent.md") as f:
    readme = f.read()

with open(agent_dir / "prompt.txt") as f:
    system_prompt = f.read()

# Register in the catalog
catalog_entry = client.agents.create(
    name=agent_def["name"],
    version=agent_def["version"],
    description=agent_def["description"],
    system_prompt=system_prompt,
    instructions=readme,
    tools=[
        {"type": "mcp", "tool_id": t["id"]}
        for t in agent_def.get("tools", [])
    ],
    metadata={
        "category": agent_def["category"],
        "tags": agent_def["metadata"]["tags"],
        "contract": agent_def["contract"],
    },
)

print(f"Published: {catalog_entry.id}")
print(f"Catalog URL: {catalog_entry.catalog_url}")
```

### Using the Azure CLI

```bash
# Deploy an agent from a definition file
az ai foundry agent create \
  --workspace-name <workspace> \
  --resource-group <rg> \
  --name "my-custom-agent" \
  --model "gpt-4o" \
  --instructions @safe_framework/agents/standalone/my-agent/prompt.txt \
  --description "My custom agent for enterprise research"
```

---

## Step 3: Publish a Multi-Agent Route (Workflow)

For pattern-based routes, publish the entire route as a Foundry workflow:

```python
from azure.ai.foundry import AIFoundryClient

client = AIFoundryClient(
    endpoint=os.environ["FOUNDRY_ENDPOINT"],
    credential=DefaultAzureCredential(),
)

# Read the generated route code
with open("routes/contract-review/route.py") as f:
    route_code = f.read()

with open("routes/contract-review/config.yaml") as f:
    route_config = yaml.safe_load(f)

# Publish as a named workflow in Foundry
workflow = client.workflows.create(
    name="contract-review",
    version="1.0",
    description="Contract review workflow: RAG + evaluator-optimizer + gate-guard",
    code=route_code,
    config=route_config,
    tags=["contracts", "legal", "compliance"],
)

print(f"Workflow published: {workflow.id}")
```

---

## Step 4: Register an MCP Tool in Foundry

Tools registered in Foundry are available to any agent across the workspace.

```python
# Register the safe-durable-task MCP tool
tool = client.tools.create(
    name="safe-durable-task",
    display_name="SAFE Durable Task",
    tool_type="mcp",
    mcp_config={
        "server_module": "safe_framework.tools.mcp.durable_task_mcp",
        "environment": {
            "DURABLE_TASK_ENDPOINT": os.environ["DURABLE_TASK_ENDPOINT"],
            "DURABLE_TASK_KEY": os.environ["DURABLE_TASK_KEY"],
        },
    },
    description="Checkpoint, suspend, and resume long-running agent workflows",
)
print(f"Tool registered: {tool.id}")
```

For the Azure IQ tools (`iq-foundry`, `iq-work`, etc.), they are provisioned at the Foundry workspace level and do not need to be registered manually. They appear automatically in the tool catalog once the Foundry workspace is configured.

---

## Step 5: Update the SAFE Framework Local Catalog

After publishing to Foundry, update the local `catalog.yaml` with the Foundry resource IDs so that `safe tool info` and `safe catalog` reflect the live state:

```yaml
# safe_framework/safe_core/catalog.yaml  (add your agent)
- name: my-custom-agent
  foundry_id: "agent-abc123"           # From catalog_entry.id above
  version: "1.0"
  category: research
  description: My custom agent for enterprise research
  tools:
    - iq-foundry
  tags:
    - research
    - enterprise
```

---

## Step 6: Verify in the Foundry UI

1. Open [Azure AI Foundry](https://ai.azure.com)
2. Navigate to your workspace → **Agents** tab
3. Search for your agent by name
4. Click **Test** to run a quick validation against a sample payload
5. Navigate to **Tools** tab to verify MCP tools are registered

---

## Version Management

SAFE Framework uses semantic versioning for catalog entries. When updating a published agent:

```python
# Publish a new version (does not replace the old one)
updated = client.agents.create(
    name="my-custom-agent",
    version="1.1",                      # Bump the version
    ...
)

# Deprecate the old version (keeps it available but marks as deprecated)
client.agents.update(
    agent_id="agent-abc123",
    lifecycle_stage="deprecated",
)
```

---

## Org-Wide Discovery

Once published, engineers across your organisation can discover and use your agents via:

```bash
# Via SAFE CLI (if catalog.yaml is synced)
safe catalog my-custom-agent

# Via Azure AI Foundry SDK
from azure.ai.foundry import AIFoundryClient
agents = client.agents.list(tags=["research"])

# Via Foundry UI
# ai.azure.com → Workspace → Agents → Browse Catalog
```
