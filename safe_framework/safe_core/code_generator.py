"""Code generation from route definitions"""

import json
from pathlib import Path
from typing import Callable
from jinja2 import Environment, FileSystemLoader
from .models import RouteDefinition, GeneratedRoute, RoutePattern, ValidationError
from .config import config

_PATTERNS_DIR = Path(__file__).parent.parent / "agents" / "patterns"

_PATTERN_TEMPLATE_DIRS = {
    RoutePattern.SUPERVISOR_MANAGER:   _PATTERNS_DIR / "supervisor-manager",
    RoutePattern.FAN_OUT_FAN_IN:       _PATTERNS_DIR / "fan-out-fan-in",
    RoutePattern.MAP_REDUCE:           _PATTERNS_DIR / "map-reduce",
    RoutePattern.SEQUENTIAL_PIPELINE:  _PATTERNS_DIR / "sequential-pipeline",
    RoutePattern.ROUND_ROBIN:          _PATTERNS_DIR / "round-robin",
    RoutePattern.MIXTURE_OF_EXPERTS:   _PATTERNS_DIR / "mixture-of-experts",
    RoutePattern.HIERARCHICAL_TEAMS:   _PATTERNS_DIR / "hierarchical-teams",
    RoutePattern.FALLBACK_CHAIN:       _PATTERNS_DIR / "fallback-chain",
    RoutePattern.RETRY_LOOP:           _PATTERNS_DIR / "retry-loop",
    RoutePattern.DIAMOND:              _PATTERNS_DIR / "diamond",
    RoutePattern.CONDITIONAL_BRANCHING: _PATTERNS_DIR / "conditional-branching",
    RoutePattern.TREE_REDUCE:          _PATTERNS_DIR / "tree-reduce",
    # Backlog patterns
    RoutePattern.EVALUATOR_OPTIMIZER:  _PATTERNS_DIR / "evaluator-optimizer",
    RoutePattern.HUMAN_IN_THE_LOOP:    _PATTERNS_DIR / "human-in-the-loop",
    RoutePattern.REFLECTION:           _PATTERNS_DIR / "reflection",
    RoutePattern.ORCHESTRATOR_WORKERS: _PATTERNS_DIR / "orchestrator-workers",
    RoutePattern.RAG:                  _PATTERNS_DIR / "rag",
    RoutePattern.PLANNING:             _PATTERNS_DIR / "planning",
    RoutePattern.GATE_GUARD:           _PATTERNS_DIR / "gate-guard",
    RoutePattern.SELF_CONSISTENCY:     _PATTERNS_DIR / "self-consistency",
    RoutePattern.DEBATE:               _PATTERNS_DIR / "debate",
    RoutePattern.AGENT_AS_A_TOOL:      _PATTERNS_DIR / "agent-as-a-tool",
    RoutePattern.MEMORY_AUGMENTED:     _PATTERNS_DIR / "memory-augmented",
    RoutePattern.EVENT_DRIVEN:         _PATTERNS_DIR / "event-driven",
    RoutePattern.CHECKPOINT_RESUME:    _PATTERNS_DIR / "checkpoint-resume",
    RoutePattern.BUDGET_AWARE_ROUTING: _PATTERNS_DIR / "budget-aware-routing",
    RoutePattern.ADAPTIVE_ROUTING:            _PATTERNS_DIR / "adaptive-routing",
    RoutePattern.PLANNER_GENERATOR_EVALUATOR: _PATTERNS_DIR / "planner-generator-evaluator",
    RoutePattern.LATS:                        _PATTERNS_DIR / "lats",
    RoutePattern.RALPH_LOOP:                  _PATTERNS_DIR / "ralph-loop",
    # Agent-loop patterns
    RoutePattern.REACT_LOOP:                  _PATTERNS_DIR / "react-loop",
    RoutePattern.GOAL_DRIVEN_LOOP:            _PATTERNS_DIR / "goal-driven-loop",
    RoutePattern.INTERVAL_LOOP:               _PATTERNS_DIR / "interval-loop",
}

def _get_template(pattern: RoutePattern):
    template_dir = _PATTERN_TEMPLATE_DIRS[pattern]
    env = Environment(loader=FileSystemLoader(str(template_dir)), keep_trailing_newline=True)
    return env.get_template("route.py.jinja2")


