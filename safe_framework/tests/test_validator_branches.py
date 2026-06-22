"""Tests for safe_core.validator (ContractValidator) — one test per validation branch."""

import pytest
from safe_core.models import Agent, RouteDefinition, RoutePattern
from safe_core.validator import ContractValidator


def make_agent(name, inputs=None, outputs=None, deps=None):
    """Convenience factory."""
    return Agent(
        name=name,
        category="test",
        version="1.0",
        input_schema={"properties": {k: {} for k in (inputs or [])}, "required": list(inputs or [])},
        output_schema={"properties": {k: {} for k in (outputs or [])}, "required": list(outputs or [])},
        dependencies=deps or [],
    )


def route(pattern, agents, total=120, per_agent=60):
    return RouteDefinition(
        name="test-route",
        pattern=pattern,
        agents=agents,
        timeout_seconds=total,
        per_agent_timeout_seconds=per_agent,
    )


# ---------------------------------------------------------------------------
# validate_timeouts
# ---------------------------------------------------------------------------

class TestValidateTimeouts:
    def test_valid_timeouts_no_errors(self):
        errors = ContractValidator.validate_timeouts(120, 60)
        assert errors == []

    def test_total_less_than_per_agent_error(self):
        errors = ContractValidator.validate_timeouts(30, 60)
        assert any("timeout" in e.error_type for e in errors)

    def test_total_too_low_error(self):
        errors = ContractValidator.validate_timeouts(5, 2)
        assert any("too_low" in e.error_type for e in errors)

    def test_both_errors_combined(self):
        errors = ContractValidator.validate_timeouts(5, 10)
        types = {e.error_type for e in errors}
        assert "timeout_mismatch" in types
        assert "timeout_too_low" in types


# ---------------------------------------------------------------------------
# validate_no_cycles
# ---------------------------------------------------------------------------

class TestValidateNoCycles:
    def test_no_deps_no_cycles(self):
        agents = {
            "a": make_agent("AgentA"),
            "b": make_agent("AgentB"),
        }
        errors = ContractValidator.validate_no_cycles(agents)
        assert errors == []

    def test_linear_chain_no_cycles(self):
        agents = {
            "a": make_agent("AgentA"),
            "b": make_agent("AgentB", deps=["AgentA"]),
        }
        errors = ContractValidator.validate_no_cycles(agents)
        assert errors == []

    def test_cycle_detected(self):
        agents = {
            "a": make_agent("AgentA", deps=["AgentB"]),
            "b": make_agent("AgentB", deps=["AgentA"]),
        }
        errors = ContractValidator.validate_no_cycles(agents)
        assert any("circular" in e.error_type for e in errors)


# ---------------------------------------------------------------------------
# validate_agent_contracts — SUPERVISOR_MANAGER
# ---------------------------------------------------------------------------

class TestSupervisorManager:
    def test_missing_supervisor_error(self):
        agents = {"specialist_a": make_agent("SpecialistA")}
        errors = ContractValidator.validate_agent_contracts(RoutePattern.SUPERVISOR_MANAGER, agents)
        assert any("missing_agent" in e.error_type for e in errors)

    def test_specialist_missing_input_from_supervisor_error(self):
        agents = {
            "supervisor": make_agent("Supervisor", outputs=["loan_type"]),
            "specialist_a": make_agent("SpecialistA", inputs=["credit_score"]),
        }
        errors = ContractValidator.validate_agent_contracts(RoutePattern.SUPERVISOR_MANAGER, agents)
        assert any("contract_mismatch" in e.error_type for e in errors)

    def test_valid_supervisor_manager_no_errors(self):
        agents = {
            "supervisor": make_agent("Supervisor", outputs=["score"]),
            "specialist_a": make_agent("SpecialistA", inputs=["score"]),
        }
        errors = ContractValidator.validate_agent_contracts(RoutePattern.SUPERVISOR_MANAGER, agents)
        assert errors == []


# ---------------------------------------------------------------------------
# validate_agent_contracts — FAN_OUT_FAN_IN
# ---------------------------------------------------------------------------

