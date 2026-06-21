# SAFE Phase 4: Route Writer Agent - Detailed Specification

**Interactive CLI for Route Creation & Code Generation**

**Weeks:** 4-5  
**Effort:** 10 engineer-days  
**Status:** Specification

---

## OVERVIEW

The Route Writer Agent is an interactive CLI that interviews a CSA and generates production-ready route orchestration code.

**User Journey:**
```
CSA: safe route create
  ↓
Route Writer: "What pattern?" → supervisor-manager
  ↓
Route Writer: "Supervisor agent?" → loan-supervisor-router
  ↓
Route Writer: "Specialist agents?" → [specialist-mortgage, specialist-auto, specialist-personal]
  ↓
Route Writer: "Timeout?" → 120 seconds
  ↓
Route Writer: ✓ Validating contracts...
  ↓
Route Writer: ✓ Generating code...
  ↓
Route Writer: ✓ Testing route...
  ↓
Route Writer: ✓ Route created: /routes/loan-approval-v1/
  ↓
CSA: "Ready to deploy?"
```

---

## REQUIREMENTS

### Functional Requirements

| ID | Requirement | Acceptance Criteria |
|----|-------------|-------------------|
| R1 | Interactive interview loop | CSA can answer 5-8 questions, go back to previous answers |
| R2 | Pattern selection | CSA can choose from 4 patterns (supervisor, fan-out, map-reduce, sequential) |
| R3 | Agent selection | CSA can select agents from catalog using name search + recommendations |
| R4 | Contract validation | All selected agents validated for compatibility |
| R5 | Code generation | Python code generated from Jinja2 templates |
| R6 | Test generation | Sample test data created from input schema |
| R7 | Route testing | Generated route tested with sample data before saving |
| R8 | Version management | Route saved as v1.0 with metadata |
| R9 | Error recovery | CSA can go back and change answers if validation fails |
| R10 | Dry-run mode | CSA can preview generated code without saving |

### Non-Functional Requirements

| ID | Requirement | Acceptance Criteria |
|----|-------------|-------------------|
| NF1 | Interview time | Complete in <15 minutes |
| NF2 | Code generation time | <30 seconds |
| NF3 | Test execution time | <10 seconds |
| NF4 | UX responsiveness | All interactions <200ms |
| NF5 | Code quality | Generated Python passes linting (Black, pylint) |
| NF6 | Error messages | Clear, actionable, suggest remediation |

---

## DETAILED INTERVIEW FLOW

### Step 1: Pattern Selection (1-2 min)

**Question:**
```
What pattern do you need?

1. Supervisor-Manager
   └─ Route incoming requests to different specialists
   └─ Use when: loan type → mortgage/auto/personal specialist

2. Fan-Out/Fan-In
   └─ Process requests in parallel
   └─ Use when: get data from multiple sources, combine results

3. Map-Reduce
   └─ Transform/aggregate large datasets
   └─ Use when: process list of items independently, combine results

4. Sequential-Pipeline
   └─ Step-by-step processing
   └─ Use when: data flow through stages (extract → clean → enrich)

Choose (1-4): _
```

**What happens:**
- Load pattern definition
- Validate pattern is available
- Show agents relevant to pattern
- Proceed to agent selection

**Error handling:**
```
You chose: 5
Error: Invalid choice. Please enter 1-4.
```

---

### Step 2: Agent Selection (3-5 min)

**For Supervisor-Manager pattern:**

```
You selected: Supervisor-Manager

Step 1/3: Select SUPERVISOR agent
(Routes incoming requests to specialists)

Recommended agents:
  ⭐⭐⭐⭐⭐ loan-supervisor-router    [Exactly matches pattern]
  ⭐⭐⭐⭐   generic-supervisor         [Similar, less specialized]
  ⭐⭐⭐     custom-router              [Generic option]

Search agents (or Enter for recommendation): _
```

**Search behavior:**
- Type name to filter
- Show recommendations (ML-scored for pattern)
- Show agent ratings (from Phase 3 agent library)
- Show example usage

**Then ask for specialist agents:**

