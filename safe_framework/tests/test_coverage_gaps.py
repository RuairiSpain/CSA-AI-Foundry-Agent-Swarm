"""
Targeted tests that cover the remaining uncovered lines across safe_core modules.
Each section notes the file and lines being hit.
"""
import asyncio
import ast
from collections import OrderedDict
from datetime import datetime, timedelta
from pathlib import Path
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _run(coro):
    return asyncio.run(coro)


# ===========================================================================
# chain_interview — _list_routes (lines 32-47)
# ===========================================================================

from safe_core.chain_interview import _list_routes, _extract_fields, ChainInterviewer


class TestListRoutes:
    def test_nonexistent_dir(self, tmp_path):
        assert _list_routes(tmp_path / "missing") == []

    def test_dir_without_route_py_skipped(self, tmp_path):
        (tmp_path / "no-route-file").mkdir()
        assert _list_routes(tmp_path) == []

    def test_reads_pattern_from_config(self, tmp_path):
        d = tmp_path / "my-route"
        d.mkdir()
        (d / "route.py").write_text("")
        (d / "config.yaml").write_text("pattern: sequential-pipeline\n")
        result = _list_routes(tmp_path)
        assert result == [{"name": "my-route", "pattern": "sequential-pipeline"}]

    def test_no_config_yaml_pattern_empty(self, tmp_path):
        d = tmp_path / "bare-route"
        d.mkdir()
        (d / "route.py").write_text("")
        result = _list_routes(tmp_path)
        assert result == [{"name": "bare-route", "pattern": ""}]

    def test_bad_yaml_config_defaults_to_empty(self, tmp_path):
        d = tmp_path / "bad-cfg"
        d.mkdir()
        (d / "route.py").write_text("")
        (d / "config.yaml").write_text("{{{invalid")
        result = _list_routes(tmp_path)
        assert result == [{"name": "bad-cfg", "pattern": ""}]

    def test_multiple_routes_sorted(self, tmp_path):
        for name in ("b-route", "a-route"):
            d = tmp_path / name
            d.mkdir()
            (d / "route.py").write_text("")
        result = _list_routes(tmp_path)
        assert [r["name"] for r in result] == ["a-route", "b-route"]


# ===========================================================================
# chain_interview — _extract_fields (lines 52-63)
# ===========================================================================

class TestExtractFields:
    def test_missing_route_file(self, tmp_path):
        assert _extract_fields(tmp_path, "nonexistent", "required_output_fields") == []

    def test_field_found(self, tmp_path):
        d = tmp_path / "my-route"
        d.mkdir()
        (d / "route.py").write_text('required_output_fields = ["answer", "score"]\n')
        assert _extract_fields(tmp_path, "my-route", "required_output_fields") == [
            "answer",
            "score",
        ]

    def test_field_not_in_source(self, tmp_path):
        d = tmp_path / "my-route"
        d.mkdir()
        (d / "route.py").write_text("# no fields here\n")
        assert _extract_fields(tmp_path, "my-route", "required_output_fields") == []

    def test_invalid_literal_returns_empty(self, tmp_path):
        d = tmp_path / "my-route"
        d.mkdir()
        (d / "route.py").write_text("required_output_fields = [not valid python]\n")
        assert _extract_fields(tmp_path, "my-route", "required_output_fields") == []


# ===========================================================================
# interview.py — no-recommendations path (lines 222, 231-232)
# ===========================================================================

from safe_core.interview import RouteInterviewer
from safe_core.agent_catalog import AgentCatalog
from safe_core.models import Agent


def _empty_catalog_interviewer():
    """Return a RouteInterviewer whose catalog always returns no recommendations."""
    from safe_core.models import Agent

    stub_agent = Agent(
        name="stub-agent",
        category="stub",
        version="1.0",
        description="stub",
        input_schema={"properties": {}},
        output_schema={"properties": {}},
    )
    iv = RouteInterviewer(AgentCatalog())
    iv.catalog.search_by_category = lambda _cat: []
    iv.catalog.search_by_name = lambda _q: [stub_agent]
    return iv


class TestNoRecommendations:
    """interview.py lines 222, 231-232: no-recommendations path in _select_agent."""

    def test_empty_category_shows_message_then_search_succeeds(self):
        # MAP_REDUCE: 3 agents (splitter, mapper, reducer) each with empty category
        # For each agent:
        #   1st input "" → line 231-232: "No agents available..." + continue
        #   2nd input "s" → search → 1 result → auto-select
        # Then timeouts + metadata + confirm
        inputs = [
            "3",                     # MAP_REDUCE pattern
            "", "s",                 # splitter: empty → retry; search → select
            "", "s",                 # mapper:   empty → retry; search → select
            "", "s",                 # reducer:  empty → retry; search → select
            "", "",                  # timeouts
            "mr-r", "", "",          # metadata
            "y",                     # confirm
        ]
        iv = _empty_catalog_interviewer()
        with patch("builtins.input", side_effect=inputs):
            result = _run(iv.start_interview())
        assert result is not None


# ===========================================================================
# chain_interview — inline route creation success path (lines 174-175, 233, 265-288)
# ===========================================================================

def _make_mock_route_def(name: str = "inline-route"):
    """Build a minimal mock RouteDefinition for patching RouteInterviewer."""
    agent = Agent(
        name="fake-agent",
        category="processor",
        version="1.0",
        description="",
        input_schema={"properties": {"text": {}}},
        output_schema={"properties": {"answer": {}}},
    )
    mock_def = MagicMock()
    mock_def.name = name
    # Use an OrderedDict so values()[0] and values()[-1] are deterministic
    mock_def.agents = OrderedDict([("stage_0", agent)])
    return mock_def


