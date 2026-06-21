"""Unit tests for RouteChainGenerator."""
import ast
import textwrap
from pathlib import Path

import pytest
import yaml

from safe_core.chain_models import RouteChain, RouteChainStep
from safe_core.chain_generator import RouteChainGenerator, _class_name


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_chain(**kwargs) -> RouteChain:
    defaults = {
        "name": "test-chain",
        "steps": [
            RouteChainStep(route_name="step-one"),
            RouteChainStep(route_name="step-two", field_mapping={"text": "answer"}),
        ],
    }
    defaults.update(kwargs)
    return RouteChain(**defaults)


# ---------------------------------------------------------------------------
# _class_name helper
# ---------------------------------------------------------------------------

class TestClassNameHelper:
    def test_kebab_to_pascal(self):
        assert _class_name("contract-review-chain") == "ContractReviewChain"

    def test_snake_to_pascal(self):
        assert _class_name("my_route") == "MyRoute"

    def test_single_word(self):
        assert _class_name("rag") == "Rag"


# ---------------------------------------------------------------------------
# Code generation
# ---------------------------------------------------------------------------

class TestGenerateReturnsContent:
    def test_returns_chain_code_key(self):
        result = RouteChainGenerator.generate(make_chain())
        assert "chain_code" in result
        assert len(result["chain_code"]) > 100

    def test_returns_chain_yaml_key(self):
        result = RouteChainGenerator.generate(make_chain())
        assert "chain_yaml" in result
        data = yaml.safe_load(result["chain_yaml"])
        assert data["name"] == "test-chain"


class TestGeneratedCodeIsValidPython:
    def test_parses_without_error(self):
        code = RouteChainGenerator.generate(make_chain())["chain_code"]
        ast.parse(code)

    def test_with_condition_parses(self):
        chain = make_chain(steps=[
            RouteChainStep(route_name="step-one"),
            RouteChainStep(route_name="step-two", condition="score >= 0.8"),
        ])
        ast.parse(RouteChainGenerator.generate(chain)["chain_code"])

    def test_with_history_parses(self):
        ast.parse(
            RouteChainGenerator.generate(make_chain(include_chain_history=True))["chain_code"]
        )

    def test_skip_on_failure_parses(self):
        ast.parse(
            RouteChainGenerator.generate(make_chain(on_step_failure="skip"))["chain_code"]
        )


class TestGeneratedCodeStructure:
    def setup_method(self):
        self.code = RouteChainGenerator.generate(make_chain())["chain_code"]

    def test_class_name_present(self):
        assert "class TestChainChain:" in self.code

    def test_imports_match_steps(self):
        assert "from routes.step_one.route import StepOneRoute" in self.code
        assert "from routes.step_two.route import StepTwoRoute" in self.code

    def test_step_instances_created(self):
        assert "self._step_0 = StepOneRoute(kernel)" in self.code
        assert "self._step_1 = StepTwoRoute(kernel)" in self.code

    def test_context_update_present(self):
        assert self.code.count("context.update(_step_output)") == 2

    def test_timeout_check_between_steps(self):
        assert "self._check_timeout(start)" in self.code

    def test_timeout_check_absent_after_last_step(self):
        # self._check_timeout(start) call must not appear after the final step block
        lines = self.code.splitlines()
        last_update = max(i for i, l in enumerate(lines) if "context.update(_step_output)" in l)
        after_last = "\n".join(lines[last_update:])
        assert "self._check_timeout(start)" not in after_last

    def test_check_timeout_method_defined(self):
        assert "def _check_timeout(" in self.code

    def test_field_mapping_rendered(self):
        assert '_step_input["text"] = context["answer"]' in self.code

    def test_first_step_copies_request(self):
        assert "for _k, _v in request.items():" in self.code


class TestConditionalStep:
    def test_condition_rendered_in_run_var(self):
        chain = make_chain(steps=[
            RouteChainStep(route_name="step-one"),
            RouteChainStep(route_name="step-two", condition="quality >= 0.9"),
        ])
        code = RouteChainGenerator.generate(chain)["chain_code"]
        assert "_run_1 = quality >= 0.9" in code

    def test_no_condition_renders_true(self):
        code = RouteChainGenerator.generate(make_chain())["chain_code"]
        assert "_run_0 = True" in code

    def test_skipped_log_present(self):
        chain = make_chain(steps=[
            RouteChainStep(route_name="step-one"),
            RouteChainStep(route_name="step-two", condition="flag"),
        ])
        code = RouteChainGenerator.generate(chain)["chain_code"]
        assert "step 2 skipped: condition false" in code


class TestChainHistory:
    def test_history_key_appended_when_enabled(self):
        code = RouteChainGenerator.generate(
            make_chain(include_chain_history=True)
        )["chain_code"]
        assert '_chain_history' in code
        assert '"step":' in code

    def test_history_absent_when_disabled(self):
        code = RouteChainGenerator.generate(
            make_chain(include_chain_history=False)
        )["chain_code"]
        assert "_chain_history" not in code


class TestOnStepFailure:
    def test_halt_mode_reraises(self):
        code = RouteChainGenerator.generate(make_chain(on_step_failure="halt"))["chain_code"]
        assert "raise" in code
        assert "return context" not in code.split("except Exception")[1].split("def ")[0]

    def test_skip_mode_returns_context(self):
        code = RouteChainGenerator.generate(
            make_chain(on_step_failure="skip")
        )["chain_code"]
        assert "return context" in code.split("except Exception")[1]


class TestPassThroughFields:
    def test_pass_through_renders_setdefault(self):
        chain = make_chain(steps=[
            RouteChainStep(route_name="step-one"),
            RouteChainStep(
                route_name="step-two",
                pass_through_fields=["contract_id"],
            ),
        ])
        code = RouteChainGenerator.generate(chain)["chain_code"]
        assert 'if "contract_id" in request:' in code
        assert '_step_input.setdefault("contract_id", request["contract_id"])' in code


class TestSaveToDisk:
    def test_writes_chain_py_and_yaml(self, tmp_path):
        chain = make_chain()
        chain_dir = RouteChainGenerator.save(chain, tmp_path)
        assert (chain_dir / "chain.py").exists()
        assert (chain_dir / "chain.yaml").exists()

    def test_chain_py_contains_class(self, tmp_path):
        chain = make_chain()
        chain_dir = RouteChainGenerator.save(chain, tmp_path)
        src = (chain_dir / "chain.py").read_text()
        assert "class TestChainChain:" in src

    def test_load_from_yaml_round_trips(self, tmp_path):
        original = make_chain(description="round-trip test", timeout_seconds=300)
        chain_dir = RouteChainGenerator.save(original, tmp_path)
        loaded = RouteChainGenerator.load_from_yaml(chain_dir / "chain.yaml")
        assert loaded.name == original.name
        assert loaded.description == original.description
        assert loaded.timeout_seconds == original.timeout_seconds
        assert len(loaded.steps) == len(original.steps)
        assert loaded.steps[1].field_mapping == original.steps[1].field_mapping
