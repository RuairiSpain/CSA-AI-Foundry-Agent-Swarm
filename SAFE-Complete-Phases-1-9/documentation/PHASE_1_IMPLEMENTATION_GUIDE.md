# PHASE 1: FOUNDATION - IMPLEMENTATION GUIDE
## Status: PRODUCTION READY

**What's Included:**
- ✅ Agent contract schema
- ✅ CATALOG.yaml (23 agents)
- ✅ Directory structure setup
- ✅ ContractValidator system
- ✅ AgentDiscovery system
- ✅ CLI commands (8 commands)
- ✅ Agent provisioning
- ✅ Testing framework

---

## 1. Setup & Installation

### Step 1: Create SAFE project directory

```bash
mkdir my-safe-project
cd my-safe-project
git init
```

### Step 2: Create Python environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

pip install pydantic pyyaml typer rich
```

### Step 3: Copy SAFE core files

```bash
# Directory structure
mkdir -p safe_core safe_cli tests
mkdir -p templates/agents/{standalone,patterns}

# Copy Python files
# - safe_core/agent_validation.py
# - safe_core/agent_discovery.py
# - safe_core/agent_provisioning.py
# - safe_cli/agent_commands.py

# Copy CATALOG.yaml
cp templates/agents/CATALOG.yaml .
```

### Step 4: Initialize project

```bash
python -c "
from safe_core.agent_provisioning import setup_safe_project
from pathlib import Path
setup_safe_project(Path('.'))
"
```

---

## 2. CLI Commands Reference

### List agents

```bash
# List all agents
python -m safe_cli.cli list-agents

# Filter by category
python -m safe_cli.cli list-agents --category generation

# Filter by pattern
python -m safe_cli.cli list-agents --pattern supervisor-manager

# Filter by complexity
python -m safe_cli.cli list-agents --complexity intermediate

# Filter by rating
python -m safe_cli.cli list-agents --min-rating 4.7
```

### Show agent details

```bash
python -m safe_cli.cli show-agent document-writer
```

### Search agents

```bash
python -m safe_cli.cli search-agents document
python -m safe_cli.cli search-agents "word processing"
```

### Create agent from template

```bash
python -m safe_cli.cli create-agent --from-template document-writer

# Interactive selection
python -m safe_cli.cli create-agent
```

### Validate agent

```bash
python -m safe_cli.cli validate-agent \
  --agent agents/my-agent/ \
  --pattern supervisor-manager \
  --placeholder supervisor
```

### Get statistics

```bash
python -m safe_cli.cli agent-stats
```

### Create route interactively

```bash
python -m safe_cli.cli create-route-interactive --pattern supervisor-manager
```

---

## 3. Example Workflows

### Workflow 1: Create Simple Document Writer Route

```bash
# 1. Create route with supervisor-manager pattern
python -m safe_cli.cli create-route-interactive --pattern supervisor-manager

# When prompted, select:
# - Supervisor: Loan Supervisor Router
# - Aggregator: Decision Aggregator

# 2. Customize supervisor agent
vim agents/supervisor-router/agent.yaml

# 3. Customize aggregator agent
vim agents/decision-aggregator/agent.yaml

# 4. Validate agents
python -m safe_cli.cli validate-agent \
  --agent agents/supervisor-router \
  --pattern supervisor-manager \
  --placeholder supervisor

# 5. Test agents
python -m agents.supervisor_router --test
```

### Workflow 2: Create Custom Agent from Template

```bash
# 1. Search for agent to copy
python -m safe_cli.cli search-agents document

# 2. Create agent from template
python -m safe_cli.cli create-agent --from-template document-writer

