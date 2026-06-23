"""
Pattern Library for SAFE Framework Phase 1.5

Defines all 12 composition patterns with their structure, placeholders,
variables, and metadata.
"""

import logging
from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class PatternComplexity(str, Enum):
    """Pattern complexity level."""
    SIMPLE = "simple"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class PatternCategory(str, Enum):
    """Pattern category/group."""
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"
    CONDITIONAL = "conditional"
    REDUCTION = "reduction"


@dataclass
class PlaceholderNode:
    """A slot in a pattern where an agent goes."""
    id: str                           # "processor", "worker", "aggregator"
    name: str                         # Display name
    description: str
    stage: str                        # "input", "processing", "aggregation", "output"
    is_array: bool = False            # Multiple agents? (fan-out workers)
    required: bool = True
    agent_type: Optional[str] = None  # Suggested agent type


@dataclass
class VariableParameter:
    """Variable aspect of pattern."""
    name: str                         # "worker_count"
    display_name: str                 # Display name
    description: str
    param_type: str                   # "integer", "string", "boolean"
    default: int | str
    min_value: Optional[int] = None
    max_value: Optional[int] = None
    choices: Optional[List[str]] = None


@dataclass
class PatternTemplate:
    """A reusable composition pattern."""
    pattern_id: str
    name: str
    version: str
    category: PatternCategory
    complexity: PatternComplexity
    description: str
    use_cases: List[str]

    # Structure
    diagram_ascii: str
    placeholders: List[PlaceholderNode]
    variables: List[VariableParameter]

    # Implementation
    code_template: str  # Path to Jinja2 template

    # Example
    example_workflow: Dict

    # Metadata
    created_date: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    author: str = "SAFE Team"
    source: str = "builtin"  # or "user" or "community"
    rating: float = 0.0
    usage_count: int = 0


# ============================================================================
# PATTERN 1: FAN-OUT / FAN-IN
# ============================================================================

FAN_OUT_FAN_IN = PatternTemplate(
    pattern_id="fan-out-fan-in",
    name="Fan-Out / Fan-In",
    version="1.0",
    category=PatternCategory.PARALLEL,
    complexity=PatternComplexity.INTERMEDIATE,
    description="Distribute work to multiple parallel workers, aggregate results.",
    use_cases=[
        "Document review with multiple reviewers",
        "Opinion aggregation from experts",
        "Parallel quality checks",
        "Multi-perspective analysis"
    ],
    diagram_ascii="""
    [Input]
      ↓
  [Processor]
      ↓
    ┌─┴─┬─────┐
    ↓   ↓     ↓
[W1][W2]...[Wn]
    ↓   ↓     ↓
    └─┬─┴─────┘
      ↓
 [Aggregator]
      ↓
   [Output]
    """,
    placeholders=[
        PlaceholderNode(
            id="processor",
            name="Processor",
            description="Initial processing agent",
            stage="processing",
            required=True
        ),
        PlaceholderNode(
            id="workers",
            name="Workers",
            description="Parallel processing workers",
            stage="processing",
            is_array=True,
            required=True
        ),
        PlaceholderNode(
            id="aggregator",
            name="Aggregator",
            description="Combines results from workers",
            stage="aggregation",
            required=True
        ),
    ],
    variables=[
        VariableParameter(
            name="worker_count",
            display_name="Number of Workers",
            description="How many parallel workers? (2-20)",
            param_type="integer",
            default=3,
            min_value=2,
            max_value=20
        )
    ],
    code_template="pattern_templates/fan_out_fan_in.py.jinja2",
    example_workflow={
        "name": "document-review",
        "processor": "DocumentExtractor",
        "workers": ["ReviewerA", "ReviewerB", "ReviewerC"],
        "aggregator": "ReviewAggregator"
    }
)

# ============================================================================
# PATTERN 2: MAP-REDUCE
# ============================================================================

