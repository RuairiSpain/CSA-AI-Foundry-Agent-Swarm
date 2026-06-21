"""Tests for HandoffValidator — pattern-specific structural rules."""
import pytest

from safe_core.handoff_models import HandoffDefinition, HandoffPattern, SubAgent
from safe_core.handoff_validator import HandoffValidator


def _sub(description: str = "test sub-agent", name: str = "agent") -> SubAgent:
    return SubAgent(name=name, description=description)


def _errors(handoff: HandoffDefinition):
    return [e.error_type for e in HandoffValidator().validate(handoff)]


# ── common checks ──────────────────────────────────────────────────────────────

class TestCommonValidation:
    def test_empty_pool_rejected(self):
        h = HandoffDefinition(
            name="x", pattern=HandoffPattern.DIRECT, sub_agents={}
        )
        assert "empty_pool" in _errors(h)

    def test_invalid_return_policy(self):
        h = HandoffDefinition(
            name="x",
            pattern=HandoffPattern.DIRECT,
            sub_agents={"delegate": _sub()},
            return_policy="maybe",
        )
        assert "invalid_return_policy" in _errors(h)

    def test_valid_return_policies(self):
        for policy in ("always", "on_partial", "on_failure"):
            h = HandoffDefinition(
                name="x",
                pattern=HandoffPattern.DIRECT,
                sub_agents={"delegate": _sub()},
                return_policy=policy,
            )
            assert "invalid_return_policy" not in _errors(h)

    def test_max_depth_zero_rejected(self):
        h = HandoffDefinition(
            name="x",
            pattern=HandoffPattern.DIRECT,
            sub_agents={"delegate": _sub()},
            max_depth=0,
        )
        assert "invalid_max_depth" in _errors(h)

    def test_timeout_too_low(self):
        h = HandoffDefinition(
            name="x",
            pattern=HandoffPattern.DIRECT,
            sub_agents={"delegate": _sub()},
            timeout_seconds=5,
        )
        assert "timeout_too_low" in _errors(h)


# ── direct-handoff ─────────────────────────────────────────────────────────────

class TestDirectHandoff:
    def test_valid(self):
        h = HandoffDefinition(
            name="my-handoff",
            pattern=HandoffPattern.DIRECT,
            sub_agents={"delegate": _sub()},
        )
        assert _errors(h) == []

    def test_missing_delegate_key(self):
        h = HandoffDefinition(
            name="my-handoff",
            pattern=HandoffPattern.DIRECT,
            sub_agents={"specialist": _sub()},
        )
        assert "missing_sub_agent" in _errors(h)

    def test_too_many_sub_agents(self):
        h = HandoffDefinition(
            name="my-handoff",
            pattern=HandoffPattern.DIRECT,
            sub_agents={"delegate": _sub(), "extra": _sub()},
        )
        assert "too_many_sub_agents" in _errors(h)

    def test_validate_or_raise_passes(self):
        h = HandoffDefinition(
            name="ok", pattern=HandoffPattern.DIRECT, sub_agents={"delegate": _sub()}
        )
        HandoffValidator().validate_or_raise(h)  # should not raise

    def test_validate_or_raise_fails(self):
        h = HandoffDefinition(
            name="bad", pattern=HandoffPattern.DIRECT, sub_agents={}
        )
        with pytest.raises(ValueError, match="at least one sub-agent"):
            HandoffValidator().validate_or_raise(h)


# ── selective-handoff ──────────────────────────────────────────────────────────

