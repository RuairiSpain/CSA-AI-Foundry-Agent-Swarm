"""Tests for safe_core.agent_validation (AgentContractValidator + AgentDiscovery)."""

import pytest
from safe_core.agent_validation import AgentContractValidator, AgentDiscovery, ValidationResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _agent_contract(outputs=None, inputs=None, timeout=60, dependencies=None):
    """Build a minimal agent YAML dict."""
    out_list = [{"name": n} for n in (outputs or [])]
    in_list = [{"name": n} for n in (inputs or [])]
    return {
        "contract": {
            "outputs": out_list,
            "inputs": in_list,
        },
        "description": "test agent",
        "metadata": {
            "timeout_seconds": timeout,
            "dependencies": dependencies or [],
            "requirements": {"packages": []},
        },
    }


CATALOG = {
    "standalone": [
        {
            "id": "researcher-001",
            "name": "researcher",
            "category": "research",
            "description": "multi-step research agent for documents",
            "tags": ["research", "documents"],
            "discovery": {"keywords": ["research"], "quality_rating": 4.5, "usage_count": 100},
            "use_cases": ["document analysis"],
        },
        {
            "id": "summarizer-001",
            "name": "summarizer",
            "category": "nlp",
            "description": "summarize text",
            "tags": ["nlp", "summary"],
            "discovery": {"keywords": ["summary"], "quality_rating": 4.0, "usage_count": 50},
            "use_cases": [],
        },
    ],
    "patterns": {
        "fan-out-fan-in": [
            {
                "id": "fan-aggregator-001",
                "name": "fan-aggregator",
                "category": "aggregator",
                "placeholder": "aggregator",
                "description": "aggregates parallel results",
                "tags": ["aggregator"],
                "discovery": {"quality_rating": 3.8, "usage_count": 20, "keywords": []},
                "use_cases": [],
            }
        ]
    },
}


# ---------------------------------------------------------------------------
# AgentContractValidator
# ---------------------------------------------------------------------------

class TestAgentContractValidatorPatternNotFound:
    def test_returns_error_for_unknown_pattern(self):
        v = AgentContractValidator()
        result = v.validate_agent_for_pattern({}, "no-such-pattern", "processor")
        assert not result.valid
        assert any("not found" in e for e in result.errors)


class TestAgentContractValidatorPlaceholderNotFound:
    def test_returns_error_for_unknown_placeholder(self):
        v = AgentContractValidator()
        result = v.validate_agent_for_pattern(
            _agent_contract(), "fan-out-fan-in", "no-such-placeholder"
        )
        assert not result.valid
        assert any("no placeholder" in e for e in result.errors)


class TestAgentContractValidatorNoContract:
    def test_returns_error_when_contract_missing(self):
        v = AgentContractValidator()
        result = v.validate_agent_for_pattern({}, "fan-out-fan-in", "processor")
        assert not result.valid
        assert any("contract" in e for e in result.errors)


class TestAgentContractValidatorHappyPath:
    def test_valid_processor_passes(self):
        v = AgentContractValidator()
        contract = _agent_contract(outputs=["processed"])
        result = v.validate_agent_for_pattern(contract, "fan-out-fan-in", "processor")
        assert result.valid
        assert result.errors == []

    def test_no_inputs_generates_warning(self):
        v = AgentContractValidator()
        contract = {
            "contract": {"outputs": [{"name": "x"}], "inputs": []},
            "description": "",
            "metadata": {"timeout_seconds": 30, "dependencies": [], "requirements": {"packages": []}},
        }
        result = v.validate_agent_for_pattern(contract, "fan-out-fan-in", "processor")
        assert any("inputs" in w for w in result.warnings)

    def test_no_outputs_generates_warning(self):
        v = AgentContractValidator()
        contract = {
            "contract": {"outputs": [], "inputs": [{"name": "x"}]},
            "description": "",
            "metadata": {"timeout_seconds": 30, "dependencies": [], "requirements": {"packages": []}},
        }
        result = v.validate_agent_for_pattern(contract, "fan-out-fan-in", "processor")
        assert any("outputs" in w for w in result.warnings)


class TestAgentContractValidatorWarnings:
    def test_high_timeout_warns(self):
        v = AgentContractValidator()
        contract = _agent_contract(outputs=["x"], timeout=400)
        result = v.validate_agent_for_pattern(contract, "fan-out-fan-in", "processor")
        assert any("timeout" in w.lower() for w in result.warnings)

    def test_many_dependencies_warns(self):
        v = AgentContractValidator()
        contract = _agent_contract(outputs=["x"], dependencies=list(range(11)))
        result = v.validate_agent_for_pattern(contract, "fan-out-fan-in", "processor")
        assert any("dependenc" in w.lower() for w in result.warnings)

    def test_many_packages_warns(self):
        v = AgentContractValidator()
        contract = _agent_contract(outputs=["x"])
        contract["metadata"]["requirements"]["packages"] = list(range(21))
        result = v.validate_agent_for_pattern(contract, "fan-out-fan-in", "processor")
        assert any("package" in w.lower() for w in result.warnings)