MAP_REDUCE = PatternTemplate(
    pattern_id="map-reduce",
    name="Map-Reduce",
    version="1.0",
    category=PatternCategory.PARALLEL,
    complexity=PatternComplexity.INTERMEDIATE,
    description="Process large batches via map stage, shuffle, then reduce stage.",
    use_cases=[
        "Large batch processing (1000+ items)",
        "Distributed computation",
        "Data aggregation from multiple sources",
        "Hierarchical analysis"
    ],
    diagram_ascii="""
    [Input]
      ↓
  [Splitter]
      ↓
    ┌─┴─┬──┐
    ↓   ↓  ↓
  [M1][M2][Mn] (Mappers)
    ↓   ↓  ↓
    └─┬─┴──┘
      ↓
  [Shuffle]
      ↓
    ┌─┴─┬──┐
    ↓   ↓  ↓
  [R1][R2][Rn] (Reducers)
    ↓   ↓  ↓
    └─┬─┴──┘
      ↓
  [Final Reduce]
      ↓
   [Output]
    """,
    placeholders=[
        PlaceholderNode(
            id="splitter",
            name="Splitter",
            description="Splits input into batches",
            stage="input",
            required=True
        ),
        PlaceholderNode(
            id="mappers",
            name="Mappers",
            description="Parallel mapping workers",
            stage="processing",
            is_array=True,
            required=True
        ),
        PlaceholderNode(
            id="shuffle",
            name="Shuffle",
            description="Reorganizes mapped data",
            stage="processing",
            required=True
        ),
        PlaceholderNode(
            id="reducers",
            name="Reducers",
            description="Parallel reduction workers",
            stage="processing",
            is_array=True,
            required=True
        ),
        PlaceholderNode(
            id="final",
            name="Final Reduce",
            description="Final aggregation",
            stage="aggregation",
            required=True
        ),
    ],
    variables=[
        VariableParameter(
            name="mapper_count",
            display_name="Number of Mappers",
            description="How many parallel mappers? (2-20)",
            param_type="integer",
            default=5,
            min_value=2,
            max_value=20
        ),
        VariableParameter(
            name="reducer_count",
            display_name="Number of Reducers",
            description="How many parallel reducers? (1-10)",
            param_type="integer",
            default=3,
            min_value=1,
            max_value=10
        )
    ],
    code_template="pattern_templates/map_reduce.py.jinja2",
    example_workflow={
        "name": "batch-processing",
        "splitter": "BatchSplitter",
        "mappers": ["DocumentAnalyzer"] * 10,
        "shuffle": "ShuffleAggregator",
        "reducers": ["ResultReducer"] * 3,
        "final": "FinalAggregator"
    }
)

# ============================================================================
# PATTERN 3: ROUND-ROBIN
# ============================================================================

ROUND_ROBIN = PatternTemplate(
    pattern_id="round-robin",
    name="Round-Robin",
    version="1.0",
    category=PatternCategory.PARALLEL,
    complexity=PatternComplexity.SIMPLE,
    description="Distribute work to identical workers in rotation.",
    use_cases=[
        "Load balancing across workers",
        "Work queue distribution",
        "Scalable processing with identical agents",
        "Worker pool pattern"
    ],
    diagram_ascii="""
    [Input Items]
      ↓
 [Distributor]
      ↓
    Distribution: Item1→W1, Item2→W2, Item3→W3, Item4→W1, ...
    ┌──┬──┬──┐
    ↓  ↓  ↓
   [W1][W2][W3] (identical workers)
    ↓  ↓  ↓
    └──┴──┴──┘
      ↓
 [Collector]
      ↓
   [Output]
    """,
    placeholders=[
        PlaceholderNode(
            id="distributor",
            name="Distributor",
            description="Distributes items to workers",
            stage="input",
            required=True
        ),
        PlaceholderNode(
            id="workers",
            name="Workers",
            description="Identical processing workers",
            stage="processing",
            is_array=True,
            required=True
        ),
        PlaceholderNode(
            id="collector",
            name="Collector",
            description="Collects results from workers",
            stage="aggregation",
            required=True
        ),
    ],
    variables=[
        VariableParameter(
            name="worker_count",
            display_name="Number of Workers",
            description="How many identical workers? (2-10)",
            param_type="integer",
            default=3,
            min_value=2,
            max_value=10
        )
    ],
    code_template="pattern_templates/round_robin.py.jinja2",
    example_workflow={
        "name": "load-balanced-processing",
        "distributor": "TaskDistributor",
        "workers": ["ProcessorAgent"] * 5,
        "collector": "ResultCollector"
    }
)

