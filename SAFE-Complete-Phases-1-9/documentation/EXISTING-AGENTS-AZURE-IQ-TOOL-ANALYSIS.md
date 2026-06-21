# Existing Agents — Azure IQ & Azure Tool Analysis

Review of all 12 implemented routing patterns and 12 standalone agents.
For each placeholder / agent: recommended Azure IQ or Azure service connections
and the business rationale for adding them to the catalog.

---

## IQ & Azure Service Quick Reference

| Tool | What it does |
|---|---|
| **Foundry IQ** | Indexed org knowledge — SharePoint, Blob, OneLake via Azure AI Search |
| **Work IQ** | M365 signals — documents, meetings, chats, emails, workflows |
| **Fabric IQ** | Structured business data — OneLake, Power BI semantic models, data agents |
| **Web IQ** | Live public web + news via Bing grounding (accessed via Foundry IQ MCP) |
| **Azure Cosmos DB MCP** | Persistent vector + document store; hybrid search (GA) |
| **Azure Durable Functions** | Checkpoint / suspend / resume for long-running workflows |
| **Azure AI Foundry Model Router** | Route LLM calls by Quality / Cost / Balanced policy per turn |
| **Azure AI Foundry Token Metrics API** | Granular per-request cost and token usage |
| **Azure APIM** | Gateway-level token metering, rate limiting, routing policies |
| **Azure Functions + MCP** | Expose logic as callable MCP tools; 1,400+ Logic Apps connectors |

---

## Part 1 — Pattern Agents (12 patterns)

---

### 1. supervisor-manager

| Placeholder | Recommended Tool | Rationale |
|---|---|---|
| `supervisor` | **Foundry IQ** | Retrieve routing rules and specialist capability descriptions to decide which specialist handles this request |
| `supervisor` | **Work IQ** | Understand org context — who owns what domain, past routing decisions, escalation history |
| `specialist_*` | **Foundry IQ** | Ground each specialist in its domain knowledge base (e.g. contract-specialist → legal knowledge index) |
| `specialist_*` | **Fabric IQ** | When the specialist needs to reason over business data (analytics, pricing, inventory) |
| `aggregator` | **Foundry IQ** | Validate combined specialist outputs against known outcome patterns and policies |

---

### 2. fan-out-fan-in

| Placeholder | Recommended Tool | Rationale |
|---|---|---|
| `processor_*` | **Foundry IQ** | Each parallel processor independently grounded in the shared knowledge base |
| `processor_*` | **Fabric IQ** | If processors are analysing structured business data (e.g. parallel ledger analysis) |
| `aggregator` | **Foundry IQ** | Validate merged result against known combined-output patterns |
| `aggregator` | **Azure Cosmos DB MCP** | Persist aggregation results for downstream audit or replay |

---

### 3. map-reduce

| Placeholder | Recommended Tool | Rationale |
|---|---|---|
| `splitter` | **Fabric IQ** | Split directly from OneLake / Power BI data model instead of pre-loading data |
| `splitter` | **Azure Cosmos DB MCP** | Split from an operational database — query for chunk boundaries, stream records |
| `mapper` | **Foundry IQ** | Enrich each chunk with contextual knowledge (e.g. entity lookup, classification rules) |
| `mapper` | **Web IQ** | When mapping requires live external lookup per record (e.g. company enrichment) |
| `reducer` | **Foundry IQ** | Validate reduced output against business rules before returning |

---

### 4. sequential-pipeline

Each `stage_*` serves a different role in the pipeline; tool fit varies by stage position.

| Stage position | Recommended Tool | Rationale |
|---|---|---|
| Stage 0 — ingestion | **Foundry IQ** / **Work IQ** / **Fabric IQ** | Retrieve the source data to kick off the pipeline |
| Middle stages — enrichment | **Foundry IQ** | Enrich, classify, or annotate as data flows through |
| Middle stages — lookup | **Azure Cosmos DB MCP** | Fast per-record lookups against operational data |
| Final stage — delivery | **Azure Functions + MCP** | Push output to a downstream system (CRM, ticketing, storage) via Logic Apps connector |

---

### 5. round-robin

| Placeholder | Recommended Tool | Rationale |
|---|---|---|
| `dispatcher` | **Azure AI Foundry Token Metrics API** | Track worker load and cost per turn to weight dispatch toward under-used workers |
| `dispatcher` | **Azure Cosmos DB MCP** | Persist the round-robin counter across sessions and process restarts |
| `worker_*` | **Foundry IQ** | Each worker independently grounded in the same shared knowledge base |

---

### 6. mixture-of-experts

| Placeholder | Recommended Tool | Rationale |
|---|---|---|
| `router` | **Foundry IQ** | Retrieve expert capability descriptions and past routing decisions to assign weights |
| `router` | **Work IQ** | Understand the query domain from org signals (e.g. which team owns this topic) |
| `expert_*` | **Foundry IQ** | Domain-specific knowledge index per expert (e.g. legal-expert → legal index) |
| `expert_*` | **Fabric IQ** | When the expert needs to reason over analytical business data |
| `expert_*` | **Web IQ** | When an expert needs current external information (e.g. market-expert) |
| `aggregator` | **Foundry IQ** | Ground the final synthesis in authoritative source material |

