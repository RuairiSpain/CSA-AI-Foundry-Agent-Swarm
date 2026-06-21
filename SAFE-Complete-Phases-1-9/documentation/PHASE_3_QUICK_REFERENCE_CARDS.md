# SAFE Framework: Quick Reference Cards

**Print these cards or save as PDF for quick access**

---

## CARD 1: CLI COMMANDS CHEAT SHEET

### Discovery Commands
```bash
# List all 23 agents
python -m safe_cli.cli list-agents

# Filter by category
python -m safe_cli.cli list-agents --category generation
python -m safe_cli.cli list-agents --category retrieval
python -m safe_cli.cli list-agents --category processing

# Search agents
python -m safe_cli.cli search-agents document
python -m safe_cli.cli search-agents query

# Show agent details
python -m safe_cli.cli show-agent document-writer

# Get statistics
python -m safe_cli.cli agent-stats
```

### Route Commands
```bash
# Create route interactively
python -m safe_cli.cli create-route-interactive --pattern supervisor-manager
python -m safe_cli.cli create-route-interactive --pattern fan-out-fan-in
python -m safe_cli.cli create-route-interactive --pattern map-reduce
python -m safe_cli.cli create-route-interactive --pattern sequential-pipeline

# Create agent from template
python -m safe_cli.cli create-agent --from-template document-writer

# Validate agent
python -m safe_cli.cli validate-agent \
  --agent agents/document-writer \
  --pattern sequential-pipeline \
  --placeholder presenter
```

---

## CARD 2: AVAILABLE AGENTS QUICK LIST

### Generation (5 agents)
- **document-writer** ⭐⭐⭐⭐⭐ 4.8 - Word documents
- **presenter-word** ⭐⭐⭐⭐⭐ 4.8 - Formatted Word
- **presenter-html** ⭐⭐⭐⭐⭐ 4.9 - HTML dashboards
- **presenter-markdown** ⭐⭐⭐⭐⭐ 4.8 - Markdown output
- **presenter-code** ⭐⭐⭐⭐⭐ 4.9 - Code generation

### Retrieval (3 agents)
- **rag-query** ⭐⭐⭐⭐⭐ 4.9 - Vector Q&A
- **semantic-search** ⭐⭐⭐⭐⭐ 4.8 - Semantic similarity
- **web-query** ⭐⭐⭐⭐⭐ 4.9 - Web search

### Processing (3 agents)
- **reviewer** ⭐⭐⭐⭐ 4.7 - Document review
- **summarizer** ⭐⭐⭐⭐ 4.7 - Text summarization
- **researcher** ⭐⭐⭐⭐ 4.7 - Multi-step research

### Pattern Agents (11 agents)
- **Supervisor-Manager:** supervisor, aggregator
- **Fan-Out/Fan-In:** processor, worker, aggregator
- **Map-Reduce:** splitter, mapper, shuffle, reducer, final
- **Sequential:** stage1

### Template Agent (1 agent)
- **empty-agent** - Blank template for custom agents

---

## CARD 3: PATTERN SELECTION GUIDE

| Need | Pattern | Time | Agents |
|------|---------|------|--------|
| Route decision | Supervisor-Manager | 10 min | 2 |
| Parallel work | Fan-Out/Fan-In | 15 min | 3 |
| Transform data | Map-Reduce | 20 min | 5 |
| Step-by-step | Sequential-Pipeline | 12 min | 1-4 |

### Quick Selection Guide
- **"Decide which specialist"** → Supervisor-Manager
- **"Do work in parallel"** → Fan-Out/Fan-In
- **"Transform large data"** → Map-Reduce
- **"Process step by step"** → Sequential-Pipeline

---

## CARD 4: AGENT CUSTOMIZATION CHECKLIST

```
□ Copy template
  python -m safe_cli.cli create-agent --from-template document-writer

□ Edit agent.yaml
  - Update name
  - Update description
  - Add company-specific metadata
  - Adjust timeout if needed

□ Edit prompt.txt
  - Add domain-specific instructions
  - Include company rules/policies
  - Specify output format
  - Add examples

□ Edit requirements.txt
  - Add any new dependencies
  - Keep list minimal

□ Validate
  python -m safe_cli.cli validate-agent --agent agents/my-agent

□ Test
  - Run with sample data
  - Verify output format
  - Check performance
```

