"""Tests for HandoffInterviewer — mocked input and all five handoff patterns."""
import asyncio
import pytest
from unittest.mock import patch

from safe_core.handoff_interview import (
    HandoffInterviewer,
    _safe_input,
    _HandoffCancelledError,
)
from safe_core.handoff_models import HandoffDefinition, HandoffPattern, SubAgent


PATCH_INPUT = "builtins.input"


def run(coro):
    return asyncio.run(coro)


def _iv():
    return HandoffInterviewer()


# ---------------------------------------------------------------------------
# _safe_input helper
# ---------------------------------------------------------------------------

class TestSafeInput:
    def test_returns_stripped_value(self):
        with patch(PATCH_INPUT, return_value="  hello  "):
            assert _safe_input("> ") == "hello"

    def test_raises_on_q(self):
        with patch(PATCH_INPUT, return_value="q"):
            with pytest.raises(_HandoffCancelledError):
                _safe_input("> ")

    def test_raises_on_quit(self):
        with patch(PATCH_INPUT, return_value="quit"):
            with pytest.raises(_HandoffCancelledError):
                _safe_input("> ")

    def test_raises_on_Q_uppercase(self):
        with patch(PATCH_INPUT, return_value="Q"):
            with pytest.raises(_HandoffCancelledError):
                _safe_input("> ")


# ---------------------------------------------------------------------------
# _ask_int helper
# ---------------------------------------------------------------------------

class TestAskInt:
    def test_valid_number_accepted(self):
        iv = _iv()
        with patch(PATCH_INPUT, return_value="3"):
            result = iv._ask_int("Enter [2-4]: ", 2, 4)
        assert result == 3

    def test_out_of_range_then_valid(self):
        iv = _iv()
        responses = iter(["1", "5", "2"])
        with patch(PATCH_INPUT, side_effect=lambda _: next(responses)):
            result = iv._ask_int("Enter [2-4]: ", 2, 4)
        assert result == 2

    def test_non_digit_then_valid(self):
        iv = _iv()
        responses = iter(["abc", "3"])
        with patch(PATCH_INPUT, side_effect=lambda _: next(responses)):
            result = iv._ask_int("Enter [2-4]: ", 2, 4)
        assert result == 3


# ---------------------------------------------------------------------------
# _ask_pattern
# ---------------------------------------------------------------------------

class TestAskPattern:
    def test_selects_direct_pattern(self):
        iv = _iv()
        with patch(PATCH_INPUT, return_value="1"):
            assert iv._ask_pattern() == HandoffPattern.DIRECT

    def test_selects_selective_pattern(self):
        iv = _iv()
        with patch(PATCH_INPUT, return_value="2"):
            assert iv._ask_pattern() == HandoffPattern.SELECTIVE

    def test_selects_sequential_pattern(self):
        iv = _iv()
        with patch(PATCH_INPUT, return_value="3"):
            assert iv._ask_pattern() == HandoffPattern.SEQUENTIAL

    def test_selects_hierarchical_pattern(self):
        iv = _iv()
        with patch(PATCH_INPUT, return_value="4"):
            assert iv._ask_pattern() == HandoffPattern.HIERARCHICAL

    def test_selects_recursive_pattern(self):
        iv = _iv()
        with patch(PATCH_INPUT, return_value="5"):
            assert iv._ask_pattern() == HandoffPattern.RECURSIVE

    def test_invalid_choice_then_valid(self):
        iv = _iv()
        responses = iter(["9", "0", "3"])
        with patch(PATCH_INPUT, side_effect=lambda _: next(responses)):
            assert iv._ask_pattern() == HandoffPattern.SEQUENTIAL

    def test_q_during_pattern_cancels(self):
        iv = _iv()
        with patch(PATCH_INPUT, return_value="q"):
            with pytest.raises(_HandoffCancelledError):
                iv._ask_pattern()


# ---------------------------------------------------------------------------
# _ask_metadata
# ---------------------------------------------------------------------------