class TestFanOutFanIn:
    def test_missing_processor_error(self):
        agents = {"aggregator": make_agent("Agg", inputs=["results"])}
        errors = ContractValidator.validate_agent_contracts(RoutePattern.FAN_OUT_FAN_IN, agents)
        assert any("missing_agent" in e.error_type for e in errors)

    def test_missing_aggregator_error(self):
        agents = {"processor_0": make_agent("P0")}
        errors = ContractValidator.validate_agent_contracts(RoutePattern.FAN_OUT_FAN_IN, agents)
        assert any("missing_agent" in e.error_type for e in errors)

    def test_aggregator_missing_results_field_error(self):
        agents = {
            "processor_0": make_agent("P0"),
            "aggregator": make_agent("Agg", inputs=["other"]),
        }
        errors = ContractValidator.validate_agent_contracts(RoutePattern.FAN_OUT_FAN_IN, agents)
        assert any("contract_mismatch" in e.error_type for e in errors)

    def test_valid_fan_out_no_errors(self):
        agents = {
            "processor_0": make_agent("P0"),
            "aggregator": make_agent("Agg", inputs=["results"]),
        }
        errors = ContractValidator.validate_agent_contracts(RoutePattern.FAN_OUT_FAN_IN, agents)
        assert errors == []


# ---------------------------------------------------------------------------
# validate_agent_contracts — MAP_REDUCE
# ---------------------------------------------------------------------------

class TestMapReduce:
    def test_missing_splitter_error(self):
        agents = {
            "mapper": make_agent("Mapper", inputs=["data_chunk"], outputs=["mapped_result"]),
            "reducer": make_agent("Reducer", inputs=["mapped_results"]),
        }
        errors = ContractValidator.validate_agent_contracts(RoutePattern.MAP_REDUCE, agents)
        assert any("splitter" in e.message for e in errors)

    def test_splitter_missing_chunks_output_error(self):
        agents = {
            "splitter": make_agent("Splitter", outputs=["other"]),
            "mapper": make_agent("Mapper", inputs=["data_chunk"], outputs=["mapped_result"]),
            "reducer": make_agent("Reducer", inputs=["mapped_results"]),
        }
        errors = ContractValidator.validate_agent_contracts(RoutePattern.MAP_REDUCE, agents)
        assert any("chunks" in e.message for e in errors)

    def test_mapper_missing_data_chunk_input_error(self):
        agents = {
            "splitter": make_agent("Splitter", outputs=["chunks"]),
            "mapper": make_agent("Mapper", inputs=["other"], outputs=["mapped_result"]),
            "reducer": make_agent("Reducer", inputs=["mapped_results"]),
        }
        errors = ContractValidator.validate_agent_contracts(RoutePattern.MAP_REDUCE, agents)
        assert any("data_chunk" in e.message for e in errors)

    def test_mapper_missing_mapped_result_output_error(self):
        agents = {
            "splitter": make_agent("Splitter", outputs=["chunks"]),
            "mapper": make_agent("Mapper", inputs=["data_chunk"], outputs=["other"]),
            "reducer": make_agent("Reducer", inputs=["mapped_results"]),
        }
        errors = ContractValidator.validate_agent_contracts(RoutePattern.MAP_REDUCE, agents)
        assert any("mapped_result" in e.message for e in errors)

    def test_reducer_missing_mapped_results_input_error(self):
        agents = {
            "splitter": make_agent("Splitter", outputs=["chunks"]),
            "mapper": make_agent("Mapper", inputs=["data_chunk"], outputs=["mapped_result"]),
            "reducer": make_agent("Reducer", inputs=["other"]),
        }
        errors = ContractValidator.validate_agent_contracts(RoutePattern.MAP_REDUCE, agents)
        assert any("mapped_results" in e.message for e in errors)

    def test_valid_map_reduce_no_errors(self):
        agents = {
            "splitter": make_agent("Splitter", outputs=["chunks"]),
            "mapper": make_agent("Mapper", inputs=["data_chunk"], outputs=["mapped_result"]),
            "reducer": make_agent("Reducer", inputs=["mapped_results"]),
        }
        errors = ContractValidator.validate_agent_contracts(RoutePattern.MAP_REDUCE, agents)
        assert errors == []