# ============================================================================
# PATTERN 4: MIXTURE OF EXPERTS
# ============================================================================

MIXTURE_OF_EXPERTS = PatternTemplate(
    pattern_id="mixture-of-experts",
    name="Mixture of Experts",
    version="1.0",
    category=PatternCategory.PARALLEL,
    complexity=PatternComplexity.ADVANCED,
    description="Route input to specialist agents based on conditions.",
    use_cases=[
        "Route to domain experts (legal, finance, medical)",
        "Content moderation by type",
        "Skill-based assignment",
        "Conditional expertise selection"
    ],
    diagram_ascii="""
    [Input]
      ↓
   [Router]
      ↓
    ┌─if condition_A → [ExpertA]─┐
    ├─if condition_B → [ExpertB]─┼→ [Aggregator] → [Output]
    └─if condition_C → [ExpertC]─┘
    """,
    placeholders=[
        PlaceholderNode(
            id="router",
            name="Router",
            description="Routes to appropriate experts",
            stage="input",
            required=True
        ),
        PlaceholderNode(
            id="experts",
            name="Experts",
            description="Specialist agents",
            stage="processing",
            is_array=True,
            required=True
        ),
        PlaceholderNode(
            id="aggregator",
            name="Aggregator",
            description="Combines expert results",
            stage="aggregation",
            required=True
        ),
    ],
    variables=[
        VariableParameter(
            name="branch_count",
            display_name="Number of Expert Branches",
            description="How many specialist branches? (2-10)",
            param_type="integer",
            default=3,
            min_value=2,
            max_value=10
        )
    ],
    code_template="pattern_templates/mixture_of_experts.py.jinja2",
    example_workflow={
        "name": "support-ticket-routing",
        "router": "TicketRouter",
        "branches": [
            {"condition": "type == 'billing'", "expert": "BillingExpert"},
            {"condition": "type == 'technical'", "expert": "TechExpert"},
            {"condition": "type == 'legal'", "expert": "LegalExpert"}
        ],
        "aggregator": "ResponseAggregator"
    }
)

# ============================================================================
# PATTERN 5: SEQUENTIAL PIPELINE
# ============================================================================

SEQUENTIAL_PIPELINE = PatternTemplate(
    pattern_id="sequential-pipeline",
    name="Sequential Pipeline",
    version="1.0",
    category=PatternCategory.SEQUENTIAL,
    complexity=PatternComplexity.SIMPLE,
    description="Multi-stage sequential processing where each stage transforms data.",
    use_cases=[
        "Extract → Validate → Enrich → Store",
        "Data transformation pipeline",
        "Workflow progression through stages",
        "Assembly line processing"
    ],
    diagram_ascii="""
    [Input] → [Stage1] → [Stage2] → [Stage3] → [Output]
    """,
    placeholders=[
        PlaceholderNode(
            id=f"stage_{i}",
            name=f"Stage {i}",
            description=f"Processing stage {i}",
            stage="processing" if i < 3 else "output",
            required=True
        )
        for i in range(1, 4)
    ],
    variables=[
        VariableParameter(
            name="stage_count",
            display_name="Number of Stages",
            description="How many pipeline stages? (2-10)",
            param_type="integer",
            default=3,
            min_value=2,
            max_value=10
        )
    ],
    code_template="pattern_templates/sequential_pipeline.py.jinja2",
    example_workflow={
        "name": "document-pipeline",
        "stages": ["DocumentExtractor", "DataValidator", "DataEnricher", "DocumentStore"]
    }
)