class TestAskMetadata:
    def test_valid_name_returns_tuple(self):
        iv = _iv()
        responses = iter(["my-handoff", "A description", "csa@example.com"])
        with patch(PATCH_INPUT, side_effect=lambda _: next(responses)):
            name, description, email = iv._ask_metadata()
        assert name == "my-handoff"
        assert description == "A description"
        assert email == "csa@example.com"

    def test_invalid_name_then_valid(self):
        iv = _iv()
        responses = iter(["INVALID NAME!", "valid-name", "desc", ""])
        with patch(PATCH_INPUT, side_effect=lambda _: next(responses)):
            name, _, _ = iv._ask_metadata()
        assert name == "valid-name"

    def test_empty_email_is_allowed(self):
        iv = _iv()
        responses = iter(["my-handoff", "desc", ""])
        with patch(PATCH_INPUT, side_effect=lambda _: next(responses)):
            _, _, email = iv._ask_metadata()
        assert email == ""


# ---------------------------------------------------------------------------
# _ask_sub_agents — all five patterns
# Note: for SELECTIVE the code collects coordinator BEFORE the candidate count;
#       for HIERARCHICAL it collects manager BEFORE the worker count.
# ---------------------------------------------------------------------------

class TestAskSubAgentsDirect:
    def test_direct_returns_delegate_key(self):
        iv = _iv()
        responses = iter(["Specialist", "Handles escalations", ""])
        with patch(PATCH_INPUT, side_effect=lambda _: next(responses)):
            sub_agents = iv._ask_sub_agents(HandoffPattern.DIRECT)
        assert "delegate" in sub_agents
        assert sub_agents["delegate"].name == "Specialist"


class TestAskSubAgentsSelective:
    def test_selective_returns_coordinator_and_candidates(self):
        iv = _iv()
        # coordinator (name, desc, tags) → count → each candidate (name, desc, tags)
        responses = iter([
            "Coord", "coordinates routing", "",    # coordinator
            "2",                                   # number of candidates
            "BillingAgent", "handles billing", "billing",   # candidate_0
            "TechAgent", "handles tech", "tech",            # candidate_1
        ])
        with patch(PATCH_INPUT, side_effect=lambda _: next(responses)):
            sub_agents = iv._ask_sub_agents(HandoffPattern.SELECTIVE)
        assert "coordinator" in sub_agents
        assert "candidate_0" in sub_agents
        assert "candidate_1" in sub_agents

    def test_capability_tags_parsed(self):
        iv = _iv()
        responses = iter([
            "Coord", "coord desc", "",
            "2",
            "Agent0", "desc0", "tag1, tag2",
            "Agent1", "desc1", "",
        ])
        with patch(PATCH_INPUT, side_effect=lambda _: next(responses)):
            sub_agents = iv._ask_sub_agents(HandoffPattern.SELECTIVE)
        assert sub_agents["candidate_0"].capability_tags == ["tag1", "tag2"]


class TestAskSubAgentsSequential:
    def test_sequential_returns_stage_keys(self):
        iv = _iv()
        responses = iter([
            "2",               # 2 stages
            "Stage0", "first stage", "",
            "Stage1", "second stage", "",
        ])
        with patch(PATCH_INPUT, side_effect=lambda _: next(responses)):
            sub_agents = iv._ask_sub_agents(HandoffPattern.SEQUENTIAL)
        assert "stage_0" in sub_agents
        assert "stage_1" in sub_agents


class TestAskSubAgentsHierarchical:
    def test_hierarchical_returns_manager_and_workers(self):
        iv = _iv()
        # manager (name, desc, tags) → worker count → each worker (name, desc, tags)
        responses = iter([
            "Manager", "manages workers", "",
            "2",               # 2 workers
            "Worker0", "does work", "",
            "Worker1", "also does work", "",
        ])
        with patch(PATCH_INPUT, side_effect=lambda _: next(responses)):
            sub_agents = iv._ask_sub_agents(HandoffPattern.HIERARCHICAL)
        assert "manager" in sub_agents
        assert "worker_0" in sub_agents
        assert "worker_1" in sub_agents


class TestAskSubAgentsRecursive:
    def test_recursive_returns_agent_key(self):
        iv = _iv()
        responses = iter(["RecursiveAgent", "spawns sub-agents", ""])
        with patch(PATCH_INPUT, side_effect=lambda _: next(responses)):
            sub_agents = iv._ask_sub_agents(HandoffPattern.RECURSIVE)
        assert "agent" in sub_agents
        assert sub_agents["agent"].name == "RecursiveAgent"


