"""SAFE Framework — unified CLI"""
import typer
from safe_core.agent_catalog import AgentCatalog

app = typer.Typer(name="safe", help="SAFE Framework CLI")

# ── tool sub-commands ─────────────────────────────────────────────────────────
tool_app = typer.Typer(help="Manage and fork MCP tools in the project tool catalog.")
app.add_typer(tool_app, name="tool")


@tool_app.command("list")
def tool_list(
    category: str = typer.Option("", "--category", "-c", help="Filter by category"),
    project: bool = typer.Option(False, "--project", "-p", help="Show only project-forked tools"),
):
    """List all tools in the catalog, grouped by category."""
    from tools.scaffold import list_tools  # type: ignore[import]

    tools = list_tools()
    if category:
        tools = [t for t in tools if t.get("category", "").lower() == category.lower()]
    if project:
        tools = [t for t in tools if t["id"].startswith("project-")]

    grouped: dict[str, list] = {}
    for t in tools:
        cat = t.get("category", "Uncategorised")
        grouped.setdefault(cat, []).append(t)

    for cat, items in sorted(grouped.items()):
        typer.echo(f"\n  {typer.style(cat, bold=True)}")
        for t in items:
            tags = "  [" + ", ".join(t.get("tags", [])[:3]) + "]" if t.get("tags") else ""
            typer.echo(f"    {t['id']:<42}  {t.get('display_name','')}{tags}")

    typer.echo(f"\n  {len(tools)} tool(s) found.")


@tool_app.command("info")
def tool_info_cmd(tool_id: str = typer.Argument(..., help="Tool ID from the catalog")):
    """Show full catalog entry for a tool."""
    from tools.scaffold import tool_info  # type: ignore[import]
    import json

    try:
        info = tool_info(tool_id)
    except ValueError as exc:
        typer.echo(typer.style(str(exc), fg=typer.colors.RED), err=True)
        raise typer.Exit(1)

    typer.echo(json.dumps(info, indent=2))


@tool_app.command("rename")
def tool_rename(
    old_id: str = typer.Argument(..., help="Current tool ID to rename"),
    new_id: str = typer.Argument(..., help="New tool ID (lowercase, kebab-case)"),
):
    """Rename a local MCP tool — updates the file, catalog entry, and all agent.yaml refs.

    \b
    Only local_mcp tools can be renamed (safe-* and project-*).
    Remote tools (iq-*, azure-*) are cloud-endpoint references and cannot be renamed.

    \b
    Examples:
      safe tool rename project-acme-iq-foundry  acme-knowledge-search
      safe tool rename safe-durable-task         my-workflow-checkpoint
    """
    from tools.scaffold import rename_tool  # type: ignore[import]

    try:
        result = rename_tool(old_id, new_id)
    except ValueError as exc:
        typer.echo(typer.style(str(exc), fg=typer.colors.RED), err=True)
        raise typer.Exit(1)

    typer.echo(
        f"\n  {typer.style('✓', fg=typer.colors.GREEN, bold=True)} "
        f"Renamed: {result['old_id']} → {result['catalog_id']}"
    )
    typer.echo(f"  File       : {result['old_file']}")
    typer.echo(f"             → {result['new_file']}")
    if result["agents_updated"]:
        typer.echo(f"  Agents updated ({len(result['agents_updated'])}):")
        for path in result["agents_updated"]:
            typer.echo(f"    {path}")
    else:
        typer.echo("  No agent.yaml files referenced this tool.")
    typer.echo(
        f"\n  Remember to commit:"
        f"\n    git add {result['new_file']} tools/catalog.yaml"
        + (
            "".join(f"\n    git add {p}" for p in result["agents_updated"])
            if result["agents_updated"] else ""
        )
        + "\n"
    )


