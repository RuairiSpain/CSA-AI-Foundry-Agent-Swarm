"""Tests for skills/scaffold.py — list_skills, skill_info, create_skill."""

import copy
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

import yaml

SAFE_ROOT = Path(__file__).parent.parent
CATALOG_PATH = SAFE_ROOT / "skills" / "catalog.yaml"


@pytest.fixture(scope="module")
def real_catalog():
    with open(CATALOG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# list_skills
# ---------------------------------------------------------------------------

class TestListSkills:
    def test_returns_all_skills_by_default(self, real_catalog):
        from skills.scaffold import list_skills  # type: ignore[import]
        skills = list_skills()
        assert len(skills) == len(real_catalog["skills"])

    def test_category_filter_nlp(self):
        from skills.scaffold import list_skills  # type: ignore[import]
        nlp = list_skills(category="NLP")
        assert all(s["category"] == "NLP" for s in nlp)
        assert len(nlp) >= 1

    def test_category_filter_text(self):
        from skills.scaffold import list_skills  # type: ignore[import]
        text = list_skills(category="Text")
        assert all(s["category"] == "Text" for s in text)
        assert len(text) >= 1

    def test_category_filter_data(self):
        from skills.scaffold import list_skills  # type: ignore[import]
        data = list_skills(category="Data")
        assert all(s["category"] == "Data" for s in data)
        assert len(data) >= 1

    def test_category_filter_case_insensitive(self):
        from skills.scaffold import list_skills  # type: ignore[import]
        upper = list_skills(category="NLP")
        lower = list_skills(category="nlp")
        assert len(upper) == len(lower)

    def test_unknown_category_returns_empty(self):
        from skills.scaffold import list_skills  # type: ignore[import]
        assert list_skills(category="DoesNotExist") == []


# ---------------------------------------------------------------------------
# skill_info
# ---------------------------------------------------------------------------

class TestSkillInfo:
    def test_known_skill_returns_dict(self):
        from skills.scaffold import skill_info  # type: ignore[import]
        info = skill_info("extract-entities")
        assert info["id"] == "extract-entities"
        assert "inputs" in info
        assert "outputs" in info

    def test_all_catalog_skills_resolvable(self, real_catalog):
        from skills.scaffold import skill_info  # type: ignore[import]
        for skill in real_catalog["skills"]:
            result = skill_info(skill["id"])
            assert result["id"] == skill["id"]

    def test_unknown_skill_raises_value_error(self):
        from skills.scaffold import skill_info  # type: ignore[import]
        with pytest.raises(ValueError, match="not found"):
            skill_info("does-not-exist")

    def test_error_message_lists_available(self):
        from skills.scaffold import skill_info  # type: ignore[import]
        with pytest.raises(ValueError) as exc_info:
            skill_info("nonexistent-skill")
        assert "Available" in str(exc_info.value)


# ---------------------------------------------------------------------------
# known_skill_ids
# ---------------------------------------------------------------------------

class TestKnownSkillIds:
    def test_returns_set(self):
        from skills.scaffold import known_skill_ids  # type: ignore[import]
        ids = known_skill_ids()
        assert isinstance(ids, set)

    def test_contains_expected_skills(self):
        from skills.scaffold import known_skill_ids  # type: ignore[import]
        ids = known_skill_ids()
        assert "extract-entities" in ids
        assert "score-sentiment" in ids
        assert "summarize-text" in ids

    def test_no_duplicates(self, real_catalog):
        from skills.scaffold import known_skill_ids  # type: ignore[import]
        ids = known_skill_ids()
        assert len(ids) == len(real_catalog["skills"])


# ---------------------------------------------------------------------------
# create_skill (writes to disk — use tmp_path + monkeypatching)
# ---------------------------------------------------------------------------

class TestCreateSkill:
    def _make_mock_catalog(self):
        return {
            "version": "1.0",
            "metadata": {"total_skills": 0},
            "skills": [],
        }

    def test_create_adds_to_catalog(self, tmp_path, monkeypatch):
        from skills import scaffold

        tmp_catalog = tmp_path / "catalog.yaml"
        tmp_catalog.write_text(yaml.dump(self._make_mock_catalog()))
        monkeypatch.setattr(scaffold, "_CATALOG_PATH", tmp_catalog)

        result = scaffold.create_skill(
            "my-new-skill", "Data", "A test skill for unit testing"
        )
        assert result["id"] == "my-new-skill"
        assert result["category"] == "Data"
        assert result["description"] == "A test skill for unit testing"

        saved = yaml.safe_load(tmp_catalog.read_text())
        assert any(s["id"] == "my-new-skill" for s in saved["skills"])

    def test_create_updates_metadata_count(self, tmp_path, monkeypatch):
        from skills import scaffold

        tmp_catalog = tmp_path / "catalog.yaml"
        tmp_catalog.write_text(yaml.dump(self._make_mock_catalog()))
        monkeypatch.setattr(scaffold, "_CATALOG_PATH", tmp_catalog)

        scaffold.create_skill("skill-one", "NLP", "First skill")
        scaffold.create_skill("skill-two", "NLP", "Second skill")

        saved = yaml.safe_load(tmp_catalog.read_text())
        assert saved["metadata"]["total_skills"] == 2

    def test_create_invalid_id_raises(self, tmp_path, monkeypatch):
        from skills import scaffold

        tmp_catalog = tmp_path / "catalog.yaml"
        tmp_catalog.write_text(yaml.dump(self._make_mock_catalog()))
        monkeypatch.setattr(scaffold, "_CATALOG_PATH", tmp_catalog)

        with pytest.raises(ValueError, match="lowercase alphanumeric"):
            scaffold.create_skill("Invalid ID!", "Data", "bad id")

    def test_create_duplicate_raises(self, tmp_path, monkeypatch):
        from skills import scaffold

        tmp_catalog = tmp_path / "catalog.yaml"
        tmp_catalog.write_text(yaml.dump(self._make_mock_catalog()))
        monkeypatch.setattr(scaffold, "_CATALOG_PATH", tmp_catalog)

        scaffold.create_skill("dupe-skill", "NLP", "First time")
        with pytest.raises(ValueError, match="already exists"):
            scaffold.create_skill("dupe-skill", "NLP", "Second time")

    def test_create_with_custom_inputs_outputs(self, tmp_path, monkeypatch):
        from skills import scaffold

        tmp_catalog = tmp_path / "catalog.yaml"
        tmp_catalog.write_text(yaml.dump(self._make_mock_catalog()))
        monkeypatch.setattr(scaffold, "_CATALOG_PATH", tmp_catalog)

        inputs = {"query": {"type": "string", "required": True}}
        outputs = {"result": {"type": "object"}}
        result = scaffold.create_skill("custom-skill", "Data", "Custom", inputs, outputs)

        assert result["inputs"] == inputs
        assert result["outputs"] == outputs

    def test_display_name_derived_from_id(self, tmp_path, monkeypatch):
        from skills import scaffold

        tmp_catalog = tmp_path / "catalog.yaml"
        tmp_catalog.write_text(yaml.dump(self._make_mock_catalog()))
        monkeypatch.setattr(scaffold, "_CATALOG_PATH", tmp_catalog)

        result = scaffold.create_skill("score-relevance", "Data", "Scores relevance")
        assert result["display_name"] == "Score Relevance"
