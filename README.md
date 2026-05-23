Here is a clean, consolidated, GitHub‑ready README for your project. I’ve merged your material into a single, coherent, enterprise-grade document aligned to how you typically position solutions with customers (clear architecture, value, and execution). 


🧠 CSA Customer Call Copilot (C3 Copilot)

An AI‑powered assistant for Cloud Solution Architects (CSAs) that listens to customer conversations and delivers real‑time guidance, discovery prompts, and solution recommendations. 


📌 Overview

CSA Customer Call Copilot (C3 Copilot) is an Azure AI Foundry-based multi-agent system designed to assist CSAs during live customer interactions (Teams calls, workshops, or calls with transcripts). 
It transforms conversation streams into actionable intelligence: 
Suggested open-ended discovery questions 

Solution architectures and Azure opportunities 

Risk identification (security, cost, governance, reliability) 

Executive-ready talk tracks and next-step recommendations 



🎯 Key Value
Capability
Outcome
Real-time call guidance
Stronger discovery and positioning
Multi-agent reasoning
Higher-quality, consistent architecture advice
Topic-aware coaching
Adaptive conversation style (technical / executive / consultative)
Enterprise guardrails
Designs always include security, networking, cost and governance
Automated talk-tracks
Faster CSA responses and sharper messaging


🏗️ Architecture Overview

The system follows a modular architecture aligned to Microsoft’s Copilot + Foundry pattern:
Audio Input (Teams / Mic / Transcript)<ctmzNwLn>        ↓<ctmzNwLn>Azure Speech SDK (optional)<ctmzNwLn>        ↓<ctmzNwLn>Listener Agent (WebSocket / MCP)<ctmzNwLn>        ↓<ctmzNwLn>AI Foundry Endpoint<ctmzNwLn>        ↓<ctmzNwLn>Enterprise Agent Swarm<ctmzNwLn>        ↓<ctmzNwLn>Guidance Cards + Talk Tracks<ctmzNwLn>
Core Concept


Copilot UX → MCP Server → AI Foundry (multi-agent “brain”)



🔩 Core Components

1. Listener Agent (Real-Time Engine)

Responsible for ingesting conversation data and generating live guidance. 
Supports: 
WebSocket streaming (/listener/ws) 

MCP tools (JSON-RPC) 

Outputs per interaction: 
Key insight 

Suggested question 

Solution hint 

Critical gap 

Structured extracted facts 



2. MCP Server (Integration Layer)

Implements the Model Context Protocol (MCP): 
initialize 

tools/list 

tools/call 

