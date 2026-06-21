# Routing Patterns Backlog — Azure IQ Tool Mapping

Candidate patterns to add to the SAFE Framework, with placeholder agents and
recommended Azure IQ / Foundry tool connections for each role.

The IQ suite (announced Build 2026) is a unified intelligence layer that connects
enterprise data sources to Foundry agents through a single retrieval API:

| IQ Tool | What it connects |
|---|---|
| **Foundry IQ** | Indexed org knowledge — SharePoint, Blob Storage, OneLake (powered by Azure AI Search) |
| **Work IQ** | M365 signals — meetings, chats, emails, documents, workflows |
| **Fabric IQ** | Structured business data — OneLake, Power BI semantic models, data agents |
| **Web IQ** | Live public web, news, images, video via Bing grounding (accessed through Foundry IQ MCP) |

Other Azure services referenced below:

| Service | Role |
|---|---|
| **Azure Cosmos DB MCP** | Persistent vector + document storage for agent memory (GA) |
| **Azure Durable Functions / Durable Task** | Checkpoint every state transition, suspend/resume long-running workflows |
| **Azure AI Foundry Model Router** | Route LLM calls by Quality / Cost / Balanced policy per turn |
| **Azure AI Foundry Token Metrics API** | Granular per-request token cost and usage history |
| **Azure APIM** | Gateway-level token metering, rate limiting, routing policies |
| **Azure Functions + MCP** | Expose workflows as callable MCP tools; 1,400+ Logic Apps connectors |

---

## Patterns Already Implemented (12)

`supervisor-manager` · `fan-out-fan-in` · `map-reduce` · `sequential-pipeline` ·
`round-robin` · `mixture-of-experts` · `hierarchical-teams` · `fallback-chain` ·
`retry-loop` · `diamond` · `conditional-branching` · `tree-reduce`

---

## Candidate Patterns to Add (15)

Ordered by business usefulness.

---

### 1. Evaluator-Optimizer

Generator produces output → evaluator scores it → optimizer refines it in a loop until a quality threshold is met. Essential for any output that must meet a defined standard (reports, contracts, generated code).

| Placeholder | Azure / IQ Tool |
|---|---|
| `generator` | Foundry IQ — ground first draft in org knowledge |
| `evaluator` | Foundry IQ — retrieve quality rubrics/standards; Work IQ — org policy context |
| `optimizer` | — (pure LLM refinement, no external tool required) |

---

### 2. Human-in-the-Loop

Workflow pauses and waits for a human approval or rejection before proceeding. Required for compliance, high-stakes decisions, and regulated industries.

| Placeholder | Azure / IQ Tool |
|---|---|
| `pre_validator` | Foundry IQ — look up approval policy for this request type |
| `human_gate` | **Azure Durable Functions** — suspend/checkpoint workflow, resume on webhook callback |
| `post_processor` | Work IQ — log decision back to M365 compliance record |

---

### 3. Reflection

A single agent critiques its own output and self-corrects before returning the final answer. Cheapest way to improve output quality without adding extra agents.

| Placeholder | Azure / IQ Tool |
|---|---|
| `generator` | Foundry IQ — RAG-grounded initial draft |
| `critic` | Work IQ — compare against internal standards and past decisions |
| `refiner` | — (pure LLM refinement) |

---

### 4. Orchestrator-Workers

Orchestrator dynamically decomposes an incoming task into subtasks, spins up workers on the fly, and synthesizes their results. Anthropic's own internal research architecture — 90% better than single-agent on complex tasks.

| Placeholder | Azure / IQ Tool |
|---|---|
| `orchestrator` | Work IQ — understands org context to plan decomposition |
| `worker` | Foundry IQ / Fabric IQ / Web IQ — depends on subtask domain |
| `synthesizer` | Foundry IQ — ground final synthesis in source material |

---

### 5. RAG (Retrieval-Augmented)

Agent queries a knowledge store first, then generates an answer grounded in retrieved documents. Foundational for any business using internal knowledge bases.

| Placeholder | Azure / IQ Tool |
|---|---|
| `retriever` | **Foundry IQ** (primary — Azure AI Search backend); Work IQ (M365 docs/meetings); Fabric IQ (OneLake/Power BI); Web IQ (public web/news); Azure Cosmos DB MCP (operational/vector data) |
| `reranker` | Azure AI Search semantic reranking |
| `generator` | — (grounded generation) |

---

### 6. Planning / Task Decomposition

Agent produces an explicit step-by-step plan with dependencies before any execution begins. Reduces errors on complex multi-step business processes.

| Placeholder | Azure / IQ Tool |
|---|---|
| `planner` | Foundry IQ — retrieve past plans and templates; Work IQ — understand org workflows |
| `executor` | Azure Functions + MCP — serverless task execution with 1,400+ Logic Apps connectors |
| `reviewer` | Foundry IQ — validate plan against known constraints |

---

### 7. Gate / Guard

A mandatory validation checkpoint between two stages that blocks progress if criteria are not met. Used for compliance checks, PII scanning, and data quality gates.

| Placeholder | Azure / IQ Tool |
|---|---|
| `guard` | Foundry IQ — policy/rule lookup; Work IQ — compliance context |
| `processor` | Any downstream IQ source as needed |

---