class RouteCodeGenerator:
    """Generates production-ready route code from definitions"""

    @staticmethod
    def generate(route_def: RouteDefinition, *, skip_validation: bool = False) -> GeneratedRoute:
        """Generate complete route from definition.

        Runs ContractValidator before rendering so that a missing required agent
        raises a structured ValueError instead of a bare KeyError deep inside a
        _generate_* method.
        """
        from .validator import ContractValidator

        if not skip_validation:
            errors = ContractValidator.validate_route(route_def)
            if errors:
                messages = "; ".join(e.message for e in errors)
                raise ValueError(f"Route '{route_def.name}' failed validation: {messages}")

        generator = _GENERATORS.get(route_def.pattern)
        if generator is None:
            raise NotImplementedError(f"Pattern {route_def.pattern} not yet implemented")
        return generator(route_def)

    @staticmethod
    def _class_name(route_name: str) -> str:
        return "".join(w.capitalize() for w in route_name.replace("-", "_").split("_"))

    @staticmethod
    def _base_context(
        route_def: RouteDefinition,
        input_key: str | None = None,
        output_key: str | None = None,
    ) -> dict:
        """Build the common Jinja2 context shared by every pattern generator.

        If *input_key*/*output_key* are given, resolves required fields from
        those agents (used to populate required_input_fields / required_output_fields
        in the template).
        """
        input_agent = route_def.agents.get(input_key) if input_key else None
        output_agent = route_def.agents.get(output_key) if output_key else None
        input_required = input_agent.input_schema.get("required", []) if input_agent else []
        output_required = output_agent.output_schema.get("required", []) if output_agent else []
        return {
            "route_name": route_def.name,
            "class_name": RouteCodeGenerator._class_name(route_def.name),
            "description": route_def.description,
            "pattern": route_def.pattern.value,
            "agent_names": ", ".join(route_def.agents.keys()),
            "created_at": route_def.created_at.strftime("%Y-%m-%d"),
            "agents": route_def.agents,
            "required_input_fields": json.dumps(input_required),
            "required_output_fields": json.dumps(output_required),
        }

    @staticmethod
    def _wrap(
        route_def: RouteDefinition,
        context: dict,
        pattern: RoutePattern,
        extra_metadata: dict | None = None,
    ) -> GeneratedRoute:
        """Render *pattern*'s template with *context* and return a GeneratedRoute."""
        route_code = _get_template(pattern).render(**context)
        metadata = {
            "pattern": route_def.pattern.value,
            "agents": list(route_def.agents.keys()),
            "created_at": route_def.created_at.isoformat(),
            "version": "v1.0",
            **(extra_metadata or {}),
        }
        return GeneratedRoute(
            route_code=route_code,
            requirements_txt=RouteCodeGenerator._generate_requirements(route_def),
            config_yaml=RouteCodeGenerator._generate_config(route_def),
            test_data_json=RouteCodeGenerator._generate_test_data(route_def),
            metadata=metadata,
        )

    # ------------------------------------------------------------------
    # Core pattern generators (p4 library)
    # ------------------------------------------------------------------

    @staticmethod
    def _generate_supervisor_manager(route_def: RouteDefinition) -> GeneratedRoute:
        specialists = {k: v for k, v in route_def.agents.items() if k.startswith("specialist_")}
        ctx = RouteCodeGenerator._base_context(route_def, "supervisor", "aggregator")
        ctx.update({
            "supervisor_key": "supervisor",
            "specialists": specialists,
            "aggregator_key": "aggregator",
            "routing_field": route_def.routing_field or "specialist",
        })
        return RouteCodeGenerator._wrap(route_def, ctx, RoutePattern.SUPERVISOR_MANAGER)

    @staticmethod
    def _generate_fan_out_fan_in(route_def: RouteDefinition) -> GeneratedRoute:
        processor_keys = sorted(k for k in route_def.agents if k.startswith("processor_"))
        input_key = processor_keys[0] if processor_keys else None
        ctx = RouteCodeGenerator._base_context(route_def, input_key, "aggregator")
        ctx.update({
            "processor_keys": processor_keys,
            "processor_count": len(processor_keys),
            "aggregator_key": "aggregator",
        })
        return RouteCodeGenerator._wrap(route_def, ctx, RoutePattern.FAN_OUT_FAN_IN)

    @staticmethod
    def _generate_map_reduce(route_def: RouteDefinition) -> GeneratedRoute:
        ctx = RouteCodeGenerator._base_context(route_def, "splitter", "reducer")
        ctx.update({"splitter_key": "splitter", "mapper_key": "mapper", "reducer_key": "reducer"})
        return RouteCodeGenerator._wrap(route_def, ctx, RoutePattern.MAP_REDUCE)

    @staticmethod
    def _generate_sequential_pipeline(route_def: RouteDefinition) -> GeneratedRoute:
        stage_keys = sorted(k for k in route_def.agents if k.startswith("stage_"))
        input_key = stage_keys[0] if stage_keys else None
        output_key = stage_keys[-1] if stage_keys else None
        ctx = RouteCodeGenerator._base_context(route_def, input_key, output_key)
        ctx.update({"stage_keys": stage_keys, "stage_count": len(stage_keys)})
        return RouteCodeGenerator._wrap(route_def, ctx, RoutePattern.SEQUENTIAL_PIPELINE)

    @staticmethod
    def _generate_round_robin(route_def: RouteDefinition) -> GeneratedRoute:
        worker_keys = sorted(k for k in route_def.agents if k.startswith("worker_"))
        output_key = worker_keys[0] if worker_keys else None
        ctx = RouteCodeGenerator._base_context(route_def, "dispatcher", output_key)
        ctx.update({
            "dispatcher_key": "dispatcher",
            "worker_keys": worker_keys,
            "worker_count": len(worker_keys),
        })
        return RouteCodeGenerator._wrap(route_def, ctx, RoutePattern.ROUND_ROBIN)

    @staticmethod
    def _generate_mixture_of_experts(route_def: RouteDefinition) -> GeneratedRoute:
        expert_keys = sorted(k for k in route_def.agents if k.startswith("expert_"))
        ctx = RouteCodeGenerator._base_context(route_def, "router", "aggregator")
        ctx.update({
            "router_key": "router",
            "expert_keys": expert_keys,
            "expert_count": len(expert_keys),
            "aggregator_key": "aggregator",
        })
        return RouteCodeGenerator._wrap(route_def, ctx, RoutePattern.MIXTURE_OF_EXPERTS)

    @staticmethod
    def _generate_hierarchical_teams(route_def: RouteDefinition) -> GeneratedRoute:
        team_keys = sorted(k for k in route_def.agents if k.startswith("team_"))
        ctx = RouteCodeGenerator._base_context(route_def, "coordinator", "aggregator")
        ctx.update({
            "coordinator_key": "coordinator",
            "team_keys": team_keys,
            "team_count": len(team_keys),
            "aggregator_key": "aggregator",
        })
        return RouteCodeGenerator._wrap(route_def, ctx, RoutePattern.HIERARCHICAL_TEAMS)

    @staticmethod
    def _generate_fallback_chain(route_def: RouteDefinition) -> GeneratedRoute:
        chain_keys = ["primary"] + sorted(k for k in route_def.agents if k.startswith("fallback_"))
        ctx = RouteCodeGenerator._base_context(route_def, "primary", "primary")
        ctx.update({"chain_keys": chain_keys})
        return RouteCodeGenerator._wrap(route_def, ctx, RoutePattern.FALLBACK_CHAIN)

    @staticmethod
    def _generate_retry_loop(route_def: RouteDefinition) -> GeneratedRoute:
        ctx = RouteCodeGenerator._base_context(route_def, "worker", "worker")
        ctx.update({
            "worker_key": "worker",
            "validator_key": "validator",
            "max_retries": config.retry_loop_max_retries,
        })
        return RouteCodeGenerator._wrap(route_def, ctx, RoutePattern.RETRY_LOOP)

    @staticmethod
    def _generate_diamond(route_def: RouteDefinition) -> GeneratedRoute:
        ctx = RouteCodeGenerator._base_context(route_def, "splitter", "merger")
        ctx.update({
            "splitter_key": "splitter",
            "left_key": "left_processor",
            "right_key": "right_processor",
            "merger_key": "merger",
        })
        return RouteCodeGenerator._wrap(route_def, ctx, RoutePattern.DIAMOND)

    @staticmethod
    def _generate_conditional_branching(route_def: RouteDefinition) -> GeneratedRoute:
        branch_keys = sorted(k for k in route_def.agents if k.startswith("branch_"))
        output_key = branch_keys[0] if branch_keys else None
        ctx = RouteCodeGenerator._base_context(route_def, "evaluator", output_key)
        ctx.update({
            "evaluator_key": "evaluator",
            "branch_keys": branch_keys,
            "branch_count": len(branch_keys),
            "condition_field": "branch",
        })
        return RouteCodeGenerator._wrap(route_def, ctx, RoutePattern.CONDITIONAL_BRANCHING)

    @staticmethod
    def _generate_tree_reduce(route_def: RouteDefinition) -> GeneratedRoute:
        leaf_keys = sorted(k for k in route_def.agents if k.startswith("leaf_"))
        input_key = leaf_keys[0] if leaf_keys else None
        ctx = RouteCodeGenerator._base_context(route_def, input_key, "reducer")
        ctx.update({"leaf_keys": leaf_keys, "leaf_count": len(leaf_keys), "reducer_key": "reducer"})
        return RouteCodeGenerator._wrap(route_def, ctx, RoutePattern.TREE_REDUCE)

    # ------------------------------------------------------------------
    # Backlog pattern generators
    # ------------------------------------------------------------------

    @staticmethod
    def _generate_evaluator_optimizer(route_def: RouteDefinition) -> GeneratedRoute:
        ctx = RouteCodeGenerator._base_context(route_def, "generator", "optimizer")
        ctx.update({"generator_key": "generator", "evaluator_key": "evaluator",
                     "optimizer_key": "optimizer",
                     "max_iterations": config.evaluator_optimizer_max_iterations,
                     "quality_threshold": config.evaluator_optimizer_quality_threshold})
        return RouteCodeGenerator._wrap(route_def, ctx, RoutePattern.EVALUATOR_OPTIMIZER)

    @staticmethod
    def _generate_human_in_the_loop(route_def: RouteDefinition) -> GeneratedRoute:
        ctx = RouteCodeGenerator._base_context(route_def, "pre_validator", "post_processor")
        ctx.update({"pre_validator_key": "pre_validator", "human_gate_key": "human_gate",
                     "post_processor_key": "post_processor"})
        return RouteCodeGenerator._wrap(route_def, ctx, RoutePattern.HUMAN_IN_THE_LOOP)

    @staticmethod
    def _generate_reflection(route_def: RouteDefinition) -> GeneratedRoute:
        ctx = RouteCodeGenerator._base_context(route_def, "generator", "refiner")
        ctx.update({"generator_key": "generator", "critic_key": "critic",
                     "refiner_key": "refiner",
                     "max_reflections": config.reflection_max_reflections})
        return RouteCodeGenerator._wrap(route_def, ctx, RoutePattern.REFLECTION)

    @staticmethod
    def _generate_orchestrator_workers(route_def: RouteDefinition) -> GeneratedRoute:
        worker_keys = sorted(k for k in route_def.agents if k.startswith("worker_"))
        ctx = RouteCodeGenerator._base_context(route_def, "orchestrator", "synthesizer")
        ctx.update({"orchestrator_key": "orchestrator", "worker_keys": worker_keys,
                     "synthesizer_key": "synthesizer"})
        return RouteCodeGenerator._wrap(route_def, ctx, RoutePattern.ORCHESTRATOR_WORKERS)

    @staticmethod
    def _generate_rag(route_def: RouteDefinition) -> GeneratedRoute:
        ctx = RouteCodeGenerator._base_context(route_def, "retriever", "generator")
        ctx.update({"retriever_key": "retriever", "reranker_key": "reranker",
                     "generator_key": "generator"})
        return RouteCodeGenerator._wrap(route_def, ctx, RoutePattern.RAG)

    @staticmethod
    def _generate_planning(route_def: RouteDefinition) -> GeneratedRoute:
        ctx = RouteCodeGenerator._base_context(route_def, "planner", "reviewer")
        ctx.update({"planner_key": "planner", "executor_key": "executor",
                     "reviewer_key": "reviewer"})
        return RouteCodeGenerator._wrap(route_def, ctx, RoutePattern.PLANNING)

    @staticmethod
    def _generate_gate_guard(route_def: RouteDefinition) -> GeneratedRoute:
        ctx = RouteCodeGenerator._base_context(route_def, "guard", "processor")
        ctx.update({"guard_key": "guard", "processor_key": "processor"})
        return RouteCodeGenerator._wrap(route_def, ctx, RoutePattern.GATE_GUARD)

    @staticmethod
    def _generate_self_consistency(route_def: RouteDefinition) -> GeneratedRoute:
        worker_keys = sorted(k for k in route_def.agents if k.startswith("worker_"))
        input_key = worker_keys[0] if worker_keys else "worker"
        ctx = RouteCodeGenerator._base_context(route_def, input_key, "voter")
        ctx.update({"worker_keys": worker_keys, "worker_count": len(worker_keys),
                     "voter_key": "voter"})
        return RouteCodeGenerator._wrap(route_def, ctx, RoutePattern.SELF_CONSISTENCY)

    @staticmethod
    def _generate_debate(route_def: RouteDefinition) -> GeneratedRoute:
        ctx = RouteCodeGenerator._base_context(route_def, "proposer", "judge")
        ctx.update({"proposer_key": "proposer", "challenger_key": "challenger",
                     "judge_key": "judge"})
        return RouteCodeGenerator._wrap(route_def, ctx, RoutePattern.DEBATE)

    @staticmethod
    def _generate_agent_as_a_tool(route_def: RouteDefinition) -> GeneratedRoute:
        sub_agent_keys = sorted(k for k in route_def.agents if k.startswith("sub_agent_"))
        output_key = sub_agent_keys[-1] if sub_agent_keys else "orchestrator"
        ctx = RouteCodeGenerator._base_context(route_def, "orchestrator", output_key)
        ctx.update({"orchestrator_key": "orchestrator", "sub_agent_keys": sub_agent_keys})
        return RouteCodeGenerator._wrap(route_def, ctx, RoutePattern.AGENT_AS_A_TOOL)

    @staticmethod
    def _generate_memory_augmented(route_def: RouteDefinition) -> GeneratedRoute:
        ctx = RouteCodeGenerator._base_context(route_def, "memory_reader", "memory_writer")
        ctx.update({"memory_reader_key": "memory_reader", "processor_key": "processor",
                     "memory_writer_key": "memory_writer"})
        return RouteCodeGenerator._wrap(route_def, ctx, RoutePattern.MEMORY_AUGMENTED)

    @staticmethod
    def _generate_event_driven(route_def: RouteDefinition) -> GeneratedRoute:
        handler_keys = sorted(k for k in route_def.agents if k.startswith("handler_"))
        output_key = handler_keys[0] if handler_keys else "handler"
        ctx = RouteCodeGenerator._base_context(route_def, "listener", output_key)
        ctx.update({"listener_key": "listener", "router_key": "router",
                     "handler_keys": handler_keys})
        return RouteCodeGenerator._wrap(route_def, ctx, RoutePattern.EVENT_DRIVEN)

    @staticmethod
    def _generate_checkpoint_resume(route_def: RouteDefinition) -> GeneratedRoute:
        ctx = RouteCodeGenerator._base_context(route_def, "coordinator", "coordinator")
        ctx.update({"coordinator_key": "coordinator", "worker_key": "worker",
                     "checkpoint_store_key": "checkpoint_store"})
        return RouteCodeGenerator._wrap(route_def, ctx, RoutePattern.CHECKPOINT_RESUME)

    @staticmethod
    def _generate_budget_aware_routing(route_def: RouteDefinition) -> GeneratedRoute:
        ctx = RouteCodeGenerator._base_context(route_def, "cost_estimator", "executor")
        ctx.update({"cost_estimator_key": "cost_estimator", "model_router_key": "model_router",
                     "executor_key": "executor"})
        return RouteCodeGenerator._wrap(route_def, ctx, RoutePattern.BUDGET_AWARE_ROUTING)

    @staticmethod
    def _generate_adaptive_routing(route_def: RouteDefinition) -> GeneratedRoute:
        worker_keys = sorted(k for k in route_def.agents if k.startswith("worker_"))
        output_key = worker_keys[0] if worker_keys else "worker"
        ctx = RouteCodeGenerator._base_context(route_def, "performance_tracker", output_key)
        ctx.update({"performance_tracker_key": "performance_tracker", "router_key": "router",
                     "worker_keys": worker_keys})
        return RouteCodeGenerator._wrap(route_def, ctx, RoutePattern.ADAPTIVE_ROUTING)

    @staticmethod
    def _generate_lats(route_def: RouteDefinition) -> GeneratedRoute:
        ctx = RouteCodeGenerator._base_context(route_def, "expander", "evaluator")
        ctx.update({
            "expander_key": "expander", "executor_key": "executor",
            "evaluator_key": "evaluator", "reflector_key": "reflector",
            "max_iterations": config.lats_max_iterations,
            "branching_factor": config.lats_branching_factor,
            "exploration_constant": config.lats_exploration_constant,
            "success_threshold": config.lats_success_threshold,
            "max_depth": config.lats_max_depth,
        })
        return RouteCodeGenerator._wrap(route_def, ctx, RoutePattern.LATS)

    @staticmethod
    def _generate_planner_generator_evaluator(route_def: RouteDefinition) -> GeneratedRoute:
        ctx = RouteCodeGenerator._base_context(route_def, "planner", "evaluator")
        ctx.update({
            "planner_key": "planner", "generator_key": "generator",
            "evaluator_key": "evaluator",
            "max_sprint_iterations": config.pge_max_sprint_iterations,
            "max_interview_turns": config.pge_max_interview_turns,
        })
        return RouteCodeGenerator._wrap(route_def, ctx, RoutePattern.PLANNER_GENERATOR_EVALUATOR)

    @staticmethod
    def _generate_ralph_loop(route_def: RouteDefinition) -> GeneratedRoute:
        ctx = RouteCodeGenerator._base_context(route_def, "planner", "verifier")
        ctx.update({
            "planner_key": "planner", "implementer_key": "implementer",
            "verifier_key": "verifier", "spawn_budget": config.loop_spawn_budget,
        })
        return RouteCodeGenerator._wrap(route_def, ctx, RoutePattern.RALPH_LOOP)

    # ------------------------------------------------------------------
    # Agent-loop pattern generators
    # ------------------------------------------------------------------

    @staticmethod
    def _generate_react_loop(route_def: RouteDefinition) -> GeneratedRoute:
        lc = route_def.loop_config
        max_iterations = lc.max_iterations if lc else config.loop_default_max_iterations
        stuck_threshold = lc.stuck_detection_threshold if lc else config.retry_loop_max_retries
        on_stuck = lc.on_stuck if lc else "graceful_degradation"
        ctx = RouteCodeGenerator._base_context(route_def, "thinker", "observer")
        ctx.update({
            "max_iterations": max_iterations,
            "stuck_threshold": stuck_threshold,
            "on_stuck": on_stuck,
        })
        return RouteCodeGenerator._wrap(
            route_def, ctx, RoutePattern.REACT_LOOP,
            extra_metadata={"max_iterations": max_iterations},
        )

    @staticmethod
    def _generate_goal_driven_loop(route_def: RouteDefinition) -> GeneratedRoute:
        lc = route_def.loop_config
        max_iterations = lc.max_iterations if lc else config.loop_default_max_iterations
        goal_expression = lc.goal_expression if lc else ""
        stuck_threshold = lc.stuck_detection_threshold if lc else config.retry_loop_max_retries
        on_stuck = lc.on_stuck if lc else "graceful_degradation"
        ctx = RouteCodeGenerator._base_context(route_def, "worker", "goal_verifier")
        ctx.update({
            "max_iterations": max_iterations,
            "goal_expression": goal_expression,
            "stuck_threshold": stuck_threshold,
            "on_stuck": on_stuck,
        })
        return RouteCodeGenerator._wrap(
            route_def, ctx, RoutePattern.GOAL_DRIVEN_LOOP,
            extra_metadata={"max_iterations": max_iterations, "goal_expression": goal_expression},
        )

    @staticmethod
    def _generate_interval_loop(route_def: RouteDefinition) -> GeneratedRoute:
        lc = route_def.loop_config
        max_iterations = lc.max_iterations if lc else config.loop_default_max_iterations
        interval_seconds = lc.tick_interval_seconds if lc else 60
        ctx = RouteCodeGenerator._base_context(route_def, "worker", "worker")
        ctx.update({"max_iterations": max_iterations, "interval_seconds": interval_seconds})
        return RouteCodeGenerator._wrap(
            route_def, ctx, RoutePattern.INTERVAL_LOOP,
            extra_metadata={"max_iterations": max_iterations, "interval_seconds": interval_seconds},
        )

    @staticmethod
    def _generate_requirements(route_def: RouteDefinition) -> str:
        requirements = [
            "semantic-kernel>=0.4.0",
            "azure-ai>=1.0.0",
            "pydantic>=2.0.0",
            "python-dateutil>=2.8.0",
        ]
        return "\n".join(requirements) + "\n"

    @staticmethod
    def _generate_config(route_def: RouteDefinition) -> str:
        yaml_str = f"""# {route_def.name} - v1.0

name: {route_def.name}
version: v1.0
pattern: {route_def.pattern.value}
description: {route_def.description}

agents:
"""
        for key, agent in route_def.agents.items():
            yaml_str += f"  {key}: {agent.name}\n"

        yaml_str += f"""
timeouts:
  total_seconds: {route_def.timeout_seconds}
  per_agent_seconds: {route_def.per_agent_timeout_seconds}

metadata:
  created_at: {route_def.created_at.isoformat()}
  created_by: {route_def.csa_email}
"""
        return yaml_str

    @staticmethod
    def _generate_test_data(route_def: RouteDefinition) -> str:
        _default = [{"name": "test_case_1", "input": {}, "expected": {}}]
        test_data = _TEST_DATA.get(route_def.pattern, _default)
        return json.dumps(test_data, indent=2) + "\n"


