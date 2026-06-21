# Guide: Governance and Audit

---

## Approval Workflows

```python
from safe_framework.safe_core.governance.approval_engine import ApprovalEngine
from safe_framework.safe_core.governance.models import ApprovalRequest, Policy

engine = ApprovalEngine()

# Register a policy
engine.register_policy(Policy(
    name="finance-data",
    applies_to_tags=["finance", "payroll"],
    required_approvers=["cfo@company.com"],
    approval_mode="any",
    auto_approve_if_cost_below=0.10,
))

# Submit for approval
request = ApprovalRequest(
    route_name="payroll-analysis",
    requested_by="engineer@company.com",
    route_definition=my_route,
)
status = await engine.submit(request)
```

---

## Policy YAML

```yaml
# safe_framework/safe_core/governance/policies.yaml
policies:
  - name: cost-guard
    rule: estimated_cost_usd > 5.0
    action: require_approval
    approvers: ["finance@company.com"]

  - name: pii-protection
    rule: tags contains "pii" and not tags contains "data-handling-approved"
    action: block
    message: "PII routes require data protection review"

  - name: external-audit
    rule: tools contains "iq-web"
    action: audit
    audit_level: detailed
```

---

## Audit Trail

```python
from safe_framework.safe_core.audit.logger import AuditLogger, AuditEventType

audit = AuditLogger()

# Write custom event
await audit.log(
    event_type=AuditEventType.ROUTE_CREATED,
    route_name="contract-review",
    actor="engineer@company.com",
    metadata={"pattern": "evaluator-optimizer"},
)

# Query
events = await audit.query(
    route_name="contract-review",
    event_types=[AuditEventType.ROUTE_EXECUTED],
    from_date="2026-01-01",
)
```

### Audit Event Types

| Event | Trigger |
|---|---|
| `route-created` | Route definition registered |
| `approval-requested` | Route submitted for approval |
| `route-executed` | Route invocation started |
| `cost-threshold-exceeded` | Run cost over budget |
| `health-alert-generated` | Health check failed |
| `policy-blocked` | Route blocked by policy |
| `human-approval-granted` | Human gate approved |
| `human-approval-rejected` | Human gate rejected |

---

## Release Management

```python
from safe_framework.safe_core.release.manager import ReleaseManager

rm = ReleaseManager()

# Promote a route from staging to production
await rm.promote(
    route_name="contract-review",
    from_env="staging",
    to_env="production",
    approver="lead-engineer@company.com",
)
```

---

## Cost Budget Controls

```python
from safe_framework.tools.mcp.token_metrics_mcp import token_metrics_get_budget

# Check remaining budget before invoking expensive routes
budget = await token_metrics_get_budget(budget_id="legal-team-monthly")
if budget["remaining_usd"] < 1.00:
    raise BudgetExceededError("Monthly budget nearly exhausted — contact finance")
```

Set budget alerts in `safe_framework/safe_core/catalog.yaml`:

```yaml
budgets:
  - id: legal-team-monthly
    limit_usd: 500.00
    alert_threshold_pct: 80
    alert_email: finance@company.com
    reset_period: monthly
```