def _fake_ef_route_a(d, n, v):
    """_extract_fields stub: route-a outputs ['answer'], no inputs for first step."""
    if v == "required_output_fields" and n == "route-a":
        return ["answer"]
    return []


class TestInlineRouteSuccessPath:
    """chain_interview.py lines 174-175, 233, 265-288."""

    def test_inline_as_first_step_covers_generation(self, tmp_path):
        """Lines 265-272, 274-278 False branch, and 174-175."""
        mock_def = _make_mock_route_def("inline-route")
        mock_generated = MagicMock()
        fake_routes = [{"name": "route-a", "pattern": "sequential-pipeline"}]

        # Inputs:
        # metadata: "", "", ""
        # choice "2" → inline (no input prompts — interview is mocked)
        #   lines 174-175: step appended to steps / context_keys extended
        # choice "1" → existing route-a
        #   no existing mapping prompts for route-a (required_input_fields=[])
        #   condition: ""
        # choice "d" → done (2 steps)
        # options: "", ""
        # timeout: ""
        # review: "y"
        inputs = ["", "", "", "2", "1", "1", "", "d", "", "", "", "y"]

        with patch(
            "safe_core.chain_interview._list_routes", return_value=fake_routes
        ), patch(
            "safe_core.chain_interview._extract_fields", side_effect=_fake_ef_route_a
        ), patch(
            "safe_core.interview.RouteInterviewer"
        ) as MockRI, patch(
            "safe_core.code_generator.RouteCodeGenerator"
        ) as MockRCG:
            MockRI.return_value.start_interview = AsyncMock(return_value=mock_def)
            MockRCG.generate.return_value = mock_generated

            with patch("builtins.input", side_effect=inputs):
                result = _run(ChainInterviewer(routes_dir=tmp_path).start_interview())

        assert result is not None
        assert result.steps[0].route_name == "inline-route"
        assert result.steps[1].route_name == "route-a"

    def test_inline_as_second_step_covers_existing_steps_branch(self, tmp_path):
        """Lines 278-286 (existing_steps True branch in _create_route_inline)."""
        mock_def = _make_mock_route_def("inline-route")
        mock_generated = MagicMock()
        fake_routes = [{"name": "route-a", "pattern": "sequential-pipeline"}]

        # Inputs:
        # metadata: "", "", ""
        # choice "1" → add route-a first (no mapping prompts since existing_steps=[])
        # choice "2" → inline as second step
        #   existing_steps=[step_a], context_keys=["answer"]
        #   entry_agent.input_schema={"properties":{"text":{}}} → required_inputs=["text"]
        #   _ask_field_mapping: "text" not in ["answer"] → unmatched
        #     options=["answer"]; input "1" → maps text → answer
        #   condition: ""
        #   lines 279-286 covered
        # choice "d" → done
        # options: "", ""
        # timeout: ""
        # review: "y"
        inputs = ["", "", "", "1", "1", "2", "1", "", "d", "", "", "", "y"]

        with patch(
            "safe_core.chain_interview._list_routes", return_value=fake_routes
        ), patch(
            "safe_core.chain_interview._extract_fields", side_effect=_fake_ef_route_a
        ), patch(
            "safe_core.interview.RouteInterviewer"
        ) as MockRI, patch(
            "safe_core.code_generator.RouteCodeGenerator"
        ) as MockRCG:
            MockRI.return_value.start_interview = AsyncMock(return_value=mock_def)
            MockRCG.generate.return_value = mock_generated

            with patch("builtins.input", side_effect=inputs):
                result = _run(ChainInterviewer(routes_dir=tmp_path).start_interview())

        assert result is not None
        assert result.steps[0].route_name == "route-a"
        assert result.steps[1].route_name == "inline-route"

    def test_pick_existing_no_input_schema_shows_message(self, tmp_path):
        """Line 233: 'Could not read input schema' when required_input_fields is empty."""
        fake_routes = [
            {"name": "route-a", "pattern": "sequential-pipeline"},
            {"name": "route-b", "pattern": "fan-out-fan-in"},
        ]

        def ef_stub(d, n, v):
            if v == "required_output_fields":
                return ["answer"]
            return []  # no required_input_fields for any route → line 233 triggered

        # Inputs:
        # metadata: "", "", ""
        # choice "1" → route-a (first step, no mapping)
        # choice "1" → route-b (second step, existing_steps=[step_a])
        #   required_input_fields=[] → line 233 printed
        #   condition: ""
        # choice "d" → done
        # options: "", ""
        # timeout: ""
        # review: "y"
        inputs = ["", "", "", "1", "1", "1", "1", "", "d", "", "", "", "y"]

        with patch(
            "safe_core.chain_interview._list_routes", return_value=fake_routes
        ), patch(
            "safe_core.chain_interview._extract_fields", side_effect=ef_stub
        ):
            with patch("builtins.input", side_effect=inputs):
                result = _run(ChainInterviewer(routes_dir=tmp_path).start_interview())

        assert result is not None
        assert len(result.steps) == 2


# ===========================================================================
# agent_validation — AgentContractValidator missing-output (lines 100-101)
# ===========================================================================

from safe_core.agent_validation import AgentContractValidator, AgentDiscovery

