# Command Reference

Full reference for every `safe` CLI command, grouped by topic.

---

## Catalog Commands

The catalog commands search and display the agent registry defined in `safe_framework/safe_core/catalog.yaml`.

---

### `safe catalog`

List all registered agents, or search by keyword.

**Syntax**

```
safe catalog [QUERY]
```

**Arguments**

| Argument | Required | Description |
|---|---|---|
| `QUERY` | No | Free-text search against agent name, category, and description |

**Examples**

```bash
# List all agents
safe catalog

# Search for agents related to "research"
safe catalog research

# Search by category
safe catalog summarizer

# Find all document-related agents
safe catalog document
```

**Output**

```
Agent Catalog  (12 agents)

 name                category    version  description
 document-writer     content     1.0      Generate structured documents from structured data
 researcher          research    1.0      Multi-hop research combining internal and external sources
 summarizer          content     1.0      Condense long content into structured summaries
 ...
```

---

## Route Commands

The route commands drive the interactive route writer, which collects pattern and agent selections and generates a production-ready Python route file.

---

### `safe route`

Launch the interactive route writer. This is a guided wizard that:

1. Asks for a route name and description
2. Presents the pattern library and asks you to choose a pattern
3. Asks you to select agents for each role in the pattern (searching the catalog)
4. Validates the route definition (contract matching, dependency checks)
5. Generates a `route.py`, `requirements.txt`, `config.yaml`, and `test_data.json`

**Syntax**

```
safe route
```

**No flags** — all configuration is collected interactively.

**Example Session**

```
$ safe route

Route name: contract-review
Description: Review contracts for compliance and risk
Pattern [sequential-pipeline]: evaluator-optimizer

Select generator agent [search]: rag-query
Select evaluator agent [search]: reviewer
Select optimizer agent [search]: document-writer

Validating route... ✓
Generating code...

Route written to: routes/contract-review/
  route.py          (executable route code)
  requirements.txt  (pip dependencies)
  config.yaml       (route configuration)
  test_data.json    (sample test payloads)
```

**Generated Output**

The generated `route.py` contains a class with an `async invoke(request)` method. It imports and orchestrates the selected agents using Semantic Kernel. The class name is derived from the route name (e.g., `ContractReviewRoute`).

---

## Tool Commands

The tool commands manage the MCP tool catalog at `safe_framework/tools/catalog.yaml`. Use these commands to discover, inspect, rename, and fork tool definitions.

---

### `safe tool list`

List all tools registered in the catalog.

**Syntax**

```
safe tool list [--category CATEGORY] [--project]
```

**Flags**

| Flag | Description |
|---|---|
| `--category CATEGORY` | Filter by category (`azure-iq`, `azure`, `safe-mcp`) |
| `--project` | Show only project-level tool overrides (forked tools) |

**Examples**

```bash
# List all tools
safe tool list

# List only Azure IQ tools
safe tool list --category azure-iq

# List only custom SAFE MCP tools
safe tool list --category safe-mcp

# List project-specific tool overrides
safe tool list --project
```

**Output**

```
Tool Catalog  (8 tools)

 id                  display name          category    version  tags
 iq-foundry          Foundry IQ            azure-iq    1.0      search, retrieval, azure-ai-search
 iq-work             Work IQ               azure-iq    1.0      m365, meetings, email, documents
 iq-fabric           Fabric IQ             azure-iq    1.0      analytics, power-bi, onelake
 iq-web              Web IQ                azure-iq    1.0      web-search, bing, grounding
 azure-cosmos-db     Azure Cosmos DB       azure       1.0      vector-search, nosql, memory
 safe-durable-task   SAFE Durable Task     safe-mcp    1.0      durable, checkpoint, resume
 safe-model-router   SAFE Model Router     safe-mcp    1.0      routing, cost, quality
 safe-token-metrics  SAFE Token Metrics    safe-mcp    1.0      cost, budget, tokens
```

---

### `safe tool info`

Show the full catalog entry for a single tool, including all function signatures and authentication details.

**Syntax**

```
safe tool info <TOOL_ID>
```

**Arguments**

| Argument | Required | Description |
|---|---|---|
| `TOOL_ID` | Yes | Tool identifier from the catalog (e.g., `iq-foundry`) |

**Example**

```bash
safe tool info iq-foundry
```

**Output**

```
Tool: iq-foundry  (Foundry IQ)
Category: azure-iq  |  Version: 1.0
Service: Azure AI Search over SharePoint, Blob Storage, OneLake
Auth: Managed Identity

Functions:
  search(query: str, top_k: int = 5, filters: dict = None) -> list[SearchResult]
    Search the indexed organisation knowledge base.

  retrieve(doc_id: str) -> Document
    Retrieve a specific document by ID.

Tags: search, retrieval, azure-ai-search, rag, knowledge-base
```

---

### `safe tool rename`

Rename a tool in the local project-level catalog. This is used after forking a tool to give it a project-specific identifier.

**Syntax**

```
safe tool rename <OLD_ID> <NEW_ID>
```

**Arguments**

| Argument | Required | Description |
|---|---|---|
| `OLD_ID` | Yes | Current tool ID |
| `NEW_ID` | Yes | New tool ID |

**Example**

```bash
# Rename a forked tool for the contract-review project
safe tool rename iq-foundry iq-foundry-contracts
```

**What it does**

- Updates the tool entry in the project-level catalog override (`tools/project-catalog.yaml`)
- Does **not** affect the shared framework catalog (`tools/catalog.yaml`)
- Updates any agent.yaml files in the current project that reference the old tool ID

---

### `safe tool fork`

Fork a catalog tool to create a project-level copy that can be customised (different endpoint, additional config, renamed functions).

**Syntax**

```
safe tool fork <TOOL_ID> <PROJECT>
```

**Arguments**

| Argument | Required | Description |
|---|---|---|
| `TOOL_ID` | Yes | Source tool ID from the catalog |
| `PROJECT` | Yes | Project name (used to namespace the fork) |

**Example**

```bash
# Fork iq-foundry for the onboarding-workflow project
safe tool fork iq-foundry onboarding-workflow
```

**What it does**

1. Copies the tool definition from `tools/catalog.yaml`
2. Writes a project override file: `tools/overrides/<project>/<tool-id>.yaml`
3. Registers the fork in `tools/project-catalog.yaml`

**After forking**, edit the override YAML to change the endpoint, authentication, or function signatures:

```yaml
# tools/overrides/onboarding-workflow/iq-foundry.yaml
id: iq-foundry-onboarding
display_name: "Foundry IQ — Onboarding"
endpoint: "https://onboarding-search.search.windows.net"
index_name: "onboarding-docs"
```

---

## Exit Codes

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | Validation error (bad pattern, contract mismatch) |
| `2` | Configuration error (missing env vars, bad YAML) |
| `3` | Network error (cannot reach Azure endpoint) |
