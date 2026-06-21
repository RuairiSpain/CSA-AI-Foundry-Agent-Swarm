"""Tests for ChainInterviewer — mocked input and route discovery."""
import asyncio
import pytest
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock

from safe_core.chain_interview import ChainInterviewer, _safe_input, _ChainCancelledError
from safe_core.chain_models import RouteChain, RouteChainStep


PATCH_INPUT = "builtins.input"
PATCH_LIST = "safe_core.chain_interview._list_routes"
PATCH_EXTRACT = "safe_core.chain_interview._extract_fields"

FAKE_ROUTES = [
    {"name": "route-a", "pattern": "sequential-pipeline"},
    {"name": "route-b", "pattern": "fan-out-fan-in"},
    {"name": "route-c", "pattern": "supervisor-manager"},
]


def _fake_extract(routes_dir, route_name, field_var):
    outputs = {"route-a": ["answer"], "route-b": ["result"], "route-c": ["summary"]}
    inputs = {"route-b": ["answer"], "route-c": ["result"]}
    if field_var == "required_output_fields":
        return outputs.get(route_name, [])
    return inputs.get(route_name, [])


def _fake_extract_unmatched(routes_dir, route_name, field_var):
    """route-b requires 'text', which is NOT in context_keys after route-a."""
    outputs = {"route-a": ["answer"], "route-b": ["result"]}
    inputs = {"route-b": ["text"]}
    if field_var == "required_output_fields":
        return outputs.get(route_name, [])
    return inputs.get(route_name, [])


def run(coro):
    return asyncio.run(coro)


def _iv(tmp_path):
    return ChainInterviewer(tmp_path / "routes")


# ---------------------------------------------------------------------------
# _safe_input helper
# ---------------------------------------------------------------------------

class TestSafeInput:
    def test_returns_stripped(self):
        with patch(PATCH_INPUT, return_value="  hi  "):
            assert _safe_input("> ") == "hi"

    def test_raises_on_q(self):
        with patch(PATCH_INPUT, return_value="q"):
            with pytest.raises(_ChainCancelledError):
                _safe_input("> ")

    def test_raises_on_quit_case_insensitive(self):
        with patch(PATCH_INPUT, return_value="QUIT"):
            with pytest.raises(_ChainCancelledError):
                _safe_input("> ")


# ---------------------------------------------------------------------------
# Cancellation
# ---------------------------------------------------------------------------

class TestCancellation:
    def test_q_at_chain_name_returns_none(self, tmp_path):
        with patch(PATCH_INPUT, side_effect=["q"]):
            assert run(_iv(tmp_path).start_interview()) is None

    def test_keyboard_interrupt_returns_none(self, tmp_path):
        with patch(PATCH_INPUT, side_effect=KeyboardInterrupt):
            assert run(_iv(tmp_path).start_interview()) is None

    def test_q_in_step_loop_returns_none(self, tmp_path):
        # get past metadata, then q at the step loop choice
        with patch(PATCH_INPUT, side_effect=["my-chain", "", "", "q"]), \
             patch(PATCH_LIST, return_value=FAKE_ROUTES), \
             patch(PATCH_EXTRACT, side_effect=_fake_extract):
            assert run(_iv(tmp_path).start_interview()) is None

    def test_q_at_review_returns_none(self, tmp_path):
        inputs = [
            "my-chain", "", "",
            "1", "1",       # add route-a (first step, no mapping)
            "1", "1", "",   # add route-b (auto-match answer, no condition)
            "d",            # done
            "h", "n",       # options
            "120",          # timeout
            "q",            # cancel at review
        ]
        with patch(PATCH_INPUT, side_effect=inputs), \
             patch(PATCH_LIST, return_value=FAKE_ROUTES), \
             patch(PATCH_EXTRACT, side_effect=_fake_extract):
            assert run(_iv(tmp_path).start_interview()) is None


# ---------------------------------------------------------------------------
# Full happy path
# ---------------------------------------------------------------------------

