# PHASE 2: AGENT LIBRARY — STARTING NOW

**Status:** Initiated June 20, 2026  
**Duration:** 1-2 weeks  
**Output:** Complete template files for all 23 agents

---

## Phase 2 Overview

### What We're Creating
- **12 Standalone Agents** - Reusable across all patterns
- **11 Pattern-Specific Agents** - Optimized for each pattern
- **For Each Agent:** 4 files (agent.yaml, agent.md, prompt.txt, requirements.txt)
- **Total Files:** ~92 files (23 agents × 4 files)
- **Total Lines:** ~15,000+ lines of agent code & documentation

### Directory Structure Being Created
```
templates/agents/
├── standalone/
│   ├── document-writer/
│   │   ├── agent.yaml
│   │   ├── agent.md
│   │   ├── prompt.txt
│   │   └── requirements.txt
│   ├── rag-query/
│   ├── reviewer/
│   ├── summarizer/
│   ├── semantic-search/
│   ├── web-query/
│   ├── researcher/
│   ├── presenter-word/
│   ├── presenter-html/
│   ├── presenter-markdown/
│   ├── presenter-code/
│   └── empty-agent/
│
└── patterns/
    ├── supervisor-manager/
    │   ├── supervisor/
    │   └── aggregator/
    ├── fan-out-fan-in/
    │   ├── processor/
    │   ├── worker/
    │   └── aggregator/
    ├── map-reduce/
    │   ├── splitter/
    │   ├── mapper/
    │   ├── shuffle/
    │   ├── reducer/
    │   └── final/
    └── sequential-pipeline/
        └── stage1/
```

---

## Phase 2 Deliverables

### 1. Standalone Agents (12)

**Generation (5):**
1. document-writer - Word document generation
2. presenter-word - Word document formatting
3. presenter-html - HTML dashboard generation
4. presenter-markdown - Markdown formatting
5. presenter-code - Code with comments

**Retrieval (3):**
6. rag-query - Vector-based Q&A
7. semantic-search - Semantic similarity
8. web-query - Web search

**Processing (3):**
9. reviewer - Quality/compliance review
10. summarizer - Text summarization
11. researcher - Multi-step research

**Template (1):**
12. empty-agent - Blank starting point

### 2. Pattern-Specific Agents (11)

**Supervisor-Manager (2):**
1. supervisor - Routing decisions
2. aggregator - Decision combining

**Fan-Out/Fan-In (3):**
3. processor - Preprocessing
4. worker - Parallel processing
5. aggregator - Result combining

**Map-Reduce (5):**
6. splitter - Batch splitting
7. mapper - Parallel mapping
8. shuffle - Data reorganization
9. reducer - Parallel reduction
10. final - Final aggregation

**Sequential-Pipeline (1):**
11. stage1 - Pipeline stage

---

## Each Agent Template Contains

### 1. agent.yaml (150-250 lines)
- Complete contract specification
- Input schema with all fields
- Output schema with all fields
- Metadata (author, license, dependencies)
- Documentation references
- Pattern assignments
- Quality metrics

### 2. agent.md (100-200 lines)
- Agent overview
- Contract specification
- Usage examples
- Use cases
- Configuration options
- Dependencies list
- Limitations & notes
- Related agents

### 3. prompt.txt (50-150 lines)
- Claude system prompt
- Role definition
- Task description
- Instructions
- Output format
- Examples
- Error handling

### 4. requirements.txt (5-20 lines)
- Python dependencies
- Specific versions
- Installation instructions

---

## Phase 2 Timeline

### Week 1: Standalone Agents
- Day 1-2: Generation agents (5)
- Day 3-4: Retrieval agents (3)
- Day 5: Processing agents (3) + Template agent (1)

### Week 2: Pattern Agents
- Day 1-2: Supervisor-Manager (2)
- Day 3-4: Fan-Out/Fan-In (3)
- Day 4-5: Map-Reduce (5)
- Day 5: Sequential-Pipeline (1)

### Week 2: Review & Polish
- Day 6: Review all contracts
- Day 6-7: Polish documentation
- Day 7: Final validation & testing

---

## Quality Standards

Each agent template must have:
- ✅ Complete contract specification
- ✅ Realistic example inputs/outputs
- ✅ System prompt for Claude
- ✅ Clear documentation
- ✅ Listed dependencies
- ✅ Usage patterns
- ✅ Error handling notes
- ✅ Related agent references

---

## Creation Order

### BATCH 1: Foundation
1. empty-agent - Template for custom agents
2. document-writer - Most common use case

### BATCH 2: Generation
3. presenter-word
4. presenter-html
5. presenter-markdown
6. presenter-code

### BATCH 3: Retrieval
7. rag-query
8. semantic-search
9. web-query

### BATCH 4: Processing
10. reviewer
11. summarizer
12. researcher

### BATCH 5: Supervisor-Manager
13. supervisor
14. aggregator

### BATCH 6: Fan-Out/Fan-In
15. processor
16. worker
17. aggregator

### BATCH 7: Map-Reduce
18. splitter
19. mapper
20. shuffle
21. reducer
22. final

### BATCH 8: Sequential-Pipeline
23. stage1

---

## Starting with Batch 1

Creating complete templates for:
1. **empty-agent** - Blank template
2. **document-writer** - Most common

Each will have:
- Complete agent.yaml with contract
- Full agent.md documentation
- System prompt (prompt.txt)
- Dependencies (requirements.txt)
- Ready to use immediately

---

**Phase 2 Start:** Batch 1 agents coming next  
**Status:** Creating empty-agent and document-writer templates now

