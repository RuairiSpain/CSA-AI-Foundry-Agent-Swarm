"""
safe skill scaffold — browse and create agent skills in the skill catalog.

Usage (via CLI):
    safe skill list   [--category]
    safe skill info   <skill-id>
    safe skill create <skill-id> <category> <description>

Skills are reusable, atomic operations (e.g. extract-entities, score-sentiment)
that agents declare in their agent.yaml under a 'skills:' key.  They sit above
MCP tools (infrastructure) and below full agent definitions (orchestration).

skill catalog lives at: safe_framework/skills/catalog.yaml
"""

from __future__ import annotations

import functools
import re
from pathlib import Path
from typing import Any

import yaml

_SKILLS_DIR = Path(__file__).parent
_CATALOG_PATH = _SKILLS_DIR / "catalog.yaml"

_VALID_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$")


def _load_catalog() -> dict[str, Any]:
    with _CATALOG_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _save_catalog(catalog: dict[str, Any]) -> None:
    with _CATALOG_PATH.open("w", encoding="utf-8") as f:
        # PyYAML does not preserve comments; section comments must be re-added manually after this write.
        yaml.dump(catalog, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
    known_skill_ids.cache_clear()


def _find_skill(catalog: dict[str, Any], skill_id: str) -> dict[str, Any] | None:
    return next((s for s in catalog.get("skills", []) if s["id"] == skill_id), None)


def list_skills(category: str = "") -> list[dict[str, Any]]:
    """Return all skills from the catalog, optionally filtered by category."""
    catalog = _load_catalog()
    skills = catalog.get("skills", [])
    if category:
        skills = [s for s in skills if s.get("category", "").lower() == category.lower()]
    return skills


def skill_info(skill_id: str) -> dict[str, Any]:
    """Return the full catalog entry for a skill.

    Raises ValueError if the skill ID is not found.
    """
    catalog = _load_catalog()
    skill = _find_skill(catalog, skill_id)
    if skill is None:
        available = [s["id"] for s in catalog.get("skills", [])]
        raise ValueError(
            f"Skill '{skill_id}' not found in catalog.\nAvailable: {', '.join(available)}"
        )
    return skill


def create_skill(
    skill_id: str,
    category: str,
    description: str,
    inputs: dict[str, Any] | None = None,
    outputs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Add a new skill entry to the catalog and return it.

    skill_id must be lowercase kebab-case (e.g. my-new-skill).
    Raises ValueError if the ID already exists or is invalid.
    """
    skill_id = skill_id.strip().lower()
    if not _VALID_ID_RE.match(skill_id):
        raise ValueError(
            f"skill-id '{skill_id}' must be lowercase alphanumeric with hyphens "
            "(e.g. my-new-skill). Must start and end with a letter or digit."
        )

    catalog = _load_catalog()
    if _find_skill(catalog, skill_id):
        raise ValueError(
            f"Skill '{skill_id}' already exists in catalog. "
            "Choose a different ID or edit the catalog directly."
        )

    display_name = " ".join(w.capitalize() for w in skill_id.split("-"))
    new_skill: dict[str, Any] = {
        "id": skill_id,
        "display_name": display_name,
        "description": description.strip(),
        "category": category.strip(),
        "tags": [skill_id, category.lower().replace(" ", "-")],
        "inputs": inputs or {
            "input":  {"type": "object", "description": "Input data", "required": True}
        },
        "outputs": outputs or {
            "output": {"type": "object", "description": "Output data"}
        },
        "discovery": {
            "keywords": skill_id.split("-"),
            "complexity": "simple",
            "quality_rating": 0.0,
            "usage_count": 0,
        },
    }

    catalog.setdefault("skills", []).append(new_skill)
    if "metadata" in catalog:
        catalog["metadata"]["total_skills"] = len(catalog["skills"])
    _save_catalog(catalog)
    return new_skill


@functools.lru_cache(maxsize=1)
def known_skill_ids() -> set[str]:
    """Return the set of all skill IDs in the catalog — used by validators."""
    catalog = _load_catalog()
    return {s["id"] for s in catalog.get("skills", [])}
