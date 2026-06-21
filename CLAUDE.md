# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

**C3 Copilot / SAFE Framework** — two layered things in one repo:

1. **C3 Copilot** (README.md): A real-time CSA customer-call assistant using Azure AI Foundry. Takes live transcript/WebSocket input and routes it through an enterprise agent swarm to produce structured guidance cards and talk tracks.

2. **SAFE Framework** (`safe_framework/`): The underlying orchestration layer — a code-generation toolkit that turns *route definitions* into production Python code for Azure AI Foundry agent swarms. Engineers define patterns + agents declaratively; SAFE generates the wiring.

---

## Commands

All commands run from `safe_framework/` (where `pyproject.toml` lives).

```bash
# Install
pip install -e ".[dev]"

# Run the CLI
safe catalog [query]         # search agents
safe route                   # interactive route creation wizard
safe tool list               # list all MCP tools
safe tool info <id>          # full catalog entry
safe tool fork <id> <proj>   # fork a tool for project customisation
safe tool rename <old> <new> # rename a local MCP tool + update all refs

# Run all tests
pytest tests/

# Run a single test file or test
pytest tests/test_validator_branches.py
pytest tests/test_code_generator_all.py::TestClassNameHelper::test_class_name_conversion

# Run by marker (MD analysis suites are independent)
pytest -m safe_md            # SAFE agent.md section + token budget checks
pytest -m project_md         # engineer project MD under routes/

# Coverage
python -m coverage run --source=safe_core -m pytest tests/ -q
python -m coverage report --show-missing

# Token budget threshold (default 8000 tokens per MD file)
MD_TOKEN_BUDGET=6000 pytest -m safe_md
```

---

## Architecture

### Code-generation pipeline

The central flow is: **RouteDefinition → RouteCodeGenerator → GeneratedRoute**

```
RouteDefinition (models.py)
    └── pattern: RoutePattern (enum, 27 values)
    └── agents: Dict[str, Agent]
        └── Agent: name, input_schema, output_schema, dependencies
    └── timeout_seconds, routing_field, routing_rules, tags

RouteCodeGenerator (safe_core/code_generator.py)
    └── dispatches to _generate_<pattern>() per RoutePattern value
    └── builds a Jinja2 context dict
    └── renders agents/patterns/<pattern>/route.py.jinja2
    └── returns GeneratedRoute (route_code, requirements_txt, config_yaml, test_data_json)
```

To add a pattern: add the enum value to `models.py`, create `agents/patterns/<pattern>/route.py.jinja2` + role dirs, add to `_PATTERN_TEMPLATE_DIRS` and a `_generate_*` method in `code_generator.py`. See `docs/guides/16-contributing.md`.

### Two catalog systems

- **`safe_core/catalog.yaml`** — agents available to the route-creation interview (`AgentCatalog`). These are *runtime* agent stubs with `input_schema`/`output_schema`.
- **`agents/catalog.yaml`** — richer discovery catalog used by `AgentDiscovery` (in `agent_validation.py`). Includes tags, quality ratings, pattern memberships, and use-cases for search/filter/suggest.
- **`tools/catalog.yaml`** — MCP tool registry. `tool_type: remote_mcp` entries (iq-*, azure-*) are Azure-hosted; `tool_type: local_mcp` entries (safe-*) have Python implementations under `tools/mcp/`.

### Validation layers

There are two validators with distinct scopes:

- **`safe_core/validator.py` → `ContractValidator`**: route-level — timeouts, pattern-specific agent key naming conventions, cross-agent contract compatibility (output of stage N covers required inputs of stage N+1), cycle detection via DFS.
- **`safe_core/agent_validation.py` → `AgentContractValidator`**: agent-level — checks an individual `agent.yaml` against a `PatternTemplate` placeholder's `required_outputs`. Also has pattern-specific rules (e.g. supervisor must output `routing_decision`).

### Pattern library (`safe_core/patterns.py`)

Defines 12 `PatternTemplate` dataclasses (the p1-3 legacy library) registered in a global `PATTERN_REGISTRY`. These are separate from `RoutePattern` enum (the p4 generator). The two systems overlap: `RoutePattern` has 27 values; `PatternRegistry` has 12 entries. `AgentContractValidator` uses `PATTERN_REGISTRY` (p1-3); `ContractValidator` and `RouteCodeGenerator` use `RoutePattern` (p4).

