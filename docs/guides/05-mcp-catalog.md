# Guide: MCP Tool Catalog

This guide covers the SAFE Framework tool catalog: the project-private MCP servers, the Azure IQ remote tools, and the public Microsoft MCP catalog.

---

## Tool Catalog Structure

The tool catalog is defined in two files:

```
safe_framework/tools/
├── catalog.yaml          Global catalog (all tools, all projects)
├── project-catalog.yaml  Project-level overrides (created by safe tool fork)
└── mcp/
    ├── durable_task_mcp.py   safe-durable-task server
    ├── model_router_mcp.py   safe-model-router server
    └── token_metrics_mcp.py  safe-token-metrics server
```

---

## Remote Azure IQ Tools

These tools run as hosted services in Azure AI Foundry. No local process required.

### `iq-foundry` — Foundry IQ

Indexes and searches enterprise knowledge from SharePoint, OneLake, and Azure Blob Storage using Azure AI Search.

**Functions:**

```python
search(
    query: str,            # Natural language or keyword query
    top_k: int = 5,        # Number of results to return
    filters: dict = None,  # OData filter expressions for metadata
    semantic: bool = True, # Use semantic ranking (default: True)
) -> list[SearchResult]

retrieve(
    doc_id: str,           # Document identifier
) -> Document
```

**Authentication:** Managed Identity
**Required role:** `Search Index Data Reader` on the AI Search resource

**Configuration in agent.yaml:**

```yaml
tools:
  - id: iq-foundry
    purpose: "Search the enterprise knowledge base"
    config:
      index_name: "enterprise-docs"          # Your AI Search index name
      semantic_config: "my-semantic-config"  # Semantic ranker config name
      top_k: 5
```

---

### `iq-work` — Work IQ

Provides access to M365 signals: meetings, emails, Teams chats, and OneDrive documents via Microsoft Graph API.

**Functions:**

```python
search(
    query: str,
    content_types: list = ["messages", "files", "meetings"],
    date_range_days: int = 30,
) -> list[WorkItem]

get_meeting_context(
    meeting_id: str,
) -> MeetingContext        # Transcript, attendees, action items

get_document(
    doc_id: str,           # SharePoint/OneDrive item ID
) -> Document
```

**Authentication:** Delegated (user context) or Application (service account)
**Required Graph permissions:** `Mail.Read`, `Calendars.Read`, `Files.Read.All`, `Chat.Read`

---

### `iq-fabric` — Fabric IQ

Queries Microsoft Fabric datasets, Power BI semantic models, and OneLake data products.

**Functions:**

```python
query(
    dataset_id: str,
    dax_query: str = None,    # DAX expression for Power BI models
    sql_query: str = None,    # SQL for Fabric warehouse/lakehouse
) -> QueryResult

get_dataset(
    dataset_id: str,
) -> DatasetMetadata
```

**Authentication:** Managed Identity
**Required role:** `Fabric Contributor` on the workspace

---

### `iq-web` — Web IQ

Searches the live public web and news using Bing grounding. Results are filtered for freshness and credibility.

**Functions:**

```python
web_search(
    query: str,
    freshness: str = "month",  # "day", "week", "month"
    market: str = "en-US",
    max_results: int = 10,
) -> list[WebResult]

fetch_page(
    url: str,
    extract_text: bool = True,
) -> PageContent
```

**Authentication:** API Key (`BING_API_KEY` environment variable)

---

### `azure-cosmos-db` — Azure Cosmos DB

Vector + document store supporting hybrid (keyword + vector) search. Used by `memory-augmented` pattern and `rag-query` agent.

**Functions:**

```python
vector_search(
    query_vector: list[float],
    container: str,
    top_k: int = 5,
    pre_filter: dict = None,   # Cosmos DB filter expression
) -> list[Document]

upsert(
    container: str,
    document: dict,            # Must include "id" field
) -> str                       # Document ID

get(
    container: str,
    doc_id: str,
) -> dict

query(
    container: str,
    sql: str,                  # Cosmos DB SQL query
) -> list[dict]
```

**Authentication:** Managed Identity or Connection String (`COSMOS_ENDPOINT`, `COSMOS_KEY`)
**Required role:** `Cosmos DB Built-in Data Contributor`

---

## Project-Private MCP Servers

These three MCP servers are implemented in Python and run as local processes. They wrap Azure services with SAFE-specific abstractions.

---

### `safe-durable-task`

Wraps the Azure Durable Functions HTTP Management API to provide checkpoint/suspend/resume for long-running workflows.

**Source:** [`safe_framework/tools/mcp/durable_task_mcp.py`](../../safe_framework/tools/mcp/durable_task_mcp.py)

**Environment variables:**
```bash
DURABLE_TASK_ENDPOINT=https://<func-app>.azurewebsites.net/runtime/webhooks/durabletask
DURABLE_TASK_KEY=<system-key>
```

**Functions:**

```python
durable_start(
    orchestrator_name: str,
    instance_id: str,
    input_data: dict,
) -> str                    # Orchestration instance ID

durable_checkpoint(
    instance_id: str,
    checkpoint_data: dict,
) -> None

durable_suspend(
    instance_id: str,
    reason: str,
) -> None                   # Pauses orchestration; awaits external event

durable_resume(
    instance_id: str,
    event_name: str,
    event_data: dict,
) -> None                   # Signals the suspended orchestration

durable_get_status(
    instance_id: str,
) -> OrchestrationStatus    # running/suspended/completed/failed
```

