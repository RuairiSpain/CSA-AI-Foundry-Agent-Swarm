
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

Added the Diagram Lint Verifier as a new agent and as a callable MCP tool, and wired it into the enterprise orchestration pipeline so every swarm run produces linted (validated + corrected) Mermaid diagrams. 
Download the upgraded ZIP (Diagrams + Lint)

CSA_Agent_Swarm_Enterprise_PowerUpgrade_Diagrams_Lint.zip 


What you get in this “lint” upgrade

1) New agent: diagram_lint_verifier

File: agents/diagram_lint_verifier.md 

Role: checks Mermaid output for: 

correct fenced blocks 

readability + line limits 

trust boundaries 

broken syntax / overly long labels 

and platform warnings (e.g., Azure DevOps wiki Mermaid wrapper differences)  

2) New MCP tool: diagram.lint

Tool: diagram.lint 

Input: { diagrams: string } 

Output: issues + corrected diagrams 

3) Orchestration updated (now enterprise-grade “diagram QA”)

Pipeline is now: 
Plan → Specialists → Principal review → Verifier → Diagrams → Diagram Lint → Report 
That means the report writer always receives linted/corrected diagrams, and it will embed them into customer-ready outputs. 


Why linting matters (grounded)

Mermaid is widely used for code-based diagrams in Markdown workflows, and modular diagrams are recommended over huge ones.  

Some platforms (notably Azure DevOps wiki) have Mermaid syntax limitations and may need alternate wrappers — so the linter flags this and outputs an ADO-friendly wrapper suggestion.  



Where the changes are in the ZIP

Code

*//swarm/core.py 

adds the diagram_linter stage into EnterpriseOrchestrator 

*//swarm/tools.py 

adds diagram_lint() tool 

adds a diagram_lint_verifier Agent in the main swarm_run() flow 

Config

config/tools.yaml 

registers diagram.lint 

Docs

docs/diagrams/mermaid-guide.md (Mermaid usage + platform caveats)  

docs/diagrams/mermaid-lint-rules.md (the lint contract/rules) 



How to use it

A) Full run (diagrams auto-linted)

Call MCP: 
swarm.run 

provide task (and optional scenario) 

B) Lint diagrams only

Call MCP: 
diagram.lint 

pass the Mermaid text you want checked 

✅ Implemented. I’ve produced a CSA Listener Agent pack that adds a live-call assist capability to your swarm, with two ingestion paths so it works for Teams, phone, and in-person (as long as you can provide audio→text or text chunks). 
Download

CSA Listener Agent Swarm (zip) 


What’s implemented (and how it maps to your goal)

1) Real-time “listener” runtime (low-friction)

A) WebSocket streaming endpoint (smoothest UX)

ws://:/listener/ws 

You stream transcript chunks (JSON messages) 

The server returns CSA guidance cards after each chunk: 

key_insight 

suggested_question 

solution_hint 

critical_gap 

plus an extracted object (goal/pain/constraints/current state) 

This gives the “live guidance” experience you described with minimal typing. 
B) MCP tools (for environments that can only call tools)

Tools included in config/tools.yaml: 
listener.start 

listener.ingest 

listener.state 

listener.export 

listener.reset 

So any client (Copilot for VS Code, GitHub tooling, a script, etc.) can feed chunks and get guidance. 


2) “Temporary transcript” / privacy-friendly model

I designed the listener as a session-scoped store that you can reset/terminate at will, mirroring the idea that Teams Copilot can operate “only during the meeting” using a temporary transcript that is deleted after the meeting ends.  That’s the right mental model for sensitive customer calls. 


3) Flexible audio input strategy

This pack does not claim it can magically capture audio from every meeting platform (that depends on device permissions / meeting platform APIs). Instead it supports: 
✅ Any source that can produce text chunks 

✅ Microphone-based transcription client (provided) 

✅ Extensible path for telephony / external feeds (via custom audio stream ingestion) 

This aligns with: 
Azure Speech offering real-time transcription with intermediate results (ideal for live assist).  

Speech SDK supporting custom audio input streams (useful if later you wire in telephony audio feeds).  



What’s inside the ZIP (key files)

Each of your three root folders contains the listener implementation: 
Server + MCP

*//server/app.py 

Adds /listener/ws WebSocket endpoint 

Keeps /mcp JSON-RPC endpoint 

Listener engine (the “agent”)

*//listener/engine.py 

Single fast model call per chunk (low latency) 