### Route-creation interview

`safe route` launches `RouteInterviewer` (`safe_core/interview.py`), an async multi-step terminal wizard:
`PATTERN → AGENTS → LOGIC → TIMEOUTS → METADATA → REVIEW → generate + save`

### MCP servers (`tools/mcp/`)

Three custom MCP servers built with `mcp.server.fastmcp.FastMCP`:
- `durable_task_mcp.py` — wraps Azure Durable Functions HTTP Management API (checkpoint/suspend/resume orchestrations)
- `model_router_mcp.py` — wraps Azure AI Foundry Model Router (Quality/Cost/Balanced routing policies + cost estimation)
- `token_metrics_mcp.py` — token budget tracking and alerts

All use `httpx` for async HTTP calls. Tests use `respx` to mock them.

### Runtime modules (`safe_core/`)

| Module | Purpose |
|---|---|
| `execution/executor.py` | Executes a `RouteDefinition` against live Foundry agents |
| `invocation/engine.py` | Low-level agent invocation with retry logic |
| `lifecycle/manager.py` | Route registration, versioning, promotion (dev→staging→prod) |
| `governance/approval_engine.py` | Policy-based approval gates; auto-approve below cost threshold |
| `audit/logger.py` | Writes structured audit events (`AuditEventType` enum) |
| `health/monitor.py` | Health checks; stores results via `health/storage/` |
| `monitoring/dashboard.py` | Aggregates metrics for dashboards |
| `security/validator.py` | Input/output validation, prompt injection blocking, PII detection |
| `release/manager.py` | `promote(route, from_env, to_env, approver)` with governance gate |

---

## Key conventions

**Agent key naming** drives validation. `ContractValidator` checks for these prefixes/exact names per pattern:
- `supervisor-manager`: `supervisor`, `specialist_*`, `aggregator`
- `fan-out-fan-in`: `processor_*`, `aggregator`
- `map-reduce`: `splitter`, `mapper`, `reducer`
- `sequential-pipeline`: `stage_*` (sorted, min 2)
- `round-robin`: `dispatcher`, `worker_*` (min 2)
- `mixture-of-experts`: `router`, `expert_*`, `aggregator`
- etc. — see `safe_core/validator.py` for all branches.

**agent.md required sections** (enforced by `tests/md_analysis/`): `## Overview`, `## Pattern Diagram`, `## Contract Specification`, `## Azure Tools`, `## Usage`. Pattern diagrams must use ` ```mermaid ` blocks.

**Python 3.11 f-string restriction**: backslashes (including `\n` in string literals) cannot appear inside `{...}` expression parts of f-strings. Extract string literals with `\n` into regular variables or helper functions before use in f-strings.

**No walrus operator in f-strings** (same 3.11 restriction).

**All agent invocations are `async/await`**. Runtime models use `@dataclass`; schema validation models use Pydantic `BaseModel`.

---

## Test organisation

```
tests/
├── test_*.py                  # safe_core unit tests (main coverage suite)
├── md_analysis/               # MD section + token budget analysis
│   ├── test_safe_md_sections.py   # marker: safe_md
│   ├── test_safe_md_tokens.py     # marker: safe_md — writes test-reports/safe_token_budget.json
│   └── test_project_md_tokens.py  # marker: project_md — scans routes/
├── agent_flow/                # MockAgent dry-runs, graph connectivity
│   ├── conftest.py            # MockAgent, RouteGraph, build_graph helpers
│   ├── test_route_graph.py
│   └── test_superagent_scenarios.py
└── tools/
    ├── test_tool_catalog.py        # catalog.yaml schema validation
    ├── test_mcp_durable_task.py    # respx mocks
    └── test_mcp_model_router.py    # respx mocks + pure-logic cost estimation
```

Token budget reports are written to `test-reports/` (gitignored in normal use). `MD_TOKEN_BUDGET` env var overrides the 8 000-token default. tiktoken `cl100k_base` is used when the BPE data is cached; otherwise a 4-chars-per-token approximation is used automatically.
