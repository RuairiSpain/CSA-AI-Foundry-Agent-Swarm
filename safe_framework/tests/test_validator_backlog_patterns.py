"""Validation tests for the 15 previously-unvalidated backlog patterns."""

import pytest
from safe_core.models import Agent, RouteDefinition, RoutePattern
from safe_core.validator import ContractValidator


def make_agent(name):
    return Agent(name=name, category="test", version="1.0",
                 input_schema={"properties": {}, "required": []},
                 output_schema={"properties": {}, "required": []})


def validate(pattern, agents):
    return ContractValidator.validate_agent_contracts(pattern, agents)


# ---------------------------------------------------------------------------
# Evaluator-Optimizer
# ---------------------------------------------------------------------------
class TestEvaluatorOptimizer:
    def test_empty_agents_fails(self):
        errors = validate(RoutePattern.EVALUATOR_OPTIMIZER, {})
        assert any("generator" in e.message for e in errors)
        assert any("evaluator" in e.message for e in errors)
        assert any("optimizer" in e.message for e in errors)

    def test_valid_agents_passes(self):
        agents = {k: make_agent(k) for k in ("generator", "evaluator", "optimizer")}
        assert validate(RoutePattern.EVALUATOR_OPTIMIZER, agents) == []


# ---------------------------------------------------------------------------
# Human-in-the-Loop
# ---------------------------------------------------------------------------
class TestHumanInTheLoop:
    def test_empty_agents_fails(self):
        errors = validate(RoutePattern.HUMAN_IN_THE_LOOP, {})
        assert any("pre_validator" in e.message for e in errors)
        assert any("human_gate" in e.message for e in errors)
        assert any("post_processor" in e.message for e in errors)

    def test_valid_agents_passes(self):
        agents = {k: make_agent(k) for k in ("pre_validator", "human_gate", "post_processor")}
        assert validate(RoutePattern.HUMAN_IN_THE_LOOP, agents) == []


# ---------------------------------------------------------------------------
# Reflection
# ---------------------------------------------------------------------------
class TestReflection:
    def test_empty_agents_fails(self):
        errors = validate(RoutePattern.REFLECTION, {})
        assert any("generator" in e.message for e in errors)
        assert any("critic" in e.message for e in errors)
        assert any("refiner" in e.message for e in errors)

    def test_valid_agents_passes(self):
        agents = {k: make_agent(k) for k in ("generator", "critic", "refiner")}
        assert validate(RoutePattern.REFLECTION, agents) == []


# ---------------------------------------------------------------------------
# Orchestrator-Workers
# ---------------------------------------------------------------------------
class TestOrchestratorWorkers:
    def test_empty_agents_fails(self):
        errors = validate(RoutePattern.ORCHESTRATOR_WORKERS, {})
        assert any("orchestrator" in e.message for e in errors)
        assert any("synthesizer" in e.message for e in errors)
        assert any("worker_" in e.message for e in errors)

    def test_missing_workers_fails(self):
        agents = {"orchestrator": make_agent("orchestrator"), "synthesizer": make_agent("synthesizer")}
        errors = validate(RoutePattern.ORCHESTRATOR_WORKERS, agents)
        assert any("worker_" in e.message for e in errors)

    def test_valid_agents_passes(self):
        agents = {k: make_agent(k) for k in ("orchestrator", "synthesizer", "worker_0", "worker_1")}
        assert validate(RoutePattern.ORCHESTRATOR_WORKERS, agents) == []


# ---------------------------------------------------------------------------
# RAG
# ---------------------------------------------------------------------------
class TestRAG:
    def test_empty_agents_fails(self):
        errors = validate(RoutePattern.RAG, {})
        assert any("retriever" in e.message for e in errors)
        assert any("reranker" in e.message for e in errors)
        assert any("generator" in e.message for e in errors)

    def test_valid_agents_passes(self):
        agents = {k: make_agent(k) for k in ("retriever", "reranker", "generator")}
        assert validate(RoutePattern.RAG, agents) == []


# ---------------------------------------------------------------------------
# Planning
# ---------------------------------------------------------------------------
class TestPlanning:
    def test_empty_agents_fails(self):
        errors = validate(RoutePattern.PLANNING, {})
        assert any("planner" in e.message for e in errors)
        assert any("executor" in e.message for e in errors)
        assert any("reviewer" in e.message for e in errors)

    def test_valid_agents_passes(self):
        agents = {k: make_agent(k) for k in ("planner", "executor", "reviewer")}
        assert validate(RoutePattern.PLANNING, agents) == []


# ---------------------------------------------------------------------------
# Gate-Guard
# ---------------------------------------------------------------------------
class TestGateGuard:
    def test_empty_agents_fails(self):
        errors = validate(RoutePattern.GATE_GUARD, {})
        assert any("guard" in e.message for e in errors)
        assert any("processor" in e.message for e in errors)

    def test_valid_agents_passes(self):
        agents = {k: make_agent(k) for k in ("guard", "processor")}
        assert validate(RoutePattern.GATE_GUARD, agents) == []


