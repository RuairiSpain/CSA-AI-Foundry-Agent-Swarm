# SAFE Framework

**Semantic Agent Framework for Enterprises** — a code-generation toolkit that turns *route definitions* into production Python code for Azure AI Foundry agent swarms.

Engineers declare patterns + agents; SAFE generates the wiring, validation, config, and test data.

---

## Quick start

```bash
pip install -e ".[dev]"

safe catalog [query]          # search available agents
safe route                    # interactive route creation wizard
safe chain                    # interactive multi-pattern chain wizard
safe tool list                # list all MCP tools
```

---

## Directory layout

```
safe_framework/
├── agents/
│   ├── catalog.yaml          # agent discovery catalog (tags, ratings, patterns)
│   └── patterns/             # one dir per RoutePattern, each with route.py.jinja2
├── safe_core/
│   ├── models.py             # RouteDefinition, Agent, RoutePattern (enum, 27 values)
│   ├── code_generator.py     # RouteCodeGenerator — dispatches to per-pattern generators
│   ├── validator.py          # ContractValidator — timeout / agent-key / cross-stage checks
│   ├── config.py             # SafeConfig singleton, all SAFE_* env vars
│   ├── catalog.py            # AgentCatalog — loads agents/catalog.yaml
│   ├── interview.py          # RouteInterviewer — async terminal wizard (safe route)
│   ├── audit/                # AuditLogger — append-only JSONL + SHA-256 hash chain
│   ├── execution/            # ExecutionEngine — asyncio.wait_for timeout + retry backoff
│   ├── governance/           # ApprovalEngine, GovernancePolicy, ApprovalRequest
│   ├── health/               # HealthMonitor, RouteHealthStatus, AlertSeverity
│   ├── incidents/            # IncidentResponder — create / resolve incidents
│   ├── lifecycle/            # RouteLifecycleManager — register / version / promote
│   ├── release/              # ReleaseManager — dev → staging → prod promotion gate
│   ├── security/             # SecurityValidator — PII, prompt-injection, schema checks
│   └── tracing.py            # correlation_headers() for distributed tracing
├── safe_cli/
│   └── main.py               # Typer app: catalog / route / chain / tool / loop commands
├── tools/
│   ├── catalog.yaml          # MCP tool registry
│   └── mcp/
│       ├── durable_task_mcp.py    # Azure Durable Functions HTTP Management API
│       ├── model_router_mcp.py    # Azure AI Foundry Model Router (Quality/Cost/Balanced)
│       └── token_metrics_mcp.py   # Token budget tracking and alerts
└── tests/                    # pytest suite (run from this directory)
```

---

## Key concepts

### Route patterns

27 `RoutePattern` enum values covering supervisor-manager, fan-out-fan-in, map-reduce, sequential-pipeline, RAG, loops (react, goal-driven, interval), LATS, and more. Each pattern maps to a Jinja2 template under `agents/patterns/`.

### Code-generation pipeline

```
RouteDefinition → ContractValidator → RouteCodeGenerator → GeneratedRoute
```

`GeneratedRoute` contains `route_code`, `requirements_txt`, `config_yaml`, `test_data_json`, and `metadata`. Generated output is deterministic: timestamps come from `route_def.created_at`, not `datetime.now()`.

### Configuration

All tuneable defaults live in `SafeConfig` (`safe_core/config.py`) and are readable via `SAFE_*` environment variables. No magic numbers in production code.

### Validation layers

- **`ContractValidator`** — route-level: timeouts, agent key naming per pattern, cross-stage output-to-input compatibility, cycle detection.
- **`AgentContractValidator`** — agent-level: validates an `agent.yaml` against a `PatternTemplate`'s required outputs.

---

## Running tests

```bash
# All tests (from safe_framework/)
pytest tests/

# By marker
pytest -m safe_md       # SAFE agent.md section + token budget checks
pytest -m project_md    # engineer project MD under routes/

# Coverage
python -m coverage run --source=safe_core -m pytest tests/ -q
python -m coverage report --show-missing
```

---

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `SAFE_EXECUTION_DEFAULT_TIMEOUT_SECONDS` | 300 | Route execution timeout |
| `SAFE_RETRY_LOOP_MAX_RETRIES` | 3 | Max retries in retry-loop pattern |
| `SAFE_RALPH_LOOP_SPAWN_BUDGET` | 10 | Ralph-loop spawn budget |
| `SAFE_LOOP_DEFAULT_MAX_ITERATIONS` | 10 | Default max iterations for agent loops |
| `SAFE_EXECUTION_MAX_RETRIES` | 3 | ExecutionEngine retry count |
| `SAFE_EXECUTION_BASE_BACKOFF_SECONDS` | 2.0 | Base exponential backoff (seconds) |
| `SAFE_EVALUATOR_OPTIMIZER_QUALITY_THRESHOLD` | 0.85 | Quality gate for evaluator-optimizer |
| `SAFE_LATS_MAX_ITERATIONS` | 20 | LATS tree search depth |
| `SAFE_GOVERNANCE_MAX_MONTHLY_COST_USD` | 10000.0 | Default cost cap for governance policy |
| `SAFE_AUDIT_LOG_PATH` | *(none)* | Optional JSONL path for audit persistence |
| `FOUNDRY_ENDPOINT` | *(required)* | Azure AI Foundry project endpoint |
| `FOUNDRY_API_KEY` | *(required)* | Azure AI Foundry API key |
| `DURABLE_TASK_ENDPOINT` | *(required)* | Azure Durable Functions base URL |
| `DURABLE_TASK_KEY` | *(required)* | Azure Durable Functions host key |

See `safe_core/config.py` for the full list.
