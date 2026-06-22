"""Parametrised code-generation tests covering all RoutePattern values."""

import ast
import pytest
from safe_core.models import Agent, RouteDefinition, RoutePattern
from safe_core.code_generator import RouteCodeGenerator


def make_agent(name, inputs=None, outputs=None):
    return Agent(
        name=name,
        category="test",
        version="1.0",
        input_schema={
            "properties": {k: {"type": "string"} for k in (inputs or [])},
            "required": list(inputs or []),
        },
        output_schema={
            "properties": {k: {"type": "string"} for k in (outputs or [])},
            "required": list(outputs or []),
        },
    )


def base_route(pattern, agents):
    return RouteDefinition(
        name="test-route",
        pattern=pattern,
        agents=agents,
        description="Test route",
        timeout_seconds=120,
        per_agent_timeout_seconds=60,
    )


# ---------------------------------------------------------------------------
# Agent sets for each pattern
# ---------------------------------------------------------------------------

PATTERN_AGENTS = {
    RoutePattern.SUPERVISOR_MANAGER: {
        "supervisor": make_agent("Supervisor", outputs=["specialist"]),
        "specialist_a": make_agent("SpecialistA", inputs=["specialist"]),
        "aggregator": make_agent("Aggregator", outputs=["result"]),
    },
    RoutePattern.FAN_OUT_FAN_IN: {
        "processor_0": make_agent("Processor0"),
        "processor_1": make_agent("Processor1"),
        "aggregator": make_agent("Aggregator", inputs=["results"], outputs=["combined"]),
    },
    RoutePattern.MAP_REDUCE: {
        "splitter": make_agent("Splitter", outputs=["chunks"]),
        "mapper": make_agent("Mapper", inputs=["data_chunk"], outputs=["mapped_result"]),
        "reducer": make_agent("Reducer", inputs=["mapped_results"], outputs=["reduced"]),
    },
    RoutePattern.SEQUENTIAL_PIPELINE: {
        "stage_0": make_agent("Stage0", outputs=["data"]),
        "stage_1": make_agent("Stage1", inputs=["data"], outputs=["result"]),
    },
    RoutePattern.ROUND_ROBIN: {
        "dispatcher": make_agent("Dispatcher", outputs=["task"]),
        "worker_0": make_agent("Worker0", inputs=["task"]),
        "worker_1": make_agent("Worker1", inputs=["task"]),
    },
    RoutePattern.MIXTURE_OF_EXPERTS: {
        "router": make_agent("Router", outputs=["route"]),
        "expert_0": make_agent("ExpertA"),
        "expert_1": make_agent("ExpertB"),
        "aggregator": make_agent("Aggregator", inputs=["expert_outputs"], outputs=["answer"]),
    },
    RoutePattern.HIERARCHICAL_TEAMS: {
        "coordinator": make_agent("Coordinator"),
        "team_0": make_agent("TeamA"),
        "team_1": make_agent("TeamB"),
        "aggregator": make_agent("Aggregator", inputs=["team_results"], outputs=["report"]),
    },
    RoutePattern.FALLBACK_CHAIN: {
        "primary": make_agent("Primary", outputs=["answer"]),
        "fallback_0": make_agent("Fallback0", outputs=["answer"]),
    },
    RoutePattern.RETRY_LOOP: {
        "worker": make_agent("Worker", outputs=["output"]),
        "validator": make_agent("Validator", outputs=["valid"]),
    },
    RoutePattern.DIAMOND: {
        "splitter": make_agent("Splitter", outputs=["left", "right"]),
        "left_processor": make_agent("LeftProc"),
        "right_processor": make_agent("RightProc"),
        "merger": make_agent("Merger", inputs=["left_result", "right_result"]),
    },
    RoutePattern.CONDITIONAL_BRANCHING: {
        "evaluator": make_agent("Evaluator"),
        "branch_0": make_agent("BranchA"),
        "branch_1": make_agent("BranchB"),
    },
    RoutePattern.TREE_REDUCE: {
        "leaf_0": make_agent("Leaf0"),
        "leaf_1": make_agent("Leaf1"),
        "reducer": make_agent("Reducer", inputs=["left", "right"], outputs=["result"]),
    },
    # Backlog patterns
    RoutePattern.EVALUATOR_OPTIMIZER: {
        "generator": make_agent("Generator", outputs=["draft"]),
        "evaluator": make_agent("Evaluator", outputs=["score"]),
        "optimizer": make_agent("Optimizer", outputs=["final"]),
    },
    RoutePattern.HUMAN_IN_THE_LOOP: {
        "pre_validator": make_agent("PreValidator", outputs=["validated"]),
        "human_gate": make_agent("HumanGate", outputs=["approved"]),
        "post_processor": make_agent("PostProcessor", outputs=["result"]),
    },
    RoutePattern.REFLECTION: {
        "generator": make_agent("Generator", outputs=["draft"]),
        "critic": make_agent("Critic", outputs=["feedback"]),
        "refiner": make_agent("Refiner", outputs=["refined"]),
    },
    RoutePattern.ORCHESTRATOR_WORKERS: {
        "orchestrator": make_agent("Orchestrator", outputs=["plan"]),
        "worker_0": make_agent("Worker0", outputs=["result0"]),
        "worker_1": make_agent("Worker1", outputs=["result1"]),
        "synthesizer": make_agent("Synthesizer", outputs=["synthesis"]),
    },
    RoutePattern.RAG: {
        "retriever": make_agent("Retriever", outputs=["chunks"]),
        "reranker": make_agent("Reranker", outputs=["ranked"]),
        "generator": make_agent("Generator", outputs=["answer"]),
    },
    RoutePattern.PLANNING: {
        "planner": make_agent("Planner", outputs=["plan"]),
        "executor": make_agent("Executor", outputs=["output"]),
        "reviewer": make_agent("Reviewer", outputs=["review"]),
    },
    RoutePattern.GATE_GUARD: {
        "guard": make_agent("Guard", outputs=["decision"]),
        "processor": make_agent("Processor", outputs=["result"]),
    },
    RoutePattern.SELF_CONSISTENCY: {
        "worker_1": make_agent("Worker1", outputs=["answer1"]),
        "worker_2": make_agent("Worker2", outputs=["answer2"]),
        "worker_3": make_agent("Worker3", outputs=["answer3"]),
        "voter": make_agent("Voter", outputs=["consensus"]),
    },
    RoutePattern.DEBATE: {
        "proposer": make_agent("Proposer", outputs=["proposal"]),
        "challenger": make_agent("Challenger", outputs=["challenge"]),
        "judge": make_agent("Judge", outputs=["verdict"]),
    },
    RoutePattern.AGENT_AS_A_TOOL: {
        "orchestrator": make_agent("Orchestrator", outputs=["result"]),
        "sub_agent_0": make_agent("SubAgent0", outputs=["sub_result"]),
    },
    RoutePattern.MEMORY_AUGMENTED: {
        "memory_reader": make_agent("MemoryReader", outputs=["context"]),
        "processor": make_agent("Processor", outputs=["result"]),
        "memory_writer": make_agent("MemoryWriter", outputs=["stored"]),
    },
    RoutePattern.EVENT_DRIVEN: {
        "listener": make_agent("Listener", outputs=["event"]),
        "router": make_agent("Router", outputs=["route"]),
        "handler_0": make_agent("Handler0", outputs=["handled"]),
    },
    RoutePattern.CHECKPOINT_RESUME: {
        "coordinator": make_agent("Coordinator", outputs=["checkpoint"]),
        "worker": make_agent("Worker", outputs=["work"]),
        "checkpoint_store": make_agent("CheckpointStore", outputs=["stored"]),
    },
    RoutePattern.BUDGET_AWARE_ROUTING: {
        "cost_estimator": make_agent("CostEstimator", outputs=["estimate"]),
        "model_router": make_agent("ModelRouter", outputs=["model"]),
        "executor": make_agent("Executor", outputs=["result"]),
    },
    RoutePattern.ADAPTIVE_ROUTING: {
        "performance_tracker": make_agent("PerfTracker", outputs=["metrics"]),
        "router": make_agent("Router", outputs=["route"]),
        "worker_0": make_agent("Worker0", outputs=["result"]),
    },
    RoutePattern.PLANNER_GENERATOR_EVALUATOR: {
        "planner": make_agent("Planner", outputs=["sprints"]),
        "generator": make_agent("Generator", outputs=["sprint_delivery"]),
        "evaluator": make_agent("Evaluator", outputs=["approved"]),
    },
    RoutePattern.LATS: {
        "expander":  make_agent("Expander",  outputs=["actions"]),
        "executor":  make_agent("Executor",  outputs=["next_state"]),
        "evaluator": make_agent("Evaluator", outputs=["value", "terminal"]),
        "reflector": make_agent("Reflector", outputs=["reflection"]),
    },
    RoutePattern.RALPH_LOOP: {
        "planner": make_agent("Planner", inputs=["spec_path"], outputs=["next_task"]),
        "implementer": make_agent("Implementer", outputs=["result"]),
        "verifier": make_agent("Verifier", outputs=["passed"]),
    },
    # Agent-loop patterns
    RoutePattern.REACT_LOOP: {
        "thinker": make_agent("Thinker", inputs=["context"], outputs=["thought", "next_action"]),
        "actor": make_agent("Actor", inputs=["next_action"], outputs=["action_result"]),
        "observer": make_agent("Observer", inputs=["action_result"], outputs=["done", "observation"]),
    },
    RoutePattern.GOAL_DRIVEN_LOOP: {
        "worker": make_agent("Worker", inputs=["data"], outputs=["result"]),
        "goal_verifier": make_agent("GoalVerifier", inputs=["output", "iteration"], outputs=["done", "reason"]),
    },
    RoutePattern.INTERVAL_LOOP: {
        "worker": make_agent("Worker", inputs=["data"], outputs=["result"]),
    },
}