# ---------------------------------------------------------------------------
# _ask_options
# ---------------------------------------------------------------------------

class TestAskOptions:
    def test_default_values_when_empty_input(self):
        iv = _iv()
        responses = iter(["", "", ""])
        with patch(PATCH_INPUT, side_effect=lambda _: next(responses)):
            depth, policy, timeout = iv._ask_options(HandoffPattern.DIRECT)
        assert depth == 1
        assert policy == "always"
        assert timeout == 120

    def test_hierarchical_default_depth_is_3(self):
        iv = _iv()
        responses = iter(["", "1", ""])
        with patch(PATCH_INPUT, side_effect=lambda _: next(responses)):
            depth, _, _ = iv._ask_options(HandoffPattern.HIERARCHICAL)
        assert depth == 3

    def test_recursive_default_depth_is_3(self):
        iv = _iv()
        responses = iter(["", "1", ""])
        with patch(PATCH_INPUT, side_effect=lambda _: next(responses)):
            depth, _, _ = iv._ask_options(HandoffPattern.RECURSIVE)
        assert depth == 3

    def test_explicit_depth_and_timeout(self):
        iv = _iv()
        responses = iter(["5", "2", "300"])
        with patch(PATCH_INPUT, side_effect=lambda _: next(responses)):
            depth, policy, timeout = iv._ask_options(HandoffPattern.SEQUENTIAL)
        assert depth == 5
        assert policy == "on_partial"
        assert timeout == 300

    def test_on_failure_policy(self):
        iv = _iv()
        responses = iter(["", "3", ""])
        with patch(PATCH_INPUT, side_effect=lambda _: next(responses)):
            _, policy, _ = iv._ask_options(HandoffPattern.DIRECT)
        assert policy == "on_failure"

    def test_unknown_policy_choice_defaults_to_always(self):
        iv = _iv()
        responses = iter(["", "9", ""])
        with patch(PATCH_INPUT, side_effect=lambda _: next(responses)):
            _, policy, _ = iv._ask_options(HandoffPattern.DIRECT)
        assert policy == "always"

    def test_non_digit_depth_uses_default(self):
        iv = _iv()
        responses = iter(["not-a-number", "1", ""])
        with patch(PATCH_INPUT, side_effect=lambda _: next(responses)):
            depth, _, _ = iv._ask_options(HandoffPattern.DIRECT)
        assert depth == 1


# ---------------------------------------------------------------------------
# _review_and_confirm
# ---------------------------------------------------------------------------

class TestReviewAndConfirm:
    def _make_handoff(self):
        return HandoffDefinition(
            name="review-test",
            pattern=HandoffPattern.DIRECT,
            sub_agents={"delegate": SubAgent(name="Agent", description="does stuff")},
            description="Test handoff",
        )

    def test_y_confirms(self):
        iv = _iv()
        with patch(PATCH_INPUT, return_value="y"):
            assert iv._review_and_confirm(self._make_handoff()) is True

    def test_empty_confirms(self):
        iv = _iv()
        with patch(PATCH_INPUT, return_value=""):
            assert iv._review_and_confirm(self._make_handoff()) is True

    def test_yes_confirms(self):
        iv = _iv()
        with patch(PATCH_INPUT, return_value="yes"):
            assert iv._review_and_confirm(self._make_handoff()) is True

    def test_n_declines(self):
        iv = _iv()
        with patch(PATCH_INPUT, return_value="n"):
            assert iv._review_and_confirm(self._make_handoff()) is False

    def test_q_raises_cancel(self):
        iv = _iv()
        with patch(PATCH_INPUT, return_value="q"):
            with pytest.raises(_HandoffCancelledError):
                iv._review_and_confirm(self._make_handoff())


# ---------------------------------------------------------------------------
# Full start_interview flows
# ---------------------------------------------------------------------------

