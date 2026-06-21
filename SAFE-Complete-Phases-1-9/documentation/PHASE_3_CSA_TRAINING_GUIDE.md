# SAFE Framework: CSA Training Guide

**Target Audience:** Customer Success Architects  
**Duration:** 2-3 hours (self-paced)  
**Prerequisites:** Basic familiarity with Azure, Microsoft Agent Framework  
**Version:** 1.0  
**Date:** June 20, 2026

---

## MODULE 1: INTRODUCTION (15 minutes)

### What is SAFE?

SAFE (Simplified Agent Flow Engineering) is a Microsoft CSA enablement platform that dramatically reduces the time needed to help customers implement AI agents on Azure.

**Before SAFE:**
- Creating one agent: 75 minutes
- Manual contract definition
- No validation until runtime
- Inconsistent implementations
- High error rates

**After SAFE:**
- Creating one agent: 23 minutes (69% faster)
- Pre-built contracts
- Validation before use
- Consistent structure
- Zero contract errors

### What You'll Learn Today

1. How to discover agents (**2 minutes**)
2. How to create routes (**10 minutes**)
3. How to customize agents (**15 minutes**)
4. How to validate before use (**5 minutes**)
5. How to troubleshoot (**10 minutes**)
6. Advanced patterns (**20 minutes**)

### Why This Matters

- ⏱️ **Save 52 minutes per agent** - 10 agents/week = 8.7 hours saved
- 🎯 **Help customers faster** - From weeks to days
- ✅ **Prevent errors** - Validation catches issues before deployment
- 📦 **Reuse solutions** - Battle-tested implementations
- 👥 **Scale quickly** - 23 agents ready to use

---

## MODULE 2: DISCOVERING AGENTS (30 minutes)

### The Agent Catalog

SAFE includes 23 pre-built agents covering common customer needs:

- **12 Standalone Agents** - Reusable across all patterns
- **11 Pattern Agents** - Optimized for specific design patterns

### Discovering Agents: Step by Step

**Step 1: List All Agents**

```bash
python -m safe_cli.cli list-agents
```

Shows all 23 agents with:
- Agent name
- Category (generation, retrieval, processing)
- Complexity (simple, intermediate, advanced)
- Quality rating (1-5 stars)
- Usage count (how many routes use it)

**What You'll See:**
```
┌──────────────────────────────────────────┐
│ ID                │ Name                │ Category      │ Rating  │
├──────────────────────────────────────────┤
│ document-writer   │ Document Writer     │ generation    │ ⭐⭐⭐⭐⭐ 4.8 │
│ rag-query         │ RAG Query Agent     │ retrieval     │ ⭐⭐⭐⭐⭐ 4.9 │
│ reviewer          │ Document Reviewer   │ processing    │ ⭐⭐⭐⭐ 4.7  │
└──────────────────────────────────────────┘
```

**Step 2: Filter by Category**

```bash
# Show only document generation agents
python -m safe_cli.cli list-agents --category generation

# Show only retrieval agents
python -m safe_cli.cli list-agents --category retrieval

# Show agents suitable for patterns
python -m safe_cli.cli list-agents --pattern supervisor-manager
```

**Step 3: Search for Specific Agents**

```bash
# Find all document-related agents
python -m safe_cli.cli search-agents document

# Find all agents for Q&A
python -m safe_cli.cli search-agents query

# Find agents for data transformation
python -m safe_cli.cli search-agents transform
```

### Understanding Agent Ratings

Each agent shows quality metrics:

- **⭐⭐⭐⭐⭐ 4.8-5.0** — Battle-tested, production-ready
- **⭐⭐⭐⭐ 4.5-4.7** — Reliable, well-documented
- **⭐⭐⭐ 4.0-4.4** — Solid, commonly used
- **⭐⭐ Below 4.0** — Use with caution, limited adoption

### Hands-On: Discover Agents

Try these commands:

```bash
# 1. List all agents
python -m safe_cli.cli list-agents

# 2. Count total agents
python -m safe_cli.cli agent-stats

# 3. Find document agents
python -m safe_cli.cli search-agents document

# 4. Show document-writer details
python -m safe_cli.cli show-agent document-writer
```