# ---------------------------------------------------------------------------
# Dispatch tables — adding a new pattern only requires entries here and in
# _PATTERN_TEMPLATE_DIRS above. The generate() and _generate_test_data()
# methods never need to change.
# ---------------------------------------------------------------------------

_GENERATORS: dict[RoutePattern, Callable[[RouteDefinition], GeneratedRoute]] = {
    RoutePattern.SUPERVISOR_MANAGER:    RouteCodeGenerator._generate_supervisor_manager,
    RoutePattern.FAN_OUT_FAN_IN:        RouteCodeGenerator._generate_fan_out_fan_in,
    RoutePattern.MAP_REDUCE:            RouteCodeGenerator._generate_map_reduce,
    RoutePattern.SEQUENTIAL_PIPELINE:   RouteCodeGenerator._generate_sequential_pipeline,
    RoutePattern.ROUND_ROBIN:           RouteCodeGenerator._generate_round_robin,
    RoutePattern.MIXTURE_OF_EXPERTS:    RouteCodeGenerator._generate_mixture_of_experts,
    RoutePattern.HIERARCHICAL_TEAMS:    RouteCodeGenerator._generate_hierarchical_teams,
    RoutePattern.FALLBACK_CHAIN:        RouteCodeGenerator._generate_fallback_chain,
    RoutePattern.RETRY_LOOP:            RouteCodeGenerator._generate_retry_loop,
    RoutePattern.DIAMOND:               RouteCodeGenerator._generate_diamond,
    RoutePattern.CONDITIONAL_BRANCHING: RouteCodeGenerator._generate_conditional_branching,
    RoutePattern.TREE_REDUCE:           RouteCodeGenerator._generate_tree_reduce,
    RoutePattern.EVALUATOR_OPTIMIZER:   RouteCodeGenerator._generate_evaluator_optimizer,
    RoutePattern.HUMAN_IN_THE_LOOP:     RouteCodeGenerator._generate_human_in_the_loop,
    RoutePattern.REFLECTION:            RouteCodeGenerator._generate_reflection,
    RoutePattern.ORCHESTRATOR_WORKERS:  RouteCodeGenerator._generate_orchestrator_workers,
    RoutePattern.RAG:                   RouteCodeGenerator._generate_rag,
    RoutePattern.PLANNING:              RouteCodeGenerator._generate_planning,
    RoutePattern.GATE_GUARD:            RouteCodeGenerator._generate_gate_guard,
    RoutePattern.SELF_CONSISTENCY:      RouteCodeGenerator._generate_self_consistency,
    RoutePattern.DEBATE:                RouteCodeGenerator._generate_debate,
    RoutePattern.AGENT_AS_A_TOOL:       RouteCodeGenerator._generate_agent_as_a_tool,
    RoutePattern.MEMORY_AUGMENTED:      RouteCodeGenerator._generate_memory_augmented,
    RoutePattern.EVENT_DRIVEN:          RouteCodeGenerator._generate_event_driven,
    RoutePattern.CHECKPOINT_RESUME:     RouteCodeGenerator._generate_checkpoint_resume,
    RoutePattern.BUDGET_AWARE_ROUTING:  RouteCodeGenerator._generate_budget_aware_routing,
    RoutePattern.ADAPTIVE_ROUTING:            RouteCodeGenerator._generate_adaptive_routing,
    RoutePattern.PLANNER_GENERATOR_EVALUATOR: RouteCodeGenerator._generate_planner_generator_evaluator,
    RoutePattern.LATS:                        RouteCodeGenerator._generate_lats,
    RoutePattern.RALPH_LOOP:                  RouteCodeGenerator._generate_ralph_loop,
    # Agent-loop patterns
    RoutePattern.REACT_LOOP:                  RouteCodeGenerator._generate_react_loop,
    RoutePattern.GOAL_DRIVEN_LOOP:            RouteCodeGenerator._generate_goal_driven_loop,
    RoutePattern.INTERVAL_LOOP:               RouteCodeGenerator._generate_interval_loop,
}