# ============================================================================
# PATTERN 6: SUPERVISOR/MANAGER
# ============================================================================

SUPERVISOR_MANAGER = PatternTemplate(
    pattern_id="supervisor-manager",
    name="Supervisor/Manager",
    version="1.0",
    category=PatternCategory.SEQUENTIAL,
    complexity=PatternComplexity.ADVANCED,
    description="One supervisor agent decides routing and orchestrates execution.",
    use_cases=[
        "Intelligent routing based on input analysis",
        "Conditional multi-agent workflows",
        "Load-aware routing",
        "Specialized workflows by category (MOST COMMON REAL-WORLD PATTERN)"
    ],
    diagram_ascii="""
    [Input]
      ↓
 [Supervisor]
    ↓ (analyzes & decides)
    ├─→ Route A: [Agent1, Agent2]
    ├─→ Route B: [Agent3]
    └─→ Route C: [Agent4, Agent5, Agent6]
        ↓
    [Aggregator]
      ↓
   [Output]
    """,
    placeholders=[
        PlaceholderNode(
            id="supervisor",
            name="Supervisor",
            description="Analyzes input and decides routing",
            stage="input",
            required=True,
            agent_type="decision_maker"
        ),
        PlaceholderNode(
            id="agents",
            name="Routing Agents",
            description="Agents invoked by supervisor",
            stage="processing",
            is_array=True,
            required=True
        ),
        PlaceholderNode(
            id="aggregator",
            name="Aggregator",
            description="Combines results from all routes",
            stage="aggregation",
            required=True
        ),
    ],
    variables=[
        VariableParameter(
            name="branch_count",
            display_name="Number of Routing Branches",
            description="How many possible routes? (2-10)",
            param_type="integer",
            default=3,
            min_value=2,
            max_value=10
        )
    ],
    code_template="pattern_templates/supervisor_manager.py.jinja2",
    example_workflow={
        "name": "loan-approval",
        "supervisor": "LoanSupervisor",
        "routing_branches": [
            {
                "condition": "loan_type == 'mortgage' AND amount > $500k",
                "agents": ["MortgageAnalyst", "ComplianceReviewer", "ExecutiveApprover"]
            },
            {
                "condition": "loan_type == 'auto'",
                "agents": ["AutoLoanAnalyst", "StandardApprover"]
            },
            {
                "condition": "else",
                "agents": ["PersonalLoanAnalyst"]
            }
        ],
        "aggregator": "LoanDecisionAggregator"
    }
)

# ============================================================================
# PATTERN 7: HIERARCHICAL TEAMS
# ============================================================================

HIERARCHICAL_TEAMS = PatternTemplate(
    pattern_id="hierarchical-teams",
    name="Hierarchical Teams",
    version="1.0",
    category=PatternCategory.SEQUENTIAL,
    complexity=PatternComplexity.ADVANCED,
    description="Multi-level delegation: top-level delegates to middle managers, who orchestrate teams.",
    use_cases=[
        "Mirror organizational structure",
        "Multi-team collaboration",
        "Escalation workflows",
        "Complex project management"
    ],
    diagram_ascii="""
    [Input]
      ↓
    [CEO/Lead]
      ↓
    ├─→ [Dir1] → [TeamA: Agent1, Agent2, Agent3]
    ├─→ [Dir2] → [TeamB: Agent4, Agent5]
    └─→ [Dir3] → [TeamC: Agent6, Agent7, Agent8]
        ↓
    [Final Aggregator]
      ↓
   [Output]
    """,
    placeholders=[
        PlaceholderNode(
            id="lead",
            name="Lead/CEO",
            description="Top-level decision maker",
            stage="input",
            required=True
        ),
        PlaceholderNode(
            id="directors",
            name="Directors",
            description="Middle-level managers",
            stage="processing",
            is_array=True,
            required=True
        ),
        PlaceholderNode(
            id="teams",
            name="Team Members",
            description="Team members for each director",
            stage="processing",
            is_array=True,
            required=True
        ),
        PlaceholderNode(
            id="final",
            name="Final Aggregator",
            description="Combines all results",
            stage="aggregation",
            required=True
        ),
    ],
    variables=[
        VariableParameter(
            name="director_count",
            display_name="Number of Directors",
            description="How many director-level managers? (2-5)",
            param_type="integer",
            default=3,
            min_value=2,
            max_value=5
        ),
        VariableParameter(
            name="team_size",
            display_name="Team Size per Director",
            description="How many agents per director? (2-5)",
            param_type="integer",
            default=3,
            min_value=2,
            max_value=5
        )
    ],
    code_template="pattern_templates/hierarchical_teams.py.jinja2",
    example_workflow={
        "name": "project-management",
        "lead": "ProjectManager",
        "directors": [
            {
                "name": "DesignDirector",
                "team": ["ArchitectAgent", "DesignSystemAgent", "UIAgent"]
            },
            {
                "name": "EngineeringDirector",
                "team": ["BackendAgent", "FrontendAgent", "TestingAgent"]
            }
        ],
        "final": "ProjectAggregator"
    }
)