def _direct_inputs(name="my-direct", confirm="y"):
    """Input sequence for a complete DIRECT handoff interview."""
    return [
        "1",                  # pattern: DIRECT
        name,                 # handoff name
        "A test handoff",     # description
        "",                   # csa email (skip)
        "Specialist",         # delegate display name
        "Handles escalations", # delegate description
        "",                   # capability tags (none)
        "",                   # max depth (default)
        "1",                  # return policy: always
        "",                   # timeout (default)
        confirm,              # confirm
    ]


class TestStartInterviewDirect:
    def test_returns_handoff_definition(self):
        responses = iter(_direct_inputs())
        with patch(PATCH_INPUT, side_effect=lambda _: next(responses)):
            result = run(_iv().start_interview())
        assert isinstance(result, HandoffDefinition)
        assert result.name == "my-direct"
        assert result.pattern == HandoffPattern.DIRECT
        assert "delegate" in result.sub_agents

    def test_decline_at_review_returns_none(self):
        responses = iter(_direct_inputs(confirm="n"))
        with patch(PATCH_INPUT, side_effect=lambda _: next(responses)):
            result = run(_iv().start_interview())
        assert result is None

    def test_cancel_at_pattern_returns_none(self):
        with patch(PATCH_INPUT, return_value="q"):
            result = run(_iv().start_interview())
        assert result is None

    def test_cancel_mid_interview_returns_none(self):
        responses = iter([
            "1",   # pattern: DIRECT
            "q",   # cancel at name prompt
        ])
        with patch(PATCH_INPUT, side_effect=lambda _: next(responses)):
            result = run(_iv().start_interview())
        assert result is None


class TestStartInterviewSelective:
    def test_selective_interview_returns_correct_pattern(self):
        responses = iter([
            "2",              # pattern: SELECTIVE
            "sel-handoff",    # name
            "Selective test", # description
            "",               # email
            # sub-agents: coordinator first, then count, then candidates
            "Coord", "coord", "",
            "2",
            "Cand0", "c0", "",
            "Cand1", "c1", "",
            "", "1", "",      # depth, policy, timeout
            "y",              # confirm
        ])
        with patch(PATCH_INPUT, side_effect=lambda _: next(responses)):
            result = run(_iv().start_interview())
        assert result is not None
        assert result.pattern == HandoffPattern.SELECTIVE
        assert "coordinator" in result.sub_agents
        assert "candidate_0" in result.sub_agents


class TestStartInterviewSequential:
    def test_sequential_interview_produces_stage_agents(self):
        responses = iter([
            "3",           # pattern: SEQUENTIAL
            "seq-handoff", "Seq test", "",
            "2",           # 2 stages
            "StageA", "stage a", "",
            "StageB", "stage b", "",
            "", "1", "",
            "y",
        ])
        with patch(PATCH_INPUT, side_effect=lambda _: next(responses)):
            result = run(_iv().start_interview())
        assert result is not None
        assert result.pattern == HandoffPattern.SEQUENTIAL
        assert "stage_0" in result.sub_agents
        assert "stage_1" in result.sub_agents


class TestStartInterviewHierarchical:
    def test_hierarchical_interview_produces_manager_and_workers(self):
        responses = iter([
            "4",               # pattern: HIERARCHICAL
            "hier-handoff", "Hier test", "",
            # sub-agents: manager first, then worker count, then workers
            "Mgr", "manages", "",
            "1",               # 1 worker
            "Wkr0", "works", "",
            "3", "1", "",      # depth=3, policy=always, timeout=default
            "y",
        ])
        with patch(PATCH_INPUT, side_effect=lambda _: next(responses)):
            result = run(_iv().start_interview())
        assert result is not None
        assert result.pattern == HandoffPattern.HIERARCHICAL
        assert "manager" in result.sub_agents
        assert "worker_0" in result.sub_agents
        assert result.max_depth == 3


class TestStartInterviewRecursive:
    def test_recursive_interview_produces_agent_key(self):
        responses = iter([
            "5",               # pattern: RECURSIVE
            "rec-handoff", "Recursive test", "",
            "RecAgent", "spawns more agents", "",
            "", "1", "",
            "y",
        ])
        with patch(PATCH_INPUT, side_effect=lambda _: next(responses)):
            result = run(_iv().start_interview())
        assert result is not None
        assert result.pattern == HandoffPattern.RECURSIVE
        assert "agent" in result.sub_agents