Produces strict JSON guidance output 

Merges extracted facts into session memory 

Session memory

*//listener/state.py 

Stores transcript + structured facts per session 

MCP tool wrappers

*//listener/tools.py 

Implements the listener.* tools 

Client (optional)

*/clients/mic_listener.py 

Uses Azure Speech SDK to transcribe microphone and stream chunks to /listener/ws 



How to run it (quick)

1) Start server (example: AI-Foundry folder)
cd AI-Foundry<ctmzNwLn>python -m venv .venv && source .venv/bin/activate<ctmzNwLn>pip install -r requirements.txt<ctmzNwLn>cp .env.example .env<ctmzNwLn>python -m uvicorn AI_Foundry.server.app:app --host 127.0.0.1 --port 8001<ctmzNwLn>
2) Stream transcript chunks via WebSocket (lowest friction)

Send messages like:
{ "session_id": "optional" }<ctmzNwLn>{ "session_id": "...", "text": "We need to deploy globally with strict data residency.", "speaker": "customer", "is_final": true }<ctmzNwLn>
You’ll receive:
{<ctmzNwLn>  "type": "guidance",<ctmzNwLn>  "key_insight": "...",<ctmzNwLn>  "suggested_question": "...",<ctmzNwLn>  "solution_hint": "...",<ctmzNwLn>  "critical_gap": "...",<ctmzNwLn>  "extracted": {...}<ctmzNwLn>}<ctmzNwLn>
3) Or run the microphone client (optional)

Set Speech env vars in .env: 
SPEECH_KEY 

SPEECH_REGION 

Then:
python clients/mic_listener.py<ctmzNwLn>
This uses Azure Speech real-time transcription behaviour (intermediate results) to provide continuous guidance. 


Current limitations (being transparent)

Capturing Teams audio directly is not implemented in this pack. Teams audio capture is a platform permission/API question. 

The implementation is channel-agnostic by design: it works best when you can supply either: 

live transcript (ideal), or 

microphone capture (provided), or 

a telephony stream routed into a custom audio stream pipeline (future extension; supported by Speech SDK concepts).  



Next “best” upgrade (if you want it in the next step)

If you confirm this direction, the next improvement is to re-introduce your earlier multi-role swarm (listener + discovery coach + solution architect + gap detector + whisper), but with a latency-aware router: 
fast mode (single call) during active speech 

deep mode (multi-agent) during pauses / topic changes 

That gives you the smooth “live assist” feel without spamming the CSA. 
If you want, tell me which target UX you want first: 
(A) single on-screen “guidance card” that updates every ~10 seconds, or 

(B) “3 suggestion cards” (questions / risks / solution directions) refreshed every ~30 seconds. 

✅ Added an auto‑mode switcher that changes conversation mode (consultative/executive/technical) and persona (director_vp/tech_lead/graduate) based on live conversation cues, with anti‑flap lockout and manual override protection. 
Download

CSA Listener Agent Swarm — AutoMode 


What’s in this upgrade

1) Auto-mode switching (based on cues)

The listener now runs a lightweight “style router” on each transcript update: 
Deterministic cue matcher (fast, no extra latency) Uses keyword cues to infer: 

Executive when the conversation turns to budget, ROI, sponsor, timeline, strategy, procurement 

Technical when it turns to VNet, Private Endpoint, APIM, AKS, RBAC/Entra, latency, DR (RTO/RPO), IaC, observability 

Otherwise stays Consultative 

Optional LLM refinement (higher precision) If enabled, a small classifier prompt can override the deterministic guess when it is medium/high confidence. 

2) Anti-flapping lockout

To avoid the mode bouncing every few seconds, there is a lockout timer: 
LISTENER_AUTO_LOCK_SECONDS (default 20s) 

Once an auto-switch happens, the system will not change mode/persona again until the lock expires. 
3) Manual selections are respected

If you manually set: 
mode or 

persona 

…auto-switching will not override it. 
We track this in the session: 
mode_source: default | auto | manual 

persona_source: default | auto | manual 

4) Visibility: you can see why it switched

When an auto-switch happens, the returned guidance card includes:
"_style_switch": {<ctmzNwLn>  "mode": "...",<ctmzNwLn>  "persona": "...",<ctmzNwLn>  "confidence": "...",<ctmzNwLn>  "cues": ["...","..."]<ctmzNwLn>}<ctmzNwLn>
So the CSA sees why the assistant moved into “executive” or “technical”. 


