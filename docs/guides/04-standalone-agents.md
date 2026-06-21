# Guide: Standalone Agents

Standalone agents are single-purpose, self-contained agents that can be used directly in routes or composed into patterns. Unlike pattern roles, standalone agents are not tied to a specific topology.

---

## Agent Index

| Agent | Category | Primary Tools | File Links |
|---|---|---|---|
| [document-writer](#document-writer) | content | `iq-work` | [agent.yaml](../../safe_framework/agents/standalone/document-writer/agent.yaml) · [agent.md](../../safe_framework/agents/standalone/document-writer/agent.md) |
| [empty-agent](#empty-agent) | template | none | [agent.yaml](../../safe_framework/agents/standalone/empty-agent/agent.yaml) · [agent.md](../../safe_framework/agents/standalone/empty-agent/agent.md) |
| [presenter-code](#presenter-code) | presentation | none | [agent.yaml](../../safe_framework/agents/standalone/presenter-code/agent.yaml) · [agent.md](../../safe_framework/agents/standalone/presenter-code/agent.md) |
| [presenter-html](#presenter-html) | presentation | none | [agent.yaml](../../safe_framework/agents/standalone/presenter-html/agent.yaml) · [agent.md](../../safe_framework/agents/standalone/presenter-html/agent.md) |
| [presenter-markdown](#presenter-markdown) | presentation | none | [agent.yaml](../../safe_framework/agents/standalone/presenter-markdown/agent.yaml) · [agent.md](../../safe_framework/agents/standalone/presenter-markdown/agent.md) |
| [presenter-word](#presenter-word) | presentation | none | [agent.yaml](../../safe_framework/agents/standalone/presenter-word/agent.yaml) · [agent.md](../../safe_framework/agents/standalone/presenter-word/agent.md) |
| [rag-query](#rag-query) | retrieval | `iq-foundry`, `azure-cosmos-db` | [agent.yaml](../../safe_framework/agents/standalone/rag-query/agent.yaml) · [agent.md](../../safe_framework/agents/standalone/rag-query/agent.md) |
| [researcher](#researcher) | research | `iq-foundry`, `iq-work`, `iq-web` | [agent.yaml](../../safe_framework/agents/standalone/researcher/agent.yaml) · [agent.md](../../safe_framework/agents/standalone/researcher/agent.md) |
| [reviewer](#reviewer) | quality | `iq-foundry` | [agent.yaml](../../safe_framework/agents/standalone/reviewer/agent.yaml) · [agent.md](../../safe_framework/agents/standalone/reviewer/agent.md) |
| [semantic-search](#semantic-search) | retrieval | `iq-foundry` | [agent.yaml](../../safe_framework/agents/standalone/semantic-search/agent.yaml) · [agent.md](../../safe_framework/agents/standalone/semantic-search/agent.md) |
| [summarizer](#summarizer) | content | `iq-work` | [agent.yaml](../../safe_framework/agents/standalone/summarizer/agent.yaml) · [agent.md](../../safe_framework/agents/standalone/summarizer/agent.md) |
| [web-query](#web-query) | retrieval | `iq-web` | [agent.yaml](../../safe_framework/agents/standalone/web-query/agent.yaml) · [agent.md](../../safe_framework/agents/standalone/web-query/agent.md) |

---

## Agent Details

### document-writer

Generates structured documents (reports, SOWs, proposals, summaries) from structured input data.

**Input:** `title`, `sections` (array of section specs), `context` (optional background)
**Output:** `document` (Markdown), `word_count`, `metadata`

**Tools:**
| Tool | MCP | Purpose |
|---|---|---|
| `iq-work` | Remote Azure IQ | Fetch org charts, templates, and style guides from M365 |

**Integration notes:** `iq-work` does not have a custom MCP implementation in this repository. It is a remote tool hosted in Azure AI Foundry. See [Integrating IQ Tools Without Local MCP](#integrating-iq-tools-without-local-mcp).

---

### empty-agent

A blank template agent for scaffolding new custom agents. All fields are `TODO` placeholders.

**Use when:** Starting a new custom agent from scratch.

**Tools:** None

---

### presenter-code

Formats analytical results or data as syntax-highlighted code blocks (Python, JSON, SQL, YAML).

**Input:** `content` (data or logic to format), `language`, `context` (optional)
**Output:** `formatted_code` (fenced code block), `language`

**Tools:** None (pure LLM transformation)

---

### presenter-html

Converts structured Markdown content into clean, styled HTML suitable for email or web embedding.

**Input:** `markdown_content`, `style_theme` (optional: `corporate`, `minimal`, `branded`)
**Output:** `html_content`, `inline_styles` (boolean)

**Tools:** None

---

### presenter-markdown

Formats raw or structured content as well-structured Markdown with proper headings, tables, and lists.

**Input:** `raw_content`, `output_format` (report, summary, list, table)
**Output:** `markdown_content`, `section_count`

**Tools:** None

---

### presenter-word

Generates Word-compatible Markdown that can be imported into Microsoft Word or exported via Pandoc.

**Input:** `content`, `document_type` (proposal, report, letter), `metadata` (author, date, title)
**Output:** `word_markdown`, `pandoc_command` (ready-to-run conversion command)

**Tools:** None

---

### rag-query

A ready-to-use RAG query agent that retrieves, reranks, and synthesises answers from indexed sources.

**Input:** `query` (natural language), `top_k` (optional, default 5), `filters` (optional metadata filters)
**Output:** `answer`, `citations` (array), `sources` (array), `confidence`

**Tools:**
| Tool | MCP | Purpose |
|---|---|---|
| `iq-foundry` | Remote Azure IQ | Primary knowledge base search via AI Search |
| `azure-cosmos-db` | Remote Azure / [local MCP catalog](05-mcp-catalog.md) | Vector similarity search for semantic matching |

---

### researcher

Multi-hop research agent that combines internal and external sources to produce comprehensive research briefs.

**Input:** `topic`, `depth` (shallow/deep), `sources` (internal/external/both), `max_hops` (optional)
**Output:** `research_brief`, `key_findings` (array), `sources_used` (array), `confidence`

**Tools:**
| Tool | MCP | Purpose |
|---|---|---|
| `iq-foundry` | Remote Azure IQ | Internal knowledge base and SharePoint |
| `iq-work` | Remote Azure IQ | M365 meetings, emails, documents |
| `iq-web` | Remote Azure IQ | Public web and news via Bing grounding |

**Customising for a specific domain:** Fork the researcher's `agent.yaml` and update the tool configurations to point to a domain-specific AI Search index. See [Guide: Business Workflow](02-business-workflow.md) for an example.

---

### reviewer

Reviews content against defined criteria and produces a structured quality assessment.

**Input:** `content`, `criteria` (array of review criteria), `context` (optional)
**Output:** `assessment` (pass/fail), `score` (0–1), `feedback` (array of issues), `recommendations`

**Tools:**
| Tool | MCP | Purpose |
|---|---|---|
| `iq-foundry` | Remote Azure IQ | Look up standards, guidelines, and reference material |

---

### semantic-search

Single-step semantic search over an AI Search index, returning ranked results with metadata.

**Input:** `query`, `index` (optional, defaults to primary), `top_k` (optional), `filters` (optional)
**Output:** `results` (array of `{score, content, metadata}`), `total_hits`

**Tools:**
| Tool | MCP | Purpose |
|---|---|---|
| `iq-foundry` | Remote Azure IQ | Azure AI Search semantic search |

---

### summarizer

Condenses long content (meeting transcripts, documents, threads) into structured summaries.

**Input:** `content`, `format` (bullets/paragraph/structured), `max_length` (optional), `focus` (optional topic)
**Output:** `summary`, `key_points` (array), `action_items` (array, if applicable), `word_count`

**Tools:**
| Tool | MCP | Purpose |
|---|---|---|
| `iq-work` | Remote Azure IQ | Retrieve meeting transcripts, Teams threads, email chains |

---

### web-query

Retrieves and summarises information from the public web using Bing grounding.

**Input:** `query`, `max_results` (optional), `freshness` (optional: day/week/month)
**Output:** `results` (array of `{title, url, snippet, date}`), `summary`

**Tools:**
| Tool | MCP | Purpose |
|---|---|---|
| `iq-web` | Remote Azure IQ | Live Bing Search with web grounding |

---

## Integrating IQ Tools Without Local MCP

The four Azure IQ tools (`iq-foundry`, `iq-work`, `iq-fabric`, `iq-web`) are **remote tools** — they run as hosted services in your Azure AI Foundry workspace. There is no local Python MCP implementation in this repository because these are provisioned and managed by Microsoft.

### How Agents Use IQ Tools in Practice

**Option 1 — Semantic Kernel Plugins (Recommended)**

Use the Azure AI Foundry SDK to register IQ tools as Semantic Kernel plugins:

```python
from azure.ai.foundry import AIFoundryClient
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel import Kernel

client = AIFoundryClient(
    endpoint=os.environ["FOUNDRY_ENDPOINT"],
    credential=DefaultAzureCredential(),
)

kernel = Kernel()
kernel.add_service(AzureChatCompletion(...))

# Register iq-foundry as a kernel plugin
foundry_iq = client.get_tool("iq-foundry")
kernel.add_plugin(foundry_iq, plugin_name="iq_foundry")
```

**Option 2 — Direct REST API Calls**

For agents that call IQ tools directly (not via Semantic Kernel):

```python
import httpx
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

credential = DefaultAzureCredential()
token_provider = get_bearer_token_provider(
    credential, "https://cognitiveservices.azure.com/.default"
)

async def call_iq_foundry(query: str, top_k: int = 5) -> list:
    token = token_provider()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{os.environ['FOUNDRY_ENDPOINT']}/tools/iq-foundry/search",
            headers={"Authorization": f"Bearer {token}"},
            json={"query": query, "top_k": top_k},
        )
        response.raise_for_status()
        return response.json()["results"]
```

**Option 3 — Azure AI Search SDK Directly (for `iq-foundry`)**

If you have direct access to the underlying AI Search index:

```python
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.identity import DefaultAzureCredential

search_client = SearchClient(
    endpoint=os.environ["AZURE_SEARCH_ENDPOINT"],
    index_name="policy-documents",
    credential=DefaultAzureCredential(),
)

results = search_client.search(
    search_text=query,
    vector_queries=[VectorizedQuery(
        vector=embedding_vector,
        k_nearest_neighbors=5,
        fields="content_vector",
    )],
    query_type="semantic",
    semantic_configuration_name="my-semantic-config",
    top=5,
)
```

---

## Using an Agent in a Custom Route

```python
from safe_framework.safe_core.models import RouteDefinition, RoutePattern, Agent
from safe_framework.safe_core.agent_catalog import AgentCatalog

catalog = AgentCatalog()

# Load a standalone agent from the catalog
researcher = catalog.get_agent("researcher")

# Use it as a step in a sequential-pipeline
my_route = RouteDefinition(
    name="market-analysis",
    pattern=RoutePattern.SEQUENTIAL_PIPELINE,
    agents={
        "step1": researcher,
        "step2": catalog.get_agent("summarizer"),
        "step3": catalog.get_agent("presenter-markdown"),
    },
)
```
