"""Interactive interview for RouteChain creation."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import typer
import yaml

from .chain_models import RouteChain, RouteChainStep


class _ChainCancelledError(Exception):
    """Raised when the user types 'q' at any prompt."""


def _safe_input(prompt: str) -> str:
    """input() wrapper — raises _ChainCancelledError on 'q' or 'quit'."""
    val = input(prompt).strip()
    if val.lower() in ("q", "quit"):
        raise _ChainCancelledError
    return val


# ---------------------------------------------------------------------------
# Helpers for reading route metadata from generated files
# ---------------------------------------------------------------------------

def _list_routes(routes_dir: Path) -> List[Dict[str, str]]:
    """Return metadata for all routes that have a route.py in routes_dir."""
    routes = []
    if not routes_dir.exists():
        return routes
    for d in sorted(routes_dir.iterdir()):
        if not (d / "route.py").exists():
            continue
        pattern = ""
        config = d / "config.yaml"
        if config.exists():
            try:
                cfg = yaml.safe_load(config.read_text(encoding="utf-8"))
                pattern = cfg.get("pattern", "")
            except Exception:
                pass
        routes.append({"name": d.name, "pattern": pattern})
    return routes


def _extract_fields(routes_dir: Path, route_name: str, field_var: str) -> List[str]:
    """Extract a list literal assigned to field_var inside a generated route.py."""
    route_file = routes_dir / route_name / "route.py"
    if not route_file.exists():
        return []
    src = route_file.read_text(encoding="utf-8")
    m = re.search(rf"{re.escape(field_var)}\s*=\s*(\[.*?\])", src)
    if m:
        try:
            import ast
            return ast.literal_eval(m.group(1))
        except Exception:
            pass
    return []


# ---------------------------------------------------------------------------
# ChainInterviewer
# ---------------------------------------------------------------------------

class ChainInterviewer:
    """Interactive wizard for building a RouteChain."""

    def __init__(self, routes_dir: Optional[Path] = None) -> None:
        self.routes_dir = routes_dir or Path.cwd() / "routes"

    # ── public entry point ────────────────────────────────────────────────

    async def start_interview(self) -> Optional[RouteChain]:
        """Run the interview. Returns None if the user cancels."""
        typer.echo("\n" + "=" * 60)
        typer.echo("SAFE Chain Builder — Interactive Interview")
        typer.echo("=" * 60)
        typer.echo("\nBuild a multi-pattern chain. Each step is a complete route.")
        typer.echo("Type 'q' at any prompt to cancel.\n")

        try:
            return await self._run()
        except _ChainCancelledError:
            typer.echo("\nCancelled. No files were written.")
            return None
        except KeyboardInterrupt:
            typer.echo("\n\nCancelled. No files were written.")
            return None

    # ── interview flow ────────────────────────────────────────────────────

    async def _run(self) -> Optional[RouteChain]:
        name, description, csa_email = await self._ask_metadata()
        steps = await self._ask_steps()
        on_failure, include_history = await self._ask_options()
        timeout = await self._ask_timeout(len(steps))

        chain = RouteChain(
            name=name,
            description=description,
            csa_email=csa_email,
            steps=steps,
            timeout_seconds=timeout,
            on_step_failure=on_failure,
            include_chain_history=include_history,
        )

        if not await self._review(chain):
            typer.echo("\nCancelled. No files were written.")
            return None

        return chain

    # ── step 1: metadata ─────────────────────────────────────────────────

    async def _ask_metadata(self) -> Tuple[str, str, str]:
        typer.echo("--- Step 1: Chain Details ---\n")
        name = _safe_input("Chain name (lowercase, hyphens): ") or "my-chain"
        name = name.lower().replace(" ", "-")
        description = _safe_input("Description (optional): ")
        csa_email = _safe_input("Your email (for audit trail): ")
        typer.echo(f"\n✓ Chain: {name}\n")
        return name, description, csa_email

    # ── step 2: build steps ───────────────────────────────────────────────

    async def _ask_steps(self) -> List[RouteChainStep]:
        typer.echo("--- Step 2: Build Your Chain ---\n")
        steps: List[RouteChainStep] = []
        context_keys: List[str] = []  # accumulates all known output keys

        while True:
            typer.echo(f"\nChain so far: {self._chain_summary(steps)}")
            typer.echo("\nOptions:")
            typer.echo("  1. Add an existing route")
            typer.echo("  2. Create a new route  (launches safe route wizard)")
            if len(steps) >= 2:
                typer.echo("  d. Done — finish adding steps")
            typer.echo("  b. Remove last step")
            typer.echo("  q. Cancel\n")

            choice = _safe_input("Choice: ").lower()

            if choice in ("d", "done"):
                if len(steps) >= 2:
                    break
                typer.echo("⚠ A chain needs at least 2 steps.")
                continue

            if choice == "b":
                if steps:
                    removed = steps.pop()
                    # recalculate context_keys from scratch
                    context_keys = self._rebuild_context_keys(steps)
                    typer.echo(f"  Removed: {removed.route_name}")
                else:
                    typer.echo("  Nothing to remove.")
                continue

            if choice == "1":
                step, new_outputs = await self._pick_existing_route(steps, context_keys)
                if step:
                    steps.append(step)
                    context_keys.extend(new_outputs)

            elif choice == "2":
                step, new_outputs = await self._create_route_inline(steps, context_keys)
                if step:
                    steps.append(step)
                    context_keys.extend(new_outputs)

            else:
                typer.echo("Invalid choice.")

        return steps

    def _rebuild_context_keys(self, steps: List[RouteChainStep]) -> List[str]:
        """Re-derive context keys from the routes of current steps."""
        keys: List[str] = []
        for s in steps:
            keys.extend(_extract_fields(self.routes_dir, s.route_name, "required_output_fields"))
        return keys

    async def _pick_existing_route(
        self,
        existing_steps: List[RouteChainStep],
        context_keys: List[str],
    ) -> Tuple[Optional[RouteChainStep], List[str]]:
        routes = _list_routes(self.routes_dir)
        used = {s.route_name for s in existing_steps}
        routes = [r for r in routes if r["name"] not in used]

        if not routes:
            typer.echo(
                "\nNo generated routes found in routes/.\n"
                "Run 'safe route' first to create one."
            )
            return None, []

        typer.echo("\nAvailable routes:")
        for i, r in enumerate(routes, 1):
            tag = f"  [{r['pattern']}]" if r["pattern"] else ""
            typer.echo(f"  {i}. {r['name']}{tag}")

        raw = _safe_input(f"\nSelect route (1-{len(routes)}): ")
        try:
            selected = routes[int(raw) - 1]
        except (ValueError, IndexError):
            typer.echo("Invalid selection.")
            return None, []

        route_name = selected["name"]
        outputs = _extract_fields(self.routes_dir, route_name, "required_output_fields")

        mapping: Dict[str, str] = {}
        pass_through: List[str] = []
        condition: Optional[str] = None

        if existing_steps:
            required_inputs = _extract_fields(
                self.routes_dir, route_name, "required_input_fields"
            )
            if required_inputs:
                mapping, pass_through = await self._ask_field_mapping(
                    route_name, required_inputs, context_keys
                )
            else:
                typer.echo(
                    f"  (Could not read input schema for {route_name} — "
                    "no mapping configured. Edit chain.yaml manually if needed.)"
                )

            raw_cond = _safe_input("\nAdd a run condition? (Python expr or Enter to skip): ")
            condition = raw_cond or None

        step = RouteChainStep(
            route_name=route_name,
            field_mapping=mapping,
            pass_through_fields=pass_through,
            condition=condition,
        )
        typer.echo(f"✓ Added: {route_name}")
        return step, outputs

    async def _create_route_inline(
        self,
        existing_steps: List[RouteChainStep],
        context_keys: List[str],
    ) -> Tuple[Optional[RouteChainStep], List[str]]:
        typer.echo("\nLaunching route wizard...\n")
        from .interview import RouteInterviewer
        from .agent_catalog import AgentCatalog
        from .code_generator import RouteCodeGenerator

        cat = AgentCatalog()
        route_def = await RouteInterviewer(cat).start_interview()
        if route_def is None:
            return None, []

        generated = RouteCodeGenerator.generate(route_def)
        route_dir = self.routes_dir / route_def.name
        generated.save_to_disk(str(route_dir))
        typer.echo(f"✓ Route generated: routes/{route_def.name}/")

        # Derive output fields from the exit agent's output_schema
        exit_agent = list(route_def.agents.values())[-1]
        outputs = list(exit_agent.output_schema.get("properties", {}).keys())

        mapping: Dict[str, str] = {}
        pass_through: List[str] = []
        condition: Optional[str] = None

        if existing_steps:
            entry_agent = list(route_def.agents.values())[0]
            required_inputs = list(entry_agent.input_schema.get("properties", {}).keys())
            if required_inputs:
                mapping, pass_through = await self._ask_field_mapping(
                    route_def.name, required_inputs, context_keys
                )
            raw_cond = _safe_input("\nAdd a run condition? (Enter to skip): ")
            condition = raw_cond or None

        return RouteChainStep(
            route_name=route_def.name,
            field_mapping=mapping,
            pass_through_fields=pass_through,
            condition=condition,
        ), outputs

    # ── field mapping ────────────────────────────────────────────────────

    async def _ask_field_mapping(
        self,
        route_name: str,
        required_inputs: List[str],
        context_keys: List[str],
    ) -> Tuple[Dict[str, str], List[str]]:
        typer.echo(f"\n  Map inputs for '{route_name}':\n")

        mapping: Dict[str, str] = {}
        pass_through: List[str] = []

        auto = [f for f in required_inputs if f in context_keys]
        unmatched = [f for f in required_inputs if f not in context_keys]

        if auto:
            typer.echo("  Auto-matched (same field name):")
            for f in auto:
                typer.echo(f"    ✓ {f}")
            mapping.update({f: f for f in auto})

        for field_name in unmatched:
            typer.echo(f"\n  Required input '{field_name}' — where does it come from?")
            options: List[Any] = list(context_keys)
            for i, k in enumerate(options, 1):
                typer.echo(f"    {i}. {k}  (from previous step output)")
            typer.echo(f"    {len(options) + 1}. original request (pass-through)")

            raw = _safe_input(f"  Source for '{field_name}': ")
            try:
                idx = int(raw) - 1
                if idx == len(options):
                    pass_through.append(field_name)
                elif 0 <= idx < len(options):
                    mapping[field_name] = options[idx]
                else:
                    typer.echo("  Out of range — skipping. Edit chain.yaml manually.")
            except ValueError:
                if raw:
                    mapping[field_name] = raw  # engineer typed a literal key name
                else:
                    typer.echo("  Skipped.")

        return mapping, pass_through

    # ── step 3: options ──────────────────────────────────────────────────

    async def _ask_options(self) -> Tuple[str, bool]:
        typer.echo("\n--- Step 3: Options ---\n")

        raw = _safe_input(
            "On step failure — (h)alt and raise [default] or (s)kip and continue? [h/s]: "
        ).lower()
        on_failure = "skip" if raw == "s" else "halt"

        raw2 = _safe_input(
            "Include _chain_history in context (full input/output trace per step)? [y/N]: "
        ).lower()
        include_history = raw2 == "y"

        return on_failure, include_history

    # ── step 4: timeout ──────────────────────────────────────────────────

    async def _ask_timeout(self, n_steps: int) -> int:
        typer.echo("\n--- Step 4: Timeout ---\n")
        default = n_steps * 60
        typer.echo(f"  Suggested: {default}s  ({n_steps} steps × 60s each)")
        raw = _safe_input(f"  Combined chain timeout in seconds [{default}]: ")
        try:
            return int(raw)
        except ValueError:
            return default

    # ── step 5: review ───────────────────────────────────────────────────

    async def _review(self, chain: RouteChain) -> bool:
        typer.echo("\n--- Step 5: Review ---\n")
        typer.echo(f"  Chain   : {chain.name}")
        typer.echo(f"  Desc    : {chain.description or '(none)'}")
        typer.echo(f"  Steps   : {len(chain.steps)}")
        for i, s in enumerate(chain.steps, 1):
            cond = f"  [if: {s.condition}]" if s.condition else ""
            typer.echo(f"    {i}. {s.route_name}{cond}")
            for dest, src in s.field_mapping.items():
                typer.echo(f"         {dest} ← {src}")
            for f in s.pass_through_fields:
                typer.echo(f"         {f} ← request.{f}")
        typer.echo(f"  Timeout : {chain.timeout_seconds}s")
        typer.echo(f"  Failure : {chain.on_step_failure}")
        typer.echo(f"  History : {'yes' if chain.include_chain_history else 'no'}")
        typer.echo(f"  Email   : {chain.csa_email or '(none)'}\n")

        raw = _safe_input("Generate chain? (y/n): ").lower()
        return raw in ("y", "yes")

    # ── helpers ──────────────────────────────────────────────────────────

    def _chain_summary(self, steps: List[RouteChainStep]) -> str:
        if not steps:
            return "(empty)"
        return " → ".join(s.route_name for s in steps)