class TestFullHappyPath:
    def test_two_step_chain_returned(self, tmp_path):
        inputs = [
            "my-chain", "a chain", "a@b.com",  # metadata
            "1", "1",                           # add route-a (first step)
            "1", "1", "",                       # add route-b (auto-match, no condition)
            "d",                                # done
            "h", "n",                           # halt, no history
            "120",                              # timeout
            "y",                                # confirm
        ]
        with patch(PATCH_INPUT, side_effect=inputs), \
             patch(PATCH_LIST, return_value=FAKE_ROUTES), \
             patch(PATCH_EXTRACT, side_effect=_fake_extract):
            result = run(_iv(tmp_path).start_interview())

        assert result is not None
        assert result.name == "my-chain"
        assert result.description == "a chain"
        assert result.csa_email == "a@b.com"
        assert len(result.steps) == 2
        assert result.steps[0].route_name == "route-a"
        assert result.steps[1].route_name == "route-b"
        assert result.on_step_failure == "halt"
        assert result.include_chain_history is False
        assert result.timeout_seconds == 120

    def test_review_n_returns_none(self, tmp_path):
        inputs = [
            "my-chain", "", "",
            "1", "1",
            "1", "1", "",
            "d",
            "h", "n",
            "120",
            "n",
        ]
        with patch(PATCH_INPUT, side_effect=inputs), \
             patch(PATCH_LIST, return_value=FAKE_ROUTES), \
             patch(PATCH_EXTRACT, side_effect=_fake_extract):
            assert run(_iv(tmp_path).start_interview()) is None

    def test_skip_mode_and_history_enabled(self, tmp_path):
        inputs = [
            "x-chain", "", "",
            "1", "1",
            "1", "1", "",
            "d",
            "s",    # skip on failure
            "y",    # include history
            "60",
            "y",
        ]
        with patch(PATCH_INPUT, side_effect=inputs), \
             patch(PATCH_LIST, return_value=FAKE_ROUTES), \
             patch(PATCH_EXTRACT, side_effect=_fake_extract):
            result = run(_iv(tmp_path).start_interview())

        assert result.on_step_failure == "skip"
        assert result.include_chain_history is True

    def test_three_step_chain(self, tmp_path):
        inputs = [
            "c3", "", "",
            "1", "1",                   # route-a
            "1", "1", "",               # route-b (auto-match answer, no condition)
            "1", "1", "",               # route-c (auto-match result, no condition)
            "d",
            "h", "n",
            "180",
            "y",
        ]
        with patch(PATCH_INPUT, side_effect=inputs), \
             patch(PATCH_LIST, return_value=FAKE_ROUTES), \
             patch(PATCH_EXTRACT, side_effect=_fake_extract):
            result = run(_iv(tmp_path).start_interview())

        assert len(result.steps) == 3
        assert result.steps[2].route_name == "route-c"


# ---------------------------------------------------------------------------
# Step loop edge cases
# ---------------------------------------------------------------------------

class TestStepLoopEdgeCases:
    def test_done_before_two_steps_warns_and_retries(self, tmp_path):
        inputs = [
            "c", "", "",
            "1", "1",   # add route-a
            "d",        # try done — only 1 step, warns
            "1", "1", "",  # add route-b
            "d",
            "h", "n", "120", "y",
        ]
        with patch(PATCH_INPUT, side_effect=inputs), \
             patch(PATCH_LIST, return_value=FAKE_ROUTES), \
             patch(PATCH_EXTRACT, side_effect=_fake_extract):
            result = run(_iv(tmp_path).start_interview())

        assert len(result.steps) == 2

    def test_invalid_choice_ignored(self, tmp_path):
        inputs = [
            "c", "", "",
            "x",        # invalid choice
            "1", "1",   # add route-a
            "1", "1", "",
            "d",
            "h", "n", "120", "y",
        ]
        with patch(PATCH_INPUT, side_effect=inputs), \
             patch(PATCH_LIST, return_value=FAKE_ROUTES), \
             patch(PATCH_EXTRACT, side_effect=_fake_extract):
            result = run(_iv(tmp_path).start_interview())

        assert result is not None

    def test_b_removes_last_step(self, tmp_path):
        inputs = [
            "c", "", "",
            "1", "1",       # add route-a
            "1", "1", "",   # add route-b
            "b",            # remove route-b
            "1", "1", "",   # re-add route-b
            "d",
            "h", "n", "120", "y",
        ]
        with patch(PATCH_INPUT, side_effect=inputs), \
             patch(PATCH_LIST, return_value=FAKE_ROUTES), \
             patch(PATCH_EXTRACT, side_effect=_fake_extract):
            result = run(_iv(tmp_path).start_interview())

        assert len(result.steps) == 2
        assert result.steps[1].route_name == "route-b"

    def test_b_with_no_steps_is_safe(self, tmp_path):
        inputs = [
            "c", "", "",
            "b",        # remove when empty — should say "Nothing to remove"
            "1", "1",
            "1", "1", "",
            "d",
            "h", "n", "120", "y",
        ]
        with patch(PATCH_INPUT, side_effect=inputs), \
             patch(PATCH_LIST, return_value=FAKE_ROUTES), \
             patch(PATCH_EXTRACT, side_effect=_fake_extract):
            result = run(_iv(tmp_path).start_interview())

        assert result is not None


# ---------------------------------------------------------------------------
# No routes available
# ---------------------------------------------------------------------------

