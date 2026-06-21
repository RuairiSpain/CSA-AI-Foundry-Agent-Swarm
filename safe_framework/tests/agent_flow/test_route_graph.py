"""
Agent flow graph tests.

For each of the 12 primary patterns, verify:
  1. No disconnected nodes (all reachable from an entry node)
  2. At least one entry node and one exit node
  3. At least one edge exists for multi-agent patterns
"""

import pytest
from safe_core.models import Agent, RouteDefinition, RoutePattern

from .conftest import build_graph


def make_agent(name, inputs=None, outputs=None):
    return Agent(
        name=name,
        category="test",
        version="1.0",
        input_schema={"properties": {k: {} for k in (inputs or [])}, "required": []},
        output_schema={"properties": {k: {} for k in (outputs or [])}, "required": []},
    )


# Canonical agent sets for testable (primary) patterns
ROUTE_AGENTS = {
    RoutePattern.SUPERVISOR_MANAGER: {
        "supervisor": make_agent("Supervisor"),
        "specialist_a": make_agent("SpecialistA"),
        "specialist_b": make_agent("SpecialistB"),
        "aggregator": make_agent("Aggregator"),
    },
    RoutePattern.SEQUENTIAL_PIPELINE: {
        "stage_0": make_agent("Stage0", outputs=["data"]),
        "stage_1": make_agent("Stage1", inputs=["data"], outputs=["result"]),
        "stage_2": make_agent("Stage2", inputs=["result"]),
    },
    RoutePattern.FAN_OUT_FAN_IN: {
        "processor_0": make_agent("P0"),
        "processor_1": make_agent("P1"),
        "aggregator": make_agent("Agg", inputs=["results"]),
    },
    RoutePattern.MAP_REDUCE: {
        "splitter": make_agent("Splitter", outputs=["chunks"]),
        "mapper": make_agent("Mapper", inputs=["data_chunk"], outputs=["mapped_result"]),
        "reducer": make_agent("Reducer", inputs=["mapped_results"]),
    },
    RoutePattern.ROUND_ROBIN: {
        "dispatcher": make_agent("Dispatcher"),
        "worker_0": make_agent("W0"),
        "worker_1": make_agent("W1"),
    },
    RoutePattern.EVALUATOR_OPTIMIZER: {
        "generator": make_agent("Gen"),
        "evaluator": make_agent("Eval"),
        "optimizer": make_agent("Opt"),
    },
    RoutePattern.REFLECTION: {
        "generator": make_agent("Gen"),
        "critic": make_agent("Critic"),
        "refiner": make_agent("Refiner"),
    },
    RoutePattern.RAG: {
        "retriever": make_agent("Retriever"),
        "reranker": make_agent("Reranker"),
        "generator": make_agent("Gen"),
    },
    RoutePattern.PLANNING: {
        "planner": make_agent("Planner"),
        "executor": make_agent("Executor"),
        "reviewer": make_agent("Reviewer"),
    },
}


@pytest.mark.parametrize("pattern,agents", list(ROUTE_AGENTS.items()))
class TestRouteGraphConnectivity:
    def test_has_nodes(self, pattern, agents):
        route = RouteDefinition(
            name="test", pattern=pattern, agents=agents
        )
        graph = build_graph(route)
        assert len(graph.nodes) == len(agents)

    def test_has_entry_nodes(self, pattern, agents):
        route = RouteDefinition(
            name="test", pattern=pattern, agents=agents
        )
        graph = build_graph(route)
        assert len(graph.entry_nodes) >= 1, f"{pattern.value}: no entry nodes"

    def test_has_exit_nodes(self, pattern, agents):
        route = RouteDefinition(
            name="test", pattern=pattern, agents=agents
        )
        graph = build_graph(route)
        assert len(graph.exit_nodes) >= 1, f"{pattern.value}: no exit nodes"

    def test_multi_agent_has_edges(self, pattern, agents):
        if len(agents) < 2:
            pytest.skip("Single-agent route has no edges by definition")
        route = RouteDefinition(
            name="test", pattern=pattern, agents=agents
        )
        graph = build_graph(route)
        assert len(graph.edges) >= 1, f"{pattern.value}: no edges between agents"

    def test_no_disconnected_nodes(self, pattern, agents):
        route = RouteDefinition(
            name="test", pattern=pattern, agents=agents
        )
        graph = build_graph(route)
        disconnected = graph.has_disconnected_nodes()
        assert disconnected == [], (
            f"{pattern.value}: unreachable nodes: {disconnected}"
        )


class TestRouteGraphHelpers:
    def test_reachable_from_chain(self):
        route = RouteDefinition(
            name="test",
            pattern=RoutePattern.SEQUENTIAL_PIPELINE,
            agents={
                "stage_0": make_agent("S0"),
                "stage_1": make_agent("S1"),
                "stage_2": make_agent("S2"),
            },
        )
        graph = build_graph(route)
        reachable = graph.reachable_from("stage_0")
        assert "stage_0" in reachable
        assert "stage_1" in reachable
        assert "stage_2" in reachable

    def test_all_nodes_reachable_true(self):
        route = RouteDefinition(
            name="test",
            pattern=RoutePattern.SEQUENTIAL_PIPELINE,
            agents={
                "stage_0": make_agent("S0"),
                "stage_1": make_agent("S1"),
            },
        )
        graph = build_graph(route)
        assert graph.all_nodes_reachable()