**Starting the server:**
```bash
python -m safe_framework.tools.mcp.durable_task_mcp --port 8001
```

---

### `safe-model-router`

Routes LLM calls to the most cost-effective Azure AI Foundry deployment that meets the specified quality policy.

**Source:** [`safe_framework/tools/mcp/model_router_mcp.py`](../../safe_framework/tools/mcp/model_router_mcp.py)

**Environment variables:**
```bash
FOUNDRY_ENDPOINT=https://<workspace>.openai.azure.com/
FOUNDRY_API_KEY=<key>
```

**Functions:**

```python
model_router_chat(
    messages: list[dict],
    policy: str = "balanced",  # "quality", "cost", "balanced", "speed"
    max_tokens: int = 4096,
    temperature: float = 0.7,
) -> ChatCompletion

model_router_estimate_cost(
    messages: list[dict],
    policy: str = "balanced",
) -> CostEstimate             # Estimated tokens and USD cost
```

**Routing policies:**
| Policy | Model selected | Trade-off |
|---|---|---|
| `quality` | GPT-4o (or best available) | Highest quality, highest cost |
| `balanced` | GPT-4o-mini / GPT-4o | Good quality at moderate cost |
| `cost` | GPT-4o-mini | Lowest cost, acceptable quality |
| `speed` | Fastest available | Lowest latency |

---

### `safe-token-metrics`

Tracks per-request token usage and cost, and enforces budget limits.

**Source:** [`safe_framework/tools/mcp/token_metrics_mcp.py`](../../safe_framework/tools/mcp/token_metrics_mcp.py)

**Functions:**

```python
token_metrics_get_usage(
    request_id: str = None,   # Filter to a specific route invocation
    time_range_hours: int = 24,
) -> UsageReport

token_metrics_get_cost(
    request_id: str = None,
    time_range_hours: int = 24,
) -> CostReport

token_metrics_get_budget(
    budget_id: str,
) -> BudgetStatus              # remaining, total, alert_threshold_pct
```

---

## Adding a New Private MCP Server

To add a new MCP tool to the project catalog:

### 1. Implement the server

```python
# safe_framework/tools/mcp/my_tool_mcp.py
import os
import httpx
from mcp.server import FastMCP

mcp = FastMCP("my-tool")

@mcp.tool()
async def my_tool_search(query: str, top_k: int = 5) -> list:
    """Search my custom data source."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            os.environ["MY_TOOL_ENDPOINT"] + "/search",
            json={"query": query, "top_k": top_k},
            headers={"Authorization": f"Bearer {os.environ['MY_TOOL_KEY']}"},
        )
        resp.raise_for_status()
        return resp.json()["results"]

if __name__ == "__main__":
    mcp.run()
```

### 2. Register in catalog.yaml

```yaml
# safe_framework/tools/catalog.yaml  (add to the tools list)
- id: my-tool
  display_name: My Custom Tool
  version: "1.0"
  category: custom
  description: Search my custom data source
  authentication:
    type: api_key
    env_vars:
      - MY_TOOL_ENDPOINT
      - MY_TOOL_KEY
  mcp:
    module: safe_framework.tools.mcp.my_tool_mcp
    port: 8010
  functions:
    - name: my_tool_search
      description: Search my custom data source
      parameters:
        - name: query
          type: string
          required: true
        - name: top_k
          type: integer
          default: 5
  tags:
    - custom
    - search
```

### 3. Reference in agent.yaml

```yaml
tools:
  - id: my-tool
    purpose: "Search my custom data source for relevant information"
```

---

## Public Microsoft MCP Catalog

Microsoft publishes official MCP servers for Azure services. The most relevant for SAFE Framework:

| MCP Server | Description | GitHub |
|---|---|---|
| **Azure AI Search MCP** | Direct index search without AI Foundry wrapper | azure-samples/azure-search-mcp |
| **Microsoft Graph MCP** | Full M365 Graph API access | microsoft/graph-mcp |
| **Azure Cosmos DB MCP** | NoSQL and vector search (GA, official) | Azure/azure-cosmos-db-mcp |
| **Azure Blob Storage MCP** | Read/write blob storage | azure-samples/blob-storage-mcp |
| **Azure Key Vault MCP** | Read secrets securely | azure-samples/keyvault-mcp |
| **Bing Search MCP** | Web search with Bing | microsoft/bing-search-mcp |
| **Microsoft Purview MCP** | Data governance and classification | microsoft/purview-mcp (preview) |

### Installing a Public Microsoft MCP

```bash
# Example: Azure Cosmos DB official MCP
pip install azure-cosmos-db-mcp

# Set credentials
export COSMOS_ENDPOINT="https://<account>.documents.azure.com:443/"
# Uses DefaultAzureCredential — no key needed with Managed Identity

# Add to your catalog.yaml
```

```yaml
# In catalog.yaml, reference the official MCP
- id: azure-cosmos-db-official
  display_name: Azure Cosmos DB (Official)
  category: azure
  mcp:
    package: azure-cosmos-db-mcp
    entrypoint: azure_cosmos_db_mcp.server
```

---

## Viewing the Catalog

```bash
# List all registered tools
safe tool list

# Filter by category
safe tool list --category safe-mcp
safe tool list --category azure-iq

# Get full details for a tool
safe tool info safe-durable-task
```