---

### 7. hierarchical-teams

| Placeholder | Recommended Tool | Rationale |
|---|---|---|
| `coordinator` | **Work IQ** | Understand team structure, ownership, and past project assignments from M365 |
| `coordinator` | **Foundry IQ** | Retrieve org knowledge to decompose the task and assign to the right teams |
| `team_*` | **Foundry IQ** | Team-specific knowledge domain (each team supervisor has its own index) |
| `team_*` | **Fabric IQ** | Team needs to query business / analytics data as part of its work |
| `aggregator` | **Foundry IQ** | Cross-team synthesis grounded in authoritative org knowledge |

---

### 8. fallback-chain

| Placeholder | Recommended Tool | Rationale |
|---|---|---|
| `primary` | **Foundry IQ** | Primary attempt grounded in internal org knowledge |
| `fallback_0` | **Web IQ** | First fallback — try public web when internal knowledge is insufficient |
| `fallback_1` | **Azure Cosmos DB MCP** | Second fallback — return a cached or historical result from operational DB |

> **Pattern note:** the fallback chain is a natural fit for graceful degradation across IQ sources: try Foundry IQ → Web IQ → cached DB result → static default.

---

### 9. retry-loop

| Placeholder | Recommended Tool | Rationale |
|---|---|---|
| `worker` | **Foundry IQ** | Ground each attempt in the same knowledge base |
| `worker` | **Azure Durable Functions** | Checkpoint state between retries so a process restart doesn't lose progress |
| `validator` | **Foundry IQ** | Validate output against known-good patterns from the knowledge base |
| `validator` | **Work IQ** | Compare output against org quality standards and past accepted outputs |

---

### 10. diamond

| Placeholder | Recommended Tool | Rationale |
|---|---|---|
| `splitter` | **Fabric IQ** | Split structured data from OneLake into left/right paths |
| `splitter` | **Azure Cosmos DB MCP** | Split from an operational database |
| `left_processor` | **Foundry IQ** | Internal knowledge analysis path |
| `left_processor` | **Fabric IQ** | Quantitative / analytical path |
| `right_processor` | **Web IQ** | External context / market data path |
| `right_processor` | **Work IQ** | Internal collaboration / people context path |
| `merger` | **Foundry IQ** | Merge left + right results validated against business rules |

---

### 11. conditional-branching

| Placeholder | Recommended Tool | Rationale |
|---|---|---|
| `evaluator` | **Foundry IQ** | Retrieve classification rules and decision trees to evaluate conditions |
| `evaluator` | **Work IQ** | Use org signals (requestor, team, history) as part of the condition |
| `evaluator` | **Fabric IQ** | Query business rules or thresholds directly from the semantic data model |
| `branch_*` | **Foundry IQ** | Branch-specific knowledge index per path |
| `branch_*` | **Web IQ** | For branches that need live external information |

---

### 12. tree-reduce

| Placeholder | Recommended Tool | Rationale |
|---|---|---|
| `leaf_*` | **Foundry IQ** | Each leaf grounded in org knowledge for its individual item |
| `leaf_*` | **Fabric IQ** | When leaves are processing individual data records from OneLake |
| `reducer` | **Foundry IQ** | Validate each reduction step against known business rules |
| `reducer` | **Azure Cosmos DB MCP** | Persist intermediate reduction results for large trees that span multiple invocations |

---

## Part 2 — Standalone Agents (12 agents)

> **Note:** several standalone agents are currently stubs with placeholder content (`field1`, `Use case 1` etc.). The tool recommendations below are what each agent *should* connect to once fully implemented.

---

### document-writer
*Generates formatted Word documents from structured data.*

| Tool | Rationale |
|---|---|
| **Work IQ** | Pull org Word templates and branding from SharePoint before generating |
| **Foundry IQ** | Retrieve source content / data to populate document sections |

---

### presenter-code
*Formats code with explanations.* (currently a stub)

| Tool | Rationale |
|---|---|
| **Foundry IQ** | Retrieve internal coding standards, style guides, and patterns |
| **Work IQ** | Pull approved code examples from internal SharePoint/repos |

---

### presenter-html
*Generates HTML presentations and dashboards.* (currently a stub)

| Tool | Rationale |
|---|---|
| **Work IQ** | Retrieve org branding, CSS templates, and approved layouts from SharePoint |
| **Foundry IQ** | Source data and content for dashboard components |
| **Fabric IQ** | Embed live Power BI visuals or OneLake data into the HTML output |

---

### presenter-markdown
*Formats output as readable Markdown.* (currently a stub)

| Tool | Rationale |
|---|---|
| **Foundry IQ** | Retrieve org Markdown templates and style conventions |

---

### presenter-word
*Formats analysis results into Word documents.* (currently a stub)

