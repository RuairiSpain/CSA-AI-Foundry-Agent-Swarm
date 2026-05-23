Done — I rebuilt the ZIP as a CSA agent swarm (not SME), with three top-level root folders exactly as requested: 
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


If you want the next upgrade (no questions needed): I can extend the MCP tool registry to expose separate tools for Foundry Agents, Evals, Tracing hooks, and publish-to- patterns* directly (still keeping the same three-root-folder structure). 
