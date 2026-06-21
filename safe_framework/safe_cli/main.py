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