class TestSelectiveHandoff:
    def _valid(self):
        return HandoffDefinition(
            name="sel",
            pattern=HandoffPattern.SELECTIVE,
            sub_agents={
                "coordinator": _sub("routes to best candidate", "coordinator"),
                "candidate_0": _sub("handles billing queries", "billing"),
                "candidate_1": _sub("handles tech support", "support"),
            },
        )

    def test_valid(self):
        assert _errors(self._valid()) == []

    def test_missing_coordinator(self):
        h = HandoffDefinition(
            name="sel",
            pattern=HandoffPattern.SELECTIVE,
            sub_agents={
                "candidate_0": _sub(),
                "candidate_1": _sub(),
            },
        )
        assert "missing_sub_agent" in _errors(h)

    def test_only_one_candidate(self):
        h = HandoffDefinition(
            name="sel",
            pattern=HandoffPattern.SELECTIVE,
            sub_agents={
                "coordinator": _sub(),
                "candidate_0": _sub(),
            },
        )
        assert "insufficient_candidates" in _errors(h)


# ── sequential-handoff ─────────────────────────────────────────────────────────

class TestSequentialHandoff:
    def _valid(self):
        return HandoffDefinition(
            name="seq",
            pattern=HandoffPattern.SEQUENTIAL,
            sub_agents={
                "stage_0": _sub("first pass"),
                "stage_1": _sub("second pass"),
            },
        )

    def test_valid(self):
        assert _errors(self._valid()) == []

    def test_one_stage_rejected(self):
        h = HandoffDefinition(
            name="seq",
            pattern=HandoffPattern.SEQUENTIAL,
            sub_agents={"stage_0": _sub()},
        )
        assert "insufficient_stages" in _errors(h)

    def test_three_stages_valid(self):
        h = HandoffDefinition(
            name="seq",
            pattern=HandoffPattern.SEQUENTIAL,
            sub_agents={
                "stage_0": _sub(),
                "stage_1": _sub(),
                "stage_2": _sub(),
            },
        )
        assert _errors(h) == []


# ── hierarchical-handoff ───────────────────────────────────────────────────────

class TestHierarchicalHandoff:
    def _valid(self):
        return HandoffDefinition(
            name="hier",
            pattern=HandoffPattern.HIERARCHICAL,
            sub_agents={
                "manager": _sub("manages workers"),
                "worker_0": _sub("handles subtask A"),
            },
            max_depth=2,
        )

    def test_valid(self):
        assert _errors(self._valid()) == []

    def test_missing_manager(self):
        h = HandoffDefinition(
            name="hier",
            pattern=HandoffPattern.HIERARCHICAL,
            sub_agents={"worker_0": _sub()},
            max_depth=2,
        )
        assert "missing_sub_agent" in _errors(h)

    def test_no_workers(self):
        h = HandoffDefinition(
            name="hier",
            pattern=HandoffPattern.HIERARCHICAL,
            sub_agents={"manager": _sub()},
            max_depth=2,
        )
        assert "missing_sub_agent" in _errors(h)

    def test_shallow_depth_warning(self):
        h = HandoffDefinition(
            name="hier",
            pattern=HandoffPattern.HIERARCHICAL,
            sub_agents={"manager": _sub(), "worker_0": _sub()},
            max_depth=1,
        )
        assert "shallow_hierarchy" in _errors(h)


# ── recursive-handoff ──────────────────────────────────────────────────────────

class TestRecursiveHandoff:
    def _valid(self):
        return HandoffDefinition(
            name="rec",
            pattern=HandoffPattern.RECURSIVE,
            sub_agents={"agent": _sub("recursive processor")},
            max_depth=3,
        )

    def test_valid(self):
        assert _errors(self._valid()) == []

    def test_missing_agent_key(self):
        h = HandoffDefinition(
            name="rec",
            pattern=HandoffPattern.RECURSIVE,
            sub_agents={"worker": _sub()},
        )
        assert "missing_sub_agent" in _errors(h)

    def test_depth_too_high(self):
        h = HandoffDefinition(
            name="rec",
            pattern=HandoffPattern.RECURSIVE,
            sub_agents={"agent": _sub()},
            max_depth=11,
        )
        assert "depth_too_high" in _errors(h)

    def test_depth_10_ok(self):
        h = HandoffDefinition(
            name="rec",
            pattern=HandoffPattern.RECURSIVE,
            sub_agents={"agent": _sub()},
            max_depth=10,
        )
        assert "depth_too_high" not in _errors(h)
