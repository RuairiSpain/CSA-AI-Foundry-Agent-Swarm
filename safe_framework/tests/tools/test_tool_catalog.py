"""Tool catalog integrity tests.

Validates that catalog.yaml is well-formed and all agent entries have the
required fields defined by the SAFE agent contract specification.
"""

import pytest
import yaml
from pathlib import Path


SAFE_ROOT = Path(__file__).parents[2]  # safe_framework/
CATALOG_PATH = SAFE_ROOT / "safe_core" / "catalog.yaml"

REQUIRED_AGENT_FIELDS = {"name", "category", "version", "description", "input_schema", "output_schema"}


@pytest.fixture(scope="module")
def catalog():
    assert CATALOG_PATH.exists(), f"Catalog not found at {CATALOG_PATH}"
    with open(CATALOG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


class TestCatalogStructure:
    def test_catalog_loads(self, catalog):
        assert catalog is not None

    def test_catalog_has_version(self, catalog):
        assert "version" in catalog, "catalog.yaml must have a top-level 'version' field"

    def test_catalog_has_agents_key(self, catalog):
        assert "agents" in catalog, "catalog.yaml must have a top-level 'agents' list"

    def test_agents_is_list(self, catalog):
        assert isinstance(catalog["agents"], list), "'agents' must be a list"

    def test_at_least_one_agent(self, catalog):
        assert len(catalog["agents"]) >= 1, "catalog must contain at least one agent"


class TestAgentEntries:
    def test_all_agents_have_name(self, catalog):
        missing = [i for i, a in enumerate(catalog["agents"]) if not a.get("name")]
        assert missing == [], f"Agents at indices {missing} are missing 'name'"

    def test_all_agents_have_category(self, catalog):
        missing = [a["name"] for a in catalog["agents"] if not a.get("category")]
        assert missing == [], f"Agents missing 'category': {missing}"

    def test_all_agents_have_version(self, catalog):
        missing = [a["name"] for a in catalog["agents"] if not a.get("version")]
        assert missing == [], f"Agents missing 'version': {missing}"

    def test_all_agents_have_description(self, catalog):
        missing = [a["name"] for a in catalog["agents"] if not a.get("description")]
        assert missing == [], f"Agents missing 'description': {missing}"

    def test_all_agents_have_input_schema(self, catalog):
        missing = [a["name"] for a in catalog["agents"] if not a.get("input_schema")]
        assert missing == [], f"Agents missing 'input_schema': {missing}"

    def test_all_agents_have_output_schema(self, catalog):
        missing = [a["name"] for a in catalog["agents"] if not a.get("output_schema")]
        assert missing == [], f"Agents missing 'output_schema': {missing}"

    def test_input_schemas_are_objects(self, catalog):
        bad = [
            a["name"] for a in catalog["agents"]
            if not isinstance(a.get("input_schema"), dict)
        ]
        assert bad == [], f"Non-dict input_schema in: {bad}"

    def test_output_schemas_are_objects(self, catalog):
        bad = [
            a["name"] for a in catalog["agents"]
            if not isinstance(a.get("output_schema"), dict)
        ]
        assert bad == [], f"Non-dict output_schema in: {bad}"

    def test_no_duplicate_names(self, catalog):
        names = [a["name"] for a in catalog["agents"]]
        duplicates = [n for n in set(names) if names.count(n) > 1]
        assert duplicates == [], f"Duplicate agent names: {duplicates}"

    def test_input_schemas_have_properties(self, catalog):
        bad = [
            a["name"] for a in catalog["agents"]
            if "properties" not in a.get("input_schema", {})
        ]
        assert bad == [], f"input_schema missing 'properties' in: {bad}"

    def test_output_schemas_have_properties(self, catalog):
        bad = [
            a["name"] for a in catalog["agents"]
            if "properties" not in a.get("output_schema", {})
        ]
        assert bad == [], f"output_schema missing 'properties' in: {bad}"
