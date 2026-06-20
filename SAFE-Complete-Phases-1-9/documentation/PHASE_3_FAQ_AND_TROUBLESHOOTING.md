# SAFE Framework: FAQ & Troubleshooting Guide

**Frequently Asked Questions from CSAs**

---

## SECTION 1: GETTING STARTED

### Q: How do I get started with SAFE?
**A:** Follow these 4 steps:
1. Extract the agent templates to `templates/agents/`
2. Run `python -m safe_cli.cli list-agents` to see all 23 agents
3. Choose a pattern (supervisor-manager is most common)
4. Run `python -m safe_cli.cli create-route-interactive --pattern supervisor-manager`

Expected time: 15 minutes

---

### Q: Do I need to understand Python to use SAFE?
**A:** No! SAFE is designed for non-developers:
- All agents are pre-built
- CLI is interactive (no coding required)
- Templates handle 80% of use cases
- Only advanced customization needs Python

---

### Q: What are the system requirements?
**A:**
- Python 3.11 or higher
- 2GB RAM minimum
- Windows, macOS, or Linux
- Internet connection (for some agents)

Run `python --version` to check your Python version.

---

### Q: How long does it take to create a route?
**A:**
- Supervisor-Manager: 10 minutes
- Fan-Out/Fan-In: 15 minutes
- Map-Reduce: 20 minutes
- Sequential-Pipeline: 12 minutes

Total with customization: 30-45 minutes

---

### Q: Can I use SAFE without modifying agents?
**A:** Yes! 80% of use cases use pre-built agents as-is:
- Document generation
- Data retrieval
- Text processing
- Basic routing

Only 20% need customization for domain-specific logic.

---

## SECTION 2: AGENTS & DISCOVERY

### Q: Why are there 23 agents?
**A:**
- 12 standalone agents (reusable)
- 11 pattern agents (optimized for patterns)

This covers 80% of common use cases. More can be added as needed.

---

### Q: How do I find agents for my use case?
**A:**
```bash
# Search for agent
python -m safe_cli.cli search-agents document

# Filter by category
python -m safe_cli.cli list-agents --category generation

# Show top agents
python -m safe_cli.cli agent-stats
```

---

### Q: What does the star rating mean?
**A:**
- ⭐⭐⭐⭐⭐ (4.8+): Battle-tested, use first
- ⭐⭐⭐⭐ (4.5+): Reliable, well-documented
- ⭐⭐⭐ (4.0+): Solid, common use
- ⭐⭐ (<4.0): New/limited adoption

Always prefer higher-rated agents.

---

### Q: Can I create my own agents?
**A:** Yes!
```bash
python -m safe_cli.cli create-agent --from-template empty-agent
```

This copies the blank template for you to customize.

---

## SECTION 3: ROUTES & PATTERNS

### Q: What's a route?
**A:** A route combines multiple agents following a pattern:
```
Input → Agent 1 → Agent 2 → Agent 3 → Output
```

Example: Supervisor decides → Workers analyze → Aggregator combines

---

### Q: Which pattern should I use?
**A:**
| Your Need | Pattern |
|-----------|---------|
| Route a decision | Supervisor-Manager |
| Process in parallel | Fan-Out/Fan-In |
| Transform large data | Map-Reduce |
| Step-by-step processing | Sequential-Pipeline |

Most customer use cases: **Supervisor-Manager**

---

### Q: Can I mix patterns?
**A:** Not recommended. Stick to one pattern per route.

Mixing patterns makes routes:
- Harder to understand
- Harder to validate
- More prone to errors
- Slower performance

---

### Q: How many agents can be in a route?
**A:**
- Supervisor-Manager: 2-5 agents
- Fan-Out/Fan-In: 3-10 agents
- Map-Reduce: 5-20 agents
- Sequential: 2-10 agents

Fewer agents = faster, simpler routes

---

### Q: Can routes call other routes?
**A:** Not directly, but they can share agents. Design routes to be independent.

---

## SECTION 4: CUSTOMIZATION

### Q: When should I customize an agent?
**A:** Customize when:
- ✅ Customer has specific business logic
- ✅ Need company-specific rules
- ✅ Integrating with internal systems
- ✅ Domain-specific language

Don't customize when:
- ❌ Template works as-is
- ❌ Just testing SAFE
- ❌ POC/prototype phase

---

### Q: How much can I customize?
**A:** You can change:
- ✅ Agent name and description
- ✅ System prompt and instructions
- ✅ Dependencies and libraries
- ✅ Metadata and company info

