"""Tests for the three new loop code-generator methods."""

import pytest
from safe_core.code_generator import RouteCodeGenerator
from safe_core.models import (
    Agent,
    GeneratedRoute,
    LoopConfig,
    LoopTerminationType,
    RouteDefinition,
    RoutePattern,
)


def make_agent(name: str, inputs=None, outputs=None) -> Agent:
    return Agent(
        name=name, category="test", version="1.0",
        input_schema={"properties": {k: {} for k in (inputs or [])}, "required": list(inputs or [])},
        output_schema={"properties": {k: {} for k in (outputs or [])}, "required": list(outputs or [])},
        dependencies=[],
    )


def make_react_loop(lc=None) -> RouteDefinition:
    return RouteDefinition(
        name="my-react-loop",
        pattern=RoutePattern.REACT_LOOP,
        agents={
            "thinker": make_agent("Thinker", inputs=["context"], outputs=["thought", "next_action"]),
            "actor": make_agent("Actor", inputs=["next_action"], outputs=["action_result"]),
            "observer": make_agent("Observer", inputs=["action_result"], outputs=["done", "observation"]),
        },
        loop_config=lc or LoopConfig(max_iterations=10),
        description="A ReAct loop route",
    )


def make_goal_driven_loop(lc=None) -> RouteDefinition:
    return RouteDefinition(
        name="my-goal-loop",
        pattern=RoutePattern.GOAL_DRIVEN_LOOP,
        agents={
            "worker": make_agent("Worker", inputs=["data"], outputs=["result"]),
            "goal_verifier": make_agent("GoalVerifier", inputs=["output", "iteration"], outputs=["done", "reason"]),
        },
        loop_config=lc or LoopConfig(
            max_iterations=8,
            goal_expression="output['done'] == True",
        ),
        description="A goal-driven loop route",
    )


def make_interval_loop(lc=None) -> RouteDefinition:
    return RouteDefinition(
        name="my-interval-loop",
        pattern=RoutePattern.INTERVAL_LOOP,
        agents={
            "worker": make_agent("Worker", inputs=["data"], outputs=["result"]),
        },
        loop_config=lc or LoopConfig(max_iterations=5, tick_interval_seconds=300),
        description="An interval loop route",
    )


# ---------------------------------------------------------------------------
# REACT_LOOP
# ---------------------------------------------------------------------------

class TestGenerateReactLoop:
    def test_returns_generated_route(self):
        result = RouteCodeGenerator.generate(make_react_loop())
        assert isinstance(result, GeneratedRoute)

    def test_route_code_contains_class_name(self):
        result = RouteCodeGenerator.generate(make_react_loop())
        assert "MyReactLoopRoute" in result.route_code

    def test_route_code_contains_pattern(self):
        result = RouteCodeGenerator.generate(make_react_loop())
        assert "react-loop" in result.route_code

    def test_route_code_contains_max_iterations(self):
        result = RouteCodeGenerator.generate(make_react_loop())
        assert "10" in result.route_code

    def test_route_code_contains_stuck_threshold(self):
        lc = LoopConfig(max_iterations=5, stuck_detection_threshold=4)
        result = RouteCodeGenerator.generate(make_react_loop(lc))
        assert "4" in result.route_code

    def test_route_code_has_thinker_actor_observer(self):
        result = RouteCodeGenerator.generate(make_react_loop())
        assert "thinker" in result.route_code
        assert "actor" in result.route_code
        assert "observer" in result.route_code

    def test_requirements_generated(self):
        result = RouteCodeGenerator.generate(make_react_loop())
        assert "semantic-kernel" in result.requirements_txt

    def test_config_yaml_generated(self):
        result = RouteCodeGenerator.generate(make_react_loop())
        assert "react-loop" in result.config_yaml

    def test_test_data_json_generated(self):
        import json
        result = RouteCodeGenerator.generate(make_react_loop())
        data = json.loads(result.test_data_json)
        assert isinstance(data, list)
        assert data[0]["input"]["task"]

    def test_metadata_contains_pattern(self):
        result = RouteCodeGenerator.generate(make_react_loop())
        assert result.metadata["pattern"] == "react-loop"
        assert result.metadata["max_iterations"] == 10

    def test_no_loop_config_uses_defaults(self):
        rd = RouteDefinition(
            name="bare-react", pattern=RoutePattern.REACT_LOOP,
            agents={
                "thinker": make_agent("T"),
                "actor": make_agent("A"),
                "observer": make_agent("O"),
            },
        )
        result = RouteCodeGenerator.generate(rd)
        assert "10" in result.route_code

    def test_on_stuck_raise_rendered(self):
        lc = LoopConfig(max_iterations=5, on_stuck="raise")
        result = RouteCodeGenerator.generate(make_react_loop(lc))
        assert "raise RuntimeError" in result.route_code