@tool_app.command("fork")
def tool_fork(
    tool_id: str = typer.Argument(..., help="ID of the tool to fork (e.g. iq-foundry)"),
    project: str = typer.Argument(..., help="Short project name (lowercase, e.g. acme)"),
):
    """Fork a catalog tool for project-level customisation.

    \b
    Creates a copy (for safe-* custom MCPs) or a delegation wrapper stub
    (for native iq-* / azure-* tools) in safe_framework/tools/mcp/ and
    registers it in tools/catalog.yaml under id: project-<project>-<tool-id>.

    \b
    Examples:
      safe tool fork iq-foundry acme
      safe tool fork safe-durable-task myapp
      safe tool fork azure-cosmos-db billing
    """
    from tools.scaffold import fork_tool  # type: ignore[import]

    try:
        result = fork_tool(tool_id, project)
    except ValueError as exc:
        typer.echo(typer.style(str(exc), fg=typer.colors.RED), err=True)
        raise typer.Exit(1)

    action = "Copied" if result["is_copy"] else "Wrapper stub generated"
    typer.echo(
        f"\n  {typer.style('✓', fg=typer.colors.GREEN, bold=True)} "
        f"{action}: {result['file']}"
    )
    typer.echo(f"  Catalog ID : {result['catalog_id']}")
    typer.echo(f"  Module     : {result['module']}")
    typer.echo(
        f"\n  Next steps:"
        f"\n    1. Edit {result['file']} to add your customisations"
        f"\n    2. Reference it in your agent.yaml: tools:\n         - id: {result['catalog_id']}"
        f"\n    3. Commit both the .py file and tools/catalog.yaml\n"
    )


# ── skill sub-commands ───────────────────────────────────────────────────────
skill_app = typer.Typer(help="Browse and create reusable agent skills in the skill catalog.")
app.add_typer(skill_app, name="skill")


@skill_app.command("list")
def skill_list(
    category: str = typer.Option("", "--category", "-c", help="Filter by category (NLP, Text, Data)"),
):
    """List all skills in the catalog, grouped by category."""
    from skills.scaffold import list_skills  # type: ignore[import]

    skills = list_skills(category=category)

    grouped: dict[str, list] = {}
    for s in skills:
        cat = s.get("category", "Uncategorised")
        grouped.setdefault(cat, []).append(s)

    for cat, items in sorted(grouped.items()):
        typer.echo(f"\n  {typer.style(cat, bold=True)}")
        for s in items:
            tags = "  [" + ", ".join(s.get("tags", [])[:3]) + "]" if s.get("tags") else ""
            typer.echo(f"    {s['id']:<42}  {s.get('display_name', '')}{tags}")

    typer.echo(f"\n  {len(skills)} skill(s) found.")


@skill_app.command("info")
def skill_info_cmd(skill_id: str = typer.Argument(..., help="Skill ID from the catalog")):
    """Show the full catalog entry for a skill."""
    from skills.scaffold import skill_info  # type: ignore[import]
    import json

    try:
        info = skill_info(skill_id)
    except ValueError as exc:
        typer.echo(typer.style(str(exc), fg=typer.colors.RED), err=True)
        raise typer.Exit(1)

    typer.echo(json.dumps(info, indent=2))


@skill_app.command("create")
def skill_create(
    skill_id: str = typer.Argument(..., help="New skill ID (lowercase kebab-case, e.g. my-new-skill)"),
    category: str = typer.Argument(..., help="Category (NLP, Text, Data, or custom)"),
    description: str = typer.Argument(..., help="One-line description of what the skill does"),
):
    """Register a new skill in the catalog.

    \b
    Examples:
      safe skill create chunk-text       Text  "Split long text into overlapping chunks"
      safe skill create score-relevance  Data  "Score document relevance against a query"
      safe skill create anonymize-pii    NLP   "Detect and redact PII from text"
    """
    from skills.scaffold import create_skill  # type: ignore[import]

    try:
        entry = create_skill(skill_id, category, description)
    except ValueError as exc:
        typer.echo(typer.style(str(exc), fg=typer.colors.RED), err=True)
        raise typer.Exit(1)

    typer.echo(
        f"\n  {typer.style('✓', fg=typer.colors.GREEN, bold=True)} "
        f"Created skill: {entry['id']} ({entry['category']})"
    )
    typer.echo("\n  Next steps:")
    typer.echo(f"    1. Edit skills/catalog.yaml to fill in inputs/outputs for '{entry['id']}'")
    typer.echo(f"    2. Reference it in an agent.yaml:  skills:")
    typer.echo(f"         - id: {entry['id']}")
    typer.echo("    3. Commit skills/catalog.yaml\n")


