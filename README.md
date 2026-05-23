
AI-Foundry/ 

Copilot-VSCode/ 

Copilot-GitHub/ 

Each root contains: 
an MCP JSON-RPC server (POST /mcp) implementing the standard MCP method shape (initialize, tools/list, tools/call, plus resources/* and prompts/*)  

a multi-agent swarm (planner + specialists + verifier) 

skills markdown files placed in the correct folders (skills/, agents/) 

a config/tools.yaml defining MCP tools and a prompts/ template for quick start 

✅ Download the ZIP

CSA_Agent_Swarm_MCP.zip 


What I built (and how it maps to your Foundry + Copilot pattern)

1) MCP server + tool dispatch (per root folder)

This follows the same conceptual architecture you already documented: Copilot UX → MCP → Foundry (Foundry as “brain”), where MCP exposes tools via JSON-RPC (tools/list, tools/call). 
2) CSA “agent swarm”

Each root includes a swarm runner that executes: 
Planner agent → produces a concise execution plan 

Specialists (scenario-specific) 

Verifier agent → checks gaps/mistakes + rewrites more concisely (your requested “best quality” verification loop) 

3) Model routing: strong mid-priced primary + best-quality verifier

In .env.example (inside each root folder), defaults are: 
PRIMARY_MODEL=gpt-5-mini (strong “mini” class as a cost/quality balance — model name appears in your Foundry debugging notes)  

VERIFIER_MODEL=gpt-4.1 (high capability model name appears in Foundry materials and labs)  


You can swap these to whatever deployments you actually have in your Foundry project; the code routes by role (primary vs verifier) rather than hardcoding one model. 



Folder-by-folder contents (exactly aligned to your request)

✅ AI-Foundry/

Focus: Azure AI Foundry features — models, agents, tools, evaluation, tracing/observability, publishing patterns. This aligns with the Foundry toolchain and “move intelligence into Foundry” pattern you’ve been capturing. 
Includes: 
docs/foundry-feature-map.md (CSA checklist) 

agents/foundry_specialist.md 

scenario foundry_feature_tour 

Also includes a Foundry SDK wrapper using the AIProjectClient → get_openai_client() → responses.create(...) call shape shown in Foundry SDK guidance. 


✅ Copilot-VSCode/

Focus: Copilot in VS Code + MCP 
examples/vscode/.vscode/mcp.json provided (correct location) 

docs/vscode-workshop.md runbook 

scenario copilot_vscode_workshop 

The config style and file location match VS Code’s MCP config reference (.vscode/mcp.json, servers key). 


✅ Copilot-GitHub/

Focus: Copilot in GitHub workflows 
examples/github/.github/copilot/mcp.json provided (correct location) 

.github/workflows/ci.yml for basic CI sanity checks 

docs/github-pr-swarm.md 

scenario copilot_github_pr_swarm 

This is designed for PR/Repo hygiene workflows (PR description, reviewer checklist, verification pass). 


How to run (quick)

Each root is self-contained. Example for AI-Foundry:
cd AI-Foundry<ctmzNwLn>python -m venv .venv && source .venv/bin/activate<ctmzNwLn>pip install -r requirements.txt<ctmzNwLn>cp .env.example .env<ctmzNwLn>python -m uvicorn AI_Foundry.server.app:app --host 127.0.0.1 --port 8001<ctmzNwLn>
Then call MCP: 
initialize 

tools/list 

tools/call → swarm.run 

Those method names and payload shapes follow MCP’s published tool calling spec. 


One important note (so you don’t get surprised)

This ZIP gives you a working scaffold that’s aligned to: 
your internal “Foundry + Copilot via MCP” approach  

the standard MCP message types for tools/resources/prompts  

the Foundry SDK’s AIProjectClient access pattern  

…but it does not assume any particular Foundry project or model deployments exist. You wire those by setting FOUNDRY_PROJECT_ENDPOINT and model env vars in .env. 

Absolutely — I’ve done a full enterprise-grade gap review of the swarm artefacts (agents, tools, orchestration, code scaffolding, skills/docs) and then upgraded the swarm to close the key gaps that typically break “mission‑critical” customer work. 
✅ Updated ZIP (enterprise-hardened)

Here’s the upgraded pack with all changes applied: CSA_Agent_Swarm_Enterprise_Foundry.zip 


1) What I reviewed (and what was missing for mission-critical enterprise)

For large enterprise / regulated / multinational customers it needed explicit coverage of: 
A) Missing cross-cutting enterprise roles (biggest gap)

The original “AI Factory pillars” are commonly summarised as Models, Knowledge & Tools, Customisation, Orchestration, Observability, Trust. For mission-critical solutions, you also need specialists for: 
Network security / secure API exposure 

Reliability / Resilience (HA/DR, runbooks) 

FinOps (cost controls, routing, budgets) 

Data governance / compliance 

DevSecOps / platform engineering 

Threat modelling / red teaming 

Diagnostics / debugging 

Principal CSA + CSAM review 

Professional report writing 

These weren’t consistently present as first-class agents with responsibilities + outputs. 
B) Orchestration lacked enterprise stage gates

Previously the flow was “specialists → verifier”. For enterprise delivery, you need: 
Principal review gate (risk, simplification, story, exec alignment) 

Verifier gate (correctness + concision + missing controls) 

Report gate (audience‑tailored, customer-ready deliverable) 

C) Tooling gaps for real customer operations

You needed explicit tools for: 
Debug triage (Azure/Foundry/Copilot issues) 

Security review punchlist 

Report generation per persona 

And a single “run enterprise swarm” tool that always includes enterprise controls. 

D) Skills/docs lacked “enterprise bar”

The operating rules needed to enforce “always include identity/network/observability/cost/resilience/governance”. 


2) What I added to close those gaps (and why it helps)

✅ A) Added enterprise specialist agents (as skills files)

Across all three roots, I added first-class agent skill files under /agents/ including: 
Core AI Factory pillar agents (kept + tightened)

factory_architect.md 

model_steward.md 

knowledge_toolsmith.md 

customization_engineer.md 

orchestration_conductor.md 

observability_sre.md 

trust_guardian.md 

(These map directly to the Agent Factory pillars described in internal Foundry content. ) 
Enterprise cross-cutting agents (NEW)

security_network_architect.md (VNets, Private Link, APIM/WAF patterns, enterprise hardening) 

diagnostics_debugger.md (Azure config + agent quality debugging) 

reliability_resilience.md (HA/DR, RTO/RPO, runbooks) 

finops_cost.md (routing/caching/budgets/quota planning) 

data_governance.md (governance + safe grounding) 

devsecops_platform.md (CI/CD, IaC, policy-as-code) 

threat_model_redteam.md (prompt injection + red teaming) 

principal_csa_csam_reviewer.md (exec critique + customer narrative) 

professional_report_writer.md (multi-audience deliverable) 

These are exactly the roles you described, plus the additional ones enterprise customers reliably require. 


✅ B) Upgraded orchestration to an enterprise delivery pipeline

I implemented a true enterprise orchestrator: 

Plan → Specialists → Principal review → Verifier → Report

This is now a reusable pattern in code: 
swarm/core.py contains EnterpriseOrchestrator 

swarm/tools.py wires scenarios into that orchestrator 

Why this matters: Enterprise engagements fail less on “missing info” and more on “missing controls, risks, and narrative”. This pipeline bakes those gates in. 


✅ C) Added enterprise MCP tools (tool registry)

In config/tools.yaml I added/expanded tools so MCP clients can call these directly: 
swarm.run → runs the full enterprise orchestrator 

foundry.ask → single Foundry call 

debug.triage → produces a troubleshooting checklist + verifier pass 

security.review → produces a security punchlist (verifier model) 

report.generate → audience-specific report generator 

These tools are implemented in: 
swarm/tools.py 

So your swarm can be used as: 
Copilot UX → MCP → Swarm tools 

and it consistently returns enterprise-grade outputs. 



✅ D) Hardened operating rules + docs for enterprise

I updated and expanded: 
skills/CLAUDE.md → “enterprise bar” rules (identity/network/obs/cost/resilience/governance always present) 

docs/ai-factory-components.md → pillar mapping + enterprise extensions 

docs/enterprise-checklists.md → practical checklists for delivery quality 

This removes ambiguity and prevents “nice but incomplete” answers. 


3) What’s inside the upgraded ZIP (quick orientation)

It keeps your requested three-root structure: 
AI-Foundry/

Focus: Foundry + enterprise architecture 

Scenario: ai_factory_blueprint (recommended) 

Copilot-VSCode/

Focus: VS Code Copilot + MCP + guardrails 

Includes .vscode/mcp.json example 

Copilot-GitHub/

Focus: PR workflows + CI basics + enterprise controls 

Includes .github/copilot/mcp.json example + CI compilation check 



4) Enterprise gaps I intentionally covered (the “big 10”)

This version explicitly covers the things that typically bite in production: 
Private networking / egress controls / DNS implications 

Secure API exposure patterns (APIM/WAF/front door/app gateway) 

Identity patterns (MI/OBO, RBAC/PIM) 

Observability (trace + eval + runbooks) 

Reliability (multi-region, RTO/RPO, failover) 

FinOps (routing, caching, budgets, quota/capacity planning) 

Governance & compliance (data classification / safe grounding) 

Threat modelling (prompt injection / tool abuse) 

Diagnostics (Azure config + agent quality issues) 

Customer comms (principal review + report writer outputs per persona) 



5) How to use it immediately (no extra setup)

Run the MCP server in one folder (example AI-Foundry):
cd AI-Foundry<ctmzNwLn>python -m venv .venv && source .venv/bin/activate<ctmzNwLn>pip install -r requirements.txt<ctmzNwLn>cp .env.example .env<ctmzNwLn>python -m uvicorn AI_Foundry.server.app:app --host 127.0.0.1 --port 8001<ctmzNwLn>
Then MCP-call: 
tools/call → swarm.run 

scenario: ai_factory_blueprint 

task: your customer request 



✅ Deliverable

You now have an enterprise-ready CSA agent swarm that: 
generates better architectures, 

catches risks, 

debugs problems, 

produces exec-ready outputs, 

and supports Foundry/Copilot/MCP usage patterns consistently. 