_AGENT_CATALOG = {
    "standalone": [
        {
            "id": "researcher-001",
            "name": "researcher",
            "category": "research",
            "description": "multi-step research agent for documents",
            "tags": ["research"],
            "discovery": {
                "keywords": ["research"],
                "quality_rating": 4.5,
                "complexity": "simple",
            },
            "use_cases": ["document analysis"],
        },
        {
            "id": "summarizer-001",
            "name": "summarizer",
            "category": "nlp",
            "description": "summarize text",
            "tags": [],
            "discovery": {
                "keywords": ["summary"],
                "quality_rating": 4.0,
                "complexity": "advanced",
            },
            "use_cases": [],
        },
    ],
    "patterns": {
        "fan-out-fan-in": [
            {
                "id": "fan-aggregator-001",
                "name": "fan-aggregator",
                "category": "aggregator",
                "description": "aggregates parallel results",
                "tags": [],
                "discovery": {
                    "quality_rating": 3.8,
                    "keywords": [],
                    "complexity": "simple",
                },
                "use_cases": [],
            }
        ]
    },
}


class TestAgentValidationGaps:
    def test_missing_required_output_adds_error(self):
        """Lines 100-101: agent missing a required output field."""
        validator = AgentContractValidator()

        mock_placeholder = MagicMock()
        mock_placeholder.id = "supervisor"
        mock_placeholder.required_outputs = ["routing_decision"]

        mock_pattern = MagicMock()
        mock_pattern.placeholders = [mock_placeholder]

        agent_contract = {
            "contract": {
                "outputs": [],   # no outputs → missing "routing_decision"
                "inputs": [],
            }
        }

        with patch("safe_core.patterns.PATTERN_REGISTRY") as mock_reg:
            mock_reg.get_pattern.return_value = mock_pattern
            result = validator.validate_agent_for_pattern(
                agent_contract, "supervisor-manager", "supervisor"
            )

        assert not result.valid
        assert any("routing_decision" in e for e in result.errors)

    def test_filter_agents_complexity_skips_non_matching(self):
        """Line 260: complexity filter `continue` branch."""
        discovery = AgentDiscovery(_AGENT_CATALOG)
        # Only "simple" agents should be returned
        results = discovery.filter_agents(complexity="simple")
        for agent in results:
            assert agent.get("discovery", {}).get("complexity") == "simple"

    def test_get_agent_found_in_patterns(self):
        """Line 359: return agent found in the patterns section of the catalog."""
        discovery = AgentDiscovery(_AGENT_CATALOG)
        found = discovery.get_agent("fan-aggregator-001")
        assert found is not None
        assert found["id"] == "fan-aggregator-001"

    def test_matches_query_description_match(self):
        """Line 371: match on description field — name does NOT match."""
        discovery = AgentDiscovery(_AGENT_CATALOG)
        agent = {
            "id": "test-desc",
            "name": "zzz-no-match",
            "description": "unique-keyword-xyz",
            "tags": [],
            "discovery": {"keywords": [], "complexity": "simple"},
        }
        assert discovery._agent_matches_query(agent, "unique-keyword-xyz")

    def test_matches_query_keyword_match(self):
        """Line 381: match on keywords field — name and description do NOT match."""
        discovery = AgentDiscovery(_AGENT_CATALOG)
        agent = {
            "id": "test-kw",
            "name": "zzz-no-match",
            "description": "zzz",
            "tags": [],
            "discovery": {"keywords": ["special-keyword-abc"], "complexity": "simple"},
        }
        assert discovery._agent_matches_query(agent, "special-keyword-abc")


# ===========================================================================
# audit/logger — filter branches (lines 119, 122, 137)
# ===========================================================================

from safe_core.audit.logger import AuditLogger, AuditEventType


class TestAuditLoggerFilters:
    def _make_logger_with_events(self):
        logger = AuditLogger()

        async def populate():
            await logger.log_event(
                event_type=AuditEventType.ROUTE_CREATED,
                actor="alice@example.com",
                resource="route-a",
                resource_id="route-a-id",
                details={},
            )
            await logger.log_event(
                event_type=AuditEventType.ROUTE_DEPLOYED,
                actor="bob@example.com",
                resource="route-b",
                resource_id="route-b-id",
                details={},
            )

        _run(populate())
        return logger

    def test_filter_by_actor(self):
        """Line 119: filter events by actor."""
        logger = self._make_logger_with_events()
        results = _run(logger.get_events(actor="alice@example.com"))
        assert all(e.actor == "alice@example.com" for e in results)
        assert len(results) == 1

    def test_filter_by_event_type(self):
        """Line 122: filter events by event_type."""
        logger = self._make_logger_with_events()
        results = _run(logger.get_events(event_type=AuditEventType.ROUTE_DEPLOYED))
        assert all(e.event_type == AuditEventType.ROUTE_DEPLOYED for e in results)
        assert len(results) == 1

    def test_compliance_filter_by_severity(self):
        """Line 137: filter compliance events by severity."""
        logger = AuditLogger()

        async def add_compliance():
            await logger.log_event(
                event_type=AuditEventType.ROUTE_CREATED,
                actor="system",
                resource="route-a",
                resource_id="r-a",
                details={},
                severity="high",
                compliance_relevant=True,
            )
            await logger.log_event(
                event_type=AuditEventType.ROUTE_CREATED,
                actor="system",
                resource="route-b",
                resource_id="r-b",
                details={},
                severity="low",
                compliance_relevant=True,
            )

        _run(add_compliance())
        results = _run(logger.get_compliance_events(severity="high"))
        assert all(e.severity == "high" for e in results)
        assert len(results) == 1


# ===========================================================================
# code_generator — unimplemented pattern (line 109) and fallback test data (943)
# ===========================================================================

from safe_core.code_generator import RouteCodeGenerator
from safe_core.models import RouteDefinition, RoutePattern


