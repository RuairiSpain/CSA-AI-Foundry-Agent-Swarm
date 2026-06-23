"""Tests for loop-pattern validator branches in ContractValidator."""

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
from safe_core.validator import ContractValidator


def make_agent(name: str, inputs=None, outputs=None) -> Agent:
    return Agent(
        name=name, category="test", version="1.0",
        input_schema={"properties": {k: {} for k in (inputs or [])}, "required": list(inputs or [])},
        output_schema={"properties": {k: {} for k in (outputs or [])}, "required": list(outputs or [])},
        dependencies=[],
    )


def route(pattern, agents, lc=None, total=120, per_agent=60):
    return RouteDefinition(
        name="test", pattern=pattern, agents=agents,
        timeout_seconds=total, per_agent_timeout_seconds=per_agent,
        loop_config=lc,
    )


# ---------------------------------------------------------------------------
# validate_agent_contracts — REACT_LOOP
# ---------------------------------------------------------------------------

class TestReactLoopAgentContracts:
    def _valid_agents(self):
        return {
            "thinker": make_agent("Thinker", inputs=["context"], outputs=["thought", "next_action"]),
            "actor": make_agent("Actor", inputs=["next_action"], outputs=["action_result"]),
            "observer": make_agent("Observer", inputs=["action_result"], outputs=["done", "observation"]),
        }

    def test_valid_react_loop_no_errors(self):
        agents = self._valid_agents()
        errors = ContractValidator.validate_agent_contracts(RoutePattern.REACT_LOOP, agents)
        assert errors == []

    def test_missing_thinker(self):
        agents = self._valid_agents()
        del agents["thinker"]
        errors = ContractValidator.validate_agent_contracts(RoutePattern.REACT_LOOP, agents)
        assert any("thinker" in e.message for e in errors)

    def test_missing_actor(self):
        agents = self._valid_agents()
        del agents["actor"]
        errors = ContractValidator.validate_agent_contracts(RoutePattern.REACT_LOOP, agents)
        assert any("actor" in e.message for e in errors)

    def test_missing_observer(self):
        agents = self._valid_agents()
        del agents["observer"]
        errors = ContractValidator.validate_agent_contracts(RoutePattern.REACT_LOOP, agents)
        assert any("observer" in e.message for e in errors)

    def test_observer_missing_done_field(self):
        agents = self._valid_agents()
        agents["observer"] = make_agent("BadObserver", outputs=["observation"])
        errors = ContractValidator.validate_agent_contracts(RoutePattern.REACT_LOOP, agents)
        assert any("done" in e.message for e in errors)


# ---------------------------------------------------------------------------
# validate_agent_contracts — GOAL_DRIVEN_LOOP
# ---------------------------------------------------------------------------

class TestGoalDrivenLoopAgentContracts:
    def _valid_agents(self):
        return {
            "worker": make_agent("Worker", inputs=["data"], outputs=["result"]),
            "goal_verifier": make_agent("GoalVerifier", inputs=["output", "iteration"], outputs=["done", "reason"]),
        }

    def test_valid_goal_driven_no_errors(self):
        agents = self._valid_agents()
        errors = ContractValidator.validate_agent_contracts(RoutePattern.GOAL_DRIVEN_LOOP, agents)
        assert errors == []

    def test_missing_worker(self):
        agents = self._valid_agents()
        del agents["worker"]
        errors = ContractValidator.validate_agent_contracts(RoutePattern.GOAL_DRIVEN_LOOP, agents)
        assert any("worker" in e.message for e in errors)

    def test_missing_goal_verifier(self):
        agents = self._valid_agents()
        del agents["goal_verifier"]
        errors = ContractValidator.validate_agent_contracts(RoutePattern.GOAL_DRIVEN_LOOP, agents)
        assert any("goal_verifier" in e.message for e in errors)

    def test_goal_verifier_missing_done(self):
        agents = self._valid_agents()
        agents["goal_verifier"] = make_agent("BadGV", outputs=["reason"])
        errors = ContractValidator.validate_agent_contracts(RoutePattern.GOAL_DRIVEN_LOOP, agents)
        assert any("done" in e.message for e in errors)


# ---------------------------------------------------------------------------
# validate_agent_contracts — INTERVAL_LOOP
# ---------------------------------------------------------------------------

class TestIntervalLoopAgentContracts:
    def test_valid_interval_loop_no_errors(self):
        agents = {"worker": make_agent("W", inputs=["data"], outputs=["result"])}
        errors = ContractValidator.validate_agent_contracts(RoutePattern.INTERVAL_LOOP, agents)
        assert errors == []

    def test_missing_worker(self):
        errors = ContractValidator.validate_agent_contracts(RoutePattern.INTERVAL_LOOP, {})
        assert any("worker" in e.message for e in errors)


# ---------------------------------------------------------------------------
# validate_loop_config
# ---------------------------------------------------------------------------