# ---------------------------------------------------------------------------
# GOAL_DRIVEN_LOOP
# ---------------------------------------------------------------------------

class TestGenerateGoalDrivenLoop:
    def test_returns_generated_route(self):
        result = RouteCodeGenerator.generate(make_goal_driven_loop())
        assert isinstance(result, GeneratedRoute)

    def test_class_name_in_code(self):
        result = RouteCodeGenerator.generate(make_goal_driven_loop())
        assert "MyGoalLoopRoute" in result.route_code

    def test_pattern_in_code(self):
        result = RouteCodeGenerator.generate(make_goal_driven_loop())
        assert "goal-driven-loop" in result.route_code

    def test_goal_expression_in_code(self):
        result = RouteCodeGenerator.generate(make_goal_driven_loop())
        assert "goal_expression" in result.route_code or "output" in result.route_code

    def test_max_iterations_in_code(self):
        result = RouteCodeGenerator.generate(make_goal_driven_loop())
        assert "8" in result.route_code

    def test_metadata_contains_goal_expression(self):
        result = RouteCodeGenerator.generate(make_goal_driven_loop())
        assert result.metadata["goal_expression"] == "output['done'] == True"

    def test_test_data_json(self):
        import json
        result = RouteCodeGenerator.generate(make_goal_driven_loop())
        data = json.loads(result.test_data_json)
        assert data[0]["expected"]["done"] is True

    def test_no_loop_config_uses_defaults(self):
        rd = RouteDefinition(
            name="bare-goal", pattern=RoutePattern.GOAL_DRIVEN_LOOP,
            agents={
                "worker": make_agent("W"),
                "goal_verifier": make_agent("GV"),
            },
        )
        result = RouteCodeGenerator.generate(rd)
        assert "10" in result.route_code

    def test_on_stuck_raise_rendered(self):
        lc = LoopConfig(max_iterations=5, on_stuck="raise", goal_expression="x")
        result = RouteCodeGenerator.generate(make_goal_driven_loop(lc))
        assert "raise RuntimeError" in result.route_code


# ---------------------------------------------------------------------------
# INTERVAL_LOOP
# ---------------------------------------------------------------------------

class TestGenerateIntervalLoop:
    def test_returns_generated_route(self):
        result = RouteCodeGenerator.generate(make_interval_loop())
        assert isinstance(result, GeneratedRoute)

    def test_class_name_in_code(self):
        result = RouteCodeGenerator.generate(make_interval_loop())
        assert "MyIntervalLoopRoute" in result.route_code

    def test_pattern_in_code(self):
        result = RouteCodeGenerator.generate(make_interval_loop())
        assert "interval-loop" in result.route_code

    def test_interval_seconds_in_code(self):
        result = RouteCodeGenerator.generate(make_interval_loop())
        assert "300" in result.route_code

    def test_max_iterations_in_code(self):
        result = RouteCodeGenerator.generate(make_interval_loop())
        assert "5" in result.route_code

    def test_metadata_interval_seconds(self):
        result = RouteCodeGenerator.generate(make_interval_loop())
        assert result.metadata["interval_seconds"] == 300

    def test_test_data_json(self):
        import json
        result = RouteCodeGenerator.generate(make_interval_loop())
        data = json.loads(result.test_data_json)
        assert "task" in data[0]["input"]["data"]

    def test_no_loop_config_uses_defaults(self):
        rd = RouteDefinition(
            name="bare-interval", pattern=RoutePattern.INTERVAL_LOOP,
            agents={"worker": make_agent("W")},
        )
        result = RouteCodeGenerator.generate(rd)
        assert "interval-loop" in result.route_code

    def test_stop_method_generated(self):
        result = RouteCodeGenerator.generate(make_interval_loop())
        assert "def stop(" in result.route_code


# ---------------------------------------------------------------------------
# Dispatch coverage — ensure generate() reaches each branch
# ---------------------------------------------------------------------------

class TestGenerateDispatch:
    def test_react_loop_dispatched(self):
        rd = make_react_loop()
        result = RouteCodeGenerator.generate(rd)
        assert result.metadata["pattern"] == "react-loop"

    def test_goal_driven_loop_dispatched(self):
        rd = make_goal_driven_loop()
        result = RouteCodeGenerator.generate(rd)
        assert result.metadata["pattern"] == "goal-driven-loop"

    def test_interval_loop_dispatched(self):
        rd = make_interval_loop()
        result = RouteCodeGenerator.generate(rd)
        assert result.metadata["pattern"] == "interval-loop"
