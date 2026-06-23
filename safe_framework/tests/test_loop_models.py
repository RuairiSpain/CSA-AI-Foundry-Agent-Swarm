"""Tests for loop-related models: CompactionStrategy, LoopTerminationType, CompactionConfig, LoopConfig."""

import pytest
from safe_core.models import (
    Agent,
    CompactionConfig,
    CompactionStrategy,
    LoopConfig,
    LoopTerminationType,
    RouteDefinition,
    RoutePattern,
)


def make_agent(name: str) -> Agent:
    return Agent(
        name=name, category="test", version="1.0",
        input_schema={"properties": {}, "required": []},
        output_schema={"properties": {}, "required": []},
    )


class TestCompactionStrategy:
    def test_all_values_present(self):
        values = {s.value for s in CompactionStrategy}
        assert "sliding_window" in values
        assert "summarize_and_replace" in values
        assert "hierarchical" in values

    def test_str_equality(self):
        assert CompactionStrategy.SLIDING_WINDOW == "sliding_window"
        assert CompactionStrategy.SUMMARIZE_AND_REPLACE == "summarize_and_replace"
        assert CompactionStrategy.HIERARCHICAL == "hierarchical"


class TestLoopTerminationType:
    def test_all_values_present(self):
        values = {t.value for t in LoopTerminationType}
        assert "max_iterations" in values
        assert "goal" in values
        assert "timeout" in values
        assert "budget" in values

    def test_str_equality(self):
        assert LoopTerminationType.GOAL == "goal"
        assert LoopTerminationType.BUDGET == "budget"


class TestCompactionConfig:
    def test_defaults(self):
        cc = CompactionConfig()
        assert cc.strategy == CompactionStrategy.SUMMARIZE_AND_REPLACE
        assert cc.trigger_token_pct == 70
        assert cc.model == "haiku-4-5"
        assert cc.preserve_last_n == 2

    def test_custom_values(self):
        cc = CompactionConfig(
            strategy=CompactionStrategy.SLIDING_WINDOW,
            trigger_token_pct=50,
            model="opus-4-8",
            preserve_last_n=3,
        )
        assert cc.strategy == CompactionStrategy.SLIDING_WINDOW
        assert cc.trigger_token_pct == 50
        assert cc.model == "opus-4-8"
        assert cc.preserve_last_n == 3


class TestLoopConfig:
    def test_defaults(self):
        lc = LoopConfig()
        assert lc.max_iterations == 10
        assert lc.termination_type == LoopTerminationType.MAX_ITERATIONS
        assert lc.goal_expression == ""
        assert lc.timeout_seconds == 3600
        assert lc.tick_interval_seconds == 60
        assert lc.budget_usd == 0.0
        assert lc.stuck_detection_threshold == 3
        assert lc.on_stuck == "graceful_degradation"
        assert lc.compaction is None

    def test_with_compaction(self):
        cc = CompactionConfig(strategy=CompactionStrategy.HIERARCHICAL)
        lc = LoopConfig(compaction=cc)
        assert lc.compaction is cc
        assert lc.compaction.strategy == CompactionStrategy.HIERARCHICAL

    def test_goal_termination(self):
        lc = LoopConfig(
            termination_type=LoopTerminationType.GOAL,
            goal_expression="output['done'] == True",
        )
        assert lc.termination_type == LoopTerminationType.GOAL
        assert lc.goal_expression == "output['done'] == True"

    def test_budget_termination(self):
        lc = LoopConfig(termination_type=LoopTerminationType.BUDGET, budget_usd=5.0)
        assert lc.budget_usd == 5.0

    def test_on_stuck_raise(self):
        lc = LoopConfig(on_stuck="raise")
        assert lc.on_stuck == "raise"


class TestRouteDefinitionLoopConfig:
    def test_loop_config_default_none(self):
        rd = RouteDefinition(
            name="test", pattern=RoutePattern.SEQUENTIAL_PIPELINE,
            agents={"stage_0": make_agent("a"), "stage_1": make_agent("b")},
        )
        assert rd.loop_config is None

    def test_loop_config_attached(self):
        lc = LoopConfig(max_iterations=5)
        rd = RouteDefinition(
            name="my-loop", pattern=RoutePattern.REACT_LOOP,
            agents={},
            loop_config=lc,
        )
        assert rd.loop_config is lc
        assert rd.loop_config.max_iterations == 5


class TestNewRoutePatterns:
    def test_react_loop_in_enum(self):
        assert RoutePattern.REACT_LOOP == "react-loop"

    def test_goal_driven_loop_in_enum(self):
        assert RoutePattern.GOAL_DRIVEN_LOOP == "goal-driven-loop"

    def test_interval_loop_in_enum(self):
        assert RoutePattern.INTERVAL_LOOP == "interval-loop"

    def test_total_pattern_count(self):
        # Original 30 (from main: 27 + ralph-loop + lats + planner-generator-evaluator) + 3 new loop patterns = 33
        assert len(RoutePattern) == 33
