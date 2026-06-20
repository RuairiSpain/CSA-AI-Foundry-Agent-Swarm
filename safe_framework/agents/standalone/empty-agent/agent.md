# Empty Agent Template

## Overview

This is a blank template for creating custom agents from scratch. It provides the structure and contract specification needed to build agents that work with the SAFE Framework.

Copy this entire directory (`templates/agents/standalone/empty-agent/`) to start your custom agent implementation.

## Quick Start

1. Copy this directory: `cp -r templates/agents/standalone/empty-agent/ my-agent/`
2. Edit `agent.yaml` - Define your contract and metadata
3. Edit `prompt.txt` - Write your system prompt
4. Edit `agent.md` - Document your agent
5. Update `requirements.txt` - List dependencies
6. Test with CLI: `python -m safe_cli.cli show-agent my-agent`

## Contract Specification

Define what your agent accepts as input and returns as output.

### Inputs

Replace `input_param_1` with your actual input parameter name and structure.

Example input structures:
```json
{
  "field1": "some text",
  "field2": 42
}
```

### Outputs

Define the structure of what your agent returns.

Example output structure:
```json
{
  "status": "success",
  "data": {
    "key": "result value"
  },
  "metadata": {
    "processing_time_ms": 1234
  }
}
```

## File Structure

```
my-agent/
├── agent.yaml         # Contract + metadata (EDIT THIS)
├── agent.md           # Documentation (EDIT THIS)
├── prompt.txt         # System prompt for Claude (EDIT THIS)
├── requirements.txt   # Python dependencies (EDIT THIS)
└── scripts/           # Optional helper scripts
    └── helpers.py     # Add custom logic here
```

## Configuration

After copying, edit each file:

### agent.yaml
- Change `name` to your agent name
- Update `category` (generation, retrieval, processing, etc.)
- Define your contract `inputs` and `outputs`
- List dependencies in `requirements.packages`
- Update `documentation` with real use cases
- Remove all `[EDIT]` markers

### agent.md
- Write a clear overview
- Document your contract
- Provide usage examples
- List all dependencies
- Document limitations

### prompt.txt
- Define your agent's role
- Describe the task
- Write clear instructions
- Specify output format
- Include error handling

### requirements.txt
- List all Python packages needed
- Include specific versions
- Add comments explaining each

## Dependencies

Your agent might need:
- `anthropic` - Claude API
- `pydantic` - Data validation
- `requests` - HTTP requests
- `python-docx` - Word documents
- And many others...

Add only what you actually use.

## Usage Examples

Once implemented, your agent can be used:

```bash
# Show agent details
python -m safe_cli.cli show-agent my-agent

# Create from template
python -m safe_cli.cli create-agent --from-template my-agent

# Validate contract
python -m safe_cli.cli validate-agent --agent agents/my-agent

# Use in a route
python -m safe_cli.cli create-route-interactive --pattern supervisor-manager
# (then select your-agent as the supervisor)
```

## Use Cases

[EDIT] Fill in what your agent is designed to do:
- Use case 1
- Use case 2
- Use case 3

## Configuration Options

[EDIT] Document any configurable options:
- Option 1: Description
- Option 2: Description
- Option 3: Description

## Limitations

[EDIT] Document any known limitations:
- Limitation 1
- Limitation 2
- Limitation 3

## Related Agents

List agents that work well with yours:
- Another agent
- Another agent

## Error Handling

Your agent should return error status when:
- Input validation fails
- Processing encounters an error
- Resource limits are exceeded

Always include a clear `error_message` field.

## Testing Your Agent

### Unit Tests

```python
def test_my_agent():
    from agents.my_agent import MyAgent
    
    agent = MyAgent()
    result = await agent.invoke({
        "field1": "test",
        "field2": 42
    })
    
    assert result["status"] == "success"
    assert "data" in result
```

### Integration Tests

Test with the CLI:
```bash
python -m safe_cli.cli show-agent my-agent
```

Should display your agent's contract and metadata.

## Next Steps

1. Fill in all `[EDIT]` sections
2. Remove all `[EDIT]` markers
3. Test your agent with the CLI
4. Add to a route using `create-route-interactive`
5. Customize further as needed

## Support

For questions about the template:
- See `PHASE_1_IMPLEMENTATION_GUIDE.md`
- Review other agent examples
- Check `SAFE_AGENT_TEMPLATE_ARCHITECTURE.md`

---

**Status:** [EDIT] - Ready to customize and use  
**Created:** 2026-06-20  
**Framework Version:** SAFE 1.0