### 8. Self-Consistency

Run the same prompt N times in parallel and vote/aggregate the majority answer. Increases accuracy for factual or numerical tasks at the cost of more tokens.

| Placeholder | Azure / IQ Tool |
|---|---|
| `worker` (×N parallel) | Foundry IQ — each run independently grounded in the same knowledge base |
| `voter` | — (statistical aggregation, no external tool) |

---

### 9. Debate

Two or more agents argue opposing positions; a judge agent synthesizes the best answer. Surfaces edge cases and reduces single-agent bias in risk or investment analysis.

| Placeholder | Azure / IQ Tool |
|---|---|
| `proposer` | Foundry IQ + Web IQ — gather evidence for position A |
| `challenger` | Foundry IQ + Web IQ — gather evidence for position B |
| `judge` | Work IQ — org policy context for final verdict |

---

### 10. Agent-as-a-Tool

Specialized sub-agents are exposed as callable tools to a parent orchestrator, making it easy to compose complex systems from simple reusable agents.

| Placeholder | Azure / IQ Tool |
|---|---|
| `orchestrator` | Azure Functions MCP — sub-agents exposed as callable MCP tools |
| `sub_agent_*` | Foundry IQ / Fabric IQ / Web IQ — each tool-agent has its own grounding source |

---

### 11. Memory-Augmented

Agents read from and write to a shared memory store to preserve context across multiple turns or sessions. Needed for long-running business workflows that span days or weeks.

| Placeholder | Azure / IQ Tool |
|---|---|
| `memory_writer` | **Azure Cosmos DB MCP** — persist episodic/semantic memories with vector embeddings |
| `memory_reader` | **Azure Cosmos DB MCP** — hybrid + vector search over stored memories |
| `processor` | Foundry IQ — combine retrieved memory with org knowledge |

---

### 12. Event-Driven

Agents triggered by events (webhook, queue message, file upload) rather than direct calls. Enables reactive, asynchronous enterprise integrations.

| Placeholder | Azure / IQ Tool |
|---|---|
| `listener` | Azure Service Bus / Event Hub — via Azure Functions + Logic Apps connectors |
| `router` | Foundry IQ — classify event type to determine the correct handler |
| `handler_*` | Fabric IQ (data events) / Work IQ (M365 events) / Foundry IQ (knowledge events) |

---

### 13. Checkpoint / Resume

Workflow saves state at each stage so it can pause, be inspected, and resume without re-running completed work. Critical for long or expensive pipelines.

| Placeholder | Azure / IQ Tool |
|---|---|
| `coordinator` | **Azure Durable Functions** — manages step graph, checkpoints every state transition |
| `worker` | Foundry IQ / Fabric IQ — normal agent work between checkpoints |
| `checkpoint_store` | **Azure Durable Task** — durable storage backend (Storage / Cosmos DB / MSSQL) |

---

### 14. Budget-Aware Routing

Routes requests to a cheaper/faster model for simple queries and reserves expensive models for complex ones, based on a cost budget. Azure AI Foundry has a native Model Router purpose-built for this.

| Placeholder | Azure / IQ Tool |
|---|---|
| `cost_estimator` | **Azure AI Foundry Token Metrics API** — granular per-request cost history |
| `model_router` | **Azure AI Foundry Model Router** — Quality / Cost / Balanced routing policy; Azure APIM for gateway-level token metering |
| `executor` | Routed to appropriate model tier (Phi-4-mini → GPT-4o) |

---

### 15. Adaptive Routing

Tracks which agent performs best for each input type over time and updates routing weights dynamically. A self-improving dispatch layer.

| Placeholder | Azure / IQ Tool |
|---|---|
| `performance_tracker` | **Azure AI Foundry Token Metrics API** + Application Insights — track quality and cost per agent per input type |
| `router` | Foundry IQ — retrieve and update routing weights from knowledge store |
| `worker_*` | Any agent pool — weights updated after each run |

---

## References

- [What is Foundry IQ? — Microsoft Learn](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/what-is-foundry-iq)
- [What is Fabric IQ? — Microsoft Learn](https://learn.microsoft.com/en-us/fabric/iq/overview)
- [Microsoft Debuts Work IQ, Fabric IQ, and Foundry IQ — Cloud Wars](https://cloudwars.com/ai/microsoft-debuts-work-iq-fabric-iq-and-foundry-iq-a-unified-intelligence-layer-for-the-ai-powered-enterprise/)
- [Foundry IQ: Build smarter agents faster — Microsoft](https://devblogs.microsoft.com/foundry/build-smarter-agents-faster-with-foundry-iq/)
- [Durable Task for AI Agents — Azure](https://learn.microsoft.com/en-us/azure/durable-task/sdks/durable-task-for-ai-agents)
- [Architecting Cost-Aware LLM Workloads with Model Router — Microsoft](https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/architecting-cost-aware-llm-workloads-with-model-router-in-microsoft-foundry/4514440)
- [Azure Cosmos DB MCP Toolkit GA — Microsoft](https://devblogs.microsoft.com/cosmosdb/azure-cosmos-db-mcp-toolkit-is-now-generally-available-bringing-your-database-to-ai-agents-to-scale/)
- [microsoft/iq-series — GitHub](https://github.com/microsoft/iq-series)