class TestNoRoutes:
    def test_no_routes_skips_and_loops(self, tmp_path):
        # _list_routes returns [] → "No routes found" message, returns (None, [])
        # Then add valid routes from a second _list_routes call
        call_count = [0]

        def dynamic_list(routes_dir):
            call_count[0] += 1
            return [] if call_count[0] == 1 else FAKE_ROUTES

        inputs = [
            "c", "", "",
            "1",        # try add existing → no routes, back to loop
            "1", "1",   # add route-a
            "1", "1", "",  # add route-b
            "d",
            "h", "n", "120", "y",
        ]
        with patch(PATCH_INPUT, side_effect=inputs), \
             patch(PATCH_LIST, side_effect=dynamic_list), \
             patch(PATCH_EXTRACT, side_effect=_fake_extract):
            result = run(_iv(tmp_path).start_interview())

        assert result is not None

    def test_invalid_route_selection_returns_none_step(self, tmp_path):
        # "99" is out of range → returns (None, []) → step not appended
        inputs = [
            "c", "", "",
            "1", "99",      # invalid index → skipped, back to loop
            "1", "1",       # add route-a
            "1", "1", "",   # add route-b
            "d",
            "h", "n", "120", "y",
        ]
        with patch(PATCH_INPUT, side_effect=inputs), \
             patch(PATCH_LIST, return_value=FAKE_ROUTES), \
             patch(PATCH_EXTRACT, side_effect=_fake_extract):
            result = run(_iv(tmp_path).start_interview())

        assert len(result.steps) == 2


# ---------------------------------------------------------------------------
# Field mapping
# ---------------------------------------------------------------------------

class TestFieldMapping:
    def test_auto_matched_fields_in_step(self, tmp_path):
        # route-b requires ["answer"] which is in context after route-a outputs it
        inputs = [
            "c", "", "",
            "1", "1",
            "1", "1", "",   # no mapping prompt — auto-matched
            "d",
            "h", "n", "120", "y",
        ]
        with patch(PATCH_INPUT, side_effect=inputs), \
             patch(PATCH_LIST, return_value=FAKE_ROUTES), \
             patch(PATCH_EXTRACT, side_effect=_fake_extract):
            result = run(_iv(tmp_path).start_interview())

        assert result.steps[1].field_mapping == {"answer": "answer"}

    def test_unmatched_field_select_from_context(self, tmp_path):
        # route-b requires ["text"] — NOT in context. context has ["answer"].
        # Options: 1="answer" (from context), 2=pass-through
        # User picks "1" → maps text → answer
        inputs = [
            "c", "", "",
            "1", "1",
            "1", "1",
            "1",    # source for "text": pick context option 1 ("answer")
            "",     # condition
            "d",
            "h", "n", "120", "y",
        ]
        with patch(PATCH_INPUT, side_effect=inputs), \
             patch(PATCH_LIST, return_value=FAKE_ROUTES), \
             patch(PATCH_EXTRACT, side_effect=_fake_extract_unmatched):
            result = run(_iv(tmp_path).start_interview())

        assert result.steps[1].field_mapping == {"text": "answer"}
        assert result.steps[1].pass_through_fields == []

    def test_unmatched_field_pass_through(self, tmp_path):
        # context has ["answer"], options=[answer, pass-through(idx 2)]
        # User picks "2" → pass_through
        inputs = [
            "c", "", "",
            "1", "1",
            "1", "1",
            "2",    # last option = pass-through
            "",
            "d",
            "h", "n", "120", "y",
        ]
        with patch(PATCH_INPUT, side_effect=inputs), \
             patch(PATCH_LIST, return_value=FAKE_ROUTES), \
             patch(PATCH_EXTRACT, side_effect=_fake_extract_unmatched):
            result = run(_iv(tmp_path).start_interview())

        assert "text" in result.steps[1].pass_through_fields

    def test_unmatched_field_literal_key_name(self, tmp_path):
        # User types "raw_text" as a literal key → mapping["text"] = "raw_text"
        inputs = [
            "c", "", "",
            "1", "1",
            "1", "1",
            "raw_text",     # literal key name (non-integer input)
            "",
            "d",
            "h", "n", "120", "y",
        ]
        with patch(PATCH_INPUT, side_effect=inputs), \
             patch(PATCH_LIST, return_value=FAKE_ROUTES), \
             patch(PATCH_EXTRACT, side_effect=_fake_extract_unmatched):
            result = run(_iv(tmp_path).start_interview())

        assert result.steps[1].field_mapping == {"text": "raw_text"}

    def test_unmatched_field_empty_skipped(self, tmp_path):
        # User presses Enter on unmatched field → skipped (not in mapping or pass_through)
        inputs = [
            "c", "", "",
            "1", "1",
            "1", "1",
            "",     # skip
            "",
            "d",
            "h", "n", "120", "y",
        ]
        with patch(PATCH_INPUT, side_effect=inputs), \
             patch(PATCH_LIST, return_value=FAKE_ROUTES), \
             patch(PATCH_EXTRACT, side_effect=_fake_extract_unmatched):
            result = run(_iv(tmp_path).start_interview())

        assert "text" not in result.steps[1].field_mapping
        assert "text" not in result.steps[1].pass_through_fields

    def test_unmatched_out_of_range_skipped(self, tmp_path):
        # "99" is out of range but not pass-through index → "Out of range" message
        inputs = [
            "c", "", "",
            "1", "1",
            "1", "1",
            "99",   # out of range
            "",
            "d",
            "h", "n", "120", "y",
        ]
        with patch(PATCH_INPUT, side_effect=inputs), \
             patch(PATCH_LIST, return_value=FAKE_ROUTES), \
             patch(PATCH_EXTRACT, side_effect=_fake_extract_unmatched):
            result = run(_iv(tmp_path).start_interview())

        assert "text" not in result.steps[1].field_mapping