class TestSupervisorSpecific:
    def test_supervisor_missing_routing_decision_fails(self):
        v = AgentContractValidator()
        contract = _agent_contract(outputs=["something_else"])
        result = v.validate_agent_for_pattern(contract, "supervisor-manager", "supervisor")
        assert not result.valid
        assert any("routing_decision" in e for e in result.errors)

    def test_supervisor_with_routing_decision_passes(self):
        v = AgentContractValidator()
        contract = _agent_contract(outputs=["routing_decision"])
        result = v.validate_agent_for_pattern(contract, "supervisor-manager", "supervisor")
        assert result.valid


class TestFanOutSpecific:
    def test_aggregator_without_array_description_warns(self):
        v = AgentContractValidator()
        contract = _agent_contract(outputs=["result"])
        contract["description"] = "simple aggregator"
        result = v.validate_agent_for_pattern(contract, "fan-out-fan-in", "aggregator")
        assert any("array" in w.lower() or "parallel" in w.lower() for w in result.warnings)

    def test_aggregator_with_parallel_description_no_warn(self):
        v = AgentContractValidator()
        contract = _agent_contract(outputs=["result"])
        contract["description"] = "handles parallel results array"
        result = v.validate_agent_for_pattern(contract, "fan-out-fan-in", "aggregator")
        assert not any("array" in w.lower() or "parallel" in w.lower() for w in result.warnings)


# ---------------------------------------------------------------------------
# AgentDiscovery
# ---------------------------------------------------------------------------

class TestAgentDiscoverySearch:
    def test_search_by_name(self):
        d = AgentDiscovery(CATALOG)
        results = d.search_agents("researcher")
        assert any(a["name"] == "researcher" for a in results)

    def test_search_by_tag(self):
        d = AgentDiscovery(CATALOG)
        results = d.search_agents("nlp")
        assert any(a["name"] == "summarizer" for a in results)

    def test_search_by_use_case(self):
        d = AgentDiscovery(CATALOG)
        results = d.search_agents("document analysis")
        assert len(results) >= 1

    def test_search_includes_pattern_agents(self):
        d = AgentDiscovery(CATALOG)
        results = d.search_agents("aggregat")
        assert any("aggregator" in a.get("name", "") for a in results)

    def test_search_returns_empty_for_no_match(self):
        d = AgentDiscovery(CATALOG)
        assert d.search_agents("zzz_nothing_matches_xyz") == []


class TestAgentDiscoveryFilter:
    def test_filter_by_category(self):
        d = AgentDiscovery(CATALOG)
        results = d.filter_agents(category="research")
        assert all(a["category"] == "research" for a in results)

    def test_filter_by_min_rating(self):
        d = AgentDiscovery(CATALOG)
        results = d.filter_agents(min_rating=4.3)
        for a in results:
            assert a.get("discovery", {}).get("quality_rating", 0) >= 4.3

    def test_filter_by_pattern(self):
        d = AgentDiscovery(CATALOG)
        results = d.filter_agents(pattern="fan-out-fan-in")
        assert all(a.get("id", "").startswith("fan-out-fan-in") for a in results)


class TestAgentDiscoverySuggest:
    def test_suggest_returns_pattern_specific_first(self):
        d = AgentDiscovery(CATALOG)
        suggestions = d.suggest_agents("fan-out-fan-in", "aggregator")
        assert len(suggestions) > 0
        assert suggestions[0].get("suggestion_rank") == 1

    def test_suggest_falls_back_to_standalone(self):
        d = AgentDiscovery(CATALOG)
        suggestions = d.suggest_agents("fan-out-fan-in", "processor")
        assert len(suggestions) > 0
        assert all(s.get("suggestion_rank") == 2 for s in suggestions)


class TestAgentDiscoveryStats:
    def test_stats_contains_expected_keys(self):
        d = AgentDiscovery(CATALOG)
        stats = d.get_agent_stats()
        assert "total_agents" in stats
        assert "standalone_agents" in stats
        assert "pattern_agents" in stats
        assert "by_category" in stats
        assert "average_rating" in stats

    def test_stats_counts_match(self):
        d = AgentDiscovery(CATALOG)
        stats = d.get_agent_stats()
        standalone = len(CATALOG["standalone"])
        pattern = sum(len(v) for v in CATALOG["patterns"].values())
        assert stats["standalone_agents"] == standalone
        assert stats["pattern_agents"] == pattern
        assert stats["total_agents"] == standalone + pattern


class TestAgentDiscoveryGetAgent:
    def test_get_existing_standalone(self):
        d = AgentDiscovery(CATALOG)
        agent = d.get_agent("researcher-001")
        assert agent is not None
        assert agent["name"] == "researcher"

    def test_get_existing_pattern_agent(self):
        d = AgentDiscovery(CATALOG)
        agent = d.get_agent("fan-aggregator-001")
        assert agent is not None

    def test_get_nonexistent_returns_none(self):
        d = AgentDiscovery(CATALOG)
        assert d.get_agent("does-not-exist") is None