```
Step 2/3: Select SPECIALIST agents
(These handle specific request types)

Pattern requires specialists for:
  - Mortgage loans
  - Auto loans
  - Personal loans

Mortgage specialist (recommended: loan-specialist-mortgage):
Search: _

Auto specialist (recommended: loan-specialist-auto):
Search: _

Personal specialist (recommended: loan-specialist-personal):
Search: _
```

**Then ask for aggregator:**

```
Step 3/3: Select AGGREGATOR agent
(Combines decisions from specialists)

Recommended agents:
  ⭐⭐⭐⭐⭐ standard-aggregator  [Combines decisions, returns JSON]
  ⭐⭐⭐     custom-merger        [Custom combining logic]

Search agents (or Enter for recommendation): _
```

---

### Step 3: Configure Logic (2-3 min)

**Question:**
```
How should the SUPERVISOR route requests?

Based on which field?
  1. loan_type (recommended, used by supervisor)
  2. amount
  3. credit_score
  4. other (specify)

Choose (1-4): 1

Mapping:
  When loan_type = "mortgage" → specialist-mortgage
  When loan_type = "auto" → specialist-auto
  When loan_type = "personal" → specialist-personal
  Otherwise → error

Is this correct? (y/n): _
```

**Logic customization:**
- For Supervisor-Manager: routing field + mapping
- For Fan-Out/Fan-In: which agents run in parallel
- For Map-Reduce: splitting logic + reducing logic
- For Sequential: step order + error handling

---

### Step 4: Configure Timeouts (1-2 min)

**Question:**
```
Timeout settings:

Total route timeout (seconds, default 120): _
Per-agent timeout (seconds, default 60): _

Note:
  - Total must be >= sum of per-agent timeouts
  - Agent timeouts: specialist-mortgage=45s, specialist-auto=40s, ...
  - Remaining time for aggregation: 35s
  ✓ Configuration valid

Is this correct? (y/n): _
```

---

### Step 5: Name & Documentation (1 min)

**Question:**
```
Route name (lowercase, hyphens, no spaces):
Default: loan-approval-v1
Enter or accept: _

Route description (optional):
Default: (none)
Enter: _

CSA email (for audit trail):
Default: (current user)
Enter: _
```

---

### Step 6: Validation (Automatic, <1 min)

```
✓ Validating contracts...
  ✓ Supervisor output matches specialist inputs
  ✓ specialist-mortgage output matches aggregator input
  ✓ specialist-auto output matches aggregator input
  ✓ specialist-personal output matches aggregator input
  ✓ All agents can execute within timeout

✓ All validations passed!
```

**If validation fails:**
```
✗ Validation failed:

Error: specialist-mortgage output has {recommendation, score}
       but aggregator expects {recommendation, score, confidence}

Solution: 
  1. Update specialist-mortgage prompt to include confidence
  2. Update specialist-mortgage contract in CATALOG.yaml
  3. Or use different specialist

Would you like to:
  1. Select different specialist
  2. Go back and change timeouts
  3. Cancel and retry later

Choose (1-3): _
```

---

### Step 7: Code Generation (Automatic, <30 sec)

```
✓ Generating route code...
  ✓ Loading templates...
  ✓ Rendering supervisor-manager.jinja2...
  ✓ Rendering requirements.txt...
  ✓ Creating /routes/loan-approval-v1/

Generated files:
  - route.py        (156 lines)
  - requirements.txt (8 packages)
  - config.yaml     (metadata)
  - test_data.json  (sample inputs)
```

---

### Step 8: Testing (Automatic, <10 sec)

```
✓ Testing route with sample data...
  ✓ Loading sample inputs from CATALOG
  ✓ Running route on 5 test cases
  ✓ Validating outputs against schema

Test results:
  Case 1: mortgage loan ($250k) → ✓ approved
  Case 2: auto loan ($30k) → ✓ approved
  Case 3: personal loan ($10k) → ✓ approved
  Case 4: low credit score → ✓ rejected
  Case 5: edge case (boundary) → ✓ passed

✓ All tests passed!
```