# 3. Customize the agent
cd agents/document-writer
vim agent.yaml        # Edit contract
vim prompt.txt       # Edit system prompt
vim scripts/*        # Edit helper code

# 4. Test agent
python -m agents.document_writer --test

# 5. Mark as customized
# Edit .agent-metadata.yml:
# customized: true
# customization_notes:
#   - Added custom formatting
#   - Integrated company templates
```

### Workflow 3: Add New Agent to Catalog

```bash
# 1. Create template directory
mkdir -p templates/agents/standalone/my-agent

# 2. Create agent files
touch templates/agents/standalone/my-agent/agent.yaml
touch templates/agents/standalone/my-agent/agent.md
touch templates/agents/standalone/my-agent/prompt.txt
touch templates/agents/standalone/my-agent/requirements.txt

# 3. Fill in agent.yaml with contract
# (See sample_agent_document_writer.yaml for example)

# 4. Update CATALOG.yaml with new agent

# 5. List to verify
python -m safe_cli.cli list-agents | grep my-agent
```

---

## 4. Testing

### Unit Tests

```python
# tests/test_agent_validation.py

import pytest
from safe_core.agent_validation import ContractValidator

def test_validate_supervisor_agent():
    """Test supervisor agent validation."""
    validator = ContractValidator()
    
    agent_contract = {
        "contract": {
            "inputs": [{"name": "application", "type": "object"}],
            "outputs": [{"name": "routing_decision", "type": "object"}]
        },
        "metadata": {"timeout_seconds": 60}
    }
    
    result = validator.validate_agent_for_pattern(
        agent_contract,
        "supervisor-manager",
        "supervisor"
    )
    
    assert result.valid
    assert "routing_decision" in result.agent_outputs


def test_invalid_agent_missing_output():
    """Test validation fails for missing required output."""
    validator = ContractValidator()
    
    agent_contract = {
        "contract": {
            "inputs": [{"name": "application", "type": "object"}],
            "outputs": [{"name": "wrong_output", "type": "object"}]
        }
    }
    
    result = validator.validate_agent_for_pattern(
        agent_contract,
        "supervisor-manager",
        "supervisor"
    )
    
    assert not result.valid
    assert len(result.errors) > 0
```

### Integration Tests

```python
# tests/test_agent_provisioning.py

import pytest
import yaml
from pathlib import Path
from safe_core.agent_provisioning import AgentProvisioner

def test_provision_agent(tmp_path):
    """Test agent provisioning."""
    provisioner = AgentProvisioner(tmp_path)
    
    # Create mock template
    template_path = tmp_path / "templates/agents/standalone/test-agent"
    template_path.mkdir(parents=True, exist_ok=True)
    
    agent_yaml = template_path / "agent.yaml"
    agent_data = {
        "name": "Test Agent",
        "version": "1.0",
        "contract": {
            "inputs": [{"name": "data", "type": "object"}],
            "outputs": [{"name": "result", "type": "object"}]
        },
        "metadata": {"timeout_seconds": 60}
    }
    
    with open(agent_yaml, "w") as f:
        yaml.dump(agent_data, f)
    
    # Provision
    result = provisioner.provision_agent(
        "test-agent",
        install_deps=False
    )
    
    assert result["success"]
    assert result["agent_path"].exists()
    assert (result["agent_path"] / "agent.yaml").exists()
    assert (result["agent_path"] / ".agent-metadata.yml").exists()
```

### CLI Tests

```bash
#!/bin/bash
# tests/test_cli.sh

set -e

echo "Testing CLI commands..."

# Test list-agents
echo "✓ Testing list-agents..."
python -m safe_cli.cli list-agents > /dev/null

# Test search
echo "✓ Testing search-agents..."
python -m safe_cli.cli search-agents document > /dev/null

# Test show
echo "✓ Testing show-agent..."
python -m safe_cli.cli show-agent document-writer > /dev/null

# Test stats
echo "✓ Testing agent-stats..."
python -m safe_cli.cli agent-stats > /dev/null

echo "✅ All CLI tests passed!"
```

Run tests:
```bash
# Python tests
pytest tests/ -v

# CLI tests
bash tests/test_cli.sh
```

---

## 5. Validation Checklist

Before moving to Phase 2, verify:

### Structure
- [ ] templates/agents/CATALOG.yaml exists
- [ ] templates/agents/standalone/ directory exists
- [ ] templates/agents/patterns/ directory exists
- [ ] safe_core/agent_validation.py exists
- [ ] safe_core/agent_discovery.py exists
- [ ] safe_core/agent_provisioning.py exists
- [ ] safe_cli/agent_commands.py exists

### Functionality
- [ ] list-agents command works
- [ ] show-agent command works
- [ ] search-agents command works
- [ ] create-agent command works
- [ ] validate-agent command works
- [ ] agent-stats command works
- [ ] ContractValidator validates correctly
- [ ] AgentDiscovery searches correctly
- [ ] AgentProvisioner provisions correctly

### Data
- [ ] CATALOG.yaml has 23 agents
- [ ] All agents have contracts defined
- [ ] Standalone agents are accessible
- [ ] Pattern agents are accessible
- [ ] Search returns results
- [ ] Statistics are accurate

### Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] CLI tests pass
- [ ] Validation works for supervisor-manager
- [ ] Validation catches missing outputs
- [ ] Agents can be provisioned successfully

---

## 6. Sample CATALOG.yaml Validation

```bash
python -c "
import yaml

with open('templates/agents/CATALOG.yaml') as f:
    catalog = yaml.safe_load(f)

print('Standalone agents:')
for agent in catalog.get('standalone', []):
    print(f'  ✓ {agent[\"id\"]}: {agent[\"name\"]}')

print(f'\nTotal standalone: {len(catalog.get(\"standalone\", []))}')

print('\nPattern agents:')
for pattern, agents in catalog.get('patterns', {}).items():
    print(f'  {pattern}:')
    for agent in agents:
        print(f'    ✓ {agent[\"id\"]}: {agent[\"placeholder\"]}')

stats = catalog.get('statistics', {})
print(f'\nCatalog Statistics:')
print(f'  Total agents: {stats.get(\"total_agents\", \"?\")}')
print(f'  Average rating: {stats.get(\"average_rating\", \"?\")}')
"
```

---

## 7. Troubleshooting

### Command not found

```bash
# Make sure safe_cli is importable
export PYTHONPATH=.:$PYTHONPATH

# Try running directly
python -m safe_cli.agent_commands list-agents
```

### CATALOG.yaml not found

```bash
# Check current directory
pwd

# Make sure you're in project root
ls templates/agents/CATALOG.yaml
```

### Agent validation fails

```bash
# Check agent.yaml syntax
python -c "
import yaml
with open('agents/my-agent/agent.yaml') as f:
    agent = yaml.safe_load(f)
    
print('Contract:', agent.get('contract'))
"
```

### Dependencies not installing

```bash
# Try pip directly
pip install -r agents/my-agent/requirements.txt

# Or manually
pip install python-docx pandas jinja2
```

---

## 8. Next Steps: Phase 2

Phase 1 Foundation is **COMPLETE**. Ready to proceed to Phase 2: Agent Library.

Phase 2 will create:
- ✅ Full template files for all 12 standalone agents
- ✅ Full template files for all 11 pattern-specific agents
- ✅ Documentation for each agent
- ✅ System prompts for each agent
- ✅ Example usage for each agent

**Estimated time:** 1-2 weeks

---

**Status: ✅ PHASE 1 COMPLETE - Ready for Phase 2**
