"""Tests for HandoffCodeGenerator — template rendering and config serialisation."""
import pytest
import yaml

from safe_core.handoff_models import HandoffDefinition, HandoffPattern, SubAgent
from safe_core.handoff_generator import HandoffCodeGenerator, _class_name


def _sub(desc: str = "test", name: str = "agent") -> SubAgent:
    return SubAgent(name=name, description=desc)


# ── _class_name helper ─────────────────────────────────────────────────────────

class TestClassNameHelper:
    def test_kebab(self):
        assert _class_name("direct-handoff") == "DirectHandoff"

    def test_snake(self):
        assert _class_name("my_selective_handoff") == "MySelectiveHandoff"

    def test_single_word(self):
        assert _class_name("recursive") == "Recursive"


# ── direct-handoff generation ──────────────────────────────────────────────────

class TestDirectHandoffGeneration:
    def _handoff(self):
        return HandoffDefinition(
            name="my-direct",
            pattern=HandoffPattern.DIRECT,
            sub_agents={"delegate": _sub("specialist", "MySpecialist")},
            description="Delegates everything to one specialist",
        )

    def test_generates_handoff_code(self):
        result = HandoffCodeGenerator.generate(self._handoff())
        assert "class MyDirectHandoff" in result.handoff_code

    def test_contains_connected_agent_tool(self):
        result = HandoffCodeGenerator.generate(self._handoff())
        assert "ConnectedAgentTool" in result.handoff_code

    def test_contains_pattern_comment(self):
        result = HandoffCodeGenerator.generate(self._handoff())
        assert "direct-handoff" in result.handoff_code

    def test_config_yaml_roundtrip(self):
        result = HandoffCodeGenerator.generate(self._handoff())
        cfg = yaml.safe_load(result.config_yaml)
        assert cfg["name"] == "my-direct"
        assert cfg["pattern"] == "direct-handoff"
        assert "delegate" in cfg["sub_agents"]

    def test_requirements_contains_azure(self):
        result = HandoffCodeGenerator.generate(self._handoff())
        assert "azure-ai-projects" in result.requirements_txt

    def test_metadata_keys(self):
        result = HandoffCodeGenerator.generate(self._handoff())
        assert result.metadata["pattern"] == "direct-handoff"
        assert "delegate" in result.metadata["sub_agents"]


# ── selective-handoff generation ───────────────────────────────────────────────

class TestSelectiveHandoffGeneration:
    def _handoff(self):
        return HandoffDefinition(
            name="my-selective",
            pattern=HandoffPattern.SELECTIVE,
            sub_agents={
                "coordinator": _sub("picks best candidate", "Coordinator"),
                "candidate_0": _sub("billing specialist", "Billing"),
                "candidate_1": _sub("tech support specialist", "Support"),
            },
        )

    def test_generates_class(self):
        result = HandoffCodeGenerator.generate(self._handoff())
        assert "class MySelectiveHandoff" in result.handoff_code

    def test_all_candidates_in_code(self):
        result = HandoffCodeGenerator.generate(self._handoff())
        assert "candidate_0" in result.handoff_code
        assert "candidate_1" in result.handoff_code

    def test_coordinator_tool_setup(self):
        result = HandoffCodeGenerator.generate(self._handoff())
        assert "ConnectedAgentTool" in result.handoff_code


# ── sequential-handoff generation ─────────────────────────────────────────────

class TestSequentialHandoffGeneration:
    def _handoff(self):
        return HandoffDefinition(
            name="my-sequential",
            pattern=HandoffPattern.SEQUENTIAL,
            sub_agents={
                "stage_0": _sub("first stage", "FirstStage"),
                "stage_1": _sub("second stage", "SecondStage"),
            },
        )

    def test_generates_class(self):
        result = HandoffCodeGenerator.generate(self._handoff())
        assert "class MySequentialHandoff" in result.handoff_code

    def test_both_stages_present(self):
        result = HandoffCodeGenerator.generate(self._handoff())
        assert "stage_0" in result.handoff_code
        assert "stage_1" in result.handoff_code

    def test_stage_outputs_tracked(self):
        result = HandoffCodeGenerator.generate(self._handoff())
        assert "stage_outputs" in result.handoff_code


