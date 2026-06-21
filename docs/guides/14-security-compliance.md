# Guide: Security and Compliance

---

## Input Validation

SAFE Framework validates all agent inputs against their declared contracts before execution:

```python
from safe_framework.safe_core.security.validator import SecurityValidator

validator = SecurityValidator()

# Validate against agent contract
errors = validator.validate_input(
    agent_name="rag-query",
    payload={"query": user_input},
)
if errors:
    raise ValueError(f"Input validation failed: {errors}")
```

### What Is Validated

| Check | Description |
|---|---|
| Schema compliance | Input matches agent.yaml `contract.inputs` types |
| Required fields | All `required: true` fields are present |
| String length limits | Prevents prompt injection via oversized inputs |
| Injection patterns | Blocks common prompt injection strings |
| PII detection | Warns if PII detected in inputs to external tools |

---

## Data Residency

Configure region constraints in `catalog.yaml`:

```yaml
# Restrict iq-foundry to EU regions only
tools:
  - id: iq-foundry
    config:
      allowed_regions: ["westeurope", "northeurope"]
      data_residency: "EU"
```

---

## Managed Identity (Recommended)

Always use Managed Identity in production — no secrets in code or environment:

```python
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential

# Development: uses DefaultAzureCredential (falls back to az login)
credential = DefaultAzureCredential()

# Production (AKS/App Service with system-assigned MI)
credential = ManagedIdentityCredential()

# Production (user-assigned MI)
credential = ManagedIdentityCredential(client_id=os.environ["AZURE_CLIENT_ID"])
```

---

## Secrets Management

Never store secrets in `catalog.yaml` or `agent.yaml`. Use Azure Key Vault:

```python
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

kv_client = SecretClient(
    vault_url=os.environ["KEY_VAULT_URL"],
    credential=DefaultAzureCredential(),
)

# Retrieve at startup, not hardcoded
durable_key = kv_client.get_secret("durable-task-key").value
os.environ["DURABLE_TASK_KEY"] = durable_key
```

---

## Network Security

| Recommendation | Implementation |
|---|---|
| Private endpoints | Deploy AI Foundry, Cosmos DB, AI Search with private endpoints |
| VNet integration | Run agents in a VNet-integrated App Service or AKS |
| Outbound filtering | Use Azure Firewall to restrict outbound from agent workers |
| No public AI Search | Disable public network access on AI Search; use private link |

---

## Content Filtering

Azure AI Foundry has built-in content filters. Configure per-deployment:

```bash
az cognitiveservices account deployment update \
  --name <foundry-workspace> \
  --resource-group <rg> \
  --deployment-name gpt-4o \
  --content-filter-policy strict
```

SAFE Framework agents also validate LLM output before passing to the next step:

```python
from safe_framework.safe_core.security.validator import SecurityValidator

output_errors = SecurityValidator().validate_output(
    agent_name="rag-generator",
    output=llm_response,
)
if output_errors:
    logger.warning(f"Output validation issues: {output_errors}")
```

---

## GDPR / Data Handling

For agents processing personal data:

1. Add `"pii"` tag to the route definition
2. The governance policy engine will enforce data-handling-approved requirement
3. Use `purview-security-summary` tool in gate-guard to check asset sensitivity
4. Log all PII-touching operations in the audit trail
5. Implement data minimisation in agent prompts (don't pass full records when summary suffices)

```yaml
# In route definition
tags:
  - pii
  - data-handling-approved   # Only after compliance review
```
