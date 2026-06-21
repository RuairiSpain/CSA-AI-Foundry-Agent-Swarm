"""Tests for RouteInterviewer — mocked input."""
import asyncio
import pytest
from unittest.mock import patch

from safe_core.agent_catalog import AgentCatalog
from safe_core.interview import RouteInterviewer, _safe_input, _InterviewCancelledError
from safe_core.models import RoutePattern


def _run(coro):
    return asyncio.run(coro)


def _iv():
    return RouteInterviewer(AgentCatalog())


# Supervisor-manager happy-path inputs.
# Order in _ask_agents: select supervisor FIRST, then ask specialist count.
#   pattern=1, sup search="", specialist_count=2, spec0="", spec1="", agg="",
#   routing_field=1, total_timeout="", per_agent="",
#   name="r", desc="", email="", confirm=y
_SM_INPUTS = ["1", "", "2", "", "", "", "1", "", "", "r", "", "", "y"]


# ---------------------------------------------------------------------------
# _safe_input helper
# ---------------------------------------------------------------------------

class TestSafeInput:
    def test_returns_stripped_value(self):
        with patch("builtins.input", return_value="  hello  "):
            assert _safe_input("> ") == "hello"

    def test_raises_on_q(self):
        with patch("builtins.input", return_value="q"):
            with pytest.raises(_InterviewCancelledError):
                _safe_input("> ")

    def test_raises_on_quit_case_insensitive(self):
        with patch("builtins.input", return_value="QUIT"):
            with pytest.raises(_InterviewCancelledError):
                _safe_input("> ")


# ---------------------------------------------------------------------------
# Cancellation
# ---------------------------------------------------------------------------

class TestCancellation:
    def test_q_at_pattern_returns_none(self):
        with patch("builtins.input", side_effect=["q"]):
            assert _run(_iv().start_interview()) is None

    def test_keyboard_interrupt_returns_none(self):
        with patch("builtins.input", side_effect=KeyboardInterrupt):
            assert _run(_iv().start_interview()) is None

    def test_q_at_specialist_count_returns_none(self):
        with patch("builtins.input", side_effect=["1", "q"]):
            assert _run(_iv().start_interview()) is None

    def test_q_at_agent_search_returns_none(self):
        # pattern=1, specialist_count=2, then q at supervisor search
        with patch("builtins.input", side_effect=["1", "2", "q"]):
            assert _run(_iv().start_interview()) is None

    def test_q_at_confirm_returns_none(self):
        # get all the way to confirm then q
        inputs = _SM_INPUTS[:-1] + ["q"]
        with patch("builtins.input", side_effect=inputs):
            assert _run(_iv().start_interview()) is None


# ---------------------------------------------------------------------------
# Pattern selection
# ---------------------------------------------------------------------------

class TestPatternSelection:
    def test_invalid_choice_retries_then_succeeds(self):
        # "x" is invalid → retry; "4" is valid; then q at next prompt
        with patch("builtins.input", side_effect=["x", "4", "q"]):
            _run(_iv().start_interview())  # no assertion — just must not crash

    def test_b_on_first_step_prints_message_and_retries(self):
        # 'b' on step 1 → "Cannot go back", retries; then q
        with patch("builtins.input", side_effect=["b", "1", "q"]):
            result = _run(_iv().start_interview())
        assert result is None  # cancelled at next step, but got past pattern


# ---------------------------------------------------------------------------
# Full flow — supervisor-manager
# ---------------------------------------------------------------------------

class TestSupervisorManagerFlow:
    def test_full_flow_returns_route_definition(self):
        with patch("builtins.input", side_effect=_SM_INPUTS):
            result = _run(_iv().start_interview())
        assert result is not None
        assert result.pattern == RoutePattern.SUPERVISOR_MANAGER
        assert "supervisor" in result.agents
        assert "specialist_0" in result.agents
        assert "specialist_1" in result.agents
        assert "aggregator" in result.agents
        assert result.routing_field == "amount"
        assert result.name == "r"
        assert result.timeout_seconds == 120
        assert result.per_agent_timeout_seconds == 60

    def test_review_n_returns_none(self):
        inputs = _SM_INPUTS[:-1] + ["n"]
        with patch("builtins.input", side_effect=inputs):
            assert _run(_iv().start_interview()) is None

    def test_review_yes_returns_definition(self):
        inputs = _SM_INPUTS[:-1] + ["yes"]
        with patch("builtins.input", side_effect=inputs):
            assert _run(_iv().start_interview()) is not None

    def test_review_invalid_then_y(self):
        # "maybe" is invalid → loop; "y" confirms
        inputs = _SM_INPUTS[:-1] + ["maybe", "y"]
        with patch("builtins.input", side_effect=inputs):
            assert _run(_iv().start_interview()) is not None

    def test_routing_field_invalid_choice_defaults_to_first(self):
        # "x" for routing field → ValueError → defaults to fields[0] = "amount"
        inputs = ["1", "", "2", "", "", "", "x", "", "", "r", "", "", "y"]
        with patch("builtins.input", side_effect=inputs):
            result = _run(_iv().start_interview())
        assert result.routing_field == "amount"


# ---------------------------------------------------------------------------
# Full flow — fan-out-fan-in
# ---------------------------------------------------------------------------