**If tests fail:**
```
✗ Test case 3 failed:

Input: personal_loan_with_low_income
Expected output: {decision: "rejected", reason: "low_income"}
Actual output: {decision: "approved", reason: "income_verified"}

Possible causes:
  1. Agent logic doesn't match business rules
  2. Sample data doesn't match real scenarios
  3. Agent threshold too low

Suggestions:
  1. Review agent prompt: specialist-personal
  2. Adjust thresholds in agent prompt
  3. Select different specialist agent

Would you like to:
  1. Select different specialist
  2. Preview generated route.py and fix manually
  3. Cancel and retry

Choose (1-3): _
```

---

### Step 9: Completion

```
✓ Route created successfully!

Route: loan-approval-v1
Location: /routes/loan-approval-v1/
Version: v1.0
Pattern: supervisor-manager
Agents: supervisor, specialist-mortgage, specialist-auto, specialist-personal, aggregator
Status: ready (pending approval)

Next steps:
  1. Review generated code:
     safe route show loan-approval-v1

  2. Test with real data (optional):
     python routes/loan-approval-v1/route.py < test_input.json

  3. Deploy route:
     safe route deploy loan-approval-v1

  4. Monitor route health:
     safe route health loan-approval-v1

Need help? Run: safe route help
```

---

## GENERATED ROUTE CODE

### Example Output: Supervisor-Manager

```python
# /routes/loan-approval-v1/v1.0/route.py
# AUTO-GENERATED by SAFE Route Writer Agent
# DO NOT EDIT MANUALLY - make changes via: safe route update loan-approval-v1

from datetime import datetime
from typing import Dict, Any
import logging
from maf import HostedAgent, AgentContext
from semantic_kernel import Kernel
from safe.agents import (
    LoanSupervisorRouter,
    LoanSpecialistMortgage,
    LoanSpecialistAuto,
    LoanSpecialistPersonal,
    StandardAggregator
)

logger = logging.getLogger(__name__)

class LoanApprovalV1Route(HostedAgent):
    """
    Loan Approval Route v1.0
    
    Pattern: Supervisor-Manager
    Agents: 
      - Supervisor: LoanSupervisorRouter
      - Mortgage: LoanSpecialistMortgage
      - Auto: LoanSpecialistAuto
      - Personal: LoanSpecialistPersonal
      - Aggregator: StandardAggregator
    
    Created: 2026-06-20
    Created by: bea@microsoft.com
    """
    
    def __init__(self, kernel: Kernel):
        super().__init__("loan-approval-v1")
        self.kernel = kernel
        
        # Initialize agents
        self.supervisor = LoanSupervisorRouter(kernel)
        self.specialist_mortgage = LoanSpecialistMortgage(kernel)
        self.specialist_auto = LoanSpecialistAuto(kernel)
        self.specialist_personal = LoanSpecialistPersonal(kernel)
        self.aggregator = StandardAggregator(kernel)
    
    async def invoke(self, context: AgentContext) -> Dict[str, Any]:
        """
        Execute loan approval workflow
        
        Input contract: {amount, loan_type, credit_score, employment_status}
        Output contract: {decision, reason, confidence, timeline}
        """
        
        start_time = datetime.now()
        
        try:
            # Validate input
            request = context.input
            await self._validate_input(request)
            
            logger.info(f"Processing loan application: {request.get('amount')} {request.get('loan_type')}")
            
            # Route to supervisor
            supervisor_output = await self.supervisor.invoke(context)
            loan_type = supervisor_output.get('loan_type')
            
            logger.debug(f"Supervisor routed to: {loan_type}")
            
            # Route to appropriate specialist
            if loan_type == 'mortgage':
                specialist_output = await self.specialist_mortgage.invoke(context)
            elif loan_type == 'auto':
                specialist_output = await self.specialist_auto.invoke(context)
            elif loan_type == 'personal':
                specialist_output = await self.specialist_personal.invoke(context)
            else:
                raise ValueError(f"Unknown loan type: {loan_type}")
            
            logger.debug(f"Specialist decision: {specialist_output.get('decision')}")
            
            # Aggregate results
            final_output = await self.aggregator.invoke(specialist_output)
            
            # Validate output
            await self._validate_output(final_output)
            
            # Log success
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"Route completed in {elapsed}s: {final_output.get('decision')}")
            
            return final_output
        
        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.error(f"Route failed in {elapsed}s: {str(e)}", exc_info=True)
            raise
    
    async def _validate_input(self, request: Dict[str, Any]) -> None:
        """Validate input against contract"""
        required_fields = ['amount', 'loan_type', 'credit_score']
        for field in required_fields:
            if field not in request:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate loan_type
        valid_types = ['mortgage', 'auto', 'personal']
        if request.get('loan_type') not in valid_types:
            raise ValueError(f"Invalid loan_type: {request.get('loan_type')}. Must be one of {valid_types}")
        
        # Validate amount
        amount = request.get('amount', 0)
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ValueError(f"Invalid amount: {amount}. Must be positive number")
    
    async def _validate_output(self, output: Dict[str, Any]) -> None:
        """Validate output against contract"""
        required_fields = ['decision', 'reason', 'confidence']
        for field in required_fields:
            if field not in output:
                raise ValueError(f"Missing required output field: {field}")
        
        # Validate decision
        valid_decisions = ['approved', 'rejected', 'review']
        if output.get('decision') not in valid_decisions:
            raise ValueError(f"Invalid decision: {output.get('decision')}")

# Entry point
if __name__ == "__main__":
    import json
    from safe.kernel import get_kernel
    
    # For testing: python route.py < test_data.json
    kernel = get_kernel()
    route = LoanApprovalV1Route(kernel)
    
    # Read test data from stdin
    test_input = json.loads(input())
    
    # Create fake context
    context = AgentContext(input=test_input)
    
    # Run route
    import asyncio
    result = asyncio.run(route.invoke(context))
    print(json.dumps(result, indent=2))
```