def _minimal_route_def(**kwargs) -> RouteDefinition:
    defaults = dict(
        name="test-route",
        pattern=RoutePattern.SEQUENTIAL_PIPELINE,
        agents={},
        description="",
        timeout_seconds=120,
        per_agent_timeout_seconds=60,
        csa_email="",
        routing_field=None,
        routing_rules={},
    )
    defaults.update(kwargs)
    return RouteDefinition(**defaults)


class TestCodeGeneratorGaps:
    def test_unimplemented_pattern_raises(self):
        """Line 109: else branch raises NotImplementedError."""
        route_def = _minimal_route_def()
        route_def.pattern = "not-a-real-pattern"  # bypasses all elif branches
        with pytest.raises(NotImplementedError):
            RouteCodeGenerator.generate(route_def)

    def test_fallback_test_data_else_branch(self):
        """Line 943: else branch in _generate_test_data returns generic test data."""
        route_def = _minimal_route_def()
        route_def.pattern = "not-a-real-pattern"
        result = RouteCodeGenerator._generate_test_data(route_def)
        data = ast.literal_eval(result.strip())
        assert data[0]["name"] == "test_case_1"
        assert data[0]["input"] == {}
        assert data[0]["expected"] == {}


# ===========================================================================
# execution/executor — all retries exhausted (line 52)
# ===========================================================================

from safe_core.execution.executor import ExecutionEngine, RetryPolicy
from safe_core.invocation.engine import ExecutionResult, ExecutionStatus


class TestExecutionRetryExhausted:
    def test_all_retries_exhausted_returns_result(self):
        """Line 52: return result after all retries fail."""
        engine = ExecutionEngine(RetryPolicy(max_retries=2, backoff_seconds=0))

        async def always_fail(_input):
            raise RuntimeError("always fails")

        result = ExecutionResult(
            request_id="req-1",
            route_name="test",
            route_version="v1",
            status=ExecutionStatus.PENDING,
        )

        final = _run(engine.execute_with_retry(result, always_fail))
        assert final.status == ExecutionStatus.FAILED
        assert final.retry_count == 2  # retry_count = last attempt index + 1


# ===========================================================================
# governance/approval_engine (lines 58, 74, 79, 90, 94-99, 105-116, 143-145)
# ===========================================================================

from safe_core.governance.approval_engine import ApprovalEngine
from safe_core.governance.models import GovernancePolicy, ApprovalStatus


def _make_engine(
    max_cost: float = 1000.0,
    threshold: int = 1,
    allowed_data_sources: list = None,
) -> ApprovalEngine:
    policy = GovernancePolicy(
        name="test-policy",
        require_approval=True,
        approval_threshold=threshold,
        max_monthly_cost_usd=max_cost,
        allowed_data_sources=allowed_data_sources or [],
    )
    return ApprovalEngine(policy)


class TestApprovalEngineGaps:
    def test_high_cost_assigns_extra_approvers(self):
        """Line 58: cost > 50% of max → finance + security approvers assigned."""
        engine = _make_engine(max_cost=1000.0)
        request = _run(
            engine.create_approval_request(
                route_name="r",
                route_version="v1",
                requester_email="user@x.com",
                agents=[],
                estimated_cost=600.0,  # > 500 = 50% of 1000
                estimated_volume=10,
            )
        )
        assert "finance-lead@company.com" in request.approvers
        assert "security-lead@company.com" in request.approvers

    def test_submit_approval_request_not_found_returns_false(self):
        """Line 74: request_id not in pending → False."""
        engine = _make_engine()
        result = _run(
            engine.submit_approval("nonexistent-id", "approver@x.com", True)
        )
        assert result is False

    def test_submit_approval_approver_not_in_list_returns_false(self):
        """Line 79: approver not in request.approvers → False."""
        engine = _make_engine()
        request = _run(
            engine.create_approval_request(
                route_name="r",
                route_version="v1",
                requester_email="u@x.com",
                agents=[],
                estimated_cost=100.0,
                estimated_volume=1,
            )
        )
        result = _run(
            engine.submit_approval(request.request_id, "stranger@x.com", True)
        )
        assert result is False

    def test_submit_partial_approval_returns_true(self):
        """Line 90: approval_count < threshold → partial approval, still returns True."""
        engine = _make_engine(threshold=2)
        request = _run(
            engine.create_approval_request(
                route_name="r",
                route_version="v1",
                requester_email="u@x.com",
                agents=[],
                estimated_cost=100.0,
                estimated_volume=1,
            )
        )
        approver = request.approvers[0]
        result = _run(
            engine.submit_approval(request.request_id, approver, True)
        )
        assert result is True
        # Request still pending — not yet moved to completed
        assert request.request_id in engine.pending_requests

    def test_submit_approval_completes_request_returns_true(self):
        """Line 88: approval_count >= threshold → request moved to completed."""
        engine = _make_engine(threshold=1)
        request = _run(
            engine.create_approval_request(
                route_name="r",
                route_version="v1",
                requester_email="u@x.com",
                agents=[],
                estimated_cost=100.0,
                estimated_volume=1,
            )
        )
        approver = request.approvers[0]
        result = _run(
            engine.submit_approval(request.request_id, approver, True)
        )
        assert result is True
        assert request.request_id not in engine.pending_requests
        assert any(r.request_id == request.request_id for r in engine.completed_requests)

    def test_get_pending_filtered_by_approver(self):
        """Lines 94-99: get_pending_requests filtered by approver_email."""
        engine = _make_engine(threshold=2)
        req = _run(
            engine.create_approval_request(
                route_name="r",
                route_version="v1",
                requester_email="u@x.com",
                agents=[],
                estimated_cost=100.0,
                estimated_volume=1,
            )
        )
        approver = req.approvers[0]
        # filter matches
        pending = _run(engine.get_pending_requests(approver_email=approver))
        assert any(r.request_id == req.request_id for r in pending)
        # filter excludes
        pending_other = _run(
            engine.get_pending_requests(approver_email="nobody@x.com")
        )
        assert len(pending_other) == 0

    def test_revoke_pending_request(self):
        """Lines 105-106: revoke a pending request."""
        engine = _make_engine(threshold=2)
        req = _run(
            engine.create_approval_request(
                route_name="r",
                route_version="v1",
                requester_email="u@x.com",
                agents=[],
                estimated_cost=100.0,
                estimated_volume=1,
            )
        )
        result = _run(engine.revoke_approval(req.request_id, "policy change"))
        assert result is True
        assert req.status == ApprovalStatus.REVOKED

    def test_revoke_completed_request(self):
        """Lines 108-113: revoke a completed (approved) request."""
        engine = _make_engine(threshold=1)
        req = _run(
            engine.create_approval_request(
                route_name="r",
                route_version="v1",
                requester_email="u@x.com",
                agents=[],
                estimated_cost=100.0,
                estimated_volume=1,
            )
        )
        approver = req.approvers[0]
        _run(engine.submit_approval(req.request_id, approver, True))
        # Now req is in completed_requests
        result = _run(engine.revoke_approval(req.request_id, "revoked"))
        assert result is True
        assert req.status == ApprovalStatus.REVOKED

    def test_revoke_not_found_returns_false(self):
        """Line 111: request not found anywhere → False."""
        engine = _make_engine()
        result = _run(engine.revoke_approval("does-not-exist", "reason"))
        assert result is False

    def test_check_compliance_disallowed_data_source(self):
        """Lines 143-145: data source not in allowed list → warning added."""
        engine = _make_engine(
            max_cost=1000.0, allowed_data_sources=["approved-source"]
        )
        result = _run(
            engine.check_compliance(
                route_name="r",
                agents=[],
                estimated_cost=100.0,
                data_sources=["unapproved-source"],
            )
        )
        assert any("unapproved-source" in w for w in result.warnings)