@pytest.mark.parametrize("pattern", list(RoutePattern))
def test_generate_produces_valid_python(pattern):
    """Every pattern must produce syntactically valid Python code."""
    agents = PATTERN_AGENTS[pattern]
    route_def = base_route(pattern, agents)
    generated = RouteCodeGenerator.generate(route_def)

    assert generated.route_code, f"{pattern.value}: route_code is empty"

    try:
        ast.parse(generated.route_code)
    except SyntaxError as exc:
        pytest.fail(f"{pattern.value}: generated code has syntax error: {exc}")


@pytest.mark.parametrize("pattern", list(RoutePattern))
def test_generate_class_name_in_code(pattern):
    """Generated code must contain the PascalCase route class name."""
    agents = PATTERN_AGENTS[pattern]
    route_def = base_route(pattern, agents)
    generated = RouteCodeGenerator.generate(route_def)

    expected_class = "TestRoute"
    assert expected_class in generated.route_code, (
        f"{pattern.value}: expected class '{expected_class}' not in generated code"
    )


@pytest.mark.parametrize("pattern", list(RoutePattern))
def test_generate_metadata_fields(pattern):
    """Metadata dict must carry pattern, agents, created_at, version."""
    agents = PATTERN_AGENTS[pattern]
    route_def = base_route(pattern, agents)
    generated = RouteCodeGenerator.generate(route_def)

    meta = generated.metadata
    assert meta["pattern"] == pattern.value
    assert "agents" in meta
    assert "created_at" in meta
    assert meta.get("version") == "v1.0"


@pytest.mark.parametrize("pattern", list(RoutePattern))
def test_generate_requirements_txt(pattern):
    """requirements.txt must reference semantic-kernel."""
    agents = PATTERN_AGENTS[pattern]
    route_def = base_route(pattern, agents)
    generated = RouteCodeGenerator.generate(route_def)

    assert "semantic-kernel" in generated.requirements_txt


@pytest.mark.parametrize("pattern", list(RoutePattern))
def test_generate_config_yaml(pattern):
    """config.yaml must contain the route name and pattern value."""
    agents = PATTERN_AGENTS[pattern]
    route_def = base_route(pattern, agents)
    generated = RouteCodeGenerator.generate(route_def)

    assert "test-route" in generated.config_yaml
    assert pattern.value in generated.config_yaml


class TestClassNameHelper:
    @pytest.mark.parametrize("route_name,expected", [
        ("my-route", "MyRoute"),
        ("contract-review-pipeline", "ContractReviewPipeline"),
        ("rag", "Rag"),
        ("employee_onboarding", "EmployeeOnboarding"),
    ])
    def test_class_name_conversion(self, route_name, expected):
        assert RouteCodeGenerator._class_name(route_name) == expected