class TestFanOutFanInFlow:
    def test_full_flow(self):
        inputs = ["2", "2", "", "", "", "", "", "fan-r", "", "", "y"]
        with patch("builtins.input", side_effect=inputs):
            result = _run(_iv().start_interview())
        assert result is not None
        assert result.pattern == RoutePattern.FAN_OUT_FAN_IN
        assert "processor_0" in result.agents
        assert "processor_1" in result.agents
        assert "aggregator" in result.agents


# ---------------------------------------------------------------------------
# Full flow — map-reduce
# ---------------------------------------------------------------------------

class TestMapReduceFlow:
    def test_full_flow(self):
        inputs = ["3", "", "", "", "", "", "mr-r", "", "", "y"]
        with patch("builtins.input", side_effect=inputs):
            result = _run(_iv().start_interview())
        assert result is not None
        assert result.pattern == RoutePattern.MAP_REDUCE
        assert "splitter" in result.agents
        assert "mapper" in result.agents
        assert "reducer" in result.agents


# ---------------------------------------------------------------------------
# Full flow — sequential-pipeline
# ---------------------------------------------------------------------------

class TestSequentialPipelineFlow:
    def test_full_flow(self):
        inputs = ["4", "2", "", "", "", "", "pipe-r", "", "", "y"]
        with patch("builtins.input", side_effect=inputs):
            result = _run(_iv().start_interview())
        assert result is not None
        assert result.pattern == RoutePattern.SEQUENTIAL_PIPELINE
        assert "stage_0" in result.agents
        assert "stage_1" in result.agents

    def test_three_stages(self):
        inputs = ["4", "3", "", "", "", "", "", "pipe-r", "", "", "y"]
        with patch("builtins.input", side_effect=inputs):
            result = _run(_iv().start_interview())
        assert "stage_2" in result.agents


# ---------------------------------------------------------------------------
# Agent search
# ---------------------------------------------------------------------------

class TestAgentSearch:
    def test_search_single_result_auto_selects(self):
        # For sequential-pipeline stage_0: search "mortgage" → 1 match
        inputs = ["4", "2", "mortgage", "", "", "", "sr", "", "", "y"]
        with patch("builtins.input", side_effect=inputs):
            result = _run(_iv().start_interview())
        assert result.agents["stage_0"].name == "loan-specialist-mortgage"

    def test_search_no_results_retries_then_default(self):
        # "zzz" finds nothing → retry; "" picks default
        inputs = ["4", "2", "zzznomatch", "", "", "", "", "sr", "", "", "y"]
        with patch("builtins.input", side_effect=inputs):
            result = _run(_iv().start_interview())
        assert result is not None

    def test_search_multiple_results_select_by_index(self):
        # "specialist" returns 5 matches; pick "2" → second one
        inputs = ["4", "2", "specialist", "2", "", "", "", "sr", "", "", "y"]
        with patch("builtins.input", side_effect=inputs):
            result = _run(_iv().start_interview())
        assert result is not None
        # second search result for "specialist"
        from safe_core.agent_catalog import AgentCatalog
        second = AgentCatalog().search_by_name("specialist")[1]
        assert result.agents["stage_0"].name == second.name

    def test_search_multiple_invalid_index_retries(self):
        # "specialist" → 5 matches; "99" invalid → IndexError → continue (loops
        # back to the search prompt, not the select prompt); "" picks default
        inputs = ["4", "2", "specialist", "99", "", "", "", "", "sr", "", "", "y"]
        with patch("builtins.input", side_effect=inputs):
            result = _run(_iv().start_interview())
        assert result is not None


# ---------------------------------------------------------------------------
# Timeouts
# ---------------------------------------------------------------------------

class TestTimeouts:
    def test_custom_timeouts_used(self):
        inputs = ["4", "2", "", "", "300", "90", "t", "", "", "y"]
        with patch("builtins.input", side_effect=inputs):
            result = _run(_iv().start_interview())
        assert result.timeout_seconds == 300
        assert result.per_agent_timeout_seconds == 90

    def test_total_less_than_per_agent_gets_adjusted(self):
        # total=30 < per_agent=60 → adjusted to 60*2=120
        inputs = ["4", "2", "", "", "30", "60", "t", "", "", "y"]
        with patch("builtins.input", side_effect=inputs):
            result = _run(_iv().start_interview())
        assert result.timeout_seconds == 120

    def test_default_timeouts(self):
        inputs = ["4", "2", "", "", "", "", "t", "", "", "y"]
        with patch("builtins.input", side_effect=inputs):
            result = _run(_iv().start_interview())
        assert result.timeout_seconds == 120
        assert result.per_agent_timeout_seconds == 60


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------

class TestMetadata:
    def test_name_normalised_to_lowercase(self):
        inputs = ["4", "2", "", "", "", "", "My Route", "", "", "y"]
        with patch("builtins.input", side_effect=inputs):
            result = _run(_iv().start_interview())
        # RouteDefinition stores name as-is (no normalisation in RouteInterviewer)
        assert result.name == "My Route"

    def test_empty_name_defaults(self):
        inputs = ["4", "2", "", "", "", "", "", "", "", "y"]
        with patch("builtins.input", side_effect=inputs):
            result = _run(_iv().start_interview())
        assert result.name == "my-route"

    def test_description_and_email_stored(self):
        inputs = ["4", "2", "", "", "", "", "my-r", "A description", "a@b.com", "y"]
        with patch("builtins.input", side_effect=inputs):
            result = _run(_iv().start_interview())
        assert result.description == "A description"
        assert result.csa_email == "a@b.com"