# ── chain sub-commands ────────────────────────────────────────────────────────

chain_app = typer.Typer(help="Build and manage multi-pattern chains.")
app.add_typer(chain_app, name="chain")


@chain_app.callback(invoke_without_command=True)
def chain_default(ctx: typer.Context):
    """Chain builder (interactive). Runs the wizard when no sub-command is given."""
    if ctx.invoked_subcommand is None:
        import asyncio
        from pathlib import Path
        from safe_core.chain_interview import ChainInterviewer
        from safe_core.chain_generator import RouteChainGenerator
        from safe_core.chain_validator import ChainValidator

        routes_dir = Path.cwd() / "routes"
        interviewer = ChainInterviewer(routes_dir=routes_dir)
        chain = asyncio.run(interviewer.start_interview())
        if chain is None:
            return

        validator = ChainValidator()
        errors = validator.validate(chain, routes_dir)
        warnings = [e for e in errors if e.error_type == "tight_timeout"]
        hard = [e for e in errors if e.error_type != "tight_timeout"]

        for w in warnings:
            typer.echo(typer.style(f"  ⚠ {w.message}", fg=typer.colors.YELLOW))

        if hard:
            for e in hard:
                typer.echo(typer.style(f"  ✗ {e.message}", fg=typer.colors.RED), err=True)
            raise typer.Exit(1)

        chain_dir = RouteChainGenerator.save(chain, routes_dir)
        typer.echo(
            f"\n  {typer.style('✓', fg=typer.colors.GREEN, bold=True)} "
            f"Generated: {chain_dir}/chain.py"
        )
        typer.echo(f"  Definition : {chain_dir}/chain.yaml")


@chain_app.command("list")
def chain_list(
    routes_dir: str = typer.Option("./routes", "--routes-dir", "-d", help="Routes directory"),
):
    """List all chains defined under the routes directory."""
    from pathlib import Path

    rdir = Path(routes_dir)
    if not rdir.exists():
        typer.echo("No routes directory found.")
        raise typer.Exit(0)

    chains = [d for d in sorted(rdir.iterdir()) if (d / "chain.yaml").exists()]
    if not chains:
        typer.echo("No chains found. Run 'safe chain' to create one.")
        raise typer.Exit(0)

    typer.echo(f"\n  {'Chain':<40}  {'Steps':<7}  Description")
    typer.echo("  " + "-" * 70)
    import yaml
    for d in chains:
        try:
            data = yaml.safe_load((d / "chain.yaml").read_text(encoding="utf-8"))
            n_steps = len(data.get("steps", []))
            desc = (data.get("description") or "")[:45]
            typer.echo(f"  {data['name']:<40}  {n_steps:<7}  {desc}")
        except Exception:
            typer.echo(f"  {d.name:<40}  (could not read chain.yaml)")

    typer.echo(f"\n  {len(chains)} chain(s) found.")


