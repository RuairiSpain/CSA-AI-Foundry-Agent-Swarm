"""Agent catalog — loads from catalog.yaml in this package directory."""

import yaml
from pathlib import Path
from typing import List, Optional
from .models import Agent

_CATALOG_PATH = Path(__file__).parent / "catalog.yaml"


def _load_catalog() -> dict[str, Agent]:
    with open(_CATALOG_PATH, "r") as f:
        data = yaml.safe_load(f)

    agents: dict[str, Agent] = {}
    for entry in data.get("agents", []):
        agent = Agent(
            name=entry["name"],
            category=entry["category"],
            version=str(entry.get("version", "1.0")),
            description=entry.get("description", ""),
            input_schema=entry.get("input_schema", {}),
            output_schema=entry.get("output_schema", {}),
        )
        agents[agent.name] = agent
    return agents


class AgentCatalog:
    """Catalog of available agents, loaded from catalog.yaml."""

    def __init__(self) -> None:
        self._agents: dict[str, Agent] = _load_catalog()

    def search_by_name(self, query: str) -> List[Agent]:
        query = query.lower()
        return [a for a in self._agents.values() if query in a.name.lower()]

    def search_by_category(self, category: str) -> List[Agent]:
        return [a for a in self._agents.values() if a.category == category]

    def get_agent(self, name: str) -> Optional[Agent]:
        return self._agents.get(name)

    def list_all(self) -> List[Agent]:
        return list(self._agents.values())