### Example: requirements.txt

```
# /routes/loan-approval-v1/v1.0/requirements.txt
semantic-kernel>=0.4.0
azure-ai>=1.0.0
pydantic>=2.0.0
python-dateutil>=2.8.0
```

### Example: config.yaml

```yaml
# /routes/loan-approval-v1/v1.0/config.yaml

name: loan-approval-v1
version: v1.0
pattern: supervisor-manager
description: Loan approval with routing to specialists

agents:
  supervisor: loan-supervisor-router
  specialists:
    - loan-specialist-mortgage
    - loan-specialist-auto
    - loan-specialist-personal
  aggregator: standard-aggregator

timeouts:
  total_seconds: 120
  per_agent_seconds: 60

input_schema:
  type: object
  required: [amount, loan_type, credit_score]
  properties:
    amount:
      type: number
      minimum: 1000
      maximum: 5000000
    loan_type:
      type: string
      enum: [mortgage, auto, personal]
    credit_score:
      type: integer
      minimum: 300
      maximum: 850

output_schema:
  type: object
  required: [decision, reason, confidence]
  properties:
    decision:
      type: string
      enum: [approved, rejected, review]
    reason:
      type: string
    confidence:
      type: number
      minimum: 0
      maximum: 1

metadata:
  created_by: bea@microsoft.com
  created_at: 2026-06-20T14:30:00Z
  last_modified: 2026-06-20T14:30:00Z
  tags: [loan, approval, financial-services]
```

### Example: test_data.json

```json
[
  {
    "name": "mortgage_approval",
    "input": {
      "amount": 350000,
      "loan_type": "mortgage",
      "credit_score": 750,
      "employment_status": "employed"
    },
    "expected": {
      "decision": "approved",
      "confidence_min": 0.8
    }
  },
  {
    "name": "auto_approval",
    "input": {
      "amount": 35000,
      "loan_type": "auto",
      "credit_score": 680,
      "employment_status": "employed"
    },
    "expected": {
      "decision": "approved",
      "confidence_min": 0.7
    }
  },
  {
    "name": "personal_rejection",
    "input": {
      "amount": 15000,
      "loan_type": "personal",
      "credit_score": 580,
      "employment_status": "unemployed"
    },
    "expected": {
      "decision": "rejected"
    }
  }
]
```

---

## CLI INTEGRATION

### Command: safe route create