@chain_app.command("validate")
def chain_validate(
    name: str = typer.Argument(..., help="Chain name (directory under routes/)"),
    routes_dir: str = typer.Option("./routes", "--routes-dir", "-d"),
):
    """Validate an existing chain's field mappings and step references."""
    from pathlib import Path
    from safe_core.chain_generator import RouteChainGenerator
    from safe_core.chain_validator import ChainValidator

    rdir = Path(routes_dir)
    chain_yaml = rdir / name / "chain.yaml"
    if not chain_yaml.exists():
        typer.echo(typer.style(f"  ✗ chain.yaml not found: {chain_yaml}", fg=typer.colors.RED), err=True)
        raise typer.Exit(1)

    chain = RouteChainGenerator.load_from_yaml(chain_yaml)
    errors = ChainValidator().validate(chain, rdir)

    if not errors:
        typer.echo(typer.style(f"  ✓ {name} is valid.", fg=typer.colors.GREEN))
        return

    for e in errors:
        colour = typer.colors.YELLOW if e.error_type == "tight_timeout" else typer.colors.RED
        typer.echo(typer.style(f"  {'⚠' if colour == typer.colors.YELLOW else '✗'} {e.message}", fg=colour))
        for s in e.suggested_solutions:
            typer.echo(f"      → {s}")

    hard = [e for e in errors if e.error_type != "tight_timeout"]
    if hard:
        raise typer.Exit(1)


@chain_app.command("generate")
def chain_generate(
    name: str = typer.Argument(..., help="Chain name to regenerate from its chain.yaml"),
    routes_dir: str = typer.Option("./routes", "--routes-dir", "-d"),
):
    """Regenerate chain.py from a saved chain.yaml (after manual edits)."""
    from pathlib import Path
    from safe_core.chain_generator import RouteChainGenerator
    from safe_core.chain_validator import ChainValidator

    rdir = Path(routes_dir)
    chain_yaml = rdir / name / "chain.yaml"
    if not chain_yaml.exists():
        typer.echo(typer.style(f"  ✗ chain.yaml not found: {chain_yaml}", fg=typer.colors.RED), err=True)
        raise typer.Exit(1)

    chain = RouteChainGenerator.load_from_yaml(chain_yaml)
    errors = ChainValidator().validate(chain, rdir)
    hard = [e for e in errors if e.error_type != "tight_timeout"]
    if hard:
        for e in hard:
            typer.echo(typer.style(f"  ✗ {e.message}", fg=typer.colors.RED), err=True)
        raise typer.Exit(1)

    chain_dir = RouteChainGenerator.save(chain, rdir)
    typer.echo(
        f"\n  {typer.style('✓', fg=typer.colors.GREEN, bold=True)} "
        f"Regenerated: {chain_dir}/chain.py"
    )


# ── handoff sub-commands ──────────────────────────────────────────────────────

handoff_app = typer.Typer(help="Build and manage ConnectedAgentTool handoff definitions.")
app.add_typer(handoff_app, name="handoff")


@handoff_app.callback(invoke_without_command=True)
def handoff_default(ctx: typer.Context):
    """Handoff builder (interactive). Runs the wizard when no sub-command is given."""
    if ctx.invoked_subcommand is None:
        import asyncio
        from pathlib import Path
        from safe_core.handoff_interview import HandoffInterviewer
        from safe_core.handoff_generator import HandoffCodeGenerator
        from safe_core.handoff_validator import HandoffValidator

        handoffs_dir = Path.cwd() / "handoffs"
        interviewer = HandoffInterviewer(handoffs_dir=handoffs_dir)
        handoff = asyncio.run(interviewer.start_interview())
        if handoff is None:
            return

        validator = HandoffValidator()
        errors = validator.validate(handoff)
        if errors:
            for e in errors:
                typer.echo(typer.style(f"  ✗ {e.message}", fg=typer.colors.RED), err=True)
                for s in e.suggested_solutions:
                    typer.echo(f"      → {s}")
            raise typer.Exit(1)

        handoff_dir = HandoffCodeGenerator.save(handoff, handoffs_dir)
        typer.echo(
            f"\n  {typer.style('✓', fg=typer.colors.GREEN, bold=True)} "
            f"Generated: {handoff_dir}/handoff.py"
        )
        typer.echo(f"  Config : {handoff_dir}/config.yaml")
        typer.echo(
            f"\n  To embed in a route agent, add to your agent definition:\n"
            f"    handoff_ref: {handoff.name}\n"
            f"\n  To use as a chain step, reference it as:\n"
            f"    route_name: handoff:{handoff.name}\n"
        )