# ── hierarchical-handoff generation ───────────────────────────────────────────

class TestHierarchicalHandoffGeneration:
    def _handoff(self):
        return HandoffDefinition(
            name="my-hierarchical",
            pattern=HandoffPattern.HIERARCHICAL,
            sub_agents={
                "manager": _sub("manager agent", "Manager"),
                "worker_0": _sub("worker one", "Worker0"),
                "worker_1": _sub("worker two", "Worker1"),
            },
            max_depth=2,
        )

    def test_generates_class(self):
        result = HandoffCodeGenerator.generate(self._handoff())
        assert "class MyHierarchicalHandoff" in result.handoff_code

    def test_max_depth_in_code(self):
        result = HandoffCodeGenerator.generate(self._handoff())
        assert "self._max_depth = 2" in result.handoff_code

    def test_workers_registered(self):
        result = HandoffCodeGenerator.generate(self._handoff())
        assert "worker_0" in result.handoff_code
        assert "worker_1" in result.handoff_code


# ── recursive-handoff generation ──────────────────────────────────────────────

class TestRecursiveHandoffGeneration:
    def _handoff(self):
        return HandoffDefinition(
            name="my-recursive",
            pattern=HandoffPattern.RECURSIVE,
            sub_agents={"agent": _sub("recursive processor", "RecAgent")},
            max_depth=4,
        )

    def test_generates_class(self):
        result = HandoffCodeGenerator.generate(self._handoff())
        assert "class MyRecursiveHandoff" in result.handoff_code

    def test_max_depth_in_code(self):
        result = HandoffCodeGenerator.generate(self._handoff())
        assert "self._max_depth = 4" in result.handoff_code

    def test_depth_guard_present(self):
        result = HandoffCodeGenerator.generate(self._handoff())
        assert "_depth >= self._max_depth" in result.handoff_code


# ── load_from_yaml roundtrip ───────────────────────────────────────────────────

class TestLoadFromYaml:
    def test_roundtrip(self, tmp_path):
        original = HandoffDefinition(
            name="round-trip-test",
            pattern=HandoffPattern.SELECTIVE,
            sub_agents={
                "coordinator": _sub("coordinator", "Coord"),
                "candidate_0": _sub("cand0", "C0"),
                "candidate_1": _sub("cand1", "C1"),
            },
            max_depth=2,
            return_policy="on_partial",
            timeout_seconds=90,
            csa_email="test@example.com",
            tags=["test"],
        )
        saved_dir = HandoffCodeGenerator.save(original, tmp_path)
        loaded = HandoffCodeGenerator.load_from_yaml(saved_dir / "config.yaml")

        assert loaded.name == original.name
        assert loaded.pattern == original.pattern
        assert set(loaded.sub_agents.keys()) == set(original.sub_agents.keys())
        assert loaded.max_depth == original.max_depth
        assert loaded.return_policy == original.return_policy
        assert loaded.timeout_seconds == original.timeout_seconds
        assert loaded.csa_email == original.csa_email


# ── save_to_disk ───────────────────────────────────────────────────────────────

class TestSaveToDisk:
    def test_creates_expected_files(self, tmp_path):
        h = HandoffDefinition(
            name="disk-test",
            pattern=HandoffPattern.DIRECT,
            sub_agents={"delegate": _sub()},
        )
        HandoffCodeGenerator.save(h, tmp_path)
        handoff_dir = tmp_path / "disk-test"
        assert (handoff_dir / "handoff.py").exists()
        assert (handoff_dir / "config.yaml").exists()
        assert (handoff_dir / "requirements.txt").exists()