# ---------------------------------------------------------------------------
# Condition
# ---------------------------------------------------------------------------

class TestCondition:
    def test_condition_set_on_step(self, tmp_path):
        inputs = [
            "c", "", "",
            "1", "1",
            "1", "1", "score >= 0.9",  # condition set
            "d",
            "h", "n", "120", "y",
        ]
        with patch(PATCH_INPUT, side_effect=inputs), \
             patch(PATCH_LIST, return_value=FAKE_ROUTES), \
             patch(PATCH_EXTRACT, side_effect=_fake_extract):
            result = run(_iv(tmp_path).start_interview())

        assert result.steps[1].condition == "score >= 0.9"

    def test_no_condition_is_none(self, tmp_path):
        inputs = [
            "c", "", "",
            "1", "1",
            "1", "1", "",
            "d",
            "h", "n", "120", "y",
        ]
        with patch(PATCH_INPUT, side_effect=inputs), \
             patch(PATCH_LIST, return_value=FAKE_ROUTES), \
             patch(PATCH_EXTRACT, side_effect=_fake_extract):
            result = run(_iv(tmp_path).start_interview())

        assert result.steps[1].condition is None


# ---------------------------------------------------------------------------
# Inline route creation
# ---------------------------------------------------------------------------

class TestInlineRouteCreation:
    def test_cancelled_inline_route_not_added(self, tmp_path):
        # "2" triggers inline route wizard; wizard returns None (cancelled)
        mock_ri = MagicMock()
        mock_ri.return_value.start_interview = AsyncMock(return_value=None)

        inputs = [
            "c", "", "",
            "2",        # create inline → cancelled
            "1", "1",   # add route-a
            "1", "1", "",
            "d",
            "h", "n", "120", "y",
        ]
        with patch(PATCH_INPUT, side_effect=inputs), \
             patch(PATCH_LIST, return_value=FAKE_ROUTES), \
             patch(PATCH_EXTRACT, side_effect=_fake_extract), \
             patch("safe_core.interview.RouteInterviewer", mock_ri):
            result = run(_iv(tmp_path).start_interview())

        assert len(result.steps) == 2  # inline step not added


# ---------------------------------------------------------------------------
# Timeout
# ---------------------------------------------------------------------------

class TestTimeout:
    def test_custom_timeout(self, tmp_path):
        inputs = [
            "c", "", "",
            "1", "1",
            "1", "1", "",
            "d",
            "h", "n",
            "300",
            "y",
        ]
        with patch(PATCH_INPUT, side_effect=inputs), \
             patch(PATCH_LIST, return_value=FAKE_ROUTES), \
             patch(PATCH_EXTRACT, side_effect=_fake_extract):
            result = run(_iv(tmp_path).start_interview())

        assert result.timeout_seconds == 300

    def test_invalid_timeout_uses_default(self, tmp_path):
        # non-integer → defaults to n_steps * 60 = 2 * 60 = 120
        inputs = [
            "c", "", "",
            "1", "1",
            "1", "1", "",
            "d",
            "h", "n",
            "notanumber",
            "y",
        ]
        with patch(PATCH_INPUT, side_effect=inputs), \
             patch(PATCH_LIST, return_value=FAKE_ROUTES), \
             patch(PATCH_EXTRACT, side_effect=_fake_extract):
            result = run(_iv(tmp_path).start_interview())

        assert result.timeout_seconds == 120

    def test_default_timeout_is_steps_times_60(self, tmp_path):
        inputs = [
            "c", "", "",
            "1", "1",
            "1", "1", "",
            "d",
            "h", "n",
            "",     # empty → default = 2 steps × 60 = 120
            "y",
        ]
        with patch(PATCH_INPUT, side_effect=inputs), \
             patch(PATCH_LIST, return_value=FAKE_ROUTES), \
             patch(PATCH_EXTRACT, side_effect=_fake_extract):
            result = run(_iv(tmp_path).start_interview())

        assert result.timeout_seconds == 120