# ===========================================================================
# governance/models — add_approval rejection + add_warning (lines 87-88, 118)
# ===========================================================================

from safe_core.governance.models import ApprovalRequest, ComplianceCheckResult


class TestGovernanceModelsGaps:
    def test_add_approval_rejected(self):
        """Lines 87-88: approved=False sets REJECTED and rejection_reason."""
        req = ApprovalRequest(
            request_id="req-1",
            route_name="r",
            route_version="v1",
            requester_email="u@x.com",
            approvers=["approver@x.com"],
        )
        req.add_approval("approver@x.com", False, comment="not ready")
        assert req.status == ApprovalStatus.REJECTED
        assert req.rejection_reason == "not ready"

    def test_add_warning(self):
        """Line 118: add_warning appends to warnings list."""
        check = ComplianceCheckResult(passed=True, checks_passed=0, checks_failed=0)
        check.add_warning("borderline cost")
        assert "borderline cost" in check.warnings
        assert check.passed is True  # warning alone doesn't fail


# ===========================================================================
# health/models (lines 35, 82-83, 87-88)
# ===========================================================================

from safe_core.health.models import HealthMetric, RouteHealth, RouteHealthStatus


class TestHealthModelsGaps:
    def test_is_threshold_exceeded_no_threshold(self):
        """Line 35: threshold=None → always False."""
        m = HealthMetric(name="cpu", value=9999.0, unit="pct", threshold=None)
        assert m.is_threshold_exceeded() is False

    def test_update_status_no_executions_offline(self):
        """Lines 82-83: execution_count=0 → OFFLINE."""
        h = RouteHealth("r", "v1", RouteHealthStatus.READY)
        h.update_status()
        assert h.status == RouteHealthStatus.OFFLINE

    def test_update_status_stale_check_frozen(self):
        """Lines 87-88: last_check >1 hour ago → FROZEN."""
        h = RouteHealth("r", "v1", RouteHealthStatus.READY)
        h.execution_count = 1
        h.success_count = 1
        h.last_check = datetime.now() - timedelta(hours=2)
        h.update_status()
        assert h.status == RouteHealthStatus.FROZEN


# ===========================================================================
# health/monitor (lines 47, 173, 198)
# ===========================================================================

from safe_core.health.monitor import HealthMonitor
from safe_core.health.storage.semantic_kernel_store import SemanticKernelRouteHealthStore


class TestHealthMonitorGaps:
    def test_record_execution_auto_registers_new_route(self):
        """Line 47: route not yet registered → auto-registers it."""
        store = SemanticKernelRouteHealthStore()
        monitor = HealthMonitor(store)
        _run(
            monitor.record_execution(
                route_name="new-route",
                version="v1",
                success=True,
                execution_time_ms=50.0,
            )
        )
        assert "new-route:v1" in monitor.monitored_routes

    def test_freeze_route_unknown_key_returns_false(self):
        """Line 173: freeze_route with key not in monitored_routes → False."""
        monitor = HealthMonitor(SemanticKernelRouteHealthStore())
        result = _run(monitor.freeze_route("nonexistent", "v1"))
        assert result is False

    def test_unfreeze_route_unknown_key_returns_false(self):
        """Line 198: unfreeze_route with key not in monitored_routes → False."""
        monitor = HealthMonitor(SemanticKernelRouteHealthStore())
        result = _run(monitor.unfreeze_route("nonexistent", "v1"))
        assert result is False


# ===========================================================================
# health/storage/base — abstract pass stmts (lines 14, 19, 29, 34, 43, 48, 53)
# ===========================================================================

from safe_core.health.storage.base import IRouteHealthStore
from safe_core.health.models import HealthAlert, AlertSeverity


