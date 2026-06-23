# SAFE Framework

**Semantic Agent Framework for Enterprises** — a code-generation toolkit that turns declarative route definitions into production Python agent swarms on Azure AI Foundry.

---

## What it does

You describe *what* your agents should do and how they should be wired together. SAFE generates the boilerplate — routing logic, retry handling, contract validation, audit logging, and structured observability — so you ship agent workflows instead of plumbing.

```
RouteDefinition  →  RouteCodeGenerator  →  Production Python + config + tests
```

---

## Goals

| Goal | How SAFE delivers it |
|------|---------------------|
| **Speed** | Declare a route in minutes; SAFE generates the full `route.py`, `config.yaml`, `requirements.txt`, and test fixtures |
| **Correctness** | `ContractValidator` checks agent output/input compatibility before a line runs |
| **Observability** | Every execution carries a `correlation_id` through all agent hops, audit events, and outbound MCP calls |
| **Enterprise-ready** | Governance approval gates, cost controls, health monitors, and RBAC hooks are built in, not bolted on |
| **Extensibility** | 33 route patterns, a tool catalog, skill catalog, chain builder, and handoff system — pick only what you need |

---

## Features

- **33 route patterns** — sequential pipeline, fan-out/fan-in, map-reduce, evaluator-optimizer, supervisor-manager, mixture-of-experts, react-loop, goal-driven loop, human-in-the-loop, and more
- **Interactive wizards** — `safe route`, `safe chain`, `safe handoff` guide you through building routes step by step
- **Contract validation** — schema compatibility checked between every agent handoff at design time
- **Agent catalog** — searchable library of typed agent stubs; `safe catalog <query>` to explore
- **MCP tool support** — built-in servers for Azure Durable Functions, Foundry Model Router, and token metrics; fork any tool with `safe tool fork`
- **Skill catalog** — reusable NLP/Text/Data building blocks; attach to agents via `agent.yaml`
- **Loop lifecycle** — `safe loop run / goal / sched / stop` for interval, goal-driven, and scheduled loops
- **Correlation IDs** — propagated from entry point through every agent, audit event, and outbound HTTP header
- **Centralised config** — all env vars documented in `.env.example`; one `SafeConfig` object consumed by all modules

---

## Getting started

### Prerequisites

- Python 3.11+
- Azure AI Foundry project (for runtime execution)

### Install

```bash
git clone https://github.com/RuairiSpain/CSA-AI-Foundry-Agent-Swarm
cd CSA-AI-Foundry-Agent-Swarm/safe_framework
pip install -e ".[dev]"
```

### Configure

```bash
cp .env.example .env
# Fill in FOUNDRY_ENDPOINT, FOUNDRY_API_KEY, and optionally approver emails
```

### Explore

```bash
safe catalog                  # list all agents in the catalog
safe catalog summariser       # search for summarisation agents
safe tool list                # list all MCP tools
safe tool list --category azure
```

---

## CLI reference

```bash
# Route building
safe route                    # interactive route creation wizard
safe catalog [query]          # search agent catalog

# Chains (multi-route pipelines)
safe chain                    # interactive chain wizard
safe chain list               # list saved chains
safe chain validate <name>    # check field mappings
safe chain generate <name>    # regenerate chain.py from chain.yaml

# Handoffs (ConnectedAgentTool delegation pools)
safe handoff                  # interactive handoff wizard
safe handoff list
safe handoff validate <name>
safe handoff generate <name>

# Loop execution
safe loop run <route>  --interval 5m  --max-iter 20
safe loop goal <route> --condition "output['score'] >= 0.9" --max-iter 10
safe loop sched <route> --cron "0 9 * * *"
safe loop status <run-id>
safe loop stop <run-id>

# Tools
safe tool list
safe tool info <id>
safe tool fork <id> <project>
safe tool rename <old-id> <new-id>

# Skills
safe skill list
safe skill info <id>
safe skill create <id> <category> "<description>"

# Tests
pytest tests/
pytest tests/ -m safe_md     # agent.md section + token budget checks
python -m coverage run --source=safe_core -m pytest tests/ -q
python -m coverage report --show-missing
```

---

## Example 1 — Simple agent

**Use case:** summarise a customer support ticket in one pass.

**Pattern:** `sequential-pipeline` (a single `stage_1` agent — SAFE treats a one-stage pipeline as a straight-through call with full contract validation and audit logging).