# ============================================================================
# PATTERN 8: FALLBACK CHAIN
# ============================================================================

FALLBACK_CHAIN = PatternTemplate(
    pattern_id="fallback-chain",
    name="Fallback Chain",
    version="1.0",
    category=PatternCategory.SEQUENTIAL,
    complexity=PatternComplexity.INTERMEDIATE,
    description="Try agents in sequence; if one fails, try the next.",
    use_cases=[
        "Degraded operation (fast → accurate → expensive)",
        "Fallback agents if primary overloaded",
        "Progressive refinement",
        "System resilience"
    ],
    diagram_ascii="""
    [Input]
      ↓
    [Agent1] → Success? ✓ → [Output]
      ↓ (fail)
    [Agent2] → Success? ✓ → [Output]
      ↓ (fail)
    [Agent3] → Success? ✓ → [Output]
      ↓ (fail)
    [Escalate/Error]
    """,
    placeholders=[
        PlaceholderNode(
            id=f"agent_{i}",
            name=f"Agent {i}",
            description=f"Fallback option {i}",
            stage="processing",
            required=True
        )
        for i in range(1, 4)
    ],
    variables=[
        VariableParameter(
            name="agent_count",
            display_name="Fallback Agents",
            description="How many agents in fallback chain? (2-5)",
            param_type="integer",
            default=3,
            min_value=2,
            max_value=5
        )
    ],
    code_template="pattern_templates/fallback_chain.py.jinja2",
    example_workflow={
        "name": "document-analysis",
        "agents": ["FastModel", "AccurateModel", "ExpensiveModel"],
        "timeouts": [5, 30, 120],
        "fallback_escalate_to": "HumanReview"
    }
)

# ============================================================================
# PATTERN 9: RETRY LOOP
# ============================================================================

RETRY_LOOP = PatternTemplate(
    pattern_id="retry-loop",
    name="Retry Loop",
    version="1.0",
    category=PatternCategory.SEQUENTIAL,
    complexity=PatternComplexity.INTERMEDIATE,
    description="Retry a single agent with exponential backoff on transient failures.",
    use_cases=[
        "Handle transient failures (network, temporary unavailability)",
        "Exponential backoff strategy",
        "Circuit breaker pattern",
        "Graceful degradation"
    ],
    diagram_ascii="""
    [Input]
      ↓
    [Agent]
      ↓
    Success? ✓ → [Output]
      ↓
    Fail? → Backoff → Retry
      ↓
    Max retries exceeded? → [Fallback Agent]
      ↓
    [Output]
    """,
    placeholders=[
        PlaceholderNode(
            id="primary",
            name="Primary Agent",
            description="Main agent to retry",
            stage="processing",
            required=True
        ),
        PlaceholderNode(
            id="fallback",
            name="Fallback Agent",
            description="Agent if max retries exceeded",
            stage="processing",
            required=False
        ),
    ],
    variables=[
        VariableParameter(
            name="max_retries",
            display_name="Max Retries",
            description="Maximum retry attempts? (1-10)",
            param_type="integer",
            default=3,
            min_value=1,
            max_value=10
        ),
        VariableParameter(
            name="backoff_strategy",
            display_name="Backoff Strategy",
            description="How to space retries?",
            param_type="string",
            default="exponential",
            choices=["fixed", "linear", "exponential"]
        ),
        VariableParameter(
            name="initial_backoff_ms",
            display_name="Initial Backoff (ms)",
            description="Starting wait time between retries",
            param_type="integer",
            default=100,
            min_value=10,
            max_value=5000
        )
    ],
    code_template="pattern_templates/retry_loop.py.jinja2",
    example_workflow={
        "name": "api-call",
        "primary": "ExternalAPIAgent",
        "max_retries": 3,
        "backoff_strategy": "exponential",
        "initial_backoff_ms": 100,
        "fallback": "CacheAgent"
    }
)