# ---------------------------------------------------------------------------
# validate_agent_contracts — SEQUENTIAL_PIPELINE
# ---------------------------------------------------------------------------

class TestSequentialPipeline:
    def test_too_few_stages_error(self):
        agents = {"stage_0": make_agent("S0")}
        errors = ContractValidator.validate_agent_contracts(RoutePattern.SEQUENTIAL_PIPELINE, agents)
        assert any("missing_agent" in e.error_type for e in errors)

    def test_stage_missing_required_field_from_previous_error(self):
        agents = {
            "stage_0": make_agent("S0", outputs=["out_a"]),
            "stage_1": make_agent("S1", inputs=["required_field"]),
        }
        errors = ContractValidator.validate_agent_contracts(RoutePattern.SEQUENTIAL_PIPELINE, agents)
        assert any("contract_mismatch" in e.error_type for e in errors)

    def test_valid_pipeline_no_errors(self):
        agents = {
            "stage_0": make_agent("S0", outputs=["data"]),
            "stage_1": make_agent("S1", inputs=["data"]),
        }
        errors = ContractValidator.validate_agent_contracts(RoutePattern.SEQUENTIAL_PIPELINE, agents)
        assert errors == []


# ---------------------------------------------------------------------------
# validate_agent_contracts — ROUND_ROBIN
# ---------------------------------------------------------------------------

class TestRoundRobin:
    def test_missing_dispatcher_error(self):
        agents = {"worker_0": make_agent("W0"), "worker_1": make_agent("W1")}
        errors = ContractValidator.validate_agent_contracts(RoutePattern.ROUND_ROBIN, agents)
        assert any("dispatcher" in e.message for e in errors)

    def test_too_few_workers_error(self):
        agents = {
            "dispatcher": make_agent("Dispatcher"),
            "worker_0": make_agent("W0"),
        }
        errors = ContractValidator.validate_agent_contracts(RoutePattern.ROUND_ROBIN, agents)
        assert any("worker" in e.message.lower() for e in errors)

    def test_valid_round_robin_no_errors(self):
        agents = {
            "dispatcher": make_agent("Dispatcher"),
            "worker_0": make_agent("W0"),
            "worker_1": make_agent("W1"),
        }
        errors = ContractValidator.validate_agent_contracts(RoutePattern.ROUND_ROBIN, agents)
        assert errors == []


# ---------------------------------------------------------------------------
# validate_agent_contracts — MIXTURE_OF_EXPERTS
# ---------------------------------------------------------------------------

class TestMixtureOfExperts:
    def test_missing_router_error(self):
        agents = {
            "expert_0": make_agent("E0"),
            "aggregator": make_agent("Agg", inputs=["expert_outputs"]),
        }
        errors = ContractValidator.validate_agent_contracts(RoutePattern.MIXTURE_OF_EXPERTS, agents)
        assert any("router" in e.message for e in errors)

    def test_missing_expert_error(self):
        agents = {
            "router": make_agent("Router"),
            "aggregator": make_agent("Agg", inputs=["expert_outputs"]),
        }
        errors = ContractValidator.validate_agent_contracts(RoutePattern.MIXTURE_OF_EXPERTS, agents)
        assert any("expert" in e.message.lower() for e in errors)

    def test_aggregator_missing_expert_outputs_field_error(self):
        agents = {
            "router": make_agent("Router"),
            "expert_0": make_agent("E0"),
            "aggregator": make_agent("Agg", inputs=["other"]),
        }
        errors = ContractValidator.validate_agent_contracts(RoutePattern.MIXTURE_OF_EXPERTS, agents)
        assert any("expert_outputs" in e.message for e in errors)

    def test_valid_mixture_of_experts_no_errors(self):
        agents = {
            "router": make_agent("Router"),
            "expert_0": make_agent("E0"),
            "aggregator": make_agent("Agg", inputs=["expert_outputs"]),
        }
        errors = ContractValidator.validate_agent_contracts(RoutePattern.MIXTURE_OF_EXPERTS, agents)
        assert errors == []