_TEST_DATA: dict[RoutePattern, list] = {
    RoutePattern.SUPERVISOR_MANAGER: [
        {"name": "test_case_1",
         "input": {"amount": 100000, "loan_type": "mortgage", "credit_score": 750},
         "expected": {"decision": "approved"}},
        {"name": "test_case_2",
         "input": {"amount": 30000, "loan_type": "auto", "credit_score": 680},
         "expected": {"decision": "approved"}},
    ],
    RoutePattern.FAN_OUT_FAN_IN: [
        {"name": "test_case_1",
         "input": {"data": {"id": 1, "payload": "sample"}},
         "expected": {"combined_result": {}}},
    ],
    RoutePattern.MAP_REDUCE: [
        {"name": "test_case_1",
         "input": {"data": [{"item": i} for i in range(5)], "chunk_size": 2},
         "expected": {"reduced_result": {}}},
    ],
    RoutePattern.SEQUENTIAL_PIPELINE: [
        {"name": "test_case_1",
         "input": {"input_data": {"field": "value"}},
         "expected": {"output_data": {}}},
    ],
    RoutePattern.ROUND_ROBIN: [
        {"name": "test_case_1",
         "input": {"data": {"task": "process item 1"}},
         "expected": {"result": {}}},
        {"name": "test_case_2",
         "input": {"data": {"task": "process item 2"}},
         "expected": {"result": {}}},
    ],
    RoutePattern.MIXTURE_OF_EXPERTS: [
        {"name": "test_case_1",
         "input": {"data": {"query": "finance question"}},
         "expected": {"result": {}}},
    ],
    RoutePattern.HIERARCHICAL_TEAMS: [
        {"name": "test_case_1",
         "input": {"data": {"project": "multi-team analysis"}},
         "expected": {"result": {}}},
    ],
    RoutePattern.FALLBACK_CHAIN: [
        {"name": "test_case_1",
         "input": {"data": {"task": "process with fallback"}},
         "expected": {"result": {}}},
    ],
    RoutePattern.RETRY_LOOP: [
        {"name": "test_case_1",
         "input": {"data": {"task": "process with retry"}},
         "expected": {"result": {}}},
    ],
    RoutePattern.DIAMOND: [
        {"name": "test_case_1",
         "input": {"data": {"payload": "split and merge"}},
         "expected": {"result": {}}},
    ],
    RoutePattern.CONDITIONAL_BRANCHING: [
        {"name": "test_case_1",
         "input": {"data": {"type": "urgent", "content": "process me"}},
         "expected": {"result": {}}},
    ],
    RoutePattern.TREE_REDUCE: [
        {"name": "test_case_1",
         "input": {"data": {"segments": ["A", "B", "C", "D"]}},
         "expected": {"result": {}}},
    ],
    RoutePattern.EVALUATOR_OPTIMIZER: [
        {"name": "test_case_1",
         "input": {"payload": {"task": "write a contract clause"}},
         "expected": {"result": {}, "quality_score": 0.9}},
    ],
    RoutePattern.HUMAN_IN_THE_LOOP: [
        {"name": "test_case_1",
         "input": {"payload": {"request": "approve budget of $50k"}},
         "expected": {"decision": "approved"}},
    ],
    RoutePattern.REFLECTION: [
        {"name": "test_case_1",
         "input": {"payload": {"task": "summarise this document"}},
         "expected": {"result": {}}},
    ],
    RoutePattern.ORCHESTRATOR_WORKERS: [
        {"name": "test_case_1",
         "input": {"task": "analyse Q2 performance across all regions"},
         "expected": {"synthesis": {}}},
    ],
    RoutePattern.RAG: [
        {"name": "test_case_1",
         "input": {"query": "What is the vendor onboarding process?"},
         "expected": {"answer": ""}},
    ],
    RoutePattern.PLANNING: [
        {"name": "test_case_1",
         "input": {"goal": "prepare an RFP response by Friday"},
         "expected": {"review_result": {}}},
    ],
    RoutePattern.GATE_GUARD: [
        {"name": "test_case_1",
         "input": {"payload": {"content": "process this document"}},
         "expected": {"result": {}}},
    ],
    RoutePattern.SELF_CONSISTENCY: [
        {"name": "test_case_1",
         "input": {"question": "What is 15% of 240?"},
         "expected": {"answer": "36"}},
    ],
    RoutePattern.DEBATE: [
        {"name": "test_case_1",
         "input": {"topic": "Should we expand to APAC in Q3?"},
         "expected": {"verdict": {}}},
    ],
    RoutePattern.AGENT_AS_A_TOOL: [
        {"name": "test_case_1",
         "input": {"task": "analyse and summarise the attached contract"},
         "expected": {"result": {}}},
    ],
    RoutePattern.MEMORY_AUGMENTED: [
        {"name": "test_case_1",
         "input": {"session_id": "sess-001", "query": "What did we decide last week?"},
         "expected": {"result": {}}},
    ],
    RoutePattern.EVENT_DRIVEN: [
        {"name": "test_case_1",
         "input": {"event_type": "invoice_received", "payload": {"invoice_id": "INV-001"}},
         "expected": {"handled": True}},
    ],
    RoutePattern.CHECKPOINT_RESUME: [
        {"name": "test_case_1",
         "input": {"workflow_id": "wf-001", "payload": {"steps": ["a", "b", "c"]}},
         "expected": {"status": "completed"}},
    ],
    RoutePattern.BUDGET_AWARE_ROUTING: [
        {"name": "test_case_1",
         "input": {"prompt": "Summarise this 10-page report", "budget_usd": 0.10},
         "expected": {"result": {}}},
    ],
    RoutePattern.ADAPTIVE_ROUTING: [
        {"name": "test_case_1",
         "input": {"query": "Classify this support ticket", "input_type": "support"},
         "expected": {"result": {}}},
    ],
    RoutePattern.RALPH_LOOP: [
        {"name": "test_case_1",
         "input": {"spec_path": "/workspace/spec.md", "state_path": "/workspace/.ralph_state.json"},
         "expected": {"passed": True}},
    ],
    RoutePattern.REACT_LOOP: [
        {"name": "test_case_1",
         "input": {"task": "research and summarise AI agent loop patterns"},
         "expected": {"done": True}},
    ],
    RoutePattern.GOAL_DRIVEN_LOOP: [
        {"name": "test_case_1",
         "input": {"data": {"task": "iterate until quality threshold met"}},
         "expected": {"done": True}},
    ],
    RoutePattern.INTERVAL_LOOP: [
        {"name": "test_case_1",
         "input": {"data": {"task": "poll for status"}},
         "expected": {"result": {}}},
    ],
}
