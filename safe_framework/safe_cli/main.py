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