```python
from safe_core.models import RouteDefinition, RoutePattern, Agent
from safe_core.code_generator import RouteCodeGenerator

route = RouteDefinition(
    name="ticket-summariser",
    pattern=RoutePattern.SEQUENTIAL_PIPELINE,
    description="Summarise a support ticket into a one-paragraph executive brief",
    timeout_seconds=60,
    agents={
        "stage_1": Agent(
            name="ticket-summary-agent",
            category="processor",
            version="1.0",
            description="Reads a raw support ticket and returns a structured summary",
            input_schema={
                "type": "object",
                "required": ["ticket_id", "ticket_text"],
                "properties": {
                    "ticket_id":   {"type": "string"},
                    "ticket_text": {"type": "string"},
                },
            },
            output_schema={
                "type": "object",
                "required": ["summary", "severity"],
                "properties": {
                    "summary":  {"type": "string"},
                    "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                },
            },
        ),
    },
)

generated = RouteCodeGenerator.generate(route)
print(generated.route_code)     # production-ready route.py
print(generated.config_yaml)    # deployment config
print(generated.test_data_json) # sample test fixture
```

**What SAFE generates:**

```
routes/ticket-summariser/
  route.py          ← TicketSummariserRoute class with invoke(), _validate_input/output()
  config.yaml       ← timeout, agent names, pattern, version
  requirements.txt
  test_data.json
```

**Invoke:**

```python
from safe_core.tracing import new_correlation_id, StructuredLogger

cid = new_correlation_id()
log = StructuredLogger(route_name="ticket-summariser")

log.route_started()
result = await route_instance.invoke({
    "ticket_id": "SUP-4821",
    "ticket_text": "Customer reports login failure after password reset on mobile app...",
})
log.route_completed(elapsed_ms=230)
# Every log line carries the same correlation_id for full trace reconstruction
```

---

## Example 2 — Super agent (fan-out / fan-in)

**Use case:** analyse customer feedback from three independent angles simultaneously, then merge into a single verdict.

**Pattern:** `fan-out-fan-in` — SAFE fans the input out to all `processor_*` agents in parallel, then passes all results to `aggregator`.

```python
from safe_core.models import RouteDefinition, RoutePattern, Agent
from safe_core.code_generator import RouteCodeGenerator

_feedback_input = {
    "type": "object",
    "required": ["feedback_id", "feedback_text"],
    "properties": {
        "feedback_id":   {"type": "string"},
        "feedback_text": {"type": "string"},
    },
}

_analysis_output = {
    "type": "object",
    "required": ["score", "label"],
    "properties": {
        "score": {"type": "number"},
        "label": {"type": "string"},
    },
}

route = RouteDefinition(
    name="feedback-analyser",
    pattern=RoutePattern.FAN_OUT_FAN_IN,
    description="Parallel sentiment, category, and urgency analysis of customer feedback",
    timeout_seconds=90,
    agents={
        "processor_sentiment": Agent(
            name="sentiment-scorer",
            category="processor",
            version="1.0",
            description="Scores sentiment from -1.0 (negative) to +1.0 (positive)",
            input_schema=_feedback_input,
            output_schema=_analysis_output,
        ),
        "processor_category": Agent(
            name="topic-classifier",
            category="processor",
            version="1.0",
            description="Classifies feedback into product / billing / support / other",
            input_schema=_feedback_input,
            output_schema=_analysis_output,
        ),
        "processor_urgency": Agent(
            name="urgency-detector",
            category="processor",
            version="1.0",
            description="Flags whether the feedback needs an urgent response",
            input_schema=_feedback_input,
            output_schema=_analysis_output,
        ),
        "aggregator": Agent(
            name="feedback-aggregator",
            category="aggregator",
            version="1.0",
            description="Merges sentiment, category, and urgency into a triage verdict",
            input_schema={
                "type": "object",
                "required": ["processor_sentiment", "processor_category", "processor_urgency"],
                "properties": {
                    "processor_sentiment": {"type": "object"},
                    "processor_category":  {"type": "object"},
                    "processor_urgency":   {"type": "object"},
                },
            },
            output_schema={
                "type": "object",
                "required": ["verdict", "priority", "recommended_action"],
                "properties": {
                    "verdict":             {"type": "string"},
                    "priority":            {"type": "string"},
                    "recommended_action":  {"type": "string"},
                },
            },
        ),
    },
)

generated = RouteCodeGenerator.generate(route)
```

**Generated execution flow:**

```
feedback_text
    ├── processor_sentiment  ─┐
    ├── processor_category   ─┼──► aggregator ──► verdict + priority + action
    └── processor_urgency    ─┘
         (all three run in parallel via asyncio.gather)
```

**Use the interactive wizard instead of writing code:**

```bash
safe route
# > Select pattern: fan-out-fan-in
# > Add agent key: processor_sentiment  ...
# > Add agent key: processor_category   ...
# > Add agent key: processor_urgency    ...
# > Add agent key: aggregator           ...
# > Route name: feedback-analyser
# ✓ Generated: routes/feedback-analyser/route.py
```