resources/* 

prompts/* 

Enables integration with: 
Copilot in VS Code 

Copilot in GitHub 

Custom clients 



3. Enterprise Agent Swarm

A structured, multi-agent system:
Planner → Specialists → Principal Review → Verifier → Diagram Lint → Report<ctmzNwLn>
Agent Types

AI Factory Pillar Agents 
Model steward 

Knowledge/toolsmith 

Customisation engineer 

Orchestration conductor 

Observability SRE 

Trust guardian 

Enterprise Specialists 
Security & network architect 

Reliability & resilience 

FinOps cost optimisation 

Data governance 

DevSecOps platform 

Threat modelling (red team) 

Diagnostics debugger 

Principal CSA reviewer 

Professional report writer 



4. Topic-Aware Listener Intelligence

The system dynamically classifies conversations and adapts behaviour. 
Topics

Security & compliance 

Architecture & networking 

Cost / FinOps 

Observability / operations 

Data & AI 

Requirements discovery 

Delivery / next steps 

Modes (auto-switched)

Consultative → discovery 

Technical → architecture deep dive 

Executive → decisions, ROI, next steps 



🎴 Guidance Cards (Real-Time UX)

Each interaction produces a structured response:
{<ctmzNwLn>  "key_insight": "...",<ctmzNwLn>  "suggested_question": "...",<ctmzNwLn>  "solution_hint": "...",<ctmzNwLn>  "critical_gap": "...",<ctmzNwLn>  "_card": {<ctmzNwLn>    "schema": "csa.card.security_compliance.v1",<ctmzNwLn>    "sections": {<ctmzNwLn>      "risk": "...",<ctmzNwLn>      "controls": "...",<ctmzNwLn>      "ask": "...",<ctmzNwLn>      "next_step": "..."<ctmzNwLn>    }<ctmzNwLn>  }<ctmzNwLn>}<ctmzNwLn>
Topic-Specific Card Formats
Topic
Sections
Security
Risk → Controls → Ask → Next step
Networking
Constraint → Options → Trade-off → Ask
FinOps
Cost driver → Guardrail → Ask → Next step
Observability
Signal → SLO → Instrumentation → Ask
Data/AI
Data → Retrieval → Evaluation → Ask
Delivery
Decision → Owner → Date → Next step
Discovery
Goal → Pain → Constraints → Ask


🗣️ Talk Track Generation

Two modes: 
Template-based (default)

Deterministic, low latency 

Mirrors card structure 

LLM-generated (optional)

Enable:
LISTENER_TALKTRACK_LLM=true<ctmzNwLn>
Returns:
{<ctmzNwLn>  "talk_track": [...],<ctmzNwLn>  "one_liner": "..."<ctmzNwLn>}<ctmzNwLn>
--- 
🔄 Real-Time Processing Model
Stage
Behaviour
FAST
Immediate guidance from partial transcripts
DEEP
Structured reasoning on finalised speech
AUTO-MODE
Adjusts style/persona/topic


🔐 Enterprise Design Principles

Every output enforces: 
Identity & access (RBAC / Entra ID) 

Networking (VNet, Private Link) 

Observability (logging, tracing, evals) 

Cost controls (routing, caching, quotas) 

Resilience (HA/DR, RTO/RPO) 

Governance & compliance 

Security threat modelling 



🔧 MCP Tools

Available via JSON-RPC: 
swarm.run 

foundry.ask 

debug.triage 

security.review 

report.generate 

diagram.lint 

Listener Tools

listener.start 

listener.ingest 

listener.state 

listener.reset 

listener.talktrack 



📂 Repository Structure
AI-Foundry/<ctmzNwLn>Copilot-VSCode/<ctmzNwLn>Copilot-GitHub/<ctmzNwLn>
Each root contains:

MCP server (/mcp) 

Multi-agent swarm 

Skills (/skills, /agents) 

Prompts (/prompts) 

Tool registry (tools.yaml) 

Environment config (.env.example) 



🚀 Getting Started

1. Run the server
cd AI-Foundry<ctmzNwLn>python -m venv .venv<ctmzNwLn>source .venv/bin/activate<ctmzNwLn>pip install -r requirements.txt<ctmzNwLn>cp .env.example .env<ctmzNwLn>python -m uvicorn AI_Foundry.server.app:app --host 127.0.0.1 --port 8001<ctmzNwLn>
---

2. Start streaming transcript

WebSocket:
{<ctmzNwLn>  "session_id": "...",<ctmzNwLn>  "text": "Customer requires global deployment with strict data residency.",<ctmzNwLn>  "speaker": "customer",<ctmzNwLn>  "is_final": true<ctmzNwLn>}<ctmzNwLn>
--- 
3. Run swarm (batch mode)
tools/call → swarm.run<ctmzNwLn>
---

🎤 Audio Input Options
Source
Supported
Microphone (Speech SDK)
✅
Teams transcripts (Graph API)
✅
Post-meeting VTT ingestion
✅
Real-time Teams media bot
⚠️ advanced only


🔗 Teams Integration

Recommended Pattern: Post-meeting transcripts

Fetch transcript via Microsoft Graph 

Parse VTT 

Stream into Listener 

Generate insights and talk-track 



📊 Diagram Generation & Linting

All Mermaid diagrams are: 
Generated during swarm execution 

Validated via diagram.lint 

Corrected before report output 



🧪 Example Use Cases

Customer discovery calls 

Architecture workshops 

Executive briefings 

Pre-sales solution design 

Follow-up report generation 



⚠️ Limitations

No direct real-time Teams audio capture (requires specific APIs) 

Requires transcript or audio-to-text input 

Foundry models must be configured via environment variables 



🔮 Roadmap (Next Enhancements)

Latency-aware multi-agent routing 

Topic-aware talk-track tuning 

Teams live integration via Graph subscriptions 

Persistent session memory and learning 

Multi-language support 



✅ Summary

C3 Copilot provides: 
✅ Real-time customer call intelligence ✅ Enterprise-grade architecture reasoning ✅ Guided discovery and positioning ✅ Consistent CSA best practices ✅ Tight integration with Microsoft Copilot ecosystem 


👤 Author

Cloud Solution Architecture – Cloud & AI Microsoft 


💡 Positioning (CSA Narrative)


“This solution acts as a real-time CSA co-pilot—combining Azure AI Foundry, Copilot extensibility, and multi-agent reasoning to drive higher-quality customer outcomes during live engagements.”

