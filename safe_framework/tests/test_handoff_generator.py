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


# ── _callable_by filtering and max_calls enforcement ──────────────────────────

class TestCallableByFiltering:
    def test_selective_excludes_restricted_candidate(self):
        """candidate_0 allows only 'manager' caller → not registered as a tool for coordinator."""
        h = HandoffDefinition(
            name="sel-filter",
            pattern=HandoffPattern.SELECTIVE,
            sub_agents={
                "coordinator": _sub("coord", "Coordinator"),
                "candidate_0": SubAgent(
                    name="billing", description="billing agent",
                    allowed_callers=["manager"],
                ),
                "candidate_1": _sub("support agent", "Support"),
            },
        )
        result = HandoffCodeGenerator.generate(h)
        # candidate_0 must not be registered as a ConnectedAgentTool
        assert 'self._candidate_tools["candidate_0"]' not in result.handoff_code
        assert 'self._candidate_tools["candidate_1"]' in result.handoff_code

    def test_selective_includes_unrestricted_candidates(self):
        """Empty allowed_callers → both candidates always reachable by coordinator."""
        h = HandoffDefinition(
            name="sel-open",
            pattern=HandoffPattern.SELECTIVE,
            sub_agents={
                "coordinator": _sub("coord"),
                "candidate_0": _sub("billing"),
                "candidate_1": _sub("support"),
            },
        )
        result = HandoffCodeGenerator.generate(h)
        assert "candidate_0" in result.handoff_code
        assert "candidate_1" in result.handoff_code

    def test_selective_includes_coordinator_allowed_candidate(self):
        """candidate explicitly allows coordinator → included."""
        h = HandoffDefinition(
            name="sel-explicit",
            pattern=HandoffPattern.SELECTIVE,
            sub_agents={
                "coordinator": _sub("coord"),
                "candidate_0": SubAgent(
                    name="c0", description="c0", allowed_callers=["coordinator"]
                ),
                "candidate_1": _sub("c1"),
            },
        )
        result = HandoffCodeGenerator.generate(h)
        assert "candidate_0" in result.handoff_code

    def test_hierarchical_excludes_restricted_worker(self):
        """worker_0 restricted to 'supervisor', not reachable by manager → excluded."""
        h = HandoffDefinition(
            name="hier-filter",
            pattern=HandoffPattern.HIERARCHICAL,
            sub_agents={
                "manager": _sub("manager", "Manager"),
                "worker_0": SubAgent(
                    name="w0", description="worker zero",
                    allowed_callers=["supervisor"],
                ),
                "worker_1": _sub("worker one", "Worker1"),
            },
            max_depth=2,
        )
        result = HandoffCodeGenerator.generate(h)
        assert "worker_0" not in result.handoff_code
        assert "worker_1" in result.handoff_code

    def test_selective_max_calls_instruction_injected(self):
        """max_calls > 0 on a candidate → call limit line appears in generated instructions."""
        h = HandoffDefinition(
            name="sel-limited",
            pattern=HandoffPattern.SELECTIVE,
            sub_agents={
                "coordinator": _sub("coord"),
                "candidate_0": SubAgent(name="c0", description="billing", max_calls=2),
                "candidate_1": _sub("support"),
            },
        )
        result = HandoffCodeGenerator.generate(h)
        assert "at most 2 call(s)" in result.handoff_code
        assert "Call limits" in result.handoff_code

    def test_selective_no_max_calls_no_limit_section(self):
        """All candidates have max_calls=0 → call limits section absent."""
        h = HandoffDefinition(
            name="sel-unlimited",
            pattern=HandoffPattern.SELECTIVE,
            sub_agents={
                "coordinator": _sub("coord"),
                "candidate_0": _sub("billing"),
                "candidate_1": _sub("support"),
            },
        )
        result = HandoffCodeGenerator.generate(h)
        assert "Call limits" not in result.handoff_code

    def test_hierarchical_max_calls_instruction_injected(self):
        """max_calls > 0 on a worker → call limit line appears in generated instructions."""
        h = HandoffDefinition(
            name="hier-limited",
            pattern=HandoffPattern.HIERARCHICAL,
            sub_agents={
                "manager": _sub("manager"),
                "worker_0": SubAgent(name="w0", description="worker zero", max_calls=1),
            },
            max_depth=2,
        )
        result = HandoffCodeGenerator.generate(h)
        assert "at most 1 call(s)" in result.handoff_code
        assert "Call limits per worker" in result.handoff_code

    def test_allowed_callers_and_max_calls_roundtrip(self, tmp_path):
        """allowed_callers and max_calls survive a save → load_from_yaml roundtrip."""
        h = HandoffDefinition(
            name="roundtrip-restrict",
            pattern=HandoffPattern.SELECTIVE,
            sub_agents={
                "coordinator": _sub("coord"),
                "candidate_0": SubAgent(
                    name="c0", description="c0",
                    allowed_callers=["coordinator"],
                    max_calls=3,
                ),
                "candidate_1": _sub("c1"),
            },
        )
        saved_dir = HandoffCodeGenerator.save(h, tmp_path)
        loaded = HandoffCodeGenerator.load_from_yaml(saved_dir / "config.yaml")
        assert loaded.sub_agents["candidate_0"].allowed_callers == ["coordinator"]
        assert loaded.sub_agents["candidate_0"].max_calls == 3
        assert loaded.sub_agents["candidate_1"].allowed_callers == []
        assert loaded.sub_agents["candidate_1"].max_calls == 0


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


# ── GeneratedHandoff.save_to_disk ──────────────────────────────────────────────

class TestGeneratedHandoffSaveToDisk:
    """Tests for the save_to_disk method on GeneratedHandoff (handoff_models.py)."""

    def _result(self):
        h = HandoffDefinition(
            name="model-save-test",
            pattern=HandoffPattern.DIRECT,
            sub_agents={"delegate": _sub("specialist", "MySpecialist")},
        )
        return HandoffCodeGenerator.generate(h)

    def test_creates_all_three_files(self, tmp_path):
        result = self._result()
        dest = str(tmp_path / "output")
        result.save_to_disk(dest)
        assert (tmp_path / "output" / "handoff.py").exists()
        assert (tmp_path / "output" / "requirements.txt").exists()
        assert (tmp_path / "output" / "config.yaml").exists()

    def test_creates_parent_directories(self, tmp_path):
        result = self._result()
        deep = str(tmp_path / "a" / "b" / "c")
        result.save_to_disk(deep)
        assert (tmp_path / "a" / "b" / "c" / "handoff.py").exists()

    def test_handoff_py_content_matches(self, tmp_path):
        result = self._result()
        dest = str(tmp_path / "out")
        result.save_to_disk(dest)
        written = (tmp_path / "out" / "handoff.py").read_text()
        assert written == result.handoff_code

    def test_config_yaml_content_matches(self, tmp_path):
        result = self._result()
        dest = str(tmp_path / "out")
        result.save_to_disk(dest)
        written = (tmp_path / "out" / "config.yaml").read_text()
        assert written == result.config_yaml