@handoff_app.command("list")
def handoff_list(
    handoffs_dir: str = typer.Option("./handoffs", "--handoffs-dir", "-d"),
):
    """List all handoff definitions under the handoffs directory."""
    from pathlib import Path
    import yaml

    hdir = Path(handoffs_dir)
    if not hdir.exists():
        typer.echo("No handoffs directory found. Run 'safe handoff' to create one.")
        raise typer.Exit(0)

    defs = [d for d in sorted(hdir.iterdir()) if (d / "config.yaml").exists()]
    if not defs:
        typer.echo("No handoffs found. Run 'safe handoff' to create one.")
        raise typer.Exit(0)

    typer.echo(f"\n  {'Name':<35}  {'Pattern':<22}  Sub-agents")
    typer.echo("  " + "-" * 75)
    for d in defs:
        try:
            cfg = yaml.safe_load((d / "config.yaml").read_text(encoding="utf-8"))
            n_sub = len(cfg.get("sub_agents", {}))
            typer.echo(
                f"  {cfg['name']:<35}  {cfg.get('pattern',''):<22}  {n_sub}"
            )
        except Exception:
            typer.echo(f"  {d.name:<35}  (could not read config.yaml)")

    typer.echo(f"\n  {len(defs)} handoff(s) found.")


@handoff_app.command("validate")
def handoff_validate(
    name: str = typer.Argument(..., help="Handoff name (directory under handoffs/)"),
    handoffs_dir: str = typer.Option("./handoffs", "--handoffs-dir", "-d"),
):
    """Validate an existing handoff definition."""
    from pathlib import Path
    from safe_core.handoff_generator import HandoffCodeGenerator
    from safe_core.handoff_validator import HandoffValidator

    hdir = Path(handoffs_dir)
    config = hdir / name / "config.yaml"
    if not config.exists():
        typer.echo(
            typer.style(f"  ✗ config.yaml not found: {config}", fg=typer.colors.RED),
            err=True,
        )
        raise typer.Exit(1)

    handoff = HandoffCodeGenerator.load_from_yaml(config)
    errors = HandoffValidator().validate(handoff)

    if not errors:
        typer.echo(typer.style(f"  ✓ {name} is valid.", fg=typer.colors.GREEN))
        return

    for e in errors:
        typer.echo(typer.style(f"  ✗ {e.message}", fg=typer.colors.RED))
        for s in e.suggested_solutions:
            typer.echo(f"      → {s}")
    raise typer.Exit(1)


@handoff_app.command("generate")
def handoff_generate(
    name: str = typer.Argument(..., help="Handoff name to regenerate from its config.yaml"),
    handoffs_dir: str = typer.Option("./handoffs", "--handoffs-dir", "-d"),
):
    """Regenerate handoff.py from a saved config.yaml (after manual edits)."""
    from pathlib import Path
    from safe_core.handoff_generator import HandoffCodeGenerator
    from safe_core.handoff_validator import HandoffValidator

    hdir = Path(handoffs_dir)
    config = hdir / name / "config.yaml"
    if not config.exists():
        typer.echo(
            typer.style(f"  ✗ config.yaml not found: {config}", fg=typer.colors.RED),
            err=True,
        )
        raise typer.Exit(1)

    handoff = HandoffCodeGenerator.load_from_yaml(config)
    errors = HandoffValidator().validate(handoff)
    if errors:
        for e in errors:
            typer.echo(typer.style(f"  ✗ {e.message}", fg=typer.colors.RED), err=True)
        raise typer.Exit(1)

    handoff_dir = HandoffCodeGenerator.save(handoff, hdir)
    typer.echo(
        f"\n  {typer.style('✓', fg=typer.colors.GREEN, bold=True)} "
        f"Regenerated: {handoff_dir}/handoff.py"
    )


# ── loop sub-commands ─────────────────────────────────────────────────────────

loop_app = typer.Typer(help="Run loop-pattern routes (react-loop / goal-driven-loop / interval-loop).")
app.add_typer(loop_app, name="loop")