# ---------------------------------------------------------------------------
# validate_agent_contracts — HIERARCHICAL_TEAMS
# ---------------------------------------------------------------------------

class TestHierarchicalTeams:
    def test_missing_coordinator_error(self):
        agents = {
            "team_0": make_agent("T0"),
            "team_1": make_agent("T1"),
            "aggregator": make_agent("Agg", inputs=["team_results"]),
        }
        errors = ContractValidator.validate_agent_contracts(RoutePattern.HIERARCHICAL_TEAMS, agents)
        assert any("coordinator" in e.message for e in errors)

    def test_missing_aggregator_error(self):
        agents = {
            "coordinator": make_agent("Coord"),
            "team_0": make_agent("T0"),
            "team_1": make_agent("T1"),
        }
        errors = ContractValidator.validate_agent_contracts(RoutePattern.HIERARCHICAL_TEAMS, agents)
        assert any("aggregator" in e.message for e in errors)

    def test_aggregator_missing_team_results_field_error(self):
        agents = {
            "coordinator": make_agent("Coord"),
            "team_0": make_agent("T0"),
            "team_1": make_agent("T1"),
            "aggregator": make_agent("Agg", inputs=["other"]),
        }
        errors = ContractValidator.validate_agent_contracts(RoutePattern.HIERARCHICAL_TEAMS, agents)
        assert any("team_results" in e.message for e in errors)

    def test_valid_hierarchical_teams_no_errors(self):
        agents = {
            "coordinator": make_agent("Coord"),
            "team_0": make_agent("T0"),
            "team_1": make_agent("T1"),
            "aggregator": make_agent("Agg", inputs=["team_results"]),
        }
        errors = ContractValidator.validate_agent_contracts(RoutePattern.HIERARCHICAL_TEAMS, agents)
        assert errors == []


# ---------------------------------------------------------------------------
# validate_agent_contracts — FALLBACK_CHAIN
# ---------------------------------------------------------------------------

class TestFallbackChain:
    def test_missing_primary_error(self):
        agents = {"fallback_0": make_agent("F0")}
        errors = ContractValidator.validate_agent_contracts(RoutePattern.FALLBACK_CHAIN, agents)
        assert any("primary" in e.message for e in errors)

    def test_missing_fallback_error(self):
        agents = {"primary": make_agent("Primary")}
        errors = ContractValidator.validate_agent_contracts(RoutePattern.FALLBACK_CHAIN, agents)
        assert any("fallback" in e.message.lower() for e in errors)

    def test_valid_fallback_chain_no_errors(self):
        agents = {
            "primary": make_agent("Primary"),
            "fallback_0": make_agent("F0"),
        }
        errors = ContractValidator.validate_agent_contracts(RoutePattern.FALLBACK_CHAIN, agents)
        assert errors == []


# ---------------------------------------------------------------------------
# validate_agent_contracts — RETRY_LOOP
# ---------------------------------------------------------------------------

class TestRetryLoop:
    def test_missing_worker_error(self):
        agents = {"validator": make_agent("V", outputs=["valid"])}
        errors = ContractValidator.validate_agent_contracts(RoutePattern.RETRY_LOOP, agents)
        assert any("worker" in e.message for e in errors)

    def test_missing_validator_error(self):
        agents = {"worker": make_agent("W")}
        errors = ContractValidator.validate_agent_contracts(RoutePattern.RETRY_LOOP, agents)
        assert any("validator" in e.message for e in errors)

    def test_validator_missing_valid_output_error(self):
        agents = {
            "worker": make_agent("W"),
            "validator": make_agent("V", outputs=["other"]),
        }
        errors = ContractValidator.validate_agent_contracts(RoutePattern.RETRY_LOOP, agents)
        assert any("valid" in e.message for e in errors)

    def test_valid_retry_loop_no_errors(self):
        agents = {
            "worker": make_agent("W"),
            "validator": make_agent("V", outputs=["valid"]),
        }
        errors = ContractValidator.validate_agent_contracts(RoutePattern.RETRY_LOOP, agents)
        assert errors == []