**Expected Results:**
- Should see 23 total agents
- Search returns 3+ document agents
- document-writer shows 4.8⭐ rating

---

## MODULE 3: CREATING ROUTES (45 minutes)

### What is a Route?

A **route** combines multiple agents following a pattern:

- **Input** → Agent 1 → Agent 2 → Agent 3 → **Output**
- Example: Supervisor decides routing → Specialists analyze → Aggregator combines results

### The Supervisor-Manager Pattern

Most common pattern for customer routing decisions:

```
Application Input
    ↓
Supervisor (Decides routing)
    ↓
    ├→ Specialist 1 (Analyzes)
    ├→ Specialist 2 (Reviews)
    └→ Specialist 3 (Evaluates)
    ↓
Aggregator (Combines decisions)
    ↓
Final Decision Output
```

### Creating Your First Route

**Step 1: Start Interactive Route Creation**

```bash
python -m safe_cli.cli create-route-interactive --pattern supervisor-manager
```

**Step 2: Select Supervisor Agent**

The CLI shows:
```
Select agent for placeholder: supervisor

Recommended agents:
1. Supervisor Router ✅ (Recommended for this pattern)
2. Loan Supervisor Router (Alternative)
3. Smart Router (Custom)

→ Select [1-3]: 1
```

**Best Practices for Supervisor Selection:**
- Choose agents marked as "Recommended" first
- Select highest-rated agents (4.8+⭐)
- Match to your domain (loan routing → Loan Supervisor Router)

**Step 3: Select Aggregator Agent**

```
Select agent for placeholder: aggregator

Recommended agents:
1. Decision Aggregator ✅ (Recommended)
2. Result Combiner (Alternative)

→ Select [1-3]: 1
```

**Step 4: Name Your Route**

```
Route name: loan-approval-v1
```

Route created!

### Validating Your Route

```bash
# Before using, validate that agents work together
python -m safe_cli.cli validate-agent \
  --agent agents/supervisor-router \
  --pattern supervisor-manager \
  --placeholder supervisor
```

✅ Should show: "Agent is compatible"

### Common Patterns

| Pattern | Use Case | Effort |
|---------|----------|--------|
| Supervisor-Manager | Routing decisions | 10 min |
| Fan-Out/Fan-In | Parallel processing | 15 min |
| Map-Reduce | Large data transformation | 20 min |
| Sequential-Pipeline | Step-by-step processing | 12 min |

### Hands-On: Create a Route

```bash
# Create supervisor-manager route
python -m safe_cli.cli create-route-interactive --pattern supervisor-manager

# Follow prompts:
# - Select: Supervisor Router
# - Select: Decision Aggregator
# - Name: test-route-v1

# Verify creation
python -m safe_cli.cli show-agent supervisor-router
python -m safe_cli.cli show-agent aggregator
```

---

## MODULE 4: CUSTOMIZING AGENTS (30 minutes)

### When to Customize

Customize agents when:
- ✅ Customer needs specific logic
- ✅ Adding company-specific rules
- ✅ Integrating with internal systems
- ✅ Using domain-specific language

Don't customize when:
- ❌ Standard use case fits perfectly
- ❌ Just trying template agent
- ❌ Prototype/POC phase

### How to Customize

**Step 1: Copy Agent Template**

```bash
python -m safe_cli.cli create-agent --from-template document-writer
```

Creates: `projects/agents/document-writer/`

**Step 2: Edit Files**

Navigate to your agent directory:

```
agents/document-writer/
├── agent.yaml          ← Edit contract and metadata
├── agent.md            ← Edit documentation
├── prompt.txt          ← Edit system instructions
└── requirements.txt    ← Add dependencies
```

**Step 3: Modify agent.yaml**

```yaml
# Change the description
description: |
  Generates Word documents for our specific
  company reporting format with custom branding
  and legal footers.

# Add company-specific requirements
metadata:
  company_specific:
    branding: corporate-logo.png
    footer_legal: "© 2026 Acme Corp"
    template: company-template.docx
```

**Step 4: Modify prompt.txt**

Add company-specific instructions:

```
You are the Document Writer for Acme Corp.

Company-specific requirements:
1. Include Acme Corp header on all pages
2. Add legal footer with copyright notice
3. Use Acme blue color scheme (RGB: 0, 51, 102)
4. Include company logo on title page

Format rules:
- Font: Calibri, size 11
- Margins: 1 inch all sides
- Line spacing: 1.15
```

**Step 5: Test Customizations**

```bash
# Validate the modified agent
python -m safe_cli.cli validate-agent \
  --agent agents/document-writer \
  --pattern sequential-pipeline \
  --placeholder presenter

# Check with CLI
python -m safe_cli.cli show-agent document-writer
```

### Customization Examples

**Example 1: Loan Routing Supervisor**

Original: Generic supervisor  
Customized: 
```yaml
description: Routes loan applications based on:
- Loan amount (mortgage vs auto vs personal)
- Credit score brackets
- Employment status
- Company risk policies
```

**Example 2: Company Data Reviewer**

Original: Generic document reviewer  
Customized:
```yaml
description: Reviews documents for:
- Company compliance requirements
- Legal liability concerns
- Data privacy rules
- Internal naming standards
```

### Hands-On: Customize an Agent

```bash
# 1. Create agent from template
python -m safe_cli.cli create-agent --from-template document-writer

# 2. Edit the agent.yaml
# - Change name to "Acme Document Writer"
# - Add description of customization
# - Add company-specific metadata

# 3. Edit prompt.txt
# - Add company branding instructions
# - Add specific formatting rules

# 4. Validate
python -m safe_cli.cli validate-agent \
  --agent agents/document-writer \
  --pattern sequential-pipeline \
  --placeholder presenter

# 5. Verify
python -m safe_cli.cli show-agent document-writer
```

---

## MODULE 5: VALIDATION & ERROR HANDLING (25 minutes)

### Why Validation Matters

**Without validation:**
- Routes fail at runtime
- Agents output wrong format
- Hours wasted debugging

**With validation:**
- Errors caught before deployment
- Clear error messages
- Prevents customer issues

### Validation Checklist

Before deploying any route, validate:

```bash
# 1. Agent contract matches pattern
python -m safe_cli.cli validate-agent \
  --agent agents/supervisor-router \
  --pattern supervisor-manager \
  --placeholder supervisor

# 2. All required fields present
# ✅ Check: Agent has routing_decision output
# ✅ Check: Output includes all required fields

# 3. Dependencies installable
pip install -r agents/supervisor-router/requirements.txt

# 4. Configuration correct
# ✅ Timeout < 120 seconds
# ✅ Dependencies < 20 packages
# ✅ No circular dependencies
```

### Common Errors & Solutions

**Error: "Agent missing required output 'routing_decision'"**

Solution:
```bash
# Check agent.yaml outputs
grep -A5 "outputs:" agents/my-agent/agent.yaml

# Should include:
# - name: routing_decision
#   type: object
```

**Error: "Dependency installation failed"**

Solution:
```bash
# Check requirements.txt
cat agents/my-agent/requirements.txt

# Install manually
pip install python-docx pandas jinja2

# Update requirements.txt with working versions
```

**Error: "Timeout exceeded (120s)"**

Solution:
```yaml
# In agent.yaml, optimize timeout
metadata:
  timeout_seconds: 180  # Increase if needed

# Or optimize the agent logic
# - Remove unnecessary processing
# - Cache results
# - Reduce dependencies
```

### Hands-On: Validate Route

```bash
# Create a test route
python -m safe_cli.cli create-route-interactive --pattern supervisor-manager

# Validate supervisor agent
python -m safe_cli.cli validate-agent \
  --agent agents/supervisor-router \
  --pattern supervisor-manager \
  --placeholder supervisor

# Validate aggregator agent
python -m safe_cli.cli validate-agent \
  --agent agents/decision-aggregator \
  --pattern supervisor-manager \
  --placeholder aggregator

# Both should show: ✅ Agent is compatible
```

---

## MODULE 6: TROUBLESHOOTING (20 minutes)

### Quick Troubleshooting Guide

**Problem: Agent not found**

```bash
# List all agents
python -m safe_cli.cli list-agents

# Search for agent
python -m safe_cli.cli search-agents document

# Check agent directory exists
ls agents/document-writer/agent.yaml
```

