"""Integration tests for handoff_ref on Agent and chain handoff: prefix."""
import pytest
from pathlib import Path

from safe_core.models import Agent, RouteDefinition, RoutePattern
from safe_core.validator import ContractValidator
from safe_core.chain_models import RouteChain, RouteChainStep
from safe_core.chain_validator import ChainValidator, _resolve_step


# ── Agent.handoff_ref ──────────────────────────────────────────────────────────

def _agent(name, inputs=None, outputs=None, handoff_ref=None) -> Agent:
    return Agent(
        name=name,
        category="test",
        version="1.0",
        input_schema={"properties": inputs or {}, "required": list((inputs or {}).keys())},
        output_schema={"properties": outputs or {}, "required": list((outputs or {}).keys())},
        handoff_ref=handoff_ref,
    )


class TestHandoffRefOnAgent:
    def test_handoff_ref_defaults_none(self):
        a = _agent("my-agent")
        assert a.handoff_ref is None

    def test_handoff_ref_set(self):
        a = _agent("my-agent", handoff_ref="selective-resolve")
        assert a.handoff_ref == "selective-resolve"

    def test_ignore_handoff_refs_skips_contract_check(self):
        """Agent with handoff_ref should not fail contract validation when ignored."""
        route = RouteDefinition(
            name="test-route",
            pattern=RoutePattern.SUPERVISOR_MANAGER,
            agents={
                "supervisor": _agent(
                    "sup",
                    outputs={"routing_decision": {}, "task": {}},
                ),
                "specialist_0": _agent(
                    "spec",
                    inputs={"task": {}, "secret_field": {}},  # would fail without handoff_ref
                    handoff_ref="my-handoff",                  # agent delegates; skip check
                ),
                "aggregator": _agent(
                    "agg",
                    inputs={"results": {}},
                    outputs={"final": {}},
                ),
            },
        )
        errors = ContractValidator.validate_route(route, ignore_handoff_refs=True)
        contract_errors = [e for e in errors if e.error_type == "contract_mismatch"]
        assert contract_errors == [], "handoff_ref agent should be excluded from contract checks"

    def test_ignore_handoff_refs_false_includes_agent(self):
        """With ignore_handoff_refs=False, the missing field IS caught."""
        route = RouteDefinition(
            name="test-route",
            pattern=RoutePattern.SUPERVISOR_MANAGER,
            agents={
                "supervisor": _agent(
                    "sup",
                    outputs={"routing_decision": {}, "task": {}},
                ),
                "specialist_0": _agent(
                    "spec",
                    inputs={"task": {}, "secret_field": {}},
                    handoff_ref="my-handoff",
                ),
                "aggregator": _agent(
                    "agg",
                    inputs={"results": {}},
                    outputs={"final": {}},
                ),
            },
        )
        errors = ContractValidator.validate_route(route, ignore_handoff_refs=False)
        contract_errors = [e for e in errors if e.error_type == "contract_mismatch"]
        assert len(contract_errors) > 0, "secret_field mismatch should be caught"


# ── _resolve_step ──────────────────────────────────────────────────────────────

class TestResolveStep:
    def test_plain_route(self, tmp_path):
        is_handoff, bare, expected = _resolve_step("my-route", tmp_path)
        assert not is_handoff
        assert bare == "my-route"
        assert expected == tmp_path / "my-route" / "route.py"

    def test_handoff_prefix(self, tmp_path):
        is_handoff, bare, expected = _resolve_step("handoff:my-handoff", tmp_path)
        assert is_handoff
        assert bare == "my-handoff"
        assert expected == tmp_path.parent / "handoffs" / "my-handoff" / "handoff.py"


# ── ChainValidator with handoff: prefix ───────────────────────────────────────

class TestChainValidatorHandoffSteps:
    def _make_chain(self, *route_names):
        steps = [RouteChainStep(route_name=n) for n in route_names]
        return RouteChain(name="test-chain", steps=steps, timeout_seconds=300)

    def test_missing_handoff_gives_informative_error(self, tmp_path):
        chain = self._make_chain("handoff:nonexistent-handoff", "handoff:also-missing")
        errors = ChainValidator().validate(chain, tmp_path / "routes")
        missing = [e for e in errors if e.error_type == "missing_route"]
        assert len(missing) == 2
        assert all("handoff" in e.message for e in missing)

    def test_existing_handoff_passes(self, tmp_path):
        routes_dir = tmp_path / "routes"
        handoffs_dir = tmp_path / "handoffs"
        # Create a fake route and a fake handoff
        (routes_dir / "preprocess").mkdir(parents=True)
        (routes_dir / "preprocess" / "route.py").write_text("# route", encoding="utf-8")
        (handoffs_dir / "my-handoff").mkdir(parents=True)
        (handoffs_dir / "my-handoff" / "handoff.py").write_text("# handoff", encoding="utf-8")

        chain = self._make_chain("preprocess", "handoff:my-handoff")
        errors = ChainValidator().validate(chain, routes_dir)
        missing = [e for e in errors if e.error_type == "missing_route"]
        assert missing == []

    def test_mixed_steps_error_messages_identify_kind(self, tmp_path):
        chain = self._make_chain("missing-route", "handoff:missing-handoff")
        errors = ChainValidator().validate(chain, tmp_path / "routes")
        messages = [e.message for e in errors if e.error_type == "missing_route"]
        assert any("route" in m and "missing-route" in m for m in messages)
        assert any("handoff" in m and "missing-handoff" in m for m in messages)
