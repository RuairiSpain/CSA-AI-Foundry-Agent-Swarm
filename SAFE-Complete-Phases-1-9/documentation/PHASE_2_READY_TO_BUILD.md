# PHASE 2: READY TO BUILD AGENT LIBRARY

**Status:** Phase 1 Complete ✅  
**Starting Phase 2:** Immediately  
**Deliverable Timeline:** 1-2 weeks

---

## What You Have Now

### Phase 1: Complete Foundation
- ✅ safe_core/agent_validation.py (validation system)
- ✅ safe_core/agent_discovery.py (discovery system)
- ✅ safe_core/agent_provisioning.py (provisioning system)
- ✅ safe_cli/agent_commands.py (CLI with 8 commands)
- ✅ templates/agents/CATALOG.yaml (23 agents indexed)
- ✅ Complete testing framework
- ✅ Complete implementation guide

### What's Working
```bash
# Discover agents
python -m safe_cli.cli list-agents
python -m safe_cli.cli search-agents document
python -m safe_cli.cli show-agent document-writer

# Create agents
python -m safe_cli.cli create-agent --from-template
python -m safe_cli.cli create-route-interactive

# Validate
python -m safe_cli.cli validate-agent --agent agents/my-agent --pattern supervisor-manager --placeholder supervisor
```

---

## What Phase 2 Creates

### 23 Agent Templates (92 files total)

Each agent gets 4 files:

```
agents/{agent-name}/
├── agent.yaml          (150-250 lines)  - Contract + metadata
├── agent.md            (100-200 lines)  - Documentation
├── prompt.txt          (50-150 lines)   - System prompt
└── requirements.txt    (5-20 lines)     - Dependencies
```

### Standalone Agents (12)
1. document-writer → Word documents
2. rag-query → Vector Q&A
3. reviewer → Quality review
4. summarizer → Text condensing
5. semantic-search → Similarity matching
6. web-query → Web search
7. researcher → Multi-step research
8. presenter-word → Word formatting
9. presenter-html → HTML dashboards
10. presenter-markdown → Markdown output
11. presenter-code → Code generation
12. empty-agent → Blank template

### Pattern-Specific Agents (11)
- supervisor-manager: 2 agents
- fan-out-fan-in: 3 agents
- map-reduce: 5 agents
- sequential-pipeline: 1 agent

---

## How to Build Phase 2

### Step 1: Create Directory Structure

```bash
#!/bin/bash
# Create all directories

mkdir -p templates/agents/standalone/{document-writer,rag-query,reviewer,summarizer,semantic-search,web-query,researcher,presenter-word,presenter-html,presenter-markdown,presenter-code,empty-agent}

mkdir -p templates/agents/patterns/{supervisor-manager/{supervisor,aggregator},fan-out-fan-in/{processor,worker,aggregator},map-reduce/{splitter,mapper,shuffle,reducer,final},sequential-pipeline/stage1}

echo "✅ Directory structure created"
```

### Step 2: Create Agent Files

For each agent, create 4 files. Template structure:

```
agent.yaml:
- Copy contract from CATALOG.yaml
- Add full input/output schemas
- Add metadata
- Add documentation
- Add examples

agent.md:
- Overview section
- Contract specification
- Usage examples
- Use cases
- Configuration
- Dependencies
- Limitations
- Related agents

prompt.txt:
- Role definition
- Task description
- Instructions
- Output format
- Examples
- Error handling

requirements.txt:
- List dependencies
- Specific versions
- Comments for each
```

### Step 3: Build by Batches

**BATCH 1: Foundation (2 agents, 8 files)**
- empty-agent - Blank template
- document-writer - Most common

**BATCH 2: Generators (5 agents, 20 files)**
- presenter-word
- presenter-html
- presenter-markdown
- presenter-code
- (1 more generation agent)

**BATCH 3: Retrievers (3 agents, 12 files)**
- rag-query
- semantic-search
- web-query

**BATCH 4: Processors (3 agents, 12 files)**
- reviewer
- summarizer
- researcher

**BATCH 5: Supervisor-Manager (2 agents, 8 files)**
- supervisor
- aggregator

**BATCH 6: Fan-Out/Fan-In (3 agents, 12 files)**
- processor
- worker
- aggregator

**BATCH 7: Map-Reduce (5 agents, 20 files)**
- splitter
- mapper
- shuffle
- reducer
- final

**BATCH 8: Sequential (1 agent, 4 files)**
- stage1

---

## Agent Template Formula

### agent.yaml Template

```yaml
name: "[Agent Name]"
version: 1.0
category: "[category]"
description: |
  [Agent purpose and use]

contract:
  inputs:
    - name: "[input_name]"
      type: object
      required: true
      description: "[Description]"
      schema:
        type: object
        required_fields: [field1]
        field_definitions:
          field1:
            type: string
            description: "Field description"
  
  outputs:
    - name: "[output_name]"
      type: object
      required: true
      description: "[Description]"
      schema:
        type: object
        required_fields: [result_field]

metadata:
  author: SAFE Team
  source:
    repository: internal
    license: MIT
  dependencies: []
  requirements:
    python: ">=3.11"
    packages: [...]
  timeout_seconds: 60

documentation:
  use_cases: [...]
  example:
    input: {...}
    output: {...}
  limitations: [...]
  related_agents: [...]

tags: [...]
pattern_roles: [...]
```

