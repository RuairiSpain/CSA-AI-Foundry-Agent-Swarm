"""
SAFE Framework — unified models (Phases 1-9).

RouteChain models are in chain_models.py and re-exported here for convenience:
    from safe_core.models import RouteChain, RouteChainStep

This file merges two groups of models:
  - p4 runtime models (dataclass-based): used by interview / generator / validator
  - p1-3 Pydantic schema models: static/dynamic route definitions
"""

# =============================================================================
# SECTION A — p4 RUNTIME MODELS (dataclass-based)
# =============================================================================

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Literal
from enum import Enum
from datetime import datetime

from .chain_models import RouteChain, RouteChainStep  # noqa: F401 — re-export


class RoutePattern(str, Enum):
    """Supported route patterns"""
    SUPERVISOR_MANAGER = "supervisor-manager"
    FAN_OUT_FAN_IN = "fan-out-fan-in"
    MAP_REDUCE = "map-reduce"
    SEQUENTIAL_PIPELINE = "sequential-pipeline"
    ROUND_ROBIN = "round-robin"
    MIXTURE_OF_EXPERTS = "mixture-of-experts"
    HIERARCHICAL_TEAMS = "hierarchical-teams"
    FALLBACK_CHAIN = "fallback-chain"
    RETRY_LOOP = "retry-loop"
    DIAMOND = "diamond"
    CONDITIONAL_BRANCHING = "conditional-branching"
    TREE_REDUCE = "tree-reduce"
    # Backlog patterns
    EVALUATOR_OPTIMIZER  = "evaluator-optimizer"
    HUMAN_IN_THE_LOOP    = "human-in-the-loop"
    REFLECTION           = "reflection"
    ORCHESTRATOR_WORKERS = "orchestrator-workers"
    RAG                  = "rag"
    PLANNING             = "planning"
    GATE_GUARD           = "gate-guard"
    SELF_CONSISTENCY     = "self-consistency"
    DEBATE               = "debate"
    AGENT_AS_A_TOOL      = "agent-as-a-tool"
    MEMORY_AUGMENTED     = "memory-augmented"
    EVENT_DRIVEN         = "event-driven"
    CHECKPOINT_RESUME    = "checkpoint-resume"
    BUDGET_AWARE_ROUTING = "budget-aware-routing"
    ADAPTIVE_ROUTING     = "adaptive-routing"


@dataclass
class Agent:
    """Agent definition from catalog"""
    name: str
    category: str
    version: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    description: str = ""
    example_usage: str = ""
    # Optional reference to a HandoffDefinition by name. When set, this agent
    # delegates subtasks to the named handoff pool via ConnectedAgentTool at
    # runtime. The route's deterministic path continues after the handoff returns.
    handoff_ref: Optional[str] = None


@dataclass
class RouteDefinition:
    """Complete route definition (p4 runtime model)"""
    name: str
    pattern: RoutePattern
    agents: Dict[str, Agent]
    description: str = ""
    timeout_seconds: int = 120
    per_agent_timeout_seconds: int = 60
    csa_email: str = ""
    tags: List[str] = field(default_factory=list)

    # Pattern-specific config
    routing_field: Optional[str] = None   # For supervisor-manager
    routing_rules: Dict[str, str] = field(default_factory=dict)  # value -> agent_key
    fallback_agent: Optional[str] = None

    created_at: datetime = field(default_factory=datetime.now)
    version: str = "v1.0"


@dataclass
class ValidationError:
    """Validation error details"""
    error_type: str   # "contract_mismatch", "circular_dependency", "timeout", etc.
    message: str
    suggested_solutions: List[str] = field(default_factory=list)


@dataclass
class GeneratedRoute:
    """Output of code generation"""
    route_code: str          # Generated Python code
    requirements_txt: str
    config_yaml: str
    test_data_json: str
    metadata: Dict[str, Any]

    def save_to_disk(self, route_dir: str) -> None:
        """Save generated files to disk"""
        import os
        os.makedirs(route_dir, exist_ok=True)

        with open(f"{route_dir}/route.py", "w") as f:
            f.write(self.route_code)
        with open(f"{route_dir}/requirements.txt", "w") as f:
            f.write(self.requirements_txt)
        with open(f"{route_dir}/config.yaml", "w") as f:
            f.write(self.config_yaml)
        with open(f"{route_dir}/test_data.json", "w") as f:
            f.write(self.test_data_json)


@dataclass
class TestResult:
    """Route test result"""
    success: bool
    test_cases_passed: int
    test_cases_failed: int
    errors: List[str] = field(default_factory=list)
    execution_times: Dict[str, float] = field(default_factory=dict)


# =============================================================================
# SECTION B — p1-3 PYDANTIC SCHEMA MODELS
# =============================================================================

from pydantic import BaseModel, Field, field_validator


class ErrorPolicy(str, Enum):
    """How to handle agent failures."""
    FAIL_HARD = "fail_hard"
    SKIP_IF_ERROR = "skip_if_error"
    RETRY = "retry"


class AgentConfig(BaseModel):
    """Configuration for an agent in a route."""
    name: str = Field(..., description="Agent name from catalog")
    version: str = Field(default="latest", description="Agent version")
    error_policy: ErrorPolicy = Field(
        default=ErrorPolicy.FAIL_HARD,
        description="How to handle failures",
    )
    timeout_seconds: int = Field(default=3600, description="Timeout in seconds")


class ConditionalRoute(BaseModel):
    """A conditional branch in a dynamic route."""
    condition: str = Field(..., description="Condition expression (e.g., 'doc_type == contract')")
    agents: List[str] = Field(..., description="Agents to invoke if condition is true")


class StaticRouteDefinition(BaseModel):
    """Definition for a static route with fixed topology."""
    name: str = Field(..., min_length=1, description="Route name")
    version: str = Field(default="1.0", description="Route version")
    description: str = Field(default="", description="Route description")
    route_type: Literal["static"] = "static"
    pattern: Literal["sequential", "fan_out", "fan_in", "handoff"] = Field(
        ..., description="Orchestration pattern"
    )
    agents: List[AgentConfig] = Field(..., min_length=1, description="Agents in order")
    parallel_groups: Optional[List[List[str]]] = Field(
        default=None, description="Groups of agents to run in parallel"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate route name format."""
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Route name must be alphanumeric with hyphens/underscores")
        return v.lower()


class DynamicRouteDefinition(BaseModel):
    """Definition for a dynamic route with decision-driven routing."""
    name: str = Field(..., min_length=1, description="Route name")
    version: str = Field(default="1.0", description="Route version")
    description: str = Field(default="", description="Route description")
    route_type: Literal["dynamic"] = "dynamic"
    decision_inputs: List[str] = Field(..., description="Input variables for decisions")
    routes: List[ConditionalRoute] = Field(..., min_length=1, description="Conditional routes")
    orchestrator_agent: Optional[str] = Field(
        default=None, description="Agent that coordinates the flow"
    )
    fallback_agents: List[str] = Field(
        default_factory=list, description="Fallback agents if no condition matches"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate route name format."""
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Route name must be alphanumeric with hyphens/underscores")
        return v.lower()


class RouteMetadata(BaseModel):
    """Metadata for a route."""
    author: str = Field(..., description="Author/team name")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    sla_latency_p95_seconds: float = Field(default=60.0, description="SLA target")
    max_cost_per_run: float = Field(default=1.50, description="Cost budget")
    error_recovery: Dict[str, str] = Field(
        default_factory=dict, description="Error recovery policies by agent"
    )