---

## CARD 5: VALIDATION CHECKLIST

```
Before deploying, verify:

□ Agent exists
  python -m safe_cli.cli show-agent agent-name

□ Contract is valid
  - Inputs: array with name, type, schema
  - Outputs: array with name, type, schema
  - All fields required

□ Agent matches pattern
  python -m safe_cli.cli validate-agent \
    --agent agents/my-agent \
    --pattern supervisor-manager \
    --placeholder supervisor

□ Dependencies install
  pip install -r agents/my-agent/requirements.txt

□ Timeout reasonable
  - Most agents: < 60 seconds
  - Complex agents: < 120 seconds
  - Max allowed: 300 seconds

□ No circular dependencies
  - Agent A calls Agent B
  - Agent B doesn't call Agent A

□ Documentation complete
  - agent.md has examples
  - prompt.txt has instructions
  - Use cases documented
```

---

## CARD 6: ERROR SOLUTIONS

### "Agent not found"
```bash
python -m safe_cli.cli list-agents | grep agent-name
```

### "Contract validation failed"
```bash
# Check YAML syntax
python -c "import yaml; yaml.safe_load(open('agent.yaml'))"
```

### "Dependencies not installing"
```bash
pip install --upgrade pip
pip install -r requirements.txt -vv
```

### "Timeout exceeded"
```yaml
# In agent.yaml
metadata:
  timeout_seconds: 180  # Increase timeout
```

### "Output format mismatch"
```bash
# Check agent contract
python -m safe_cli.cli show-agent agent-name

# Compare to route requirements
```

### "Pattern incompatible"
```bash
# Validate in pattern context
python -m safe_cli.cli validate-agent \
  --agent agents/my-agent \
  --pattern supervisor-manager \
  --placeholder supervisor
```

---

## CARD 7: FILE STRUCTURE

```
Project/
├── templates/agents/
│   ├── standalone/
│   │   ├── document-writer/
│   │   │   ├── agent.yaml
│   │   │   ├── agent.md
│   │   │   ├── prompt.txt
│   │   │   └── requirements.txt
│   │   └── ... (11 more agents)
│   └── patterns/
│       ├── supervisor-manager/
│       │   ├── supervisor/
│       │   └── aggregator/
│       ├── fan-out-fan-in/
│       │   ├── processor/
│       │   ├── worker/
│       │   └── aggregator/
│       └── ... (more patterns)
│
└── agents/
    ├── custom-route-1/
    └── custom-route-2/
```

---

## CARD 8: PERFORMANCE TARGETS

| Metric | Target | OK | Warn |
|--------|--------|----|----|
| Agent execution | < 60s | < 60s | 60-120s |
| Dependencies | < 10 | < 10 | 10-20 |
| Agent size | < 5MB | < 5MB | 5-10MB |
| Contract fields | < 20 | < 20 | 20-30 |

---

## CARD 9: BEST PRACTICES SUMMARY

### ✅ DO
- Use pre-built agents first
- Validate before deployment
- Document customizations
- Follow naming: kebab-case
- Test with sample data
- Monitor performance
- Keep logs of changes

### ❌ DON'T
- Skip validation
- Customize unnecessarily
- Modify contracts
- Mix patterns in one route
- Ignore error messages
- Deploy untested changes
- Hardcode values in prompts

---

## CARD 10: CONTACT & SUPPORT

**SAFE Team Contact**
- Email: safe-team@microsoft.com
- Slack: #safe-framework
- Documentation: /docs/SAFE-Framework-v2.md
- Agent Catalog: templates/agents/CATALOG.yaml

**Getting Help**
1. Check troubleshooting guide (Card 6)
2. Review agent documentation
3. Search issues in team wiki
4. Post in #safe-framework Slack
5. Contact SAFE team

**Escalation Path**
- Level 1: Check documentation
- Level 2: Ask in Slack
- Level 3: Create issue in repo
- Level 4: Contact team directly

---

**Print & Save These Cards!**

Keep handy for quick reference during:
- Agent discovery
- Route creation
- Customization
- Troubleshooting
- Deployment

**Last Updated:** June 20, 2026  
**Version:** 1.0