class TestValidateLoopConfig:
    def test_non_loop_pattern_no_errors(self):
        errors = ContractValidator.validate_loop_config(RoutePattern.SEQUENTIAL_PIPELINE, None)
        assert errors == []

    def test_loop_pattern_missing_config(self):
        errors = ContractValidator.validate_loop_config(RoutePattern.REACT_LOOP, None)
        assert any("LoopConfig" in e.message for e in errors)

    def test_valid_config_no_errors(self):
        lc = LoopConfig(max_iterations=5, stuck_detection_threshold=3)
        errors = ContractValidator.validate_loop_config(RoutePattern.GOAL_DRIVEN_LOOP, lc)
        assert errors == []

    def test_max_iterations_zero(self):
        lc = LoopConfig(max_iterations=0)
        errors = ContractValidator.validate_loop_config(RoutePattern.REACT_LOOP, lc)
        assert any("max_iterations" in e.message for e in errors)

    def test_stuck_threshold_below_two(self):
        lc = LoopConfig(stuck_detection_threshold=1)
        errors = ContractValidator.validate_loop_config(RoutePattern.REACT_LOOP, lc)
        assert any("stuck_detection_threshold" in e.message for e in errors)

    def test_invalid_on_stuck_value(self):
        lc = LoopConfig(on_stuck="explode")
        errors = ContractValidator.validate_loop_config(RoutePattern.REACT_LOOP, lc)
        assert any("on_stuck" in e.message for e in errors)

    def test_goal_termination_missing_expression(self):
        lc = LoopConfig(termination_type=LoopTerminationType.GOAL, goal_expression="")
        errors = ContractValidator.validate_loop_config(RoutePattern.GOAL_DRIVEN_LOOP, lc)
        assert any("goal_expression" in e.message for e in errors)

    def test_goal_termination_with_expression_ok(self):
        lc = LoopConfig(termination_type=LoopTerminationType.GOAL, goal_expression="output['done']")
        errors = ContractValidator.validate_loop_config(RoutePattern.GOAL_DRIVEN_LOOP, lc)
        assert errors == []

    def test_budget_termination_zero_usd(self):
        lc = LoopConfig(termination_type=LoopTerminationType.BUDGET, budget_usd=0.0)
        errors = ContractValidator.validate_loop_config(RoutePattern.INTERVAL_LOOP, lc)
        assert any("budget_usd" in e.message for e in errors)

    def test_budget_termination_positive_usd_ok(self):
        lc = LoopConfig(termination_type=LoopTerminationType.BUDGET, budget_usd=5.0)
        errors = ContractValidator.validate_loop_config(RoutePattern.INTERVAL_LOOP, lc)
        assert errors == []

    def test_compaction_trigger_pct_out_of_range_low(self):
        cc = CompactionConfig(trigger_token_pct=0)
        lc = LoopConfig(compaction=cc)
        errors = ContractValidator.validate_loop_config(RoutePattern.REACT_LOOP, lc)
        assert any("trigger_token_pct" in e.message for e in errors)

    def test_compaction_trigger_pct_out_of_range_high(self):
        cc = CompactionConfig(trigger_token_pct=100)
        lc = LoopConfig(compaction=cc)
        errors = ContractValidator.validate_loop_config(RoutePattern.REACT_LOOP, lc)
        assert any("trigger_token_pct" in e.message for e in errors)

    def test_compaction_preserve_last_n_zero(self):
        cc = CompactionConfig(preserve_last_n=0)
        lc = LoopConfig(compaction=cc)
        errors = ContractValidator.validate_loop_config(RoutePattern.REACT_LOOP, lc)
        assert any("preserve_last_n" in e.message for e in errors)

    def test_compaction_valid_config_no_errors(self):
        # preserve_last_n must be >= stuck_detection_threshold (default 3)
        cc = CompactionConfig(trigger_token_pct=70, preserve_last_n=3)
        lc = LoopConfig(compaction=cc)
        errors = ContractValidator.validate_loop_config(RoutePattern.REACT_LOOP, lc)
        assert errors == []

    def test_compaction_preserve_last_n_below_stuck_threshold(self):
        # preserve_last_n=2 < stuck_detection_threshold=3 should produce an error
        cc = CompactionConfig(trigger_token_pct=70, preserve_last_n=2)
        lc = LoopConfig(stuck_detection_threshold=3, compaction=cc)
        errors = ContractValidator.validate_loop_config(RoutePattern.REACT_LOOP, lc)
        assert any("preserve_last_n" in e.message for e in errors)

    def test_all_three_loop_patterns_need_config(self):
        for pattern in (RoutePattern.REACT_LOOP, RoutePattern.GOAL_DRIVEN_LOOP, RoutePattern.INTERVAL_LOOP):
            errors = ContractValidator.validate_loop_config(pattern, None)
            assert errors, f"Expected error for {pattern}"


# ---------------------------------------------------------------------------
# validate_route — end-to-end integration
# ---------------------------------------------------------------------------

class TestValidateRouteWithLoopPatterns:
    def test_react_loop_full_valid(self):
        agents = {
            "thinker": make_agent("T", inputs=["context"], outputs=["thought", "next_action"]),
            "actor": make_agent("A", inputs=["next_action"], outputs=["action_result"]),
            "observer": make_agent("O", inputs=["action_result"], outputs=["done", "observation"]),
        }
        lc = LoopConfig(max_iterations=10, stuck_detection_threshold=3)
        rd = route(RoutePattern.REACT_LOOP, agents, lc=lc)
        errors = ContractValidator.validate_route(rd)
        assert errors == []

    def test_react_loop_missing_loop_config_error(self):
        agents = {
            "thinker": make_agent("T", inputs=["context"], outputs=["thought", "next_action"]),
            "actor": make_agent("A", inputs=["next_action"], outputs=["action_result"]),
            "observer": make_agent("O", inputs=["action_result"], outputs=["done", "observation"]),
        }
        rd = route(RoutePattern.REACT_LOOP, agents, lc=None)
        errors = ContractValidator.validate_route(rd)
        assert any("LoopConfig" in e.message for e in errors)