# ============================================================================
# PATTERN 10: DIAMOND
# ============================================================================

DIAMOND = PatternTemplate(
    pattern_id="diamond",
    name="Diamond",
    version="1.0",
    category=PatternCategory.CONDITIONAL,
    complexity=PatternComplexity.INTERMEDIATE,
    description="Two independent paths process in parallel, then converge.",
    use_cases=[
        "Parallel analysis via two methods",
        "Risk assessment with dual evaluation",
        "Quality check requiring agreement",
        "Dual validation and comparison"
    ],
    diagram_ascii="""
    [Input]
      ↓
    [PathA] ┐
    [PathB] ├→ [Convergence] → [Output]
    """,
    placeholders=[
        PlaceholderNode(
            id="path_a",
            name="Path A",
            description="First parallel path",
            stage="processing",
            required=True
        ),
        PlaceholderNode(
            id="path_b",
            name="Path B",
            description="Second parallel path",
            stage="processing",
            required=True
        ),
        PlaceholderNode(
            id="convergence",
            name="Convergence",
            description="Validates/merges results from both paths",
            stage="aggregation",
            required=True
        ),
    ],
    variables=[],
    code_template="pattern_templates/diamond.py.jinja2",
    example_workflow={
        "name": "fraud-detection",
        "path_a": "FraudModelA",
        "path_b": "FraudModelB",
        "convergence": "FraudValidator"
    }
)

# ============================================================================
# PATTERN 11: CONDITIONAL BRANCHING
# ============================================================================

CONDITIONAL_BRANCHING = PatternTemplate(
    pattern_id="conditional-branching",
    name="Conditional Branching",
    version="1.0",
    category=PatternCategory.CONDITIONAL,
    complexity=PatternComplexity.ADVANCED,
    description="Complex routing with multiple conditions and paths.",
    use_cases=[
        "Complex business logic routing",
        "Compliance routing by regulation",
        "Risk-based routing by score",
        "Type-based handling without custom code"
    ],
    diagram_ascii="""
    [Input]
      ↓
    [Router]
    ├─if condition₁ → [Path₁]─┐
    ├─if condition₂ → [Path₂]─┼→ [Merger] → [Output]
    ├─if condition₃ → [Path₃]─┘
    └─else → [Default]
    """,
    placeholders=[
        PlaceholderNode(
            id="router",
            name="Router",
            description="Decision router",
            stage="input",
            required=True,
            agent_type="router"
        ),
        PlaceholderNode(
            id="paths",
            name="Conditional Paths",
            description="Agents for each condition",
            stage="processing",
            is_array=True,
            required=True
        ),
        PlaceholderNode(
            id="merger",
            name="Merger",
            description="Combines results from paths",
            stage="aggregation",
            required=True
        ),
    ],
    variables=[
        VariableParameter(
            name="branch_count",
            display_name="Number of Conditions",
            description="How many conditional branches? (2-10)",
            param_type="integer",
            default=3,
            min_value=2,
            max_value=10
        )
    ],
    code_template="pattern_templates/conditional_branching.py.jinja2",
    example_workflow={
        "name": "loan-routing",
        "router": "LoanRouter",
        "conditions": [
            {
                "expression": "amount > $1M AND country == 'EU'",
                "agents": ["ComplianceReviewer", "RegulatoryAgent"]
            },
            {
                "expression": "100k < amount ≤ $1M",
                "agents": ["StandardAnalyst"]
            },
            {
                "expression": "else",
                "agents": ["AutoApprovalAgent"]
            }
        ],
        "merger": "DecisionMerger"
    }
)