# ---------------------------------------------------------------------------
# Self-Consistency
# ---------------------------------------------------------------------------
class TestSelfConsistency:
    def test_empty_agents_fails(self):
        errors = validate(RoutePattern.SELF_CONSISTENCY, {})
        assert any("worker_" in e.message for e in errors)
        assert any("voter" in e.message for e in errors)

    def test_valid_agents_passes(self):
        agents = {k: make_agent(k) for k in ("worker_0", "worker_1", "voter")}
        assert validate(RoutePattern.SELF_CONSISTENCY, agents) == []


# ---------------------------------------------------------------------------
# Debate
# ---------------------------------------------------------------------------
class TestDebate:
    def test_empty_agents_fails(self):
        errors = validate(RoutePattern.DEBATE, {})
        assert any("proposer" in e.message for e in errors)
        assert any("challenger" in e.message for e in errors)
        assert any("judge" in e.message for e in errors)

    def test_valid_agents_passes(self):
        agents = {k: make_agent(k) for k in ("proposer", "challenger", "judge")}
        assert validate(RoutePattern.DEBATE, agents) == []


# ---------------------------------------------------------------------------
# Agent-as-a-Tool
# ---------------------------------------------------------------------------
class TestAgentAsATool:
    def test_empty_agents_fails(self):
        errors = validate(RoutePattern.AGENT_AS_A_TOOL, {})
        assert any("orchestrator" in e.message for e in errors)
        assert any("sub_agent_" in e.message for e in errors)

    def test_valid_agents_passes(self):
        agents = {k: make_agent(k) for k in ("orchestrator", "sub_agent_0")}
        assert validate(RoutePattern.AGENT_AS_A_TOOL, agents) == []


# ---------------------------------------------------------------------------
# Memory-Augmented
# ---------------------------------------------------------------------------
class TestMemoryAugmented:
    def test_empty_agents_fails(self):
        errors = validate(RoutePattern.MEMORY_AUGMENTED, {})
        assert any("memory_reader" in e.message for e in errors)
        assert any("processor" in e.message for e in errors)
        assert any("memory_writer" in e.message for e in errors)

    def test_valid_agents_passes(self):
        agents = {k: make_agent(k) for k in ("memory_reader", "processor", "memory_writer")}
        assert validate(RoutePattern.MEMORY_AUGMENTED, agents) == []


# ---------------------------------------------------------------------------
# Event-Driven
# ---------------------------------------------------------------------------
class TestEventDriven:
    def test_empty_agents_fails(self):
        errors = validate(RoutePattern.EVENT_DRIVEN, {})
        assert any("listener" in e.message for e in errors)
        assert any("router" in e.message for e in errors)
        assert any("handler_" in e.message for e in errors)

    def test_valid_agents_passes(self):
        agents = {k: make_agent(k) for k in ("listener", "router", "handler_0")}
        assert validate(RoutePattern.EVENT_DRIVEN, agents) == []


# ---------------------------------------------------------------------------
# Checkpoint-Resume
# ---------------------------------------------------------------------------
class TestCheckpointResume:
    def test_empty_agents_fails(self):
        errors = validate(RoutePattern.CHECKPOINT_RESUME, {})
        assert any("coordinator" in e.message for e in errors)
        assert any("worker" in e.message for e in errors)
        assert any("checkpoint_store" in e.message for e in errors)

    def test_valid_agents_passes(self):
        agents = {k: make_agent(k) for k in ("coordinator", "worker", "checkpoint_store")}
        assert validate(RoutePattern.CHECKPOINT_RESUME, agents) == []


# ---------------------------------------------------------------------------
# Budget-Aware-Routing
# ---------------------------------------------------------------------------
class TestBudgetAwareRouting:
    def test_empty_agents_fails(self):
        errors = validate(RoutePattern.BUDGET_AWARE_ROUTING, {})
        assert any("cost_estimator" in e.message for e in errors)
        assert any("model_router" in e.message for e in errors)
        assert any("executor" in e.message for e in errors)

    def test_valid_agents_passes(self):
        agents = {k: make_agent(k) for k in ("cost_estimator", "model_router", "executor")}
        assert validate(RoutePattern.BUDGET_AWARE_ROUTING, agents) == []


# ---------------------------------------------------------------------------
# Adaptive-Routing
# ---------------------------------------------------------------------------
class TestAdaptiveRouting:
    def test_empty_agents_fails(self):
        errors = validate(RoutePattern.ADAPTIVE_ROUTING, {})
        assert any("performance_tracker" in e.message for e in errors)
        assert any("router" in e.message for e in errors)
        assert any("worker_" in e.message for e in errors)

    def test_valid_agents_passes(self):
        agents = {k: make_agent(k) for k in ("performance_tracker", "router", "worker_0")}
        assert validate(RoutePattern.ADAPTIVE_ROUTING, agents) == []