| Tool | Rationale |
|---|---|
| **Work IQ** | Pull org-approved Word templates from SharePoint |
| **Foundry IQ** | Retrieve structured source content to populate the document |

---

### rag-query
*Vector-based retrieval-augmented generation for Q&A.* (currently a stub — this agent IS the retrieval layer)

| Tool | Rationale |
|---|---|
| **Foundry IQ** | **Primary** — this agent's core function; indexes org docs via Azure AI Search |
| **Work IQ** | Extend retrieval to M365 content (meetings, emails, Teams chats) |
| **Fabric IQ** | Extend retrieval to structured business data in OneLake / Power BI |
| **Web IQ** | Fallback or augmentation when internal knowledge is insufficient |
| **Azure Cosmos DB MCP** | Vector search over operational / transactional data |

---

### researcher
*Multi-step research and synthesis.* (currently a stub)

| Tool | Rationale |
|---|---|
| **Web IQ** | **Primary** — live web and news search for external research |
| **Foundry IQ** | Internal knowledge base for org-specific context |
| **Work IQ** | Search past internal projects, meeting notes, and decisions |
| **Fabric IQ** | Pull business data to support or validate research findings |

---

### reviewer
*Reviews documents for quality, accuracy, compliance.* (currently a stub)

| Tool | Rationale |
|---|---|
| **Foundry IQ** | Retrieve review rubrics, compliance standards, and past review outcomes |
| **Work IQ** | Compare against org review history and approved versions in SharePoint |

---

### semantic-search
*Semantic similarity search across documents.* (currently a stub)

| Tool | Rationale |
|---|---|
| **Foundry IQ** | **Primary** — powered by Azure AI Search semantic ranking |
| **Azure Cosmos DB MCP** | Vector search over operational / product data |
| **Fabric IQ** | Semantic search over business data entities in OneLake |

---

### summarizer
*Generates concise summaries from long documents.* (currently a stub)

| Tool | Rationale |
|---|---|
| **Foundry IQ** | Retrieve source documents to summarise from the knowledge index |
| **Work IQ** | Summarise M365 content — meeting transcripts, email threads, documents |
| **Fabric IQ** | Summarise data reports and Power BI datasets |

---

### web-query
*Performs web searches and aggregates results.* (currently a stub)

| Tool | Rationale |
|---|---|
| **Web IQ** | **Primary** — Bing grounding via Foundry IQ MCP for web, news, images, video |

---

## Summary — Highest Priority Tool Additions

Agents where the tool connection is the core function (stubs that should be wired first):

| Agent / Placeholder | Tool | Priority |
|---|---|---|
| `rag-query` standalone | Foundry IQ | High — agent does nothing without it |
| `semantic-search` standalone | Foundry IQ | High — agent does nothing without it |
| `web-query` standalone | Web IQ | High — agent does nothing without it |
| `researcher` standalone | Web IQ + Foundry IQ | High |
| `supervisor` (all patterns) | Foundry IQ | High — routing quality depends on it |
| `evaluator` (conditional-branching) | Foundry IQ + Fabric IQ | High — classification rules must come from somewhere |
| `router` (mixture-of-experts) | Foundry IQ | High — expert weighting needs capability knowledge |
| `fallback-chain` (fallback_0) | Web IQ | Medium — natural first fallback |
| `retry-loop` validator | Foundry IQ | Medium — validation against known patterns |
| `dispatcher` (round-robin) | Token Metrics API + Cosmos DB MCP | Medium — load-aware dispatch and state persistence |
| All `stage_*` ingestion stages | Foundry IQ / Work IQ / Fabric IQ | Medium — pipeline needs a data source |
| `reviewer` standalone | Foundry IQ + Work IQ | Medium |
| `document-writer` standalone | Work IQ | Medium — org templates |

---

## References

- [Foundry IQ — Microsoft Learn](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/what-is-foundry-iq)
- [Fabric IQ — Microsoft Learn](https://learn.microsoft.com/en-us/fabric/iq/overview)
- [Work IQ / Foundry IQ / Fabric IQ overview — Cloud Wars](https://cloudwars.com/ai/microsoft-debuts-work-iq-fabric-iq-and-foundry-iq-a-unified-intelligence-layer-for-the-ai-powered-enterprise/)
- [Azure Cosmos DB MCP Toolkit GA](https://devblogs.microsoft.com/cosmosdb/azure-cosmos-db-mcp-toolkit-is-now-generally-available-bringing-your-database-to-ai-agents-at-scale/)
- [Durable Task for AI Agents — Azure](https://learn.microsoft.com/en-us/azure/durable-task/sdks/durable-task-for-ai-agents)
- [Model Router — Microsoft Foundry](https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/architecting-cost-aware-llm-workloads-with-model-router-in-microsoft-foundry/4514440)
- [Token Metrics for Foundry Agents](https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/tracking-every-token-granular-cost-and-usage-metrics-for-microsoft-foundry-agent/4503143)