**Problem: CLI command not recognized**

```bash
# Ensure CLI is installed
pip install -e .

# Check PYTHONPATH
export PYTHONPATH=.:$PYTHONPATH

# Try running directly
python -m safe_cli.agent_commands list-agents
```

**Problem: Contract validation failing**

```bash
# Check contract syntax
python -c "
import yaml
with open('agents/my-agent/agent.yaml') as f:
    agent = yaml.safe_load(f)
    print('Contract:', agent.get('contract'))
"

# Ensure all required fields present
# - inputs (array)
# - outputs (array)
```

**Problem: Dependencies not installing**

```bash
# Try upgrading pip
pip install --upgrade pip

# Install dependencies manually
pip install python-docx pandas jinja2

# Check Python version >= 3.11
python --version
```

**Problem: Agent works locally but fails in route**

```bash
# Validate in pattern context
python -m safe_cli.cli validate-agent \
  --agent agents/my-agent \
  --pattern supervisor-manager \
  --placeholder supervisor

# Check error messages for incompatibilities
```

### Getting Help

**For CLI issues:**
```bash
python -m safe_cli.cli --help
python -m safe_cli.cli list-agents --help
```

**For agent issues:**
- Check `agent.md` documentation
- Review `prompt.txt` for instructions
- Check `requirements.txt` for dependencies

**For pattern issues:**
- Review pattern documentation in SAFE Framework
- Check APPENDIX_C for pattern specifications
- Validate agent contracts match pattern

---

## MODULE 7: ADVANCED PATTERNS (30 minutes)

### Fan-Out / Fan-In Pattern

**Use Case:** Process data in parallel

```
Input Data
    ↓
Processor (splits data)
    ↓
    ├→ Worker 1 (parallel)
    ├→ Worker 2 (parallel)
    └→ Worker 3 (parallel)
    ↓
Aggregator (combines results)
    ↓
Combined Output
```

**Example:** Processing 1000 documents
- Processor: Split into 100-document chunks
- Workers: Process chunks in parallel
- Aggregator: Combine results

**To Create:**
```bash
python -m safe_cli.cli create-route-interactive --pattern fan-out-fan-in

# Select:
# - Processor: Document Processor
# - Worker: Parallel Worker (x3)
# - Aggregator: Fan-In Aggregator
```

### Map-Reduce Pattern

**Use Case:** Transform large datasets

```
Data
  ↓
Splitter (divide)
  ↓
Mappers (transform, parallel)
  ↓
Shuffle (reorganize)
  ↓
Reducers (aggregate, parallel)
  ↓
Final (combine)
  ↓
Result
```

**Example:** Analyzing customer transactions
1. Splitter: Split 10M transactions by date
2. Mapper: Extract patterns per day
3. Shuffle: Group by pattern
4. Reducer: Aggregate per pattern
5. Final: Create summary

### Sequential Pipeline Pattern

**Use Case:** Step-by-step transformation

```
Input
  ↓
Stage 1 (preprocess)
  ↓
Stage 2 (analyze)
  ↓
Stage 3 (format)
  ↓
Output
```

**Example:** Report generation
1. Stage 1: Collect data
2. Stage 2: Analyze and calculate
3. Stage 3: Format as document

---

## MODULE 8: BEST PRACTICES (20 minutes)

### Do's ✅

- ✅ **Use pre-built agents first** — They're tested and documented
- ✅ **Validate before deployment** — Catch errors early
- ✅ **Document customizations** — Help future maintainers
- ✅ **Follow naming conventions** — Keep routes organized
- ✅ **Test with sample data** — Verify before going live
- ✅ **Monitor agent performance** — Track execution time
- ✅ **Update dependencies** — Keep security current

### Don'ts ❌

- ❌ **Don't skip validation** — It exists for a reason
- ❌ **Don't customize unnecessarily** — Use templates as-is when possible
- ❌ **Don't modify agent contracts** — Breaks pattern compatibility
- ❌ **Don't ignore error messages** — They're helpful!
- ❌ **Don't deploy untested changes** — Always validate first
- ❌ **Don't mix patterns** — Stick to one per route

### Performance Tips