# ============================================================================
# PATTERN 12: TREE-REDUCE
# ============================================================================

TREE_REDUCE = PatternTemplate(
    pattern_id="tree-reduce",
    name="Tree-Reduce",
    version="1.0",
    category=PatternCategory.REDUCTION,
    complexity=PatternComplexity.ADVANCED,
    description="Hierarchical reduction: pair-wise reduction across levels.",
    use_cases=[
        "Large batch hierarchical aggregation",
        "Tree-structured merge",
        "Scalable summarization",
        "Distributed consensus voting"
    ],
    diagram_ascii="""
    Layer 0: [Item₁][Item₂][Item₃][Item₄][Item₅][Item₆][Item₇][Item₈]
               ↓       ↓       ↓       ↓       ↓       ↓       ↓       ↓
    Layer 1: [Red(1,2)] [Red(3,4)] [Red(5,6)] [Red(7,8)]
               ↓              ↓              ↓              ↓
    Layer 2:  [Red(1-2,3-4)]  [Red(5-6,7-8)]
               ↓                      ↓
    Layer 3:          [Final Reduce]
    """,
    placeholders=[
        PlaceholderNode(
            id=f"level_{i}",
            name=f"Level {i} Reducer",
            description=f"Reduction at level {i}",
            stage="processing" if i < 3 else "aggregation",
            required=True
        )
        for i in range(1, 4)
    ],
    variables=[
        VariableParameter(
            name="input_count",
            display_name="Initial Item Count",
            description="How many items to reduce? (4, 8, 16, 32)",
            param_type="integer",
            default=8,
            min_value=4,
            max_value=32,
            choices=["4", "8", "16", "32"]
        ),
        VariableParameter(
            name="reduction_factor",
            display_name="Reduction Factor",
            description="Items per reduction node (2, 3, or 4)",
            param_type="integer",
            default=2,
            min_value=2,
            max_value=4
        )
    ],
    code_template="pattern_templates/tree_reduce.py.jinja2",
    example_workflow={
        "name": "batch-aggregation",
        "input_count": 8,
        "reduction_factor": 2,
        "level_reducers": [
            "PairwiseReducer",
            "GroupReducer",
            "FinalReducer"
        ]
    }
)


# ============================================================================
# PATTERN 13: RALPH LOOP
# ============================================================================

RALPH_LOOP = PatternTemplate(
    pattern_id="ralph-loop",
    name="Ralph Loop",
    version="1.0",
    category=PatternCategory.SEQUENTIAL,
    complexity=PatternComplexity.ADVANCED,
    description=(
        "Autonomous iteration with fresh context per round: planner reads spec from disk, "
        "implementer makes changes, verifier runs machine checks (tests/linter). "
        "Loops until verifier passes or spawn budget exhausted. "
        "Named after Geoffrey Huntley's Ralph Wiggum loop pattern."
    ),
    use_cases=[
        "Overnight autonomous coding — run until all tests pass",
        "Self-healing pipelines that fix their own failures",
        "Spec-driven implementation where completion is machine-verifiable",
        "Iterative document generation against a compliance checklist",
        "Autonomous refactoring with linter/type-check exit criteria",
    ],
    diagram_ascii="""
    [Spec / State on Disk]
          ↓
    [Planner] (reads spec fresh)
          ↓
    next_task → [Implementer]
          ↓
    result → [Verifier] (machine checks)
          ↓
    passed? ✓ → [Output]
          ↓
    fail? → write diagnostics → next iteration (fresh context)
          ↓
    budget exhausted? → [Error]
    """,
    placeholders=[
        PlaceholderNode(
            id="planner",
            name="Planner",
            description="Reads spec and state from disk; selects the next task for this iteration",
            stage="input",
            required=True
        ),
        PlaceholderNode(
            id="implementer",
            name="Implementer",
            description="Executes the planned task and writes changes to the filesystem",
            stage="processing",
            required=True
        ),
        PlaceholderNode(
            id="verifier",
            name="Verifier",
            description="Runs machine checks (tests, linter, type checker) and outputs passed boolean",
            stage="output",
            required=True
        ),
    ],
    variables=[
        VariableParameter(
            name="spawn_budget",
            display_name="Spawn Budget",
            description="Maximum iterations before giving up (1-50)",
            param_type="integer",
            default=10,
            min_value=1,
            max_value=50
        ),
    ],
    code_template="pattern_templates/ralph_loop.py.jinja2",
    example_workflow={
        "name": "autonomous-coder",
        "planner": "SpecPlannerAgent",
        "implementer": "CodeImplementerAgent",
        "verifier": "TestRunnerAgent",
        "spawn_budget": 10,
    }
)