```bash
safe route create [--pattern PATTERN] [--name NAME] [--dry-run]

Options:
  --pattern     Skip pattern selection (supervisor|fan-out|map-reduce|sequential)
  --name        Skip naming (provide route name)
  --dry-run     Preview generated code without saving
  --interactive Force interactive mode (default)
  --help        Show help
```

### Examples

```bash
# Interactive mode (full interview)
$ safe route create
...interview flow...

# Skip pattern selection
$ safe route create --pattern supervisor-manager
...ask for agents...

# Dry-run (preview without saving)
$ safe route create --dry-run
...interview...
✓ Generated code:
cat route.py
...print route code...
Continue? (y/n): n
Route not saved (--dry-run mode)

# Fully scripted (for automation)
$ safe route create --pattern supervisor-manager \
  --supervisor loan-supervisor \
  --specialist loan-specialist-a \
  --specialist loan-specialist-b \
  --name my-route
```

---

## ERROR HANDLING

### Contract Validation Errors

```
Error: Agent contract mismatch

Supervisor output: {loan_type, decision}
Specialist input requires: {loan_type, decision, confidence}

Solution: Specialist expects confidence field that supervisor doesn't provide

Options:
  1. Select different specialist (one that doesn't require confidence)
  2. Select different supervisor (one that provides confidence)
  3. Update supervisor prompt to include confidence field
  4. Update specialist contract to not require confidence

Choose option or go back: _
```

### Circular Dependency Errors

```
Error: Circular dependency detected

Agent A → Agent B → Agent C → Agent A

This would cause infinite loop. Agent sequences must be acyclic.

Solution: Reorder agents or remove one of the connections

Current sequence: supervisor → specialist-1 → specialist-2 → supervisor
Fixed sequence: supervisor → specialist-1 → specialist-2 → aggregator

Review and confirm: (y/n): _
```

### Timeout Errors

```
Error: Timeout configuration invalid

Total timeout: 120s
Agent timeouts: specialist-a=45s, specialist-b=50s, specialist-c=40s
Sum of agent timeouts: 135s > 120s total

Solution: Increase total timeout or reduce per-agent timeouts

Recommended: total=180s (sum of agent timeouts + 20% buffer)

Accept recommendation? (y/n): _
```

---

## TESTING

### Unit Tests

```python
# tests/test_route_writer_interview.py

class TestInterviewFlow:
    async def test_pattern_selection():
        """CSA can select pattern"""
        assert await select_pattern("supervisor-manager") == Pattern.SUPERVISOR
    
    async def test_agent_selection():
        """CSA can select agents"""
        agents = await select_agents(Pattern.SUPERVISOR)
        assert len(agents) >= 4  # supervisor + specialists + aggregator
    
    async def test_contract_validation():
        """Contracts validated before code generation"""
        agents = [supervisor, specialist_a, specialist_b, aggregator]
        errors = await validate_contracts(agents)
        assert len(errors) == 0
    
    async def test_code_generation():
        """Code generation produces valid Python"""
        code = await generate_route(agents)
        assert "class" in code
        assert "async def invoke" in code
        assert is_valid_python(code)
    
    async def test_interview_time():
        """Interview completes in <15 minutes"""
        start = time.time()
        await run_interview()
        elapsed = time.time() - start
        assert elapsed < 15 * 60

# tests/test_route_writer_edge_cases.py

class TestEdgeCases:
    async def test_long_agent_names():
        """Handles long agent names"""
        long_name = "a" * 255
        result = await select_agents_by_name(long_name)
        # Should handle gracefully
    
    async def test_special_characters_in_route_name():
        """Handles special characters"""
        names = ["my-route", "route_v2", "route.backup"]
        for name in names:
            route = await create_route(name=name)
            assert route.name == name
    
    async def test_large_timeout():
        """Handles large timeout values"""
        route = await create_route(timeout=3600)  # 1 hour
        assert route.timeout == 3600
    
    async def test_minimal_route():
        """Creates minimal valid route"""
        route = await create_route(
            pattern="sequential",
            agents=["agent-a", "agent-b"]
        )
        assert route is not None
```

---

**SAFE Phase 4: Route Writer Agent Specification**  
**Detailed Implementation Guide**  
**Weeks 4-5 | 10 Engineer-Days**