class TestHealthStorageBaseGaps:
    """Calling unbound abstract methods on a concrete subclass covers the pass lines."""

    def test_abstract_pass_statements(self):
        store = SemanticKernelRouteHealthStore()
        health = RouteHealth("r", "v1", RouteHealthStatus.READY)
        alert = HealthAlert(
            route_name="r",
            severity=AlertSeverity.INFO,
            message="test",
            metric_name="m",
            current_value=0.0,
            threshold=1.0,
            suggested_action="none",
        )

        _run(IRouteHealthStore.save_route_health(store, health))
        _run(IRouteHealthStore.get_route_health(store, "r", "v1"))
        _run(IRouteHealthStore.get_route_health_history(store, "r", "v1"))
        _run(IRouteHealthStore.save_alert(store, alert))
        _run(IRouteHealthStore.get_alerts(store))
        _run(IRouteHealthStore.list_all_routes(store))
        _run(IRouteHealthStore.delete_route(store, "r", "v1"))


# ===========================================================================
# health/storage/semantic_kernel_store (lines 34, 37-39, 48, 51-53, 62-71,
#                                        80, 83-85, 105-107, 115-127)
# ===========================================================================

class TestSemanticKernelStoreGaps:
    def _health(self, name="r", version="v1") -> RouteHealth:
        return RouteHealth(name, version, RouteHealthStatus.READY)

    def _alert(self, name="r") -> HealthAlert:
        return HealthAlert(
            route_name=name,
            severity=AlertSeverity.INFO,
            message="m",
            metric_name="m",
            current_value=0.0,
            threshold=1.0,
            suggested_action="n",
        )

    def test_trim_snapshots_beyond_1000(self):
        """Line 34: trim when len > 1000."""
        store = SemanticKernelRouteHealthStore()
        health = self._health()
        key = "r:v1"
        store.health_snapshots[key] = [health] * 1001
        _run(store.save_route_health(health))
        assert len(store.health_snapshots[key]) == 1000

    def test_save_health_exception_returns_false(self):
        """Lines 37-39: exception → return False."""
        store = SemanticKernelRouteHealthStore()
        store.health_snapshots = None  # will raise TypeError on access
        result = _run(store.save_route_health(self._health()))
        assert result is False

    def test_get_health_no_snapshots_returns_none(self):
        """Line 48: empty snapshots list → return None."""
        store = SemanticKernelRouteHealthStore()
        result = _run(store.get_route_health("r", "v1"))
        assert result is None

    def test_get_health_exception_returns_none(self):
        """Lines 51-53: exception → return None."""
        store = SemanticKernelRouteHealthStore()
        store.health_snapshots = None
        result = _run(store.get_route_health("r", "v1"))
        assert result is None

    def test_get_health_history_returns_filtered_list(self):
        """Lines 62-71: normal path — stores and retrieves history with time filter."""
        store = SemanticKernelRouteHealthStore()
        health = self._health()
        _run(store.save_route_health(health))
        history = _run(store.get_route_health_history("r", "v1", hours=24))
        assert len(history) == 1

    def test_get_health_history_exception_returns_empty(self):
        """Lines 70-71: exception → return []."""
        store = SemanticKernelRouteHealthStore()
        store.health_snapshots = None
        result = _run(store.get_route_health_history("r", "v1"))
        assert result == []

    def test_save_alert_trims_beyond_10000(self):
        """Line 80: trim when len > 10000."""
        store = SemanticKernelRouteHealthStore()
        store.alerts = [self._alert()] * 10001
        _run(store.save_alert(self._alert()))
        assert len(store.alerts) == 10000

    def test_save_alert_exception_returns_false(self):
        """Lines 83-85: exception → return False."""
        store = SemanticKernelRouteHealthStore()
        store.alerts = None
        result = _run(store.save_alert(self._alert()))
        assert result is False

    def test_get_alerts_exception_returns_empty(self):
        """Lines 105-107: exception → return []."""
        store = SemanticKernelRouteHealthStore()
        store.alerts = None
        result = _run(store.get_alerts())
        assert result == []

    def test_delete_route_removes_snapshot_and_entry(self):
        """Lines 115-127: delete removes both health_snapshots key and routes entry."""
        store = SemanticKernelRouteHealthStore()
        health = self._health()
        _run(store.save_route_health(health))
        assert "r" in store.routes
        result = _run(store.delete_route("r", "v1"))
        assert result is True
        assert "r:v1" not in store.health_snapshots
        assert "r" not in store.routes

    def test_delete_route_nonexistent_still_returns_true(self):
        """Lines 115-127: missing key branches don't error, still returns True."""
        store = SemanticKernelRouteHealthStore()
        result = _run(store.delete_route("nonexistent", "v1"))
        assert result is True

    def test_delete_route_exception_returns_false(self):
        """Lines 125-127: exception → return False."""
        store = SemanticKernelRouteHealthStore()
        store.health_snapshots = None
        result = _run(store.delete_route("r", "v1"))
        assert result is False


# ===========================================================================
# incidents/responder (lines 44-47)
# ===========================================================================

from safe_core.incidents.responder import IncidentResponder, IncidentSeverity


class TestIncidentResponderGaps:
    def test_resolve_existing_incident(self):
        """Lines 44-46: incident found → status RESOLVED → True."""
        from safe_core.incidents.responder import IncidentStatus

        responder = IncidentResponder()
        _run(responder.create_incident("i1", "test", IncidentSeverity.HIGH, []))
        result = _run(responder.resolve_incident("i1"))
        assert result is True
        assert responder.incidents["i1"].status == IncidentStatus.RESOLVED

    def test_resolve_nonexistent_incident_returns_false(self):
        """Line 47: not found → False."""
        responder = IncidentResponder()
        result = _run(responder.resolve_incident("does-not-exist"))
        assert result is False