Don't change:
- ❌ Input/output contract structure
- ❌ Agent category
- ❌ Pattern compatibility

---

### Q: Will customization break anything?
**A:** No, if you:
1. Keep the contract structure
2. Validate before deployment
3. Don't change input/output fields
4. Test with sample data

---

### Q: How do I undo customizations?
**A:** Simply copy the original template again:
```bash
python -m safe_cli.cli create-agent --from-template document-writer
```

This creates a fresh copy.

---

## SECTION 5: VALIDATION & ERRORS

### Q: Why is validation important?
**A:** Validation catches errors BEFORE deployment:
- ❌ Without: Routes fail at runtime (bad customer experience)
- ✅ With: Errors caught early (prevents issues)

---

### Q: What happens if validation fails?
**A:** You get a clear error message:
```
Agent 'my-agent' incompatible with supervisor-manager pattern
Reason: Missing required output 'routing_decision'
Solution: Add routing_decision to agent.yaml outputs
```

Then fix it before deployment.

---

### Q: How do I validate a route?
**A:**
```bash
python -m safe_cli.cli validate-agent \
  --agent agents/my-agent \
  --pattern supervisor-manager \
  --placeholder supervisor
```

Should show: ✅ Agent is compatible

---

### Q: What are common validation errors?
**A:**

| Error | Cause | Fix |
|-------|-------|-----|
| "Missing required output" | Contract incomplete | Add field to agent.yaml |
| "Dependency not found" | Missing library | `pip install -r requirements.txt` |
| "Timeout exceeded" | Agent too slow | Increase timeout in agent.yaml |
| "Pattern incompatible" | Contract mismatch | Check placeholder requirements |

---

### Q: Can I disable validation?
**A:** No, and you shouldn't. Validation protects your customers.

---

## SECTION 6: PERFORMANCE & OPTIMIZATION

### Q: Why is my route slow?
**A:** Check these:

1. **Agent execution time**
   ```bash
   # Time each agent separately
   # Look for outliers
   ```

2. **Dependencies**
   - Too many imports
   - Large libraries
   - Network calls

3. **Timeout setting**
   - Increase if legitimately slow
   - Optimize if unnecessarily complex

---

### Q: What's a good execution time?
**A:**
- **Fast:** < 30 seconds
- **Acceptable:** 30-60 seconds
- **Slow:** 60-120 seconds
- **Very slow:** > 120 seconds (needs optimization)

---

### Q: How do I optimize a route?
**A:**

1. **Use high-rated agents** (4.8+⭐)
2. **Minimize dependencies**
3. **Cache results** where possible
4. **Reduce input size**
5. **Simplify logic**
6. **Parallel processing** (Fan-Out/Fan-In pattern)

---

### Q: Can I run agents in parallel?
**A:** Yes! Use the **Fan-Out/Fan-In** pattern:
```bash
python -m safe_cli.cli create-route-interactive --pattern fan-out-fan-in
```

This splits work across multiple workers.

---

## SECTION 7: TROUBLESHOOTING

### Q: "Agent not found" error
**A:**
```bash
# List all agents
python -m safe_cli.cli list-agents

# Search for it
python -m safe_cli.cli search-agents agent-name

# Check path
ls agents/agent-name/agent.yaml
```

---

### Q: "CLI command not recognized"
**A:**
```bash
# Reinstall
pip install -e .

# Check Python path
export PYTHONPATH=.:$PYTHONPATH

# Try direct import
python -m safe_cli.cli --version
```

---

### Q: "Contract validation failed"
**A:**
```bash
# Check YAML syntax
python -c "import yaml; yaml.safe_load(open('agents/my-agent/agent.yaml'))"

# Ensure required fields:
# - inputs (array)
# - outputs (array)
# - metadata
# - contract.inputs[].schema
# - contract.outputs[].schema
```

---

### Q: "Dependencies not installing"
**A:**
```bash
# Upgrade pip
pip install --upgrade pip

# Try installing manually
pip install python-docx pandas requests

# Check Python version
python --version  # Should be 3.11+
```

---

### Q: "Route fails in production but works locally"
**A:**

1. Validate in pattern context:
   ```bash
   python -m safe_cli.cli validate-agent \
     --agent agents/my-agent \
     --pattern supervisor-manager \
     --placeholder supervisor
   ```

2. Check environment differences (Python version, dependencies)

3. Test with production-like data

4. Review logs for detailed error

---

### Q: "Agent output format is wrong"
**A:**

1. Check contract:
   ```bash
   python -m safe_cli.cli show-agent my-agent
   ```