# ---------------------------------------------------------------------------
# validate_agent_contracts — DIAMOND
# ---------------------------------------------------------------------------

class TestDiamond:
    def test_missing_splitter_error(self):
        agents = {
            "left_processor": make_agent("LP"),
            "right_processor": make_agent("RP"),
            "merger": make_agent("M", inputs=["left_result", "right_result"]),
        }
        errors = ContractValidator.validate_agent_contracts(RoutePattern.DIAMOND, agents)
        assert any("splitter" in e.message for e in errors)

    def test_splitter_missing_left_right_outputs_error(self):
        agents = {
            "splitter": make_agent("S", outputs=["other"]),
            "left_processor": make_agent("LP"),
            "right_processor": make_agent("RP"),
            "merger": make_agent("M", inputs=["left_result", "right_result"]),
        }
        errors = ContractValidator.validate_agent_contracts(RoutePattern.DIAMOND, agents)
        assert any("left" in e.message or "right" in e.message for e in errors)

    def test_merger_missing_required_inputs_error(self):
        agents = {
            "splitter": make_agent("S", outputs=["left", "right"]),
            "left_processor": make_agent("LP"),
            "right_processor": make_agent("RP"),
            "merger": make_agent("M", inputs=["other"]),
        }
        errors = ContractValidator.validate_agent_contracts(RoutePattern.DIAMOND, agents)
        assert any("left_result" in e.message or "right_result" in e.message for e in errors)

    def test_valid_diamond_no_errors(self):
        agents = {
            "splitter": make_agent("S", outputs=["left", "right"]),
            "left_processor": make_agent("LP"),
            "right_processor": make_agent("RP"),
            "merger": make_agent("M", inputs=["left_result", "right_result"]),
        }
        errors = ContractValidator.validate_agent_contracts(RoutePattern.DIAMOND, agents)
        assert errors == []


# ---------------------------------------------------------------------------
# validate_agent_contracts — CONDITIONAL_BRANCHING
# ---------------------------------------------------------------------------

class TestConditionalBranching:
    def test_missing_evaluator_error(self):
        agents = {"branch_0": make_agent("B0"), "branch_1": make_agent("B1")}
        errors = ContractValidator.validate_agent_contracts(RoutePattern.CONDITIONAL_BRANCHING, agents)
        assert any("evaluator" in e.message for e in errors)

    def test_too_few_branches_error(self):
        agents = {
            "evaluator": make_agent("E"),
            "branch_0": make_agent("B0"),
        }
        errors = ContractValidator.validate_agent_contracts(RoutePattern.CONDITIONAL_BRANCHING, agents)
        assert any("branch" in e.message.lower() for e in errors)

    def test_valid_conditional_branching_no_errors(self):
        agents = {
            "evaluator": make_agent("E"),
            "branch_0": make_agent("B0"),
            "branch_1": make_agent("B1"),
        }
        errors = ContractValidator.validate_agent_contracts(RoutePattern.CONDITIONAL_BRANCHING, agents)
        assert errors == []


# ---------------------------------------------------------------------------
# validate_agent_contracts — TREE_REDUCE
# ---------------------------------------------------------------------------

