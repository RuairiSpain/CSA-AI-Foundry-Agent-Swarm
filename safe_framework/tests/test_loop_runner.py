"""Tests for safe_core.loop_runner — 100% coverage of all public + private paths."""

import asyncio
import pytest

from safe_core.loop_runner import (
    LoopRunner,
    LoopRunResult,
    compact_history,
    evaluate_goal,
    is_stuck,
    _apply_hierarchical,
    _apply_sliding_window,
    _apply_summarize_and_replace,
    _should_compact,
)
from safe_core.models import (
    CompactionConfig,
    CompactionStrategy,
    LoopConfig,
    LoopTerminationType,
    RouteDefinition,
    RoutePattern,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_route(pattern=RoutePattern.GOAL_DRIVEN_LOOP, lc=None):
    return RouteDefinition(name="test", pattern=pattern, agents={}, loop_config=lc)


async def success_invoker(role: str, inp: dict) -> dict:
    return {"result": "ok", "done": True}


async def fail_invoker(role: str, inp: dict) -> dict:
    raise RuntimeError("forced failure")


async def never_done_invoker(role: str, inp: dict) -> dict:
    return {"result": "pending", "done": False}


# ---------------------------------------------------------------------------
# Compaction strategies
# ---------------------------------------------------------------------------

class TestSlidingWindow:
    def test_shorter_than_preserve(self):
        h = [{"a": 1}, {"b": 2}]
        assert _apply_sliding_window(h, 5) == h

    def test_longer_than_preserve(self):
        h = [{"a": i} for i in range(10)]
        result = _apply_sliding_window(h, 3)
        assert len(result) == 3
        assert result == h[-3:]

    def test_exactly_preserve(self):
        h = [{"x": 1}, {"x": 2}, {"x": 3}]
        assert _apply_sliding_window(h, 3) == h


class TestSummarizeAndReplace:
    def test_shorter_than_preserve(self):
        h = [{"a": 1}]
        assert _apply_summarize_and_replace(h, 3) == h

    def test_longer_than_preserve(self):
        h = [{"a": i} for i in range(5)]
        result = _apply_summarize_and_replace(h, 2)
        assert len(result) == 3
        assert result[0]["type"] == "compacted_summary"
        assert result[0]["compacted_iterations"] == 3
        assert result[-2:] == h[-2:]

    def test_summary_keys_seen(self):
        h = [{"foo": 1}, {"bar": 2}, {"baz": 3}]
        result = _apply_summarize_and_replace(h, 1)
        assert set(result[0]["keys_seen"]) == {"foo", "bar"}


class TestHierarchical:
    def test_shorter_than_preserve(self):
        h = [{"a": 1}]
        assert _apply_hierarchical(h, 3) == h

    def test_longer_than_preserve(self):
        h = [{"step": i} for i in range(6)]
        result = _apply_hierarchical(h, 2)
        assert result[0]["type"] == "rolling_summary"
        assert len(result[0]["entries"]) == 4
        assert result[-2:] == h[-2:]


class TestCompactHistory:
    def test_sliding_window_dispatch(self):
        cfg = CompactionConfig(strategy=CompactionStrategy.SLIDING_WINDOW, preserve_last_n=2)
        h = [{"x": i} for i in range(5)]
        result = compact_history(h, cfg)
        assert len(result) == 2

    def test_summarize_dispatch(self):
        cfg = CompactionConfig(strategy=CompactionStrategy.SUMMARIZE_AND_REPLACE, preserve_last_n=2)
        h = [{"x": i} for i in range(5)]
        result = compact_history(h, cfg)
        assert result[0]["type"] == "compacted_summary"

    def test_hierarchical_dispatch(self):
        cfg = CompactionConfig(strategy=CompactionStrategy.HIERARCHICAL, preserve_last_n=2)
        h = [{"x": i} for i in range(5)]
        result = compact_history(h, cfg)
        assert result[0]["type"] == "rolling_summary"

    def test_unknown_strategy_passthrough(self):
        cfg = CompactionConfig(strategy=CompactionStrategy.SLIDING_WINDOW, preserve_last_n=2)
        cfg.strategy = "unknown"  # type: ignore
        h = [{"x": 1}]
        result = compact_history(h, cfg)
        assert result == h


# ---------------------------------------------------------------------------
# is_stuck
# ---------------------------------------------------------------------------

class TestIsStuck:
    def test_too_short_not_stuck(self):
        assert not is_stuck([{"a": 1}, {"a": 1}], threshold=3)

    def test_all_same_stuck(self):
        assert is_stuck([{"a": 1}] * 4, threshold=3)

    def test_different_not_stuck(self):
        assert not is_stuck([{"a": 1}, {"a": 2}, {"a": 1}], threshold=3)

    def test_exactly_threshold(self):
        assert is_stuck([{"x": 0}] * 3, threshold=3)


# ---------------------------------------------------------------------------
# evaluate_goal
# ---------------------------------------------------------------------------

class TestEvaluateGoal:
    def test_true_condition(self):
        assert evaluate_goal({"done": True}, "output['done'] == True")

    def test_false_condition(self):
        assert not evaluate_goal({"done": False}, "output['done'] == True")

    def test_empty_expression(self):
        assert not evaluate_goal({"done": True}, "")

    def test_invalid_expression(self):
        assert not evaluate_goal({}, "output.nonexistent > 0")

    def test_numeric_threshold(self):
        assert evaluate_goal({"coverage": 92.5}, "output['coverage'] >= 90")


# ---------------------------------------------------------------------------
# _should_compact
# ---------------------------------------------------------------------------

class TestShouldCompact:
    def test_iteration_zero_false(self):
        cfg = CompactionConfig(preserve_last_n=2)
        assert not _should_compact(0, cfg)

    def test_first_threshold(self):
        cfg = CompactionConfig(preserve_last_n=2)
        # iteration=1 → (1+1)%2==0 and 1>0 → True
        assert _should_compact(1, cfg)

    def test_non_threshold_iteration(self):
        cfg = CompactionConfig(preserve_last_n=2)
        assert not _should_compact(2, cfg)

    def test_preserve_last_n_one_zero_clamped(self):
        cfg = CompactionConfig(preserve_last_n=0)
        # preserve_last_n clamped to 1; iteration=0 → False (0>0 is False)
        assert not _should_compact(0, cfg)


# ---------------------------------------------------------------------------
# LoopRunResult
# ---------------------------------------------------------------------------

class TestLoopRunResult:
    def test_defaults(self):
        r = LoopRunResult(success=True, iterations=3, final_output={}, stop_reason="done")
        assert r.compactions == 0
        assert r.errors == []

    def test_with_errors(self):
        r = LoopRunResult(success=False, iterations=5, final_output={}, stop_reason="stuck", errors=["e1"])
        assert r.errors == ["e1"]


# ---------------------------------------------------------------------------
# LoopRunner.run_goal
# ---------------------------------------------------------------------------

class TestLoopRunnerGoal:
    def test_goal_met_on_first_iteration(self):
        cfg = LoopConfig(max_iterations=5, goal_expression="output['done'] == True")
        runner = LoopRunner(cfg)
        rd = make_route(lc=cfg)

        async def invoker(role, inp):
            return {"done": True, "value": 42}

        result = asyncio.run(runner.run_goal(rd, invoker, {}))
        assert result.success
        assert result.iterations == 1
        assert result.stop_reason == "goal_met"

    def test_goal_never_met_hits_max(self):
        # stuck_detection_threshold > max_iterations so stuck never fires
        cfg = LoopConfig(max_iterations=3, stuck_detection_threshold=10,
                         goal_expression="output['done'] == True")
        runner = LoopRunner(cfg)
        rd = make_route(lc=cfg)
        count = [0]

        async def invoker(role, inp):
            count[0] += 1
            return {"done": False, "n": count[0]}

        result = asyncio.run(runner.run_goal(rd, invoker, {}))
        assert not result.success
        assert result.iterations == 3
        assert result.stop_reason == "max_iterations_reached"

    def test_stuck_graceful_degradation(self):
        cfg = LoopConfig(max_iterations=10, stuck_detection_threshold=3,
                         goal_expression="output['done'] == True", on_stuck="graceful_degradation")
        runner = LoopRunner(cfg)
        rd = make_route(lc=cfg)

        async def invoker(role, inp):
            return {"done": False, "val": 1}

        result = asyncio.run(runner.run_goal(rd, invoker, {}))
        assert not result.success
        assert result.stop_reason == "stuck_detected"

    def test_stuck_raise(self):
        cfg = LoopConfig(max_iterations=10, stuck_detection_threshold=3,
                         goal_expression="output['done'] == True", on_stuck="raise")
        runner = LoopRunner(cfg)
        rd = make_route(lc=cfg)

        async def invoker(role, inp):
            return {"done": False, "val": 1}

        with pytest.raises(RuntimeError, match="stuck"):
            asyncio.run(runner.run_goal(rd, invoker, {}))

    def test_invoker_exception_recorded_as_error(self):
        cfg = LoopConfig(max_iterations=2, goal_expression="output['done'] == True")
        runner = LoopRunner(cfg)
        rd = make_route(lc=cfg)

        async def invoker(role, inp):
            raise ValueError("boom")

        result = asyncio.run(runner.run_goal(rd, invoker, {}))
        assert len(result.errors) == 2

    def test_compaction_triggered(self):
        cc = CompactionConfig(strategy=CompactionStrategy.SLIDING_WINDOW, preserve_last_n=1)
        cfg = LoopConfig(max_iterations=5, goal_expression="output['done'] == True",
                         compaction=cc)
        runner = LoopRunner(cfg)
        rd = make_route(lc=cfg)
        calls = []

        async def invoker(role, inp):
            calls.append(1)
            return {"done": len(calls) >= 4}

        result = asyncio.run(runner.run_goal(rd, invoker, {}))
        assert result.compactions >= 1

    def test_default_config_no_goal(self):
        # Default stuck_detection_threshold=3, so 3 identical outputs → stuck_detected
        runner = LoopRunner()
        rd = make_route()
        count = [0]

        async def invoker(role, inp):
            count[0] += 1
            return {"done": False, "n": count[0]}

        result = asyncio.run(runner.run_goal(rd, invoker, {}))
        # With varying output, reaches max_iterations; empty goal_expression never matches
        assert result.iterations == 10


# ---------------------------------------------------------------------------
# LoopRunner.run_interval
# ---------------------------------------------------------------------------

class TestLoopRunnerInterval:
    def test_runs_to_max_iterations(self):
        cfg = LoopConfig(max_iterations=3)
        runner = LoopRunner(cfg)
        rd = make_route(pattern=RoutePattern.INTERVAL_LOOP, lc=cfg)

        async def invoker(role, inp):
            return {"status": "ok"}

        result = asyncio.run(runner.run_interval(rd, invoker, {}, interval_seconds=0.01))
        assert result.success
        assert result.iterations == 3
        assert result.stop_reason == "max_iterations_reached"

    def test_stop_event_before_first_iteration(self):
        cfg = LoopConfig(max_iterations=5)
        runner = LoopRunner(cfg)
        rd = make_route(pattern=RoutePattern.INTERVAL_LOOP, lc=cfg)
        stop = asyncio.Event()
        stop.set()

        async def invoker(role, inp):
            return {"status": "ok"}

        result = asyncio.run(runner.run_interval(rd, invoker, {}, interval_seconds=0.01, stop_event=stop))
        assert result.stop_reason == "stop_requested"
        assert result.iterations == 0

    def test_stop_event_mid_run(self):
        cfg = LoopConfig(max_iterations=10)
        runner = LoopRunner(cfg)
        rd = make_route(pattern=RoutePattern.INTERVAL_LOOP, lc=cfg)
        stop = asyncio.Event()
        count = [0]

        async def invoker(role, inp):
            count[0] += 1
            if count[0] >= 2:
                stop.set()
            return {"status": "ok"}

        result = asyncio.run(runner.run_interval(rd, invoker, {}, interval_seconds=0.01, stop_event=stop))
        assert result.stop_reason == "stop_requested"
        assert result.iterations <= 10

    def test_invoker_exception_recorded(self):
        cfg = LoopConfig(max_iterations=2)
        runner = LoopRunner(cfg)
        rd = make_route(pattern=RoutePattern.INTERVAL_LOOP, lc=cfg)

        async def invoker(role, inp):
            raise RuntimeError("fail")

        result = asyncio.run(runner.run_interval(rd, invoker, {}, interval_seconds=0.01))
        assert len(result.errors) == 2

    def test_stop_mid_sleep_returns_stop_requested(self):
        """Stop event fires during the inter-iteration sleep (line 259 path)."""
        cfg = LoopConfig(max_iterations=10)
        runner = LoopRunner(cfg)
        rd = make_route(pattern=RoutePattern.INTERVAL_LOOP, lc=cfg)
        stop = asyncio.Event()
        iteration_count = [0]

        async def run():
            async def set_stop_after_tiny_delay():
                await asyncio.sleep(0.01)
                stop.set()

            async def invoker(role, inp):
                iteration_count[0] += 1
                if iteration_count[0] == 1:
                    # Schedule stop to fire while wait_for is sleeping (interval=5s)
                    asyncio.ensure_future(set_stop_after_tiny_delay())
                return {"status": "ok"}

            return await runner.run_interval(
                rd, invoker, {}, interval_seconds=5.0, stop_event=stop
            )

        result = asyncio.run(run())
        assert result.stop_reason == "stop_requested"
        assert result.iterations == 1

    def test_compaction_in_interval(self):
        cc = CompactionConfig(strategy=CompactionStrategy.SUMMARIZE_AND_REPLACE, preserve_last_n=1)
        cfg = LoopConfig(max_iterations=4, compaction=cc)
        runner = LoopRunner(cfg)
        rd = make_route(pattern=RoutePattern.INTERVAL_LOOP, lc=cfg)

        async def invoker(role, inp):
            return {"val": 1}

        result = asyncio.run(runner.run_interval(rd, invoker, {}, interval_seconds=0.001))
        assert result.compactions >= 1


# ---------------------------------------------------------------------------
# LoopRunner.run_react
# ---------------------------------------------------------------------------

class TestLoopRunnerReact:
    def test_done_on_first_iteration(self):
        cfg = LoopConfig(max_iterations=5)
        runner = LoopRunner(cfg)
        rd = make_route(pattern=RoutePattern.REACT_LOOP, lc=cfg)

        async def invoker(role, inp):
            if role == "observer":
                return {"done": True, "observation": "found it"}
            return {"thought": "think", "next_action": "act", "action_result": {}}

        result = asyncio.run(runner.run_react(rd, invoker, {"task": "test"}))
        assert result.success
        assert result.iterations == 1
        assert result.stop_reason == "done_signal"

    def test_max_iterations_reached(self):
        # stuck_detection_threshold > max_iterations so stuck never fires
        cfg = LoopConfig(max_iterations=3, stuck_detection_threshold=10)
        runner = LoopRunner(cfg)
        rd = make_route(pattern=RoutePattern.REACT_LOOP, lc=cfg)
        count = [0]

        async def invoker(role, inp):
            if role == "observer":
                count[0] += 1
                return {"done": False, "observation": f"step {count[0]}"}
            return {"thought": "t", "next_action": "a", "action_result": {}}

        result = asyncio.run(runner.run_react(rd, invoker, {}))
        assert not result.success
        assert result.iterations == 3
        assert result.stop_reason == "max_iterations_reached"

    def test_stuck_graceful(self):
        cfg = LoopConfig(max_iterations=10, stuck_detection_threshold=3, on_stuck="graceful_degradation")
        runner = LoopRunner(cfg)
        rd = make_route(pattern=RoutePattern.REACT_LOOP, lc=cfg)

        async def invoker(role, inp):
            if role == "observer":
                return {"done": False, "observation": "same"}
            return {"thought": "t", "next_action": "a", "action_result": {}}

        result = asyncio.run(runner.run_react(rd, invoker, {}))
        assert result.stop_reason == "stuck_detected"

    def test_stuck_raise(self):
        cfg = LoopConfig(max_iterations=10, stuck_detection_threshold=3, on_stuck="raise")
        runner = LoopRunner(cfg)
        rd = make_route(pattern=RoutePattern.REACT_LOOP, lc=cfg)

        async def invoker(role, inp):
            if role == "observer":
                return {"done": False, "observation": "same"}
            return {"thought": "t", "next_action": "a", "action_result": {}}

        with pytest.raises(RuntimeError, match="stuck"):
            asyncio.run(runner.run_react(rd, invoker, {}))

    def test_exception_in_step_recorded(self):
        cfg = LoopConfig(max_iterations=2)
        runner = LoopRunner(cfg)
        rd = make_route(pattern=RoutePattern.REACT_LOOP, lc=cfg)

        async def invoker(role, inp):
            raise ValueError("boom")

        result = asyncio.run(runner.run_react(rd, invoker, {}))
        assert len(result.errors) == 2

    def test_compaction_in_react(self):
        cc = CompactionConfig(strategy=CompactionStrategy.HIERARCHICAL, preserve_last_n=1)
        cfg = LoopConfig(max_iterations=5, compaction=cc)
        runner = LoopRunner(cfg)
        rd = make_route(pattern=RoutePattern.REACT_LOOP, lc=cfg)
        calls = [0]

        async def invoker(role, inp):
            if role == "observer":
                calls[0] += 1
                return {"done": calls[0] >= 4, "observation": "x"}
            return {"thought": "t", "next_action": "a", "action_result": {}}

        result = asyncio.run(runner.run_react(rd, invoker, {}))
        assert result.compactions >= 1
