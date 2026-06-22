"""Interactive interview for HandoffDefinition creation."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Optional

import typer

from .handoff_models import HandoffDefinition, HandoffPattern, SubAgent


class _HandoffCancelledError(Exception):
    """Raised when the user types 'q' at any prompt."""


def _safe_input(prompt: str) -> str:
    val = input(prompt).strip()
    if val.lower() in ("q", "quit"):
        raise _HandoffCancelledError
    return val


_PATTERN_MENU = {
    "1": HandoffPattern.DIRECT,
    "2": HandoffPattern.SELECTIVE,
    "3": HandoffPattern.SEQUENTIAL,
    "4": HandoffPattern.HIERARCHICAL,
    "5": HandoffPattern.RECURSIVE,
}

_PATTERN_DESCRIPTIONS = {
    HandoffPattern.DIRECT: (
        "direct-handoff — delegate the entire task to one specialist sub-agent"
    ),
    HandoffPattern.SELECTIVE: (
        "selective-handoff — coordinator picks the best of N candidates at runtime"
    ),
    HandoffPattern.SEQUENTIAL: (
        "sequential-handoff — task flows through A→B→C stages in order"
    ),
    HandoffPattern.HIERARCHICAL: (
        "hierarchical-handoff — manager decomposes and delegates to workers (tree)"
    ),
    HandoffPattern.RECURSIVE: (
        "recursive-handoff — agent spawns same-type sub-agents (depth-limited)"
    ),
}

_ROLE_HELP = {
    HandoffPattern.DIRECT: (
        "You need exactly 1 sub-agent with role key 'delegate'."
    ),
    HandoffPattern.SELECTIVE: (
        "You need 1 'coordinator' and at least 2 'candidate_*' sub-agents "
        "(e.g. candidate_0, candidate_1)."
    ),
    HandoffPattern.SEQUENTIAL: (
        "You need at least 2 'stage_*' sub-agents (e.g. stage_0, stage_1)."
    ),
    HandoffPattern.HIERARCHICAL: (
        "You need 1 'manager' and at least 1 'worker_*' sub-agent (e.g. worker_0)."
    ),
    HandoffPattern.RECURSIVE: (
        "You need exactly 1 sub-agent with role key 'agent'."
    ),
}


class HandoffInterviewer:
    """Interactive wizard for building a HandoffDefinition."""

    def __init__(self, handoffs_dir: Optional[Path] = None) -> None:
        self.handoffs_dir = handoffs_dir or Path.cwd() / "handoffs"

    async def start_interview(self) -> Optional[HandoffDefinition]:
        """Run the interview. Returns None if the user cancels."""
        typer.echo("\n" + "=" * 60)
        typer.echo("  SAFE Handoff Writer — Azure AI Foundry ConnectedAgentTool")
        typer.echo("  Type 'q' at any prompt to cancel.")
        typer.echo("=" * 60 + "\n")

        try:
            pattern = self._ask_pattern()
            name, description, csa_email = self._ask_metadata()
            sub_agents = self._ask_sub_agents(pattern)
            max_depth, return_policy, timeout = self._ask_options(pattern)

            handoff = HandoffDefinition(
                name=name,
                pattern=pattern,
                sub_agents=sub_agents,
                description=description,
                max_depth=max_depth,
                return_policy=return_policy,
                timeout_seconds=timeout,
                csa_email=csa_email,
            )

            confirmed = self._review_and_confirm(handoff)
            return handoff if confirmed else None

        except _HandoffCancelledError:
            typer.echo("\n  Cancelled.")
            return None

    # ── pattern selection ─────────────────────────────────────────────────────

    def _ask_pattern(self) -> HandoffPattern:
        typer.echo("  Step 1/5 — Select handoff pattern\n")
        for key, pat in _PATTERN_MENU.items():
            typer.echo(f"    {key}. {_PATTERN_DESCRIPTIONS[pat]}")
        typer.echo()

        while True:
            choice = _safe_input("  Choice [1-5]: ")
            if choice in _PATTERN_MENU:
                pat = _PATTERN_MENU[choice]
                typer.echo(f"\n  Selected: {pat.value}\n")
                return pat
            typer.echo("  Please enter a number from 1 to 5.")

    # ── metadata ──────────────────────────────────────────────────────────────

    def _ask_metadata(self):
        typer.echo("  Step 2/5 — Handoff metadata\n")

        while True:
            name = _safe_input("  Handoff name (lowercase, hyphens): ").strip()
            if re.match(r"^[a-z][a-z0-9-]*$", name):
                break
            typer.echo("  Name must be lowercase letters, digits, and hyphens.")

        description = _safe_input("  Description (one line): ").strip()
        csa_email = _safe_input("  CSA email (optional, Enter to skip): ").strip()
        typer.echo()
        return name, description, csa_email

    # ── sub-agent pool ────────────────────────────────────────────────────────

    def _ask_sub_agents(self, pattern: HandoffPattern) -> Dict[str, SubAgent]:
        typer.echo(f"  Step 3/5 — Configure sub-agents\n")
        typer.echo(f"  {_ROLE_HELP[pattern]}\n")

        sub_agents: Dict[str, SubAgent] = {}

        if pattern == HandoffPattern.DIRECT:
            sub_agents["delegate"] = self._ask_one_sub_agent("delegate")

        elif pattern == HandoffPattern.SELECTIVE:
            sub_agents["coordinator"] = self._ask_one_sub_agent("coordinator")
            n = self._ask_int("  How many candidate sub-agents? [2-6]: ", 2, 6)
            for i in range(n):
                key = f"candidate_{i}"
                sub_agents[key] = self._ask_one_sub_agent(key)

        elif pattern == HandoffPattern.SEQUENTIAL:
            n = self._ask_int("  How many stages? [2-6]: ", 2, 6)
            for i in range(n):
                key = f"stage_{i}"
                sub_agents[key] = self._ask_one_sub_agent(key)

        elif pattern == HandoffPattern.HIERARCHICAL:
            sub_agents["manager"] = self._ask_one_sub_agent("manager")
            n = self._ask_int("  How many worker sub-agents? [1-6]: ", 1, 6)
            for i in range(n):
                key = f"worker_{i}"
                sub_agents[key] = self._ask_one_sub_agent(key)

        elif pattern == HandoffPattern.RECURSIVE:
            sub_agents["agent"] = self._ask_one_sub_agent("agent")

        return sub_agents

    def _ask_one_sub_agent(self, role_key: str) -> SubAgent:
        typer.echo(f"\n  Sub-agent: {typer.style(role_key, bold=True)}")
        name = _safe_input(f"    Display name: ").strip() or role_key
        description = _safe_input(f"    Description (used by coordinator for routing): ").strip()
        tags_raw = _safe_input(f"    Capability tags (comma-separated, optional): ").strip()
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
        return SubAgent(name=name, description=description, capability_tags=tags)

    # ── options ───────────────────────────────────────────────────────────────

    def _ask_options(self, pattern: HandoffPattern):
        typer.echo("\n  Step 4/5 — Options\n")

        default_depth = 3 if pattern in (
            HandoffPattern.HIERARCHICAL, HandoffPattern.RECURSIVE
        ) else 1
        depth_raw = _safe_input(
            f"  Max delegation depth [{default_depth}]: "
        ).strip()
        max_depth = int(depth_raw) if depth_raw.isdigit() else default_depth

        typer.echo("  Return policy:")
        typer.echo("    1. always       — always return to caller")
        typer.echo("    2. on_partial   — return even if some sub-agents failed")
        typer.echo("    3. on_failure   — return only on failure (escalation)")
        policy_map = {"1": "always", "2": "on_partial", "3": "on_failure"}
        policy_choice = _safe_input("  Choice [1]: ").strip() or "1"
        return_policy = policy_map.get(policy_choice, "always")

        timeout_raw = _safe_input("  Timeout in seconds [120]: ").strip()
        timeout = int(timeout_raw) if timeout_raw.isdigit() else 120

        typer.echo()
        return max_depth, return_policy, timeout

    # ── review ────────────────────────────────────────────────────────────────

    def _review_and_confirm(self, handoff: HandoffDefinition) -> bool:
        typer.echo("  Step 5/5 — Review\n")
        typer.echo(f"  Name         : {handoff.name}")
        typer.echo(f"  Pattern      : {handoff.pattern.value}")
        typer.echo(f"  Description  : {handoff.description or '(none)'}")
        typer.echo(f"  Max depth    : {handoff.max_depth}")
        typer.echo(f"  Return policy: {handoff.return_policy}")
        typer.echo(f"  Timeout      : {handoff.timeout_seconds}s")
        typer.echo(f"  CSA email    : {handoff.csa_email or '(none)'}")
        typer.echo(f"\n  Sub-agents ({len(handoff.sub_agents)}):")
        for key, agent in handoff.sub_agents.items():
            typer.echo(f"    {key:<20} {agent.name} — {agent.description[:60]}")
        typer.echo()
        answer = _safe_input("  Generate handoff? [Y/n]: ").strip().lower()
        return answer in ("", "y", "yes")

    # ── helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _ask_int(prompt: str, lo: int, hi: int) -> int:
        while True:
            raw = _safe_input(prompt).strip()
            if raw.isdigit() and lo <= int(raw) <= hi:
                return int(raw)
            typer.echo(f"  Please enter a number from {lo} to {hi}.")