New controls (WebSocket + MCP)

WebSocket

Enable/disable auto switching
{ "type": "set", "session_id": "...", "auto_mode": true, "auto_persona": true }<ctmzNwLn>
Disable:
{ "type": "set", "session_id": "...", "auto_mode": false, "auto_persona": false }<ctmzNwLn>
Manual override still works
{ "type": "set", "session_id": "...", "mode": "technical" }<ctmzNwLn>{ "type": "set", "session_id": "...", "persona": "director_vp" }<ctmzNwLn>
MCP Tools

Added: 
listener.set_auto(session_id, auto_mode?, auto_persona?) 

Existing: 
listener.set_mode 

listener.set_persona 



Environment knobs

In .env.example: 
LISTENER_AUTO_LOCK_SECONDS=20 

LISTENER_AUTO_LLM=true 

set to false to use only deterministic cues 



What changed in the code

Key files: 
listener/engine.py 

adds _maybe_auto_style() cue router + lockout + LLM refinement 

listener/state.py 

stores auto_mode, auto_persona, mode_source, persona_source, last_style_change_ts 

listener/tools.py + config/tools.yaml 

adds listener.set_auto 



If you want the next polish step: I can make the router topic-aware (e.g., “security/compliance” → executive-but-risk, “architecture deep dive” → technical, “requirements discovery” → consultative) using the same DEEP pipeline signals you already generate.
Brilliant — I’ve implemented the topic-aware router so the listener now auto-switches mode (consultative / executive / technical) based on the current conversation topic, not just keywords, while still respecting your lockout and manual overrides. 
✅ Download: Topic-aware router build

CSA_Listener_Agent_Swarm_TopicAware_Router.zip 


What changed (high signal)

1) New “Topic” layer drives the mode

Each guidance card now carries: 
topic (e.g., security_compliance, architecture_networking, cost_finops) 

topic_confidence 

topic_source (default | auto | manual) 

and the mode is chosen primarily via topic → mode mapping. 

This aligns with real facilitation guidance that explicitly talks about using tone like consultative / executive / technical depending on the scenario and audience. 
Topic → Mode mapping implemented

Executive mode when topic is: 

security_compliance, governance_risk, cost_finops, delivery_next_steps 

Technical mode when topic is: 

architecture_networking, operations_observability, data_ai 

Consultative mode when topic is: 

requirements_discovery 



2) Topic detection uses both conversation cues and DEEP pipeline signals

The topic detector looks at: 
the recent transcript window (last ~25 lines) 

the structured extracted facts (facts.constraints, facts.current_state, etc.) 

So if the conversation implicitly moves into compliance (e.g., it shows up in constraints), the router can still switch even if the latest utterance doesn’t contain the cue. 


3) Anti-flap lockout + manual override still enforced

LISTENER_AUTO_LOCK_SECONDS (default 20s) prevents switching too frequently 

If the CSA manually sets mode/persona, auto will not override those. 



4) Visibility: “why it switched” metadata

When a switch happens, the returned card includes:
"_style_switch": {<ctmzNwLn>  "topic": "...",<ctmzNwLn>  "mode": "...",<ctmzNwLn>  "persona": "...",<ctmzNwLn>  "confidence": "...",<ctmzNwLn>  "cues": ["..."]<ctmzNwLn>}<ctmzNwLn>
So the CSA can instantly see why the assistant changed behaviour. 


New/updated controls

WebSocket: enable/disable topic auto-routing

You can now toggle topic auto-routing alongside mode/persona:
{ "type": "set", "session_id": "...", "auto_mode": true, "auto_persona": true, "auto_topic": true }<ctmzNwLn>
Disable:
{ "type": "set", "session_id": "...", "auto_mode": false, "auto_persona": false, "auto_topic": false }<ctmzNwLn>
Manual mode is still:
{ "type": "set", "session_id": "...", "mode": "technical" }<ctmzNwLn>
--- 
MCP tool added/extended

listener.set_auto(session_id, auto_mode?, auto_persona?, auto_topic?) 


What’s in the ZIP (where to look)

listener/engine.py 

Topic cues dictionary + topic scoring 

Topic → mode mapping 

Uses both transcript + extracted facts 

Optional LLM refinement via TOPIC_STYLE_CLASSIFIER_SYSTEM 

listener/prompts.py 

Adds TOPIC_STYLE_CLASSIFIER_SYSTEM which returns {topic, mode, persona, confidence, cues} 

