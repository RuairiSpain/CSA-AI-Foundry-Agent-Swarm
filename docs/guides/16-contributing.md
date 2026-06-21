# Guide: Contributing to SAFE Framework

---

## Adding a New Agent Pattern

### 1. Add the Enum Value

```python
# safe_framework/safe_core/models.py — RoutePattern enum
MY_PATTERN = "my-pattern"
```

### 2. Create the Directory Structure

```
safe_framework/agents/patterns/my-pattern/
├── route.py.jinja2
├── role-a/
│   ├── agent.yaml
│   └── agent.md
└── role-b/
    ├── agent.yaml
    └── agent.md
```

### 3. Write the Jinja2 Template

See `safe_framework/agents/patterns/sequential-pipeline/route.py.jinja2` as a reference. The template receives these context variables:

| Variable | Type | Description |
|---|---|---|
| `route_name` | str | Route name |
| `class_name` | str | PascalCase class name |
| `description` | str | Route description |
| `pattern` | str | Pattern enum value |
| `agent_names` | str | Comma-separated agent key names |
| `agents` | dict | `{key: Agent}` mapping |
| `created_at` | str | ISO date |

### 4. Register in the Code Generator

```python
# safe_framework/safe_core/code_generator.py

# Add to _PATTERN_TEMPLATE_DIRS
RoutePattern.MY_PATTERN: _PATTERNS_DIR / "my-pattern",

# Add a generate method
def _generate_my_pattern(self, route_def: RouteDefinition) -> GeneratedRoute:
    context = self._backlog_route(route_def, "role_a", "role_b")
    return self._wrap(route_def, context, RoutePattern.MY_PATTERN)

# Add elif branch in generate()
elif route_def.pattern == RoutePattern.MY_PATTERN:
    return self._generate_my_pattern(route_def)
```

### 5. Write Documentation

Follow the agent.md format from any existing pattern role. Required sections:
- Title and tagline
- Overview (role's purpose in the pattern)
- Pattern Diagram (Mermaid `flowchart LR`)
- Contract Specification (inputs/outputs)
- Azure Tools table
- Usage (Python code example)
- Use Cases
- Limitations
- Related Roles
- Footer

### 6. Write Tests

```python
# safe_framework/tests/test_patterns.py — add test cases
def test_my_pattern_validates():
    route = RouteDefinition(
        name="test-my-pattern",
        pattern=RoutePattern.MY_PATTERN,
        agents={"role_a": mock_agent(), "role_b": mock_agent()},
    )
    errors = RouteValidator().validate(route)
    assert not errors

def test_my_pattern_generates_code():
    route = RouteDefinition(...)
    generated = RouteCodeGenerator().generate(route)
    assert "MyPatternRoute" in generated.route_code
```

---

## Adding a New Standalone Agent

### 1. Create the Directory

```
safe_framework/agents/standalone/my-agent/
├── agent.yaml
├── agent.md
├── prompt.txt
└── requirements.txt
```

### 2. Define the Contract (agent.yaml)

Required fields: `name`, `version`, `category`, `description`, `contract.inputs`, `contract.outputs`, `metadata`, `documentation`, `tags`.

### 3. Register in catalog.yaml

```yaml
# safe_framework/safe_core/catalog.yaml
- name: my-agent
  version: "1.0"
  category: <category>
  description: One-line description
  tools:
    - <tool-id>
  tags:
    - <tag>
```

### 4. Write agent.md

Follow the format from `safe_framework/agents/standalone/researcher/agent.md`.

---

## Adding a New MCP Tool

1. Implement the server in `safe_framework/tools/mcp/my_tool_mcp.py`
2. Register in `safe_framework/tools/catalog.yaml`
3. Add to the tool table in `safe_framework/safe_core/code_generator.py` (the `TOOL_TABLE` constant used for docs)
4. Write a usage section in [MCP Catalog Guide](05-mcp-catalog.md)

See [MCP Catalog Guide](05-mcp-catalog.md#adding-a-new-private-mcp-server) for the full steps.

---

## Code Style

- Python 3.11+ compatible (no walrus operator in f-strings, no backslash in f-string expressions)
- Type annotations on all public functions
- No inline comments unless the WHY is non-obvious
- `async/await` for all agent invocations
- Dataclasses for runtime models, Pydantic for schema validation

---

## Submitting a PR

1. Create a branch: `git checkout -b feat/my-pattern`
2. Run tests: `pytest safe_framework/tests/`
3. Run the validator on any new routes
4. Ensure `agent.md` files exist for all new roles
5. Update `docs/patterns-overview.md` to include the new pattern
6. Open a PR against `main` — CI will validate test coverage

---

## Questions?

- Check [Troubleshooting](../SAFE-Complete-Phases-1-9/documentation/PHASE_3_FAQ_AND_TROUBLESHOOTING.md)
- Review existing patterns for reference implementations
- Open a GitHub Discussion for design questions before implementing