---

## Example 3 — Complex loop: iterative marketing copy improvement

**Use case:** generate marketing copy for a company, score it against brand and quality criteria, then iteratively refine it until it meets a quality threshold — or return the best version after a fixed number of attempts.

**Pattern:** `evaluator-optimizer` — SAFE loops `generator → evaluator → optimizer` up to `max_iterations` times. The loop exits early when `evaluator` returns `quality_score ≥ 0.85`.

```python
from safe_core.models import RouteDefinition, RoutePattern, Agent
from safe_core.code_generator import RouteCodeGenerator

route = RouteDefinition(
    name="marketing-copy-refiner",
    pattern=RoutePattern.EVALUATOR_OPTIMIZER,
    description=(
        "Iteratively improve marketing copy until it scores ≥ 0.85 on brand "
        "alignment, clarity, and call-to-action strength"
    ),
    timeout_seconds=300,
    agents={
        "generator": Agent(
            name="copy-writer",
            category="generator",
            version="1.0",
            description=(
                "Writes marketing copy from a product brief. On iterations > 0 "
                "it receives structured feedback from the optimizer and rewrites accordingly."
            ),
            input_schema={
                "type": "object",
                "required": ["product_brief", "target_audience", "tone"],
                "properties": {
                    "product_brief":    {"type": "string"},
                    "target_audience":  {"type": "string"},
                    "tone":             {"type": "string", "enum": ["professional", "casual", "inspirational"]},
                    "feedback":         {"type": "string"},   # populated from iteration 2 onward
                    "iteration":        {"type": "integer"},
                },
            },
            output_schema={
                "type": "object",
                "required": ["headline", "body", "cta"],
                "properties": {
                    "headline": {"type": "string"},
                    "body":     {"type": "string"},
                    "cta":      {"type": "string"},
                },
            },
        ),

        "evaluator": Agent(
            name="copy-quality-scorer",
            category="evaluator",
            version="1.0",
            description=(
                "Scores generated copy on brand alignment (0–1), clarity (0–1), "
                "and CTA strength (0–1). Returns a weighted quality_score and "
                "structured feedback for the optimizer."
            ),
            input_schema={
                "type": "object",
                "required": ["output", "iteration"],
                "properties": {
                    "output":    {"type": "object"},   # the generator's output
                    "iteration": {"type": "integer"},
                },
            },
            output_schema={
                "type": "object",
                "required": ["quality_score", "feedback"],
                "properties": {
                    "quality_score":    {"type": "number", "minimum": 0, "maximum": 1},
                    "feedback":         {"type": "string"},
                    "brand_alignment":  {"type": "number"},
                    "clarity":          {"type": "number"},
                    "cta_strength":     {"type": "number"},
                },
            },
        ),

        "optimizer": Agent(
            name="copy-prompt-optimizer",
            category="optimizer",
            version="1.0",
            description=(
                "Translates evaluator feedback into specific, actionable rewrite "
                "instructions for the generator: which sections to change, what "
                "tone adjustments to make, and which claims to strengthen."
            ),
            input_schema={
                "type": "object",
                "required": ["output", "feedback", "iteration"],
                "properties": {
                    "output":    {"type": "object"},
                    "feedback":  {"type": "string"},
                    "iteration": {"type": "integer"},
                },
            },
            output_schema={
                "type": "object",
                "required": ["product_brief", "target_audience", "tone", "feedback", "iteration"],
                "properties": {
                    "product_brief":   {"type": "string"},
                    "target_audience": {"type": "string"},
                    "tone":            {"type": "string"},
                    "feedback":        {"type": "string"},   # passed back to generator
                    "iteration":       {"type": "integer"},
                },
            },
        ),
    },
)

generated = RouteCodeGenerator.generate(route)
```

**Generated loop logic (inside `route.py`):**

```python
for iteration in range(3):                    # max_iterations = 3
    # 1. Generate copy
    generated = await self.generator.invoke(request)

    # 2. Score it
    eval_result = await self.evaluator.invoke(
        {"output": generated, "iteration": iteration}
    )
    score = eval_result.get("quality_score", 0)

    if score >= 0.85:                         # quality_threshold
        final_output = generated
        break                                 # exit early — goal reached

    # 3. Optimise the prompt for the next round
    request = await self.optimizer.invoke(
        {"output": generated, "feedback": eval_result["feedback"], "iteration": iteration}
    )
else:
    final_output = generated                  # best-effort after max iterations
```

**Run as a goal-driven loop from the CLI:**