### agent.md Template

```markdown
# [Agent Name]

## Overview
[Description of what the agent does]

## Contract

### Inputs
- [input_name] (type): Description

### Outputs
- [output_name] (type): Description

## Usage

### Example
\`\`\`python
from agents.[agent_name] import Agent

agent = Agent()
result = await agent.invoke({"input": "..."})
\`\`\`

## Use Cases
- [Use case 1]
- [Use case 2]

## Configuration
- [Config option 1]
- [Config option 2]

## Dependencies
- python-docx >= 0.8.10
- pandas >= 1.0

## Limitations
- [Limitation 1]

## Source
[Attribution if from external source]
```

### prompt.txt Template

```
You are a [Agent Name].

Your role: [Role description]

Your task: [Task description]

Instructions:
1. [Instruction 1]
2. [Instruction 2]

Output Format:
{
  "status": "success|error",
  "data": {...},
  "error_message": "[Optional error details]"
}

Example:
Input: [Example input]
Output: [Example output]

Error Handling:
- If [condition], return error status
- Always include clear error messages
```

### requirements.txt Template

```
# [Agent Name] Dependencies
python-docx>=0.8.10    # Word document generation
pandas>=1.0             # Data manipulation
jinja2>=3.0             # Template rendering
```

---

## Quality Checklist for Each Agent

Before marking agent complete:

- [ ] agent.yaml has complete contract
- [ ] agent.yaml has all metadata
- [ ] agent.md has documentation
- [ ] agent.md has usage example
- [ ] prompt.txt has system prompt
- [ ] prompt.txt has output format
- [ ] requirements.txt lists dependencies
- [ ] All fields are realistic
- [ ] Example inputs/outputs match contract
- [ ] Error handling is documented
- [ ] Related agents are noted

---

## Phase 2 Completion Criteria

All 23 agents must have:
- ✅ Complete agent.yaml
- ✅ Complete agent.md
- ✅ Complete prompt.txt
- ✅ Complete requirements.txt
- ✅ Validation passes CATALOG.yaml spec
- ✅ CLI can list all agents
- ✅ CLI can show each agent
- ✅ CLI can create from each template
- ✅ Contracts are validated

---

## Estimated Effort

**Per Agent:** 30-60 minutes
- agent.yaml: 10 minutes
- agent.md: 15 minutes
- prompt.txt: 10 minutes
- requirements.txt: 5 minutes
- Testing/validation: 5 minutes

**Total for 23 agents:**
- Low estimate: 12 hours
- High estimate: 23 hours
- **Realistic: 15-20 hours (2-3 days intense work)**

**With testing & review: 1-2 weeks**

---

## Recommended Build Order

### Day 1: Foundation (BATCH 1)
- empty-agent
- document-writer
- ✅ Test with CLI

### Day 2-3: Generators (BATCH 2)
- presenter-word
- presenter-html
- presenter-markdown
- presenter-code

### Day 4: Retrievers (BATCH 3)
- rag-query
- semantic-search
- web-query

### Day 5: Processors (BATCH 4)
- reviewer
- summarizer
- researcher

### Day 6-7: Pattern Agents (BATCHES 5-8)
- supervisor-manager (2)
- fan-out-fan-in (3)
- map-reduce (5)
- sequential-pipeline (1)

### Day 8: Testing & Review
- Validate all contracts
- Test all CLI commands
- Review documentation
- Polish examples

---

## Success Metrics

When Phase 2 is complete:

```bash
# All commands work
✅ python -m safe_cli.cli list-agents
   # Should show 23 agents

✅ python -m safe_cli.cli search-agents document
   # Should find document-writer, presenter-word, etc.

✅ python -m safe_cli.cli show-agent document-writer
   # Should show full documentation

✅ python -m safe_cli.cli create-agent --from-template document-writer
   # Should create agents/document-writer/ with all 4 files

✅ python -m safe_cli.cli validate-agent --agent agents/document-writer --pattern sequential-pipeline --placeholder presenter
   # Should validate successfully

✅ python -m safe_cli.cli agent-stats
   # Should show 23 agents, statistics, etc.

✅ python -m safe_cli.cli create-route-interactive --pattern supervisor-manager
   # Should let user select agents for pattern
```

---

## Next Steps After Phase 2

Once Phase 2 agents are complete:

### Phase 3: Deployment (1 week)
- Training materials
- Team onboarding
- Documentation
- User guides
- Support setup

### Phase 4+: Enhancement
- Community agents
- Performance analytics
- Advanced features
- Marketplace

---

## Phase 2 Start

**Batches 1-8 ready to build**  
**Starting with Batch 1: empty-agent and document-writer**  
**All templates and infrastructure in place**

Each agent needs:
1. Copy contract from CATALOG.yaml → agent.yaml
2. Expand with full schema
3. Write documentation → agent.md
4. Create system prompt → prompt.txt
5. List dependencies → requirements.txt
6. Test with CLI
7. Validate contract
8. Move to next

---

**Total Effort:** 15-20 hours  
**Total Impact:** 69% time savings per agent  
**Result:** 23 production-ready agent templates

Ready to build! 🚀

