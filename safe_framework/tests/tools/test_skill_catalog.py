"""Skill catalog integrity tests.

Validates that skills/catalog.yaml is well-formed, every skill has the
required fields, inputs/outputs are properly structured, and IDs are unique.
"""

import pytest
import yaml
from pathlib import Path


SAFE_ROOT = Path(__file__).parents[2]  # safe_framework/
CATALOG_PATH = SAFE_ROOT / "skills" / "catalog.yaml"

REQUIRED_SKILL_FIELDS = {"id", "display_name", "description", "category", "inputs", "outputs"}


@pytest.fixture(scope="module")
def catalog():
    assert CATALOG_PATH.exists(), f"Skills catalog not found at {CATALOG_PATH}"
    with open(CATALOG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def skills(catalog):
    return catalog.get("skills", [])


class TestCatalogStructure:
    def test_catalog_loads(self, catalog):
        assert catalog is not None

    def test_catalog_has_version(self, catalog):
        assert "version" in catalog

    def test_catalog_has_skills_key(self, catalog):
        assert "skills" in catalog

    def test_skills_is_list(self, catalog):
        assert isinstance(catalog["skills"], list)

    def test_at_least_one_skill(self, skills):
        assert len(skills) >= 1


class TestSkillEntries:
    def test_all_skills_have_required_fields(self, skills):
        for skill in skills:
            missing = REQUIRED_SKILL_FIELDS - set(skill.keys())
            assert not missing, f"Skill '{skill.get('id', '?')}' missing fields: {missing}"

    def test_no_duplicate_ids(self, skills):
        ids = [s["id"] for s in skills]
        duplicates = [sid for sid in set(ids) if ids.count(sid) > 1]
        assert duplicates == [], f"Duplicate skill IDs: {duplicates}"

    def test_all_ids_are_kebab_case(self, skills):
        import re
        bad = [s["id"] for s in skills if not re.match(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$", s["id"])]
        assert bad == [], f"Non-kebab-case skill IDs: {bad}"

    def test_all_skills_have_display_name(self, skills):
        missing = [s["id"] for s in skills if not s.get("display_name")]
        assert missing == [], f"Skills missing display_name: {missing}"

    def test_all_skills_have_description(self, skills):
        missing = [s["id"] for s in skills if not s.get("description")]
        assert missing == [], f"Skills missing description: {missing}"

    def test_all_skills_have_category(self, skills):
        missing = [s["id"] for s in skills if not s.get("category")]
        assert missing == [], f"Skills missing category: {missing}"

    def test_all_skills_have_inputs(self, skills):
        missing = [s["id"] for s in skills if not s.get("inputs")]
        assert missing == [], f"Skills missing inputs: {missing}"

    def test_all_skills_have_outputs(self, skills):
        missing = [s["id"] for s in skills if not s.get("outputs")]
        assert missing == [], f"Skills missing outputs: {missing}"

    def test_inputs_are_dicts(self, skills):
        bad = [s["id"] for s in skills if not isinstance(s.get("inputs"), dict)]
        assert bad == [], f"Non-dict inputs in: {bad}"

    def test_outputs_are_dicts(self, skills):
        bad = [s["id"] for s in skills if not isinstance(s.get("outputs"), dict)]
        assert bad == [], f"Non-dict outputs in: {bad}"

    def test_each_input_has_type(self, skills):
        for skill in skills:
            for name, spec in skill.get("inputs", {}).items():
                assert "type" in spec, (
                    f"Skill '{skill['id']}' input '{name}' missing 'type'"
                )

    def test_each_output_has_type(self, skills):
        for skill in skills:
            for name, spec in skill.get("outputs", {}).items():
                assert "type" in spec, (
                    f"Skill '{skill['id']}' output '{name}' missing 'type'"
                )

    def test_known_categories(self, skills):
        allowed = {"NLP", "Text", "Data"}
        unknown = {s["category"] for s in skills} - allowed
        assert not unknown, (
            f"Unknown skill categories {unknown}. "
            "Add them to the allowed set if intentional."
        )

    def test_discovery_block_present(self, skills):
        missing = [s["id"] for s in skills if "discovery" not in s]
        assert missing == [], f"Skills missing 'discovery' block: {missing}"

    def test_quality_ratings_in_range(self, skills):
        bad = [
            s["id"] for s in skills
            if not (0.0 <= s.get("discovery", {}).get("quality_rating", 0) <= 5.0)
        ]
        assert bad == [], f"quality_rating out of 0–5 range: {bad}"