2. Verify output matches schema:
   ```json
   {
     "status": "success|error|partial",
     "data": {...},
     "error_message": ""
   }
   ```

3. Test with sample data

---

### Q: "Timeout exceeded"
**A:**
```bash
# In agent.yaml, increase timeout:
metadata:
  timeout_seconds: 180  # From default 60

# Or optimize the agent:
# - Remove unnecessary processing
# - Use caching
# - Reduce dependencies
# - Simplify logic
```

---

## SECTION 8: TEAM & DEPLOYMENT

### Q: How do I train my team?
**A:**
1. Share PHASE_3_CSA_TRAINING_GUIDE.md (3-hour course)
2. Have team complete hands-on lab
3. Run together on first 2-3 customer projects
4. Team leads spot-check work

Total onboarding: 2-3 days

---

### Q: How do I deploy to production?
**A:**
1. Validate route (see validation section)
2. Test with production-like data
3. Get approval from team lead
4. Deploy to production environment
5. Monitor performance

Deployment time: 30 minutes

---

### Q: What should I monitor?
**A:**
- ✅ Execution time
- ✅ Success rate
- ✅ Error messages
- ✅ Customer feedback
- ✅ Resource usage

---

### Q: Can multiple teams use SAFE?
**A:** Yes! SAFE is designed for scale:
- 23 agents + patterns
- 5-10 CSAs can use simultaneously
- Each builds separate routes
- Share templates, not routes

---

### Q: How do I share routes between teams?
**A:** Use version control:
1. Commit agents to Git
2. Team pulls latest
3. Each team customizes for their needs
4. Contribute improvements back

---

## SECTION 9: ADVANCED QUESTIONS

### Q: Can I add my own agents to the catalog?
**A:** Yes, after Phase 4 (not in current release):

For now:
1. Create custom agent using empty-agent template
2. Document thoroughly
3. Test extensively
4. Share with team
5. Contribute to SAFE if generally useful

---

### Q: Can SAFE integrate with existing tools?
**A:** Yes, through agent customization:
- Add API calls to internal systems
- Connect to databases
- Integrate with other Microsoft tools
- Add custom business logic

See agent.md for integration examples.

---

### Q: What if I need an agent that doesn't exist?
**A:**
1. Check if similar agent can be customized
2. If not, create using empty-agent template
3. Document and validate thoroughly
4. Request addition to catalog

Expected contribution time: 2-4 hours

---

### Q: How do I update agents?
**A:** Update process (coming in Phase 4):

For now:
1. Create new version directory
2. Copy original agent
3. Make changes
4. Name: agent-name-v2
5. Update route to use new version

---

## SECTION 10: GETTING HELP

### Q: Where do I find documentation?
**A:**
- **Overview:** PHASE_3_CSA_TRAINING_GUIDE.md
- **Quick Reference:** PHASE_3_QUICK_REFERENCE_CARDS.md
- **Architecture:** APPENDIX_C_AGENT_TEMPLATE_ARCHITECTURE.md
- **Implementation:** PHASE_1_IMPLEMENTATION_GUIDE.md
- **Agent Catalog:** templates/agents/CATALOG.yaml

---

### Q: How do I get support?
**A:**
1. **Check documentation** (most questions answered there)
2. **Review quick reference cards** (Card 6 has solutions)
3. **Ask in Slack** (#safe-framework channel)
4. **Contact SAFE team** (safe-team@microsoft.com)
5. **Create GitHub issue** (if bug)

Response time: 24 hours

---

### Q: Can I provide feedback?
**A:** Yes! We want to hear from you:
- What's working
- What's difficult
- Feature requests
- Bug reports

Post in #safe-framework or email safe-team@microsoft.com

---

### Q: Where can I report bugs?
**A:**
1. Describe the issue clearly
2. Include error message
3. Include steps to reproduce
4. Share your agent files (if possible)
5. Email safe-team@microsoft.com

---

## QUICK ANSWER KEY

| Question | Answer |
|----------|--------|
| How long to learn SAFE? | 3 hours (training) + 2-3 days (practice) |
| How long to create a route? | 10-20 minutes |
| How long to customize agent? | 15-30 minutes |
| How many agents? | 23 pre-built + unlimited custom |
| Time savings per agent? | 52 minutes (69% faster) |
| Validation required? | YES (always) |
| Test required? | YES (before deployment) |
| Support available? | YES (24-hour response) |

---

**Can't find your answer?** Post in #safe-framework Slack or email safe-team@microsoft.com

---

**Last Updated:** June 20, 2026  
**Version:** 1.0