# ===========================================================================
# invocation/engine (lines 65, 70)
# ===========================================================================

from safe_core.invocation.engine import RouteInvocationEngine


class TestInvocationEngineGaps:
    def test_dequeue_empty_queue_returns_none(self):
        """Line 65: empty queue → None."""
        engine = RouteInvocationEngine()
        result = _run(engine.dequeue_request())
        assert result is None

    def test_save_result_removes_from_pending(self):
        """Line 70: request deleted from pending after save_result."""
        engine = RouteInvocationEngine()
        req = _run(
            engine.create_execution_request("route", "v1", {"x": 1})
        )
        assert req.request_id in engine.pending_requests
        result = ExecutionResult(
            request_id=req.request_id,
            route_name="route",
            route_version="v1",
            status=ExecutionStatus.SUCCESS,
        )
        _run(engine.save_result(result))
        assert req.request_id not in engine.pending_requests


# ===========================================================================
# lifecycle/manager (lines 47, 72, 123, 129-134, 138)
# ===========================================================================

from safe_core.lifecycle.manager import RouteLifecycleManager
from safe_core.governance.models import RouteLifecycleState


class TestLifecycleManagerGaps:
    def test_transition_state_missing_key_returns_false(self):
        """Line 47: key not in routes → False."""
        mgr = RouteLifecycleManager()
        result = _run(
            mgr.transition_state("nonexistent", "v1", RouteLifecycleState.DEPLOYED)
        )
        assert result is False

    def test_transition_to_archived_sets_retired_at(self):
        """Line 72: ARCHIVED state → retired_at set."""
        mgr = RouteLifecycleManager()
        _run(mgr.create_route_entry("r", "v1"))
        _run(mgr.transition_state("r", "v1", RouteLifecycleState.PENDING_APPROVAL))
        _run(mgr.transition_state("r", "v1", RouteLifecycleState.APPROVED))
        _run(mgr.transition_state("r", "v1", RouteLifecycleState.DEPLOYED))
        _run(mgr.transition_state("r", "v1", RouteLifecycleState.ACTIVE))
        _run(mgr.transition_state("r", "v1", RouteLifecycleState.ARCHIVED))
        assert mgr.routes["r:v1"]["retired_at"] is not None

    def test_transition_to_disabled_sets_retired_at(self):
        """Line 72: DISABLED state → retired_at set."""
        mgr = RouteLifecycleManager()
        _run(mgr.create_route_entry("r", "v1"))
        _run(mgr.transition_state("r", "v1", RouteLifecycleState.PENDING_APPROVAL))
        _run(mgr.transition_state("r", "v1", RouteLifecycleState.APPROVED))
        _run(mgr.transition_state("r", "v1", RouteLifecycleState.DISABLED))
        assert mgr.routes["r:v1"]["retired_at"] is not None

    def test_get_route_state_missing_returns_none(self):
        """Line 123: key not in routes → None."""
        mgr = RouteLifecycleManager()
        result = _run(mgr.get_route_state("nonexistent", "v1"))
        assert result is None

    def test_get_route_history_returns_list(self):
        """Lines 129-134: existing route → state_history list returned."""
        mgr = RouteLifecycleManager()
        _run(mgr.create_route_entry("r", "v1"))
        history = _run(mgr.get_route_history("r", "v1"))
        assert isinstance(history, list)
        assert len(history) >= 1

    def test_get_route_history_missing_returns_none(self):
        """Line 129: key not found → None."""
        mgr = RouteLifecycleManager()
        result = _run(mgr.get_route_history("nonexistent", "v1"))
        assert result is None

    def test_list_routes_by_state(self):
        """Line 138: list routes matching the given state."""
        mgr = RouteLifecycleManager()
        _run(mgr.create_route_entry("r", "v1"))
        routes = _run(mgr.list_routes_by_state(RouteLifecycleState.DRAFT))
        assert "r:v1" in routes


# ===========================================================================
# models — Pydantic name validator (lines 181-183, 205-207)
# ===========================================================================

import pytest
from pydantic import ValidationError as PydanticValidationError


class TestPydanticModelsValidation:
    def test_static_route_definition_invalid_name(self):
        """Line 182: name with special chars → ValidationError (raises branch)."""
        from safe_core.models import StaticRouteDefinition, AgentConfig

        with pytest.raises(PydanticValidationError):
            StaticRouteDefinition(
                name="invalid name!",
                pattern="sequential",
                agents=[AgentConfig(name="a")],
            )

    def test_static_route_definition_valid_name(self):
        """Line 183: valid name → return v.lower()."""
        from safe_core.models import StaticRouteDefinition, AgentConfig

        r = StaticRouteDefinition(
            name="My-Route",
            pattern="sequential",
            agents=[AgentConfig(name="a")],
        )
        assert r.name == "my-route"

    def test_dynamic_route_definition_invalid_name(self):
        """Line 206: DynamicRouteDefinition invalid name → ValidationError."""
        from safe_core.models import DynamicRouteDefinition, ConditionalRoute

        with pytest.raises(PydanticValidationError):
            DynamicRouteDefinition(
                name="bad name!",
                decision_inputs=["field"],
                routes=[ConditionalRoute(condition="x > 0", agents=["a"])],
            )

    def test_dynamic_route_definition_valid_name(self):
        """Line 207: DynamicRouteDefinition valid name → return v.lower()."""
        from safe_core.models import DynamicRouteDefinition, ConditionalRoute

        d = DynamicRouteDefinition(
            name="My-Route",
            decision_inputs=["field"],
            routes=[ConditionalRoute(condition="x > 0", agents=["a"])],
        )
        assert d.name == "my-route"