listener/state.py 

Adds topic, topic_confidence, topic_source, auto_topic 

clients/mic_listener.py 

Prints topic and displays auto-switch reason 

auto on|off toggles all three (mode/persona/topic) 



Why “delivery_next_steps” is a useful topic

The router treats terms like VBD, workshop, pilot, PoC, scope, milestone as “delivery next steps”, which reliably indicates it’s time to switch to an executive/next-steps posture (clear decisions, ownership, timeline). This aligns with scoping and delivery guidance patterns found in FY26-VBD Execution Playbook. 


Next (if you want to keep going)

One very high-impact enhancement is to add “topic-specific card layout” (same card, different sections), e.g.: 
Security topic → “Risk / Control / Ask / Next step” 

Networking topic → “Constraint / Option A/B / Ask / Trade-off” 

FinOps topic → “Cost driver / Guardrail / Ask / Next step” 

Say: “Add topic-specific card formats” and I’ll implement it cleanly on top of this build.
✅ Done — I’ve added topic-specific card formats on top of your topic-aware router. 
Download

Topic-specific cards pack 


What you now get

Every guidance response still includes your “universal” fields: 
key_insight 

suggested_question 

solution_hint 

critical_gap 

extracted 

…and now also includes a UI-friendly, topic-specific payload:
"_card": {<ctmzNwLn>  "schema": "csa.card.<topic>.v1",<ctmzNwLn>  "title": "...",<ctmzNwLn>  "topic": "...",<ctmzNwLn>  "sections": { ... }<ctmzNwLn>}<ctmzNwLn>
This structure is designed to render different layouts per topic while keeping the existing card fields intact. The topic choices align with the kind of discovery categories you’ve already captured in CSA Customer Copilot Prompts (e.g., security/compliance, cost, monitoring/logging, data, etc.). 


Topic-specific formats implemented (schemas)

Below are the stable schemas and the section keys each contains (all generated automatically from the existing extracted + _deep data where available): 
csa.card.security_compliance.v1

Sections: risk, controls, ask, next_step 
csa.card.governance_risk.v1

Sections: ownership, guardrails, ask, next_step 
csa.card.cost_finops.v1

Sections: cost_driver, guardrail, ask, next_step 
csa.card.architecture_networking.v1

Sections: constraint, options, tradeoff, ask 
csa.card.operations_observability.v1

Sections: signal, slo, instrumentation, ask 
csa.card.data_ai.v1

Sections: data_sources, retrieval, evaluation, ask 
csa.card.delivery_next_steps.v1

Sections: decision, owner, date, next_step 
csa.card.requirements_discovery.v1

Sections: goal, pain, constraints, ask 


How the sections are populated (no hallucination)

The formatter does not invent content. It only rearranges: 
extracted.customer_goal / pain_points / constraints / current_state 

_deep.hypotheses (where present) 

_deep.gap (where present) 

existing core fields (key_insight, suggested_question, solution_hint, critical_gap) 

So the format becomes “what the CSA needs to see” per topic, without changing your underlying guidance. 


Where it lives in the code

In this pack, the work is in: 
listener/engine.py 

Adds CARD_FORMATS mapping 

Adds _apply_card_format(guidance, state) 

Injects _card into every guidance response after FAST/DEEP generation 

Keeps original output fields unchanged 

Docs updated: 
skills/listener.md and agents/csa_listener.md explain _card and schemas, grounded in CSA Customer Copilot Prompts.  



Why this is consistent with your internal CSA approach

Your own CSA Customer Copilot Prompts already organises questions into pillars (security/compliance, cost optimisation, monitoring/logging, data, etc.). These topic-specific cards essentially turn those pillar buckets into live, on-call card layouts. 


If you want one more “UX upgrade”: I can also add topic-specific talk-track templates so the “talk-track” output mirrors the _card.sections (e.g., security card talk-track becomes: risk → control → ask → next step).

✅ Done — I’ve added topic-specific card formats on top of your topic-aware router. 
Download

Topic-specific cards pack 


What you now get

Every guidance response still includes your “universal” fields: 
key_insight 

suggested_question 

solution_hint 

critical_gap 

extracted 