# ============================================================================
# PATTERN REGISTRY
# ============================================================================

class PatternRegistry:
    """Manages all patterns (built-in + user-defined)."""

    def __init__(self):
        self.patterns: Dict[str, PatternTemplate] = {}
        self._initialize_builtin_patterns()

    def _initialize_builtin_patterns(self) -> None:
        """Register all built-in patterns."""
        builtin_patterns = [
            FAN_OUT_FAN_IN,
            MAP_REDUCE,
            ROUND_ROBIN,
            MIXTURE_OF_EXPERTS,
            SEQUENTIAL_PIPELINE,
            SUPERVISOR_MANAGER,
            HIERARCHICAL_TEAMS,
            FALLBACK_CHAIN,
            RETRY_LOOP,
            DIAMOND,
            CONDITIONAL_BRANCHING,
            TREE_REDUCE,
            RALPH_LOOP,
        ]

        for pattern in builtin_patterns:
            self.register_pattern(pattern)
            logger.info(f"Registered pattern: {pattern.pattern_id}")

    def register_pattern(self, pattern: PatternTemplate) -> None:
        """Register a new pattern (built-in or user-defined)."""
        self.patterns[pattern.pattern_id] = pattern
        logger.debug(f"Pattern '{pattern.pattern_id}' registered")

    def get_pattern(self, pattern_id: str) -> Optional[PatternTemplate]:
        """Get pattern by ID."""
        return self.patterns.get(pattern_id)

    def list_patterns(self,
                      category: Optional[PatternCategory] = None,
                      complexity: Optional[PatternComplexity] = None) -> List[PatternTemplate]:
        """List patterns with optional filters."""
        patterns = list(self.patterns.values())

        if category:
            patterns = [p for p in patterns if p.category == category]

        if complexity:
            patterns = [p for p in patterns if p.complexity == complexity]

        return sorted(patterns, key=lambda p: p.pattern_id)

    def search_patterns(self, query: str) -> List[PatternTemplate]:
        """Search patterns by keyword."""
        query_lower = query.lower()
        results = []

        for pattern in self.patterns.values():
            if (query_lower in pattern.pattern_id.lower() or
                    query_lower in pattern.name.lower() or
                    query_lower in pattern.description.lower() or
                    any(query_lower in uc.lower() for uc in pattern.use_cases)):
                results.append(pattern)

        return results

    def get_statistics(self) -> Dict:
        """Get registry statistics."""
        return {
            "total_patterns": len(self.patterns),
            "by_category": {
                cat.value: len([p for p in self.patterns.values() if p.category == cat])
                for cat in PatternCategory
            },
            "by_complexity": {
                cplx.value: len([p for p in self.patterns.values() if p.complexity == cplx])
                for cplx in PatternComplexity
            }
        }


# Global registry instance
PATTERN_REGISTRY = PatternRegistry()
