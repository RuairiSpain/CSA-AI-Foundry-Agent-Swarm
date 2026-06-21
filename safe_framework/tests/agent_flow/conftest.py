"""Fixtures for agent flow tests: MockAgent, graph builder, scenario helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pytest

from safe_core.models import Agent, RouteDefinition, RoutePattern


# ---------------------------------------------------------------------------
# MockAgent
# ---------------------------------------------------------------------------

@dataclass
class MockResult:
    """Synthetic output from a MockAgent invocation."""
    agent_name: str
    inputs_received: Dict[str, Any]
    outputs: Dict[str, Any]
    calls: int = 1


class MockAgent:
    """Drop-in agent stub that records calls and returns schema-compliant output."""

    def __init__(self, agent: Agent, synthetic_outputs: Optional[Dict[str, Any]] = None):
        self.agent = agent
        self._synthetic = synthetic_outputs or {}
        self._calls: List[Dict[str, Any]] = []

    async def invoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        self._calls.append(inputs)
        outputs = {
            k: self._synthetic.get(k, f"synthetic_{k}")
            for k in self.agent.output_schema.get("properties", {})
        }
        return outputs

    @property
    def calls(self) -> int:
        return len(self._calls)

    @property
    def last_input(self) -> Optional[Dict[str, Any]]:
        return self._calls[-1] if self._calls else None


# ---------------------------------------------------------------------------
# Graph helpers
# ---------------------------------------------------------------------------

@dataclass
class RouteGraph:
    """Static topology of a route for connectivity analysis."""
    pattern: RoutePattern
    nodes: List[str]                    # all agent keys
    edges: List[tuple]                  # (source_key, target_key)
    entry_nodes: List[str] = field(default_factory=list)
    exit_nodes: List[str] = field(default_factory=list)

    def reachable_from(self, start: str) -> set:
        """BFS reachability from a node."""
        visited = set()
        queue = [start]
        adj = {}
        for src, dst in self.edges:
            adj.setdefault(src, []).append(dst)
        while queue:
            node = queue.pop(0)
            if node in visited:
                continue
            visited.add(node)
            queue.extend(adj.get(node, []))
        return visited

    def all_nodes_reachable(self) -> bool:
        """Check all nodes are reachable from at least one entry node."""
        if not self.entry_nodes:
            return True  # no topology defined
        reachable = set()
        for entry in self.entry_nodes:
            reachable |= self.reachable_from(entry)
        return all(n in reachable for n in self.nodes)

    def has_disconnected_nodes(self) -> List[str]:
        if not self.entry_nodes:
            return []
        reachable = set()
        for entry in self.entry_nodes:
            reachable |= self.reachable_from(entry)
        return [n for n in self.nodes if n not in reachable]


def build_graph(route_def: RouteDefinition) -> RouteGraph:
    """Infer route topology from agent key naming conventions."""
    pattern = route_def.pattern
    agents = route_def.agents
    keys = list(agents.keys())
    edges = []
    entry = []
    exits = []

    if pattern == RoutePattern.SUPERVISOR_MANAGER:
        sup = [k for k in keys if k == "supervisor"]
        specs = sorted(k for k in keys if k.startswith("specialist_"))
        agg = [k for k in keys if k == "aggregator"]
        entry = sup or keys[:1]
        for s in sup:
            for sp in specs:
                edges.append((s, sp))
        for sp in specs:
            for a in agg:
                edges.append((sp, a))
        exits = agg or keys[-1:]

    elif pattern == RoutePattern.SEQUENTIAL_PIPELINE:
        stages = sorted(k for k in keys if k.startswith("stage_"))
        entry = stages[:1]
        exits = stages[-1:]
        for i in range(len(stages) - 1):
            edges.append((stages[i], stages[i + 1]))

    elif pattern == RoutePattern.FAN_OUT_FAN_IN:
        procs = sorted(k for k in keys if k.startswith("processor_"))
        agg = [k for k in keys if k == "aggregator"]
        entry = procs if procs else keys[:1]   # all processors are entry nodes
        for p in procs:
            for a in agg:
                edges.append((p, a))
        exits = agg

    elif pattern == RoutePattern.MAP_REDUCE:
        order = ["splitter", "mapper", "reducer"]
        present = [k for k in order if k in keys]
        entry = present[:1]
        exits = present[-1:]
        for i in range(len(present) - 1):
            edges.append((present[i], present[i + 1]))

    elif pattern == RoutePattern.ROUND_ROBIN:
        disp = [k for k in keys if k == "dispatcher"]
        workers = sorted(k for k in keys if k.startswith("worker_"))
        entry = disp
        for d in disp:
            for w in workers:
                edges.append((d, w))
        exits = workers

    elif pattern in (
        RoutePattern.EVALUATOR_OPTIMIZER, RoutePattern.REFLECTION,
        RoutePattern.PLANNING, RoutePattern.RAG,
    ):
        # Linear 3-stage patterns
        entry = keys[:1]
        exits = keys[-1:]
        for i in range(len(keys) - 1):
            edges.append((keys[i], keys[i + 1]))

    else:
        # Generic: treat all as connected chain
        entry = keys[:1]
        exits = keys[-1:]
        for i in range(len(keys) - 1):
            edges.append((keys[i], keys[i + 1]))

    return RouteGraph(
        pattern=pattern,
        nodes=keys,
        edges=edges,
        entry_nodes=entry,
        exit_nodes=exits,
    )


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_agent_factory():
    """Return a function that wraps Agent in a MockAgent."""
    def factory(agent: Agent, synthetic_outputs=None) -> MockAgent:
        return MockAgent(agent, synthetic_outputs)
    return factory