…and now also includes a UI-friendly, topic-specific payload:
"_card": {<ctmzNwLn>  "schema": "csa.card.<topic>.v1",<ctmzNwLn>  "title": "...",<ctmzNwLn>  "topic": "...",<ctmzNwLn>  "sections": { ... }<ctmzNwLn>}<ctmzNwLn>
This structure is designed to render different layouts per topic while keeping the existing card fields intact. The topic choices align with the kind of discovery categories you’ve already captured in CSA Customer Copilot Prompts (e.g., security/compliance, cost, monitoring/logging, data, etc.). 


Topic-specific formats implemented (schemas)

Below are the stable schemas and the section keys each contains (all generated automatically from the existing extracted + _deep data where available): 
csa.card.security_compliance.v1

Sections: risk, controls, ask, next_step 
csa.card.governance_risk.v1

Sections: ownership, guardrails, ask, next_step 
csa.card.cost_finops.v1

Sections: cost_driver, guardrail, ask, next_step 
csa.card.architecture_networking.v1

Sections: constraint, options, tradeoff, ask 
csa.card.operations_observability.v1

Sections: signal, slo, instrumentation, ask 
csa.card.data_ai.v1

Sections: data_sources, retrieval, evaluation, ask 
csa.card.delivery_next_steps.v1

Sections: decision, owner, date, next_step 
csa.card.requirements_discovery.v1

Sections: goal, pain, constraints, ask 


How the sections are populated (no hallucination)

The formatter does not invent content. It only rearranges: 
extracted.customer_goal / pain_points / constraints / current_state 

_deep.hypotheses (where present) 

_deep.gap (where present) 

existing core fields (key_insight, suggested_question, solution_hint, critical_gap) 

So the format becomes “what the CSA needs to see” per topic, without changing your underlying guidance. 


Where it lives in the code

In this pack, the work is in: 
listener/engine.py 

Adds CARD_FORMATS mapping 

Adds _apply_card_format(guidance, state) 

Injects _card into every guidance response after FAST/DEEP generation 

Keeps original output fields unchanged 

Docs updated: 
skills/listener.md and agents/csa_listener.md explain _card and schemas, grounded in CSA Customer Copilot Prompts.  



Why this is consistent with your internal CSA approach

Your own CSA Customer Copilot Prompts already organises questions into pillars (security/compliance, cost optimisation, monitoring/logging, data, etc.). These topic-specific cards essentially turn those pillar buckets into live, on-call card layouts. 


If you want one more “UX upgrade”: I can also add topic-specific talk-track templates so the “talk-track” output mirrors the _card.sections (e.g., security card talk-track becomes: risk → control → ask → next step).
✅ Added topic-specific talk-track templates that mirror each card’s _card.sections (so the script you say out loud follows the same structure as the UI card). 
Download

CSA Listener – Topic-Specific Talk-Track Templates (ZIP) 


What changed

1) Talk-track is now template-driven by default

When you call listener.talktrack (or WebSocket {type:"talktrack"}), the engine: 
reads the card’s topic 

reads the card’s _card.sections 

emits a 4–7 line script that follows the topic’s section order (e.g., Security: risk → controls → ask → next step) 

This keeps the talk-track stable and predictable (no tone drift), while staying aligned to the CSA discovery categories you already use (security/compliance, cost optimisation, monitoring/logging, data, etc.) from your internal prompt guide. 
2) Optional LLM talk-track remains available (off by default)

If you want the model to generate the talk track instead of templates: 
set LISTENER_TALKTRACK_LLM=true 

Default in .env.example is false (templates). 


Template behaviours by topic (what the CSA gets)

These are the built-in talk-track patterns (verbatim-style): 
security_compliance: Risk check → Current controls → Key question → Next step 

architecture_networking: Constraint → Options → Trade-off → Confirm question 

cost_finops: Cost driver → Guardrail → Key question → Next step 

operations_observability: Operational signal → SLO/constraint → Instrumentation ideas → Key question 

data_ai: Data sources → Retrieval/RAG → Evaluation gap → Key question 

delivery_next_steps: Decision → Owner (optional) → Date (optional) → Next step 

requirements_discovery: Goal → Pain → Constraints → Key question 

All lines are built directly from the card’s _card.sections (or fall back to the standard key_insight/suggested_question/solution_hint fields if sections are missing). 


How to use (same APIs)

WebSocket

Send:
{ "type": "talktrack", "session_id": "<id>" }<ctmzNwLn>
MCP Tool

Call: 
listener.talktrack(session_id, card_id?, mode?, persona?) 



If you want the next UX bump: I can add a “talk-track style dial” (e.g., more direct, more consultative, more technical) that tweaks the templates without switching back to LLM generation.
