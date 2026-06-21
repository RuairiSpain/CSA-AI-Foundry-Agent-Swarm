"""Unit tests for ChainValidator."""
from pathlib import Path

import pytest

from safe_core.chain_models import RouteChain, RouteChainStep
from safe_core.chain_validator import ChainValidator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_chain(steps=None, timeout_seconds=120, **kwargs) -> RouteChain:
    if steps is None:
        steps = [
            RouteChainStep(route_name="route-a"),
            RouteChainStep(route_name="route-b"),
        ]
    return RouteChain(name="test-chain", steps=steps, timeout_seconds=timeout_seconds, **kwargs)


def routes_with(*names: str, tmp_path: Path) -> Path:
    """Create fake route.py stubs under tmp_path/routes/<name>/."""
    rdir = tmp_path / "routes"
    for name in names:
        d = rdir / name
        d.mkdir(parents=True)
        (d / "route.py").write_text(f"# route {name}\n")
    return rdir


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestMinSteps:
    def test_single_step_raises(self, tmp_path):
        chain = make_chain(steps=[RouteChainStep(route_name="only-one")])
        errors = ChainValidator().validate(chain, tmp_path / "routes")
        assert any(e.error_type == "min_steps" for e in errors)

    def test_two_steps_no_min_error(self, tmp_path):
        rdir = routes_with("route-a", "route-b", tmp_path=tmp_path)
        errors = ChainValidator().validate(make_chain(), rdir)
        assert not any(e.error_type == "min_steps" for e in errors)


class TestMissingRoute:
    def test_missing_route_file_caught(self, tmp_path):
        rdir = routes_with("route-a", tmp_path=tmp_path)  # route-b missing
        errors = ChainValidator().validate(make_chain(), rdir)
        assert any(e.error_type == "missing_route" for e in errors)
        assert any("route-b" in e.message for e in errors)

    def test_all_routes_present_no_error(self, tmp_path):
        rdir = routes_with("route-a", "route-b", tmp_path=tmp_path)
        errors = ChainValidator().validate(make_chain(), rdir)
        assert not any(e.error_type == "missing_route" for e in errors)


class TestConditionValidation:
    def test_invalid_condition_syntax_caught(self, tmp_path):
        rdir = routes_with("route-a", "route-b", tmp_path=tmp_path)
        chain = make_chain(steps=[
            RouteChainStep(route_name="route-a"),
            RouteChainStep(route_name="route-b", condition="if True =="),
        ])
        errors = ChainValidator().validate(chain, rdir)
        assert any(e.error_type == "invalid_condition" for e in errors)

    def test_valid_condition_no_error(self, tmp_path):
        rdir = routes_with("route-a", "route-b", tmp_path=tmp_path)
        chain = make_chain(steps=[
            RouteChainStep(route_name="route-a"),
            RouteChainStep(route_name="route-b", condition="score >= 0.8"),
        ])
        errors = ChainValidator().validate(chain, rdir)
        assert not any(e.error_type == "invalid_condition" for e in errors)

    def test_complex_valid_condition(self, tmp_path):
        rdir = routes_with("route-a", "route-b", tmp_path=tmp_path)
        chain = make_chain(steps=[
            RouteChainStep(route_name="route-a"),
            RouteChainStep(route_name="route-b", condition="x is not None and x > 0"),
        ])
        errors = ChainValidator().validate(chain, rdir)
        assert not any(e.error_type == "invalid_condition" for e in errors)


class TestEmptyMappingKey:
    def test_empty_dest_caught(self, tmp_path):
        rdir = routes_with("route-a", "route-b", tmp_path=tmp_path)
        chain = make_chain(steps=[
            RouteChainStep(route_name="route-a"),
            RouteChainStep(route_name="route-b", field_mapping={"": "some_key"}),
        ])
        errors = ChainValidator().validate(chain, rdir)
        assert any(e.error_type == "empty_mapping_key" for e in errors)

    def test_empty_src_caught(self, tmp_path):
        rdir = routes_with("route-a", "route-b", tmp_path=tmp_path)
        chain = make_chain(steps=[
            RouteChainStep(route_name="route-a"),
            RouteChainStep(route_name="route-b", field_mapping={"dest": ""}),
        ])
        errors = ChainValidator().validate(chain, rdir)
        assert any(e.error_type == "empty_mapping_key" for e in errors)

    def test_valid_mapping_no_error(self, tmp_path):
        rdir = routes_with("route-a", "route-b", tmp_path=tmp_path)
        chain = make_chain(steps=[
            RouteChainStep(route_name="route-a"),
            RouteChainStep(route_name="route-b", field_mapping={"text": "answer"}),
        ])
        errors = ChainValidator().validate(chain, rdir)
        assert not any(e.error_type == "empty_mapping_key" for e in errors)


class TestTightTimeout:
    def test_tight_timeout_produces_warning(self, tmp_path):
        rdir = routes_with("route-a", "route-b", tmp_path=tmp_path)
        chain = make_chain(timeout_seconds=10)  # 2 steps × 30s = 60s minimum
        errors = ChainValidator().validate(chain, rdir)
        assert any(e.error_type == "tight_timeout" for e in errors)

    def test_tight_timeout_is_not_a_hard_error(self, tmp_path):
        rdir = routes_with("route-a", "route-b", tmp_path=tmp_path)
        chain = make_chain(timeout_seconds=10)
        # validate_or_raise should NOT raise for timeout warning only
        ChainValidator().validate_or_raise(chain, rdir)

    def test_adequate_timeout_no_warning(self, tmp_path):
        rdir = routes_with("route-a", "route-b", tmp_path=tmp_path)
        chain = make_chain(timeout_seconds=120)
        errors = ChainValidator().validate(chain, rdir)
        assert not any(e.error_type == "tight_timeout" for e in errors)


class TestValidChain:
    def test_fully_valid_chain_returns_empty(self, tmp_path):
        rdir = routes_with("route-a", "route-b", tmp_path=tmp_path)
        chain = make_chain(
            steps=[
                RouteChainStep(route_name="route-a"),
                RouteChainStep(
                    route_name="route-b",
                    field_mapping={"input": "output"},
                    condition="result is not None",
                ),
            ],
            timeout_seconds=120,
        )
        errors = ChainValidator().validate(chain, rdir)
        hard = [e for e in errors if e.error_type != "tight_timeout"]
        assert hard == []


class TestValidateOrRaise:
    def test_raises_on_hard_error(self, tmp_path):
        chain = make_chain(steps=[RouteChainStep(route_name="only")])
        with pytest.raises(ValueError, match="validation failed"):
            ChainValidator().validate_or_raise(chain, tmp_path / "routes")

    def test_does_not_raise_on_valid_chain(self, tmp_path):
        rdir = routes_with("route-a", "route-b", tmp_path=tmp_path)
        ChainValidator().validate_or_raise(make_chain(), rdir)

    def test_error_message_lists_all_hard_errors(self, tmp_path):
        # missing both routes
        chain = make_chain()
        try:
            ChainValidator().validate_or_raise(chain, tmp_path / "routes")
        except ValueError as exc:
            assert "route-a" in str(exc)
            assert "route-b" in str(exc)