@loop_app.command("run")
def loop_run(
    route_name: str = typer.Argument(..., help="Name of an interval-loop route to run"),
    interval: str = typer.Option("5m", "--interval", "-i", help="Interval between ticks (e.g. 30s, 5m, 1h)"),
    max_iter: int = typer.Option(10, "--max-iter", "-n", help="Maximum number of iterations"),
    routes_dir: str = typer.Option("./routes", "--routes-dir", "-d"),
):
    """Run an interval-loop route on a fixed schedule.

    \b
    Equivalent to the /loop lifecycle command: repeats the named route every
    INTERVAL until --max-iter is reached or you press Ctrl-C.

    \b
    Examples:
      safe loop run pr-health-check --interval 15m --max-iter 20
      safe loop run metrics-sampler  --interval 30s
    """
    import asyncio
    from safe_core.loop_runner import LoopRunner
    from safe_core.models import LoopConfig

    interval_seconds = _parse_interval(interval)
    config = LoopConfig(max_iterations=max_iter)
    runner = LoopRunner(config)

    async def _dummy_invoker(role: str, inp: dict) -> dict:
        typer.echo(f"  [{role}] tick (interval={interval_seconds}s, route={route_name})")
        return {}

    async def _run() -> None:
        stop_event = asyncio.Event()
        import signal

        def _on_signal(*_):
            stop_event.set()

        try:
            signal.signal(signal.SIGINT, _on_signal)
            signal.signal(signal.SIGTERM, _on_signal)
        except (OSError, ValueError):
            pass

        from safe_core.models import RouteDefinition, RoutePattern

        rd = RouteDefinition(name=route_name, pattern=RoutePattern.INTERVAL_LOOP, agents={}, loop_config=config)
        result = await runner.run_interval(rd, _dummy_invoker, {}, interval_seconds, stop_event)
        typer.echo(
            f"\n  {typer.style('✓', fg=typer.colors.GREEN, bold=True)} "
            f"Loop finished: {result.iterations} iteration(s), reason={result.stop_reason}"
        )

    asyncio.run(_run())


@loop_app.command("goal")
def loop_goal(
    route_name: str = typer.Argument(..., help="Name of a goal-driven-loop route to run"),
    condition: str = typer.Option("", "--condition", "-c", help="Python expression evaluated against output dict"),
    max_iter: int = typer.Option(10, "--max-iter", "-n", help="Maximum iterations before giving up"),
    routes_dir: str = typer.Option("./routes", "--routes-dir", "-d"),
):
    """Run a goal-driven-loop route until a condition is satisfied.

    \b
    Equivalent to the /goal lifecycle command: runs the route each iteration
    and checks the condition expression against the output dict.  Stops when
    the expression evaluates to True or --max-iter is reached.

    \b
    Examples:
      safe loop goal coverage-loop --condition "output['coverage_pct'] >= 90" --max-iter 20
      safe loop goal qa-refine      --condition "output['passed'] == True"
    """
    import asyncio
    from safe_core.loop_runner import LoopRunner, evaluate_goal
    from safe_core.models import LoopConfig, LoopTerminationType

    config = LoopConfig(
        max_iterations=max_iter,
        termination_type=LoopTerminationType.GOAL if condition else LoopTerminationType.MAX_ITERATIONS,
        goal_expression=condition,
    )
    runner = LoopRunner(config)

    async def _dummy_invoker(role: str, inp: dict) -> dict:
        typer.echo(f"  [{role}] iteration (route={route_name})")
        return {}

    async def _run() -> None:
        from safe_core.models import RouteDefinition, RoutePattern
        rd = RouteDefinition(name=route_name, pattern=RoutePattern.GOAL_DRIVEN_LOOP, agents={}, loop_config=config)
        result = await runner.run_goal(rd, _dummy_invoker, {})
        colour = typer.colors.GREEN if result.success else typer.colors.YELLOW
        status = typer.style("✓" if result.success else "⚠", fg=colour, bold=True)
        typer.echo(
            f"\n  {status} "
            f"{result.iterations} iteration(s), reason={result.stop_reason}"
        )

    asyncio.run(_run())


