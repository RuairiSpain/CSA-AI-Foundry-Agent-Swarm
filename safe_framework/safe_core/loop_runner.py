"""
SAFE Framework — LoopRunner

Executes loop-pattern routes with lifecycle management:
  - Interval-based repetition  (INTERVAL_LOOP)
  - Goal-verified termination  (GOAL_DRIVEN_LOOP)
  - ReAct Think/Act/Observe    (REACT_LOOP)

Handles iteration caps, stuck-detection, graceful degradation, and
context compaction when token budget approaches threshold.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .models import (
    CompactionConfig,
    CompactionStrategy,
    LoopConfig,
    LoopTerminationType,
    RouteDefinition,
    RoutePattern,
)

logger = logging.getLogger(__name__)

_LOOP_PATTERNS = {
    RoutePattern.REACT_LOOP,
    RoutePattern.GOAL_DRIVEN_LOOP,
    RoutePattern.INTERVAL_LOOP,
}


# ---------------------------------------------------------------------------
# Public result type
# ---------------------------------------------------------------------------

@dataclass
class LoopRunResult:
    """Outcome of a completed loop run."""
    success: bool
    iterations: int
    final_output: Dict[str, Any]
    stop_reason: str
    compactions: int = 0
    errors: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Compaction helpers
# ---------------------------------------------------------------------------

def _apply_sliding_window(
    history: List[Dict[str, Any]],
    preserve_last_n: int,
) -> List[Dict[str, Any]]:
    """Drop oldest iterations, keep the last *preserve_last_n*."""
    return history[-preserve_last_n:] if len(history) > preserve_last_n else history


def _apply_summarize_and_replace(
    history: List[Dict[str, Any]],
    preserve_last_n: int,
) -> List[Dict[str, Any]]:
    """Replace all but the last *preserve_last_n* with a single summary entry."""
    if len(history) <= preserve_last_n:
        return history
    older = history[:-preserve_last_n]
    summary = {
        "type": "compacted_summary",
        "compacted_iterations": len(older),
        "keys_seen": sorted({k for item in older for k in item}),
    }
    return [summary] + history[-preserve_last_n:]


def _apply_hierarchical(
    history: List[Dict[str, Any]],
    preserve_last_n: int,
) -> List[Dict[str, Any]]:
    """Keep rolling summary of prior iterations + last *preserve_last_n* in full."""
    if len(history) <= preserve_last_n:
        return history
    older = history[:-preserve_last_n]
    rolling_summary: Dict[str, Any] = {"type": "rolling_summary", "entries": []}
    for entry in older:
        rolling_summary["entries"].append({k: v for k, v in entry.items() if k != "type"})
    return [rolling_summary] + history[-preserve_last_n:]


def compact_history(
    history: List[Dict[str, Any]],
    config: CompactionConfig,
) -> List[Dict[str, Any]]:
    """Apply the configured compaction strategy to *history*."""
    strategy = config.strategy
    n = config.preserve_last_n

    if strategy == CompactionStrategy.SLIDING_WINDOW:
        return _apply_sliding_window(history, n)
    if strategy == CompactionStrategy.SUMMARIZE_AND_REPLACE:
        return _apply_summarize_and_replace(history, n)
    if strategy == CompactionStrategy.HIERARCHICAL:
        return _apply_hierarchical(history, n)
    return history


# ---------------------------------------------------------------------------
# Stuck-detection
# ---------------------------------------------------------------------------

def is_stuck(
    history: List[Dict[str, Any]],
    threshold: int,
) -> bool:
    """Return True when the last *threshold* outputs are identical."""
    if len(history) < threshold:
        return False
    tail = history[-threshold:]
    return all(item == tail[0] for item in tail[1:])


# ---------------------------------------------------------------------------
# Goal verification
# ---------------------------------------------------------------------------

def evaluate_goal(output: Dict[str, Any], goal_expression: str) -> bool:
    """Evaluate *goal_expression* against *output* via a restricted eval."""
    if not goal_expression:
        return False
    try:
        return bool(eval(goal_expression, {"__builtins__": {}}, {"output": output}))  # noqa: S307
    except Exception as exc:
        logger.warning("Goal expression evaluation failed: %s", exc)
        return False


# ---------------------------------------------------------------------------
# Core LoopRunner
# ---------------------------------------------------------------------------

class LoopRunner:
    """Manages lifecycle for all three loop pattern types."""

    def __init__(self, config: Optional[LoopConfig] = None) -> None:
        self._config = config or LoopConfig()

    # ------------------------------------------------------------------
    # Public entry points
    # ------------------------------------------------------------------

    async def run_goal(
        self,
        route_def: RouteDefinition,
        agent_invoker: Callable[[str, Dict[str, Any]], Any],
        initial_input: Dict[str, Any],
    ) -> LoopRunResult:
        """Run until the goal expression is satisfied or max_iterations hit."""
        cfg = self._config
        history: List[Dict[str, Any]] = []
        compactions = 0
        errors: List[str] = []

        for iteration in range(cfg.max_iterations):
            logger.info("goal-loop iteration %d/%d", iteration + 1, cfg.max_iterations)
            try:
                output = await agent_invoker("worker", initial_input)
            except Exception as exc:
                err = f"iteration {iteration + 1}: {exc}"
                errors.append(err)
                logger.warning(err)
                output = {}

            history.append(dict(output))

            if cfg.compaction and _should_compact(iteration, cfg.compaction):
                history = compact_history(history, cfg.compaction)
                compactions += 1
                logger.info("compacted context at iteration %d", iteration + 1)

            if is_stuck(history, cfg.stuck_detection_threshold):
                return self._handle_stuck(
                    cfg.on_stuck,
                    iteration + 1,
                    output,
                    compactions,
                    errors,
                )

            if evaluate_goal(output, cfg.goal_expression):
                return LoopRunResult(
                    success=True,
                    iterations=iteration + 1,
                    final_output=output,
                    stop_reason="goal_met",
                    compactions=compactions,
                    errors=errors,
                )

        last = history[-1] if history else {}
        return LoopRunResult(
            success=False,
            iterations=cfg.max_iterations,
            final_output=last,
            stop_reason="max_iterations_reached",
            compactions=compactions,
            errors=errors,
        )

    async def run_interval(
        self,
        route_def: RouteDefinition,
        agent_invoker: Callable[[str, Dict[str, Any]], Any],
        initial_input: Dict[str, Any],
        interval_seconds: float,
        stop_event: Optional[asyncio.Event] = None,
    ) -> LoopRunResult:
        """Run on a fixed interval until stop_event is set or max_iterations hit."""
        cfg = self._config
        stop_event = stop_event or asyncio.Event()
        history: List[Dict[str, Any]] = []
        compactions = 0
        errors: List[str] = []
        last_output: Dict[str, Any] = {}

        for iteration in range(cfg.max_iterations):
            if stop_event.is_set():
                return LoopRunResult(
                    success=True,
                    iterations=iteration,
                    final_output=last_output,
                    stop_reason="stop_requested",
                    compactions=compactions,
                    errors=errors,
                )

            logger.info("interval-loop iteration %d/%d", iteration + 1, cfg.max_iterations)
            try:
                last_output = await agent_invoker("worker", initial_input)
            except Exception as exc:
                err = f"iteration {iteration + 1}: {exc}"
                errors.append(err)
                logger.warning(err)
                last_output = {}

            history.append(dict(last_output))

            if cfg.compaction and _should_compact(iteration, cfg.compaction):
                history = compact_history(history, cfg.compaction)
                compactions += 1

            if iteration < cfg.max_iterations - 1 and not stop_event.is_set():
                try:
                    await asyncio.wait_for(stop_event.wait(), timeout=interval_seconds)
                    return LoopRunResult(
                        success=True,
                        iterations=iteration + 1,
                        final_output=last_output,
                        stop_reason="stop_requested",
                        compactions=compactions,
                        errors=errors,
                    )
                except asyncio.TimeoutError:
                    pass

        return LoopRunResult(
            success=True,
            iterations=cfg.max_iterations,
            final_output=last_output,
            stop_reason="max_iterations_reached",
            compactions=compactions,
            errors=errors,
        )

    async def run_react(
        self,
        route_def: RouteDefinition,
        agent_invoker: Callable[[str, Dict[str, Any]], Any],
        initial_input: Dict[str, Any],
    ) -> LoopRunResult:
        """Execute a ReAct Think/Act/Observe loop."""
        cfg = self._config
        history: List[Dict[str, Any]] = []
        compactions = 0
        errors: List[str] = []
        context: Dict[str, Any] = dict(initial_input)

        for iteration in range(cfg.max_iterations):
            logger.info("react-loop iteration %d/%d", iteration + 1, cfg.max_iterations)

            try:
                thought = await agent_invoker("thinker", context)
                context.update(thought)

                action = await agent_invoker("actor", context)
                context.update(action)

                observation = await agent_invoker("observer", context)
                context.update(observation)
            except Exception as exc:
                err = f"react iteration {iteration + 1}: {exc}"
                errors.append(err)
                logger.warning(err)
                history.append({"error": str(exc)})
                continue

            step = {"thought": thought, "action": action, "observation": observation}
            history.append(step)

            if cfg.compaction and _should_compact(iteration, cfg.compaction):
                history = compact_history(history, cfg.compaction)
                compactions += 1

            if is_stuck(history, cfg.stuck_detection_threshold):
                return self._handle_stuck(
                    cfg.on_stuck,
                    iteration + 1,
                    context,
                    compactions,
                    errors,
                )

            if observation.get("done"):
                return LoopRunResult(
                    success=True,
                    iterations=iteration + 1,
                    final_output=context,
                    stop_reason="done_signal",
                    compactions=compactions,
                    errors=errors,
                )

        return LoopRunResult(
            success=False,
            iterations=cfg.max_iterations,
            final_output=context,
            stop_reason="max_iterations_reached",
            compactions=compactions,
            errors=errors,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _handle_stuck(
        on_stuck: str,
        iteration: int,
        last_output: Dict[str, Any],
        compactions: int,
        errors: List[str],
    ) -> LoopRunResult:
        if on_stuck == "raise":
            raise RuntimeError(f"Loop stuck after {iteration} iterations")
        return LoopRunResult(
            success=False,
            iterations=iteration,
            final_output=last_output,
            stop_reason="stuck_detected",
            compactions=compactions,
            errors=errors,
        )


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _should_compact(iteration: int, config: CompactionConfig) -> bool:
    """True every *preserve_last_n* iterations starting from the first threshold crossing."""
    n = max(1, config.preserve_last_n)
    return (iteration + 1) % n == 0 and iteration > 0