```bash
# Generate the route
safe route
# > Select pattern: evaluator-optimizer
# > Route name: marketing-copy-refiner
# ✓ Generated: routes/marketing-copy-refiner/route.py

# Execute with a goal condition
safe loop goal marketing-copy-refiner \
    --condition "output['quality_score'] >= 0.85" \
    --max-iter 5
```

**Trace a full run** — every iteration shares the same `correlation_id`:

```
{"correlation_id": "f3a1...", "route_name": "marketing-copy-refiner", "stage": "generator",  "event": "agent_invoked",  "elapsed_ms": 0,    "iteration": 0}
{"correlation_id": "f3a1...", "route_name": "marketing-copy-refiner", "stage": "evaluator",  "event": "agent_invoked",  "elapsed_ms": 820,  "quality_score": 0.61}
{"correlation_id": "f3a1...", "route_name": "marketing-copy-refiner", "stage": "optimizer",  "event": "agent_invoked",  "elapsed_ms": 1540}
{"correlation_id": "f3a1...", "route_name": "marketing-copy-refiner", "stage": "generator",  "event": "agent_invoked",  "elapsed_ms": 2200, "iteration": 1}
{"correlation_id": "f3a1...", "route_name": "marketing-copy-refiner", "stage": "evaluator",  "event": "agent_succeeded","elapsed_ms": 3010,  "quality_score": 0.91}
{"correlation_id": "f3a1...", "route_name": "marketing-copy-refiner", "event": "route_completed", "elapsed_ms": 3015, "iterations": 2}
```

---

## Route patterns (33 available)

| Category | Patterns |
|----------|----------|
| **Pipeline** | `sequential-pipeline`, `fan-out-fan-in`, `map-reduce`, `tree-reduce`, `diamond` |
| **Routing** | `supervisor-manager`, `round-robin`, `mixture-of-experts`, `conditional-branching`, `fallback-chain`, `adaptive-routing`, `budget-aware-routing` |
| **Teams** | `hierarchical-teams`, `orchestrator-workers`, `debate` |
| **Loops** | `retry-loop`, `evaluator-optimizer`, `reflection`, `react-loop`, `goal-driven-loop`, `interval-loop`, `ralph-loop`, `planner-generator-evaluator`, `lats` |
| **Human / Gate** | `human-in-the-loop`, `gate-guard` |
| **Memory / RAG** | `rag`, `memory-augmented`, `self-consistency` |
| **Integration** | `agent-as-a-tool`, `event-driven`, `checkpoint-resume`, `planning` |

---

## Repository structure

```
safe_framework/
  safe_core/           # Core framework — validators, generator, patterns, runtime
    config.py          # Centralised SafeConfig (all SAFE_ env vars)
    tracing.py         # Correlation IDs + StructuredLogger
    models.py          # RouteDefinition, Agent, RoutePattern, LoopConfig
    code_generator.py  # RouteCodeGenerator — dispatches to 33 Jinja2 templates
    validator.py       # ContractValidator — design-time contract checks
    interview.py       # RouteInterviewer — interactive route creation wizard
    audit/             # Immutable audit trail
    execution/         # Execution engine with retry logic
    governance/        # Approval gates, policy engine
    health/            # Health monitors and alerts
    invocation/        # Route invocation engine + correlation ID propagation
    lifecycle/         # Route registration, versioning, promotion
    security/          # Input validation, PII detection, injection blocking
  agents/
    catalog.yaml       # Agent discovery catalog (search / filter / suggest)
    patterns/          # 33 Jinja2 route templates (one dir per pattern)
  tools/
    catalog.yaml       # MCP tool registry
    mcp/               # Custom MCP servers: durable-task, model-router, token-metrics
  safe_cli/
    main.py            # CLI entry point (safe route / chain / loop / tool / skill)
  tests/               # 935 tests across all modules
  pyproject.toml
  .env.example         # All supported env vars with descriptions and defaults
```

---

## Environment variables

See `safe_framework/.env.example` for the full list. Key variables:

```bash
# Azure AI Foundry (required for MCP servers)
FOUNDRY_ENDPOINT=https://<your-hub>.openai.azure.com
FOUNDRY_API_KEY=<your-key>

# Runtime timeouts (optional — sensible defaults)
SAFE_EXECUTION_DEFAULT_TIMEOUT_SECONDS=300
SAFE_AGENT_DEFAULT_TIMEOUT_SECONDS=3600

# Health thresholds
SAFE_HEALTH_FAILURE_THRESHOLD=2
SAFE_HEALTH_COST_THRESHOLD_USD=1000.0
```

---

## Author

Cloud Solution Architecture — Cloud & AI, Microsoft