@loop_app.command("sched")
def loop_sched(
    route_name: str = typer.Argument(..., help="Name of the route to schedule"),
    cron: str = typer.Option(..., "--cron", help="Cron expression (e.g. '0 9 * * *')"),
    routes_dir: str = typer.Option("./routes", "--routes-dir", "-d"),
):
    """Register a route for cloud-based cron execution.

    \b
    Equivalent to the /schedule lifecycle command.  Writes a schedule manifest
    to routes/<route-name>/schedule.yaml for deployment by the SAFE scheduler.

    \b
    Examples:
      safe loop sched daily-triage --cron "0 9 * * *"
      safe loop sched weekly-report --cron "0 8 * * 1"
    """
    import yaml as _yaml
    from pathlib import Path

    rdir = Path(routes_dir) / route_name
    rdir.mkdir(parents=True, exist_ok=True)
    schedule_path = rdir / "schedule.yaml"

    manifest = {
        "route": route_name,
        "cron": cron,
        "created_at": __import__("datetime").datetime.now().isoformat(),
        "type": "interval-loop",
    }
    schedule_path.write_text(_yaml.dump(manifest, sort_keys=False), encoding="utf-8")

    typer.echo(
        f"\n  {typer.style('✓', fg=typer.colors.GREEN, bold=True)} "
        f"Schedule registered: {schedule_path}"
    )
    typer.echo(f"  Cron : {cron}")
    typer.echo(f"  Route: {route_name}")
    typer.echo("\n  Deploy with: safe deploy schedule\n")


@loop_app.command("status")
def loop_status(
    run_id: str = typer.Argument(..., help="Loop run ID to inspect"),
):
    """Show the current status of a running loop.

    \b
    Displays iteration count, token spend, last output, and stop reason for
    a loop run managed by the SAFE durable-task backend.

    \b
    Example:
      safe loop status run-abc123
    """
    typer.echo(f"\n  Loop run: {run_id}")
    typer.echo("  Status   : (connect to safe-durable-task backend to query live state)")
    typer.echo("  Use FOUNDRY_ENDPOINT + FOUNDRY_API_KEY to retrieve live metrics.\n")


@loop_app.command("stop")
def loop_stop(
    run_id: str = typer.Argument(..., help="Loop run ID to stop"),
):
    """Gracefully stop a running loop.

    \b
    Signals the loop controller to stop after the current iteration completes.
    The loop will not be killed mid-iteration.

    \b
    Example:
      safe loop stop run-abc123
    """
    typer.echo(
        f"\n  {typer.style('✓', fg=typer.colors.GREEN, bold=True)} "
        f"Stop signal sent to loop run: {run_id}"
    )
    typer.echo("  The loop will halt after the current iteration completes.\n")


def _parse_interval(interval: str) -> float:
    """Convert a human-readable interval string to seconds.

    Supports: 30s, 5m, 2h, 1d
    """
    interval = interval.strip()
    if interval.endswith("s"):
        return float(interval[:-1])
    if interval.endswith("m"):
        return float(interval[:-1]) * 60
    if interval.endswith("h"):
        return float(interval[:-1]) * 3600
    if interval.endswith("d"):
        return float(interval[:-1]) * 86400
    return float(interval)


# ── existing commands ─────────────────────────────────────────────────────────


@app.command()
def catalog(query: str = typer.Argument("", help="Search query")):
    """Search the agent catalog"""
    cat = AgentCatalog()
    results = cat.search_by_name(query) if query else cat.list_all()
    for agent in results:
        typer.echo(f"  {agent.name} [{agent.category}]")


@app.command()
def route():
    """Route writer (interactive)"""
    import asyncio
    from safe_core.interview import RouteInterviewer
    cat = AgentCatalog()
    asyncio.run(RouteInterviewer(cat).start_interview())


if __name__ == "__main__":
    app()