class TestTreeReduce:
    def test_too_few_leaves_error(self):
        agents = {
            "leaf_0": make_agent("L0"),
            "reducer": make_agent("R", inputs=["left", "right"], outputs=["result"]),
        }
        errors = ContractValidator.validate_agent_contracts(RoutePattern.TREE_REDUCE, agents)
        assert any("leaf" in e.message.lower() for e in errors)

    def test_missing_reducer_error(self):
        agents = {
            "leaf_0": make_agent("L0"),
            "leaf_1": make_agent("L1"),
        }
        errors = ContractValidator.validate_agent_contracts(RoutePattern.TREE_REDUCE, agents)
        assert any("reducer" in e.message for e in errors)

    def test_reducer_missing_left_right_inputs_error(self):
        agents = {
            "leaf_0": make_agent("L0"),
            "leaf_1": make_agent("L1"),
            "reducer": make_agent("R", inputs=["other"], outputs=["result"]),
        }
        errors = ContractValidator.validate_agent_contracts(RoutePattern.TREE_REDUCE, agents)
        assert any("left" in e.message or "right" in e.message for e in errors)

    def test_reducer_missing_result_output_error(self):
        agents = {
            "leaf_0": make_agent("L0"),
            "leaf_1": make_agent("L1"),
            "reducer": make_agent("R", inputs=["left", "right"], outputs=["other"]),
        }
        errors = ContractValidator.validate_agent_contracts(RoutePattern.TREE_REDUCE, agents)
        assert any("result" in e.message for e in errors)

    def test_valid_tree_reduce_no_errors(self):
        agents = {
            "leaf_0": make_agent("L0"),
            "leaf_1": make_agent("L1"),
            "reducer": make_agent("R", inputs=["left", "right"], outputs=["result"]),
        }
        errors = ContractValidator.validate_agent_contracts(RoutePattern.TREE_REDUCE, agents)
        assert errors == []


# ---------------------------------------------------------------------------
# validate_route (end-to-end)
# ---------------------------------------------------------------------------

class TestValidateRoute:
    def test_valid_route_returns_no_errors(self):
        agents = {
            "supervisor": make_agent("Supervisor", outputs=["data"]),
            "specialist_a": make_agent("SpecialistA", inputs=["data"]),
        }
        r = route(RoutePattern.SUPERVISOR_MANAGER, agents)
        errors = ContractValidator.validate_route(r)
        assert errors == []

    def test_invalid_route_accumulates_errors(self):
        agents = {"supervisor": make_agent("Supervisor")}
        r = route(RoutePattern.SUPERVISOR_MANAGER, agents, total=5, per_agent=60)
        errors = ContractValidator.validate_route(r)
        assert len(errors) >= 1


# ---------------------------------------------------------------------------
# Pre-existing uncovered branches (mixture-of-experts, hierarchical-teams, diamond)
# ---------------------------------------------------------------------------

class TestMixtureOfExpertsMissingAggregator:
    def test_missing_aggregator_error(self):
        agents = {
            "router": make_agent("Router"),
            "expert_0": make_agent("ExpertA"),
        }
        errors = ContractValidator.validate_agent_contracts(RoutePattern.MIXTURE_OF_EXPERTS, agents)
        assert any("aggregator" in e.message for e in errors)


class TestHierarchicalTeamsMissingTeams:
    def test_fewer_than_two_teams_error(self):
        agents = {
            "coordinator": make_agent("Coord"),
            "team_0": make_agent("Team0"),
            "aggregator": make_agent("Agg", inputs=["team_results"]),
        }
        errors = ContractValidator.validate_agent_contracts(RoutePattern.HIERARCHICAL_TEAMS, agents)
        assert any("team_*" in e.message or "2 team_*" in e.message for e in errors)


class TestDiamondMissingProcessorsAndMerger:
    def test_missing_left_processor_error(self):
        agents = {
            "splitter": make_agent("Splitter", outputs=["left", "right"]),
            "right_processor": make_agent("RightProc"),
            "merger": make_agent("Merger", inputs=["left_result", "right_result"]),
        }
        errors = ContractValidator.validate_agent_contracts(RoutePattern.DIAMOND, agents)
        assert any("left_processor" in e.message for e in errors)

    def test_missing_right_processor_error(self):
        agents = {
            "splitter": make_agent("Splitter", outputs=["left", "right"]),
            "left_processor": make_agent("LeftProc"),
            "merger": make_agent("Merger", inputs=["left_result", "right_result"]),
        }
        errors = ContractValidator.validate_agent_contracts(RoutePattern.DIAMOND, agents)
        assert any("right_processor" in e.message for e in errors)

    def test_missing_merger_error(self):
        agents = {
            "splitter": make_agent("Splitter", outputs=["left", "right"]),
            "left_processor": make_agent("LeftProc"),
            "right_processor": make_agent("RightProc"),
        }
        errors = ContractValidator.validate_agent_contracts(RoutePattern.DIAMOND, agents)
        assert any("merger" in e.message for e in errors)
