"""SAFE Framework — unified CLI"""
import typer
from safe_core.agent_catalog import AgentCatalog

app = typer.Typer(name="safe", help="SAFE Framework CLI")


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