# ===========================================================================
# performance/benchmark (lines 21-22, 32)
# ===========================================================================

from safe_core.performance.benchmark import PerformanceBenchmark


class TestPerformanceBenchmarkGaps:
    def test_measure_failing_callable_still_returns_elapsed(self):
        """Lines 21-22: callable raises → result=None, elapsed still tracked."""
        bench = PerformanceBenchmark()

        def boom():
            raise ValueError("oops")

        elapsed = _run(bench.measure("test", boom))
        assert isinstance(elapsed, float)
        assert elapsed >= 0

    def test_get_stats_empty_returns_empty_dict(self):
        """Line 32: unknown name → empty dict."""
        bench = PerformanceBenchmark()
        result = _run(bench.get_stats("never-measured"))
        assert result == {}


# ===========================================================================
# release/manager (lines 30-33)
# ===========================================================================

from safe_core.release.manager import ReleaseManager, ReleaseStatus


class TestReleaseManagerGaps:
    def test_transition_to_deployed_found(self):
        """Lines 30-32: version found → status DEPLOYED → True."""
        mgr = ReleaseManager()
        _run(mgr.create_release("1.0.0", ["comp-a"]))
        result = _run(mgr.transition_to_deployed("1.0.0"))
        assert result is True
        assert mgr.releases["1.0.0"].status == ReleaseStatus.DEPLOYED

    def test_transition_to_deployed_not_found(self):
        """Line 33: version not found → False."""
        mgr = ReleaseManager()
        result = _run(mgr.transition_to_deployed("9.9.9"))
        assert result is False


# ===========================================================================
# results/tracker (line 25)
# ===========================================================================

from safe_core.results.tracker import ResultTracker


class TestResultTrackerGaps:
    def test_get_route_stats_no_history_returns_none(self):
        """Line 25: no history for route → None."""
        tracker = ResultTracker()
        result = _run(tracker.get_route_stats("unknown-route", "v1"))
        assert result is None


# ===========================================================================
# security/validator (lines 25-26)
# ===========================================================================

from safe_core.security.validator import SecurityValidator


class TestSecurityValidatorGaps:
    def test_check_authentication_returns_true(self):
        """Lines 25-26: check_authentication records and returns True."""
        v = SecurityValidator()
        result = _run(v.check_authentication("my-component"))
        assert result is True
        assert v.checks_performed.get("my-component_authentication") is True


# ===========================================================================
# validator.py — missing pattern-specific agent checks (lines 219, 242, 320, 327)
# ===========================================================================

from safe_core.validator import ContractValidator
from safe_core.models import RouteDefinition, RoutePattern, Agent, ValidationError


def _agent(name: str, category: str = "generic", *, inp=None, out=None) -> Agent:
    return Agent(
        name=name,
        category=category,
        version="1.0",
        description="",
        input_schema=inp or {"properties": {}},
        output_schema=out or {"properties": {}},
    )


def _route(pattern: RoutePattern, agents: dict) -> RouteDefinition:
    return RouteDefinition(
        name="r",
        pattern=pattern,
        agents=agents,
        description="",
        timeout_seconds=120,
        per_agent_timeout_seconds=60,
        csa_email="",
        routing_field=None,
        routing_rules={},
    )


class TestValidatorBranchGaps:
    def test_mixture_of_experts_missing_aggregator(self):
        """Line 219: no aggregator in mixture-of-experts → error."""
        route = _route(
            RoutePattern.MIXTURE_OF_EXPERTS,
            {
                "router": _agent("router"),
                "expert_0": _agent("exp0"),
                "expert_1": _agent("exp1"),
                # no aggregator
            },
        )
        errors = ContractValidator.validate_route(route)
        error_messages = [e.message for e in errors]
        assert any("aggregator" in m for m in error_messages)

    def test_hierarchical_teams_too_few_teams(self):
        """Line 242: only one team_* agent in hierarchical-teams → error."""
        route = _route(
            RoutePattern.HIERARCHICAL_TEAMS,
            {
                "coordinator": _agent("coord"),
                "team_0": _agent("t0"),  # only 1, need >= 2
                "aggregator": _agent(
                    "agg",
                    inp={"properties": {"team_results": {}}},
                ),
            },
        )
        errors = ContractValidator.validate_route(route)
        error_messages = [e.message for e in errors]
        assert any("2 team_" in m for m in error_messages)

    def test_diamond_missing_left_processor(self):
        """Line 320: diamond without left_processor → error."""
        route = _route(
            RoutePattern.DIAMOND,
            {
                "splitter": _agent(
                    "spl",
                    out={"properties": {"left": {}, "right": {}}},
                ),
                "right_processor": _agent("rp"),
                # no left_processor
                "merger": _agent(
                    "mgr",
                    inp={"properties": {"left_result": {}, "right_result": {}}},
                ),
            },
        )
        errors = ContractValidator.validate_route(route)
        error_messages = [e.message for e in errors]
        assert any("left_processor" in m for m in error_messages)

    def test_diamond_missing_merger(self):
        """Line 327: diamond without merger → error."""
        route = _route(
            RoutePattern.DIAMOND,
            {
                "splitter": _agent(
                    "spl",
                    out={"properties": {"left": {}, "right": {}}},
                ),
                "left_processor": _agent("lp"),
                "right_processor": _agent("rp"),
                # no merger
            },
        )
        errors = ContractValidator.validate_route(route)
        error_messages = [e.message for e in errors]
        assert any("merger" in m for m in error_messages)