1. **Use agents with 4.8+ rating** — Battle-tested, optimized
2. **Keep timeout reasonable** — Most agents complete in <60 seconds
3. **Minimize dependencies** — Each adds overhead
4. **Cache when possible** — Reuse results within route
5. **Monitor execution** — Track which agents are slow

### Customer Communication

**When introducing SAFE:**

> "We can now implement AI agents 3x faster using tested templates. This means we get your solution live in days instead of weeks, and with higher quality and fewer errors."

**When explaining route architecture:**

> "Your route uses a supervisor-manager pattern: a smart router decides which specialist analyzes your data, then an aggregator combines their results into your final decision."

**When customizing agents:**

> "We're customizing the standard agent with your company-specific logic. This preserves the reliability of the base implementation while adding your unique requirements."

---

## MODULE 9: HANDS-ON LAB (60 minutes)

### Lab Scenario: Loan Application Processor

**Your Task:** Build a complete loan routing system using SAFE

**Step 1: Discover the Route (10 min)**

```bash
# List available agents
python -m safe_cli.cli list-agents --category decision

# Search for loan-related agents
python -m safe_cli.cli search-agents loan

# Show supervisor details
python -m safe_cli.cli show-agent supervisor-router
```

**Step 2: Create the Route (15 min)**

```bash
# Create supervisor-manager route
python -m safe_cli.cli create-route-interactive --pattern supervisor-manager

# Follow prompts:
# Pattern: supervisor-manager
# Supervisor: Loan Supervisor Router
# Aggregator: Decision Aggregator  
# Name: loan-processor-v1
```

**Step 3: Customize Agents (20 min)**

```bash
# Create custom supervisor
python -m safe_cli.cli create-agent --from-template supervisor-router

# Edit agent.yaml with loan-specific rules:
# - Route by loan type (mortgage, auto, personal)
# - Route by credit score
# - Route by loan amount

# Edit prompt.txt with:
# - Company loan policies
# - Risk thresholds
# - Routing rules
```

**Step 4: Validate Route (10 min)**

```bash
# Validate supervisor
python -m safe_cli.cli validate-agent \
  --agent agents/loan-supervisor \
  --pattern supervisor-manager \
  --placeholder supervisor

# Validate aggregator
python -m safe_cli.cli validate-agent \
  --agent agents/decision-aggregator \
  --pattern supervisor-manager \
  --placeholder aggregator

# Both should show ✅ compatible
```

**Step 5: Test with Sample Data (5 min)**

```bash
# Test supervisor with sample loan application
python -c "
import json

test_input = {
    'application': {
        'loan_type': 'mortgage',
        'amount': 350000,
        'credit_score': 780,
        'employment_status': 'employed'
    }
}

print('Testing with:', json.dumps(test_input, indent=2))
# Would run agent here with actual implementation
"
```

**Expected Results:**
- ✅ Route created successfully
- ✅ Agents validated
- ✅ Custom logic added
- ✅ Ready for deployment

---

## SUMMARY

You now know how to:

| Skill | Time | Where |
|-------|------|-------|
| Discover agents | 2 min | Module 2 |
| Create routes | 10 min | Module 3 |
| Customize agents | 15 min | Module 4 |
| Validate | 5 min | Module 5 |
| Troubleshoot | varies | Module 6 |
| Use advanced patterns | 30 min | Module 7 |

---

## NEXT STEPS

1. **Complete the lab** - Loan processor example
2. **Build your first customer route** - Use template agents
3. **Customize for your domain** - Add company-specific logic
4. **Validate and deploy** - To production
5. **Monitor performance** - Track metrics

---

## RESOURCES

- **Documentation:** APPENDIX_C_AGENT_TEMPLATE_ARCHITECTURE.md
- **Implementation Guide:** PHASE_1_IMPLEMENTATION_GUIDE.md
- **Agent Catalog:** CATALOG.yaml
- **CLI Help:** `python -m safe_cli.cli --help`

---

**Training Complete!**

You're ready to help customers implement AI agents in days instead of weeks.

**Questions?** Refer to the troubleshooting module or contact the SAFE team.

---

**Training Version:** 1.0  
**Duration:** ~3 hours (self-paced)  
**Completion Date:** ________  
**Trainer Name:** ____________
