"""Comprehensive tests for Phase 4: Route Writer Agent"""

import json
import pytest
import asyncio
from safe_core.models import RoutePattern, Agent, RouteDefinition, ValidationError
from safe_core.interview import RouteInterviewer
from safe_core.code_generator import RouteCodeGenerator
from safe_core.validator import ContractValidator
from safe_core.agent_catalog import AgentCatalog

class TestAgentCatalog:
    """Tests for agent catalog"""
    
    def test_search_by_name(self):
        """Search agents by name"""
        catalog = AgentCatalog()
        results = catalog.search_by_name("mortgage")
        
        assert len(results) > 0
        assert any("mortgage" in agent.name.lower() for agent in results)
    
    def test_search_by_category(self):
        """Search agents by category"""
        catalog = AgentCatalog()
        results = catalog.search_by_category("supervisor")
        
        assert len(results) > 0
        assert all(agent.category == "supervisor" for agent in results)
    
    def test_get_agent(self):
        """Get specific agent"""
        catalog = AgentCatalog()
        agent = catalog.get_agent("loan-supervisor-router")
        
        assert agent is not None
        assert agent.name == "loan-supervisor-router"
        assert agent.category == "supervisor"
    
    def test_list_all(self):
        """List all agents"""
        catalog = AgentCatalog()
        agents = catalog.list_all()

        assert len(agents) > 0

    # P1 catalog-unification tests ──────────────────────────────────────────

    def test_all_interview_categories_present(self):
        """Every category the interview searches for has at least one agent."""
        catalog = AgentCatalog()
        required = ["supervisor", "specialist", "aggregator", "processor", "splitter", "mapper", "reducer"]
        for cat in required:
            results = catalog.search_by_category(cat)
            assert len(results) > 0, f"No agents found for category '{cat}'"

    def test_non_loan_agents_present(self):
        """Catalog contains non-loan agents for each pattern-specific role."""
        catalog = AgentCatalog()
        non_loan = {
            "processor": "document-processor",
            "splitter": "batch-splitter",
            "mapper": "data-mapper",
            "reducer": "data-reducer",
            "aggregator": "fan-in-aggregator",
        }
        for cat, name in non_loan.items():
            agent = catalog.get_agent(name)
            assert agent is not None, f"Expected agent '{name}' not found"
            assert agent.category == cat

    def test_catalog_agents_have_schemas(self):
        """Every agent loaded from YAML has non-empty input and output schemas."""
        catalog = AgentCatalog()
        for agent in catalog.list_all():
            assert agent.input_schema, f"{agent.name} has empty input_schema"
            assert agent.output_schema, f"{agent.name} has empty output_schema"


class TestContractValidator:
    """Tests for contract validation"""
    
    def test_validate_timeout_mismatch(self):
        """Detect timeout mismatch errors"""
        errors = ContractValidator.validate_timeouts(30, 60)
        
        assert len(errors) > 0
        assert any(e.error_type == "timeout_mismatch" for e in errors)
    
    def test_validate_timeout_too_low(self):
        """Detect timeout too low"""
        errors = ContractValidator.validate_timeouts(5, 2)
        
        assert len(errors) > 0
        assert any(e.error_type == "timeout_too_low" for e in errors)
    
    def test_validate_valid_timeout(self):
        """Accept valid timeouts"""
        errors = ContractValidator.validate_timeouts(120, 60)
        
        # Should have no timeout errors (might have others)
        timeout_errors = [e for e in errors if "timeout" in e.error_type]
        assert len(timeout_errors) == 0
    
    def test_validate_supervisor_manager_pattern(self):
        """Validate supervisor-manager contracts"""
        catalog = AgentCatalog()
        
        # Create valid supervisor-manager route
        route_def = RouteDefinition(
            name="test-route",
            pattern=RoutePattern.SUPERVISOR_MANAGER,
            agents={
                "supervisor": catalog.get_agent("loan-supervisor-router"),
                "specialist_0": catalog.get_agent("loan-specialist-mortgage"),
                "specialist_1": catalog.get_agent("loan-specialist-auto"),
                "aggregator": catalog.get_agent("standard-aggregator"),
            },
            description="Test route",
            timeout_seconds=120,
            per_agent_timeout_seconds=60,
        )
        
        errors = ContractValidator.validate_route(route_def)
        
        # Should have minimal errors
        critical_errors = [e for e in errors if e.error_type in ["contract_mismatch", "missing_agent"]]
        assert len(critical_errors) == 0

    def test_validate_no_cycles_detects_cycle(self):
        """Cycle detection catches A -> B -> A"""
        agent_a = Agent(
            name="agent-a", category="processor", version="1.0",
            input_schema={}, output_schema={}, dependencies=["agent-b"],
        )
        agent_b = Agent(
            name="agent-b", category="processor", version="1.0",
            input_schema={}, output_schema={}, dependencies=["agent-a"],
        )
        errors = ContractValidator.validate_no_cycles({"agent_a": agent_a, "agent_b": agent_b})
        assert any(e.error_type == "circular_dependency" for e in errors)

    def test_validate_no_cycles_clean(self):
        """Acyclic dependencies produce no cycle errors"""
        agent_a = Agent(
            name="agent-a", category="processor", version="1.0",
            input_schema={}, output_schema={}, dependencies=[],
        )
        agent_b = Agent(
            name="agent-b", category="processor", version="1.0",
            input_schema={}, output_schema={}, dependencies=["agent-a"],
        )
        errors = ContractValidator.validate_no_cycles({"agent_a": agent_a, "agent_b": agent_b})
        assert not any(e.error_type == "circular_dependency" for e in errors)


class TestCodeGenerator:
    """Tests for code generation"""
    
    def test_generate_supervisor_manager(self):
        """Generate supervisor-manager route code"""
        catalog = AgentCatalog()
        
        route_def = RouteDefinition(
            name="loan-approval-v1",
            pattern=RoutePattern.SUPERVISOR_MANAGER,
            agents={
                "supervisor": catalog.get_agent("loan-supervisor-router"),
                "specialist_0": catalog.get_agent("loan-specialist-mortgage"),
                "aggregator": catalog.get_agent("standard-aggregator"),
            },
            description="Loan approval workflow",
            timeout_seconds=120,
            per_agent_timeout_seconds=60,
            routing_field="loan_type",
            csa_email="test@example.com",
        )
        
        generated = RouteCodeGenerator.generate(route_def)
        
        # Verify generated code
        assert "class LoanApprovalV1Route:" in generated.route_code
        assert "async def invoke" in generated.route_code
        assert "supervisor" in generated.route_code
        assert "specialist" in generated.route_code
        assert "aggregator" in generated.route_code
    
    def test_generated_code_has_validation(self):
        """Generated code includes input/output validation"""
        catalog = AgentCatalog()
        
        route_def = RouteDefinition(
            name="test-route",
            pattern=RoutePattern.SUPERVISOR_MANAGER,
            agents={
                "supervisor": catalog.get_agent("loan-supervisor-router"),
                "specialist_0": catalog.get_agent("loan-specialist-mortgage"),
                "aggregator": catalog.get_agent("standard-aggregator"),
            },
            description="Test",
            timeout_seconds=120,
        )
        
        generated = RouteCodeGenerator.generate(route_def)
        
        # Should have validation methods
        assert "_validate_input" in generated.route_code
        assert "_validate_output" in generated.route_code
    
    def test_generate_requirements(self):
        """Generate requirements.txt"""
        catalog = AgentCatalog()
        
        route_def = RouteDefinition(
            name="test",
            pattern=RoutePattern.SUPERVISOR_MANAGER,
            agents={
                "supervisor": catalog.get_agent("loan-supervisor-router"),
                "specialist_0": catalog.get_agent("loan-specialist-mortgage"),
                "aggregator": catalog.get_agent("standard-aggregator"),
            },
        )
        
        generated = RouteCodeGenerator.generate(route_def)
        
        assert "semantic-kernel" in generated.requirements_txt
        assert "azure-ai" in generated.requirements_txt
        assert "pydantic" in generated.requirements_txt
    
    def test_generate_config(self):
        """Generate config.yaml"""
        catalog = AgentCatalog()
        
        route_def = RouteDefinition(
            name="my-route",
            pattern=RoutePattern.SUPERVISOR_MANAGER,
            agents={
                "supervisor": catalog.get_agent("loan-supervisor-router"),
                "specialist_0": catalog.get_agent("loan-specialist-mortgage"),
                "aggregator": catalog.get_agent("standard-aggregator"),
            },
            description="My route",
            csa_email="test@example.com",
        )
        
        generated = RouteCodeGenerator.generate(route_def)
        
        assert "name: my-route" in generated.config_yaml
        assert "version: v1.0" in generated.config_yaml
        assert "supervisor-manager" in generated.config_yaml
    
    def test_generated_files_save_to_disk(self, tmp_path):
        """Generated files can be saved to disk"""
        catalog = AgentCatalog()
        
        route_def = RouteDefinition(
            name="test",
            pattern=RoutePattern.SUPERVISOR_MANAGER,
            agents={
                "supervisor": catalog.get_agent("loan-supervisor-router"),
                "specialist_0": catalog.get_agent("loan-specialist-mortgage"),
                "aggregator": catalog.get_agent("standard-aggregator"),
            },
        )
        
        generated = RouteCodeGenerator.generate(route_def)
        route_dir = tmp_path / "test_route"
        
        generated.save_to_disk(str(route_dir))
        
        # Verify files exist
        assert (route_dir / "route.py").exists()
        assert (route_dir / "requirements.txt").exists()
        assert (route_dir / "config.yaml").exists()
        assert (route_dir / "test_data.json").exists()


class TestRouteInterviewer:
    """Tests for interview logic"""
    
    def test_interviewer_initialization(self):
        """Interviewer initializes correctly"""
        catalog = AgentCatalog()
        interviewer = RouteInterviewer(catalog)
        
        assert interviewer.catalog is not None
        assert interviewer.route_def is None


# Integration tests
class TestPhase4Integration:
    """Integration tests for complete Phase 4"""
    
    def test_complete_route_creation_flow(self):
        """Test complete route creation flow"""
        catalog = AgentCatalog()
        
        # Create route definition
        route_def = RouteDefinition(
            name="integration-test-route",
            pattern=RoutePattern.SUPERVISOR_MANAGER,
            agents={
                "supervisor": catalog.get_agent("loan-supervisor-router"),
                "specialist_0": catalog.get_agent("loan-specialist-mortgage"),
                "specialist_1": catalog.get_agent("loan-specialist-auto"),
                "aggregator": catalog.get_agent("standard-aggregator"),
            },
            description="Integration test route",
            timeout_seconds=120,
            per_agent_timeout_seconds=60,
            csa_email="integration@test.com",
        )
        
        # Validate
        errors = ContractValidator.validate_route(route_def)
        assert len(errors) == 0, f"Validation failed: {errors}"
        
        # Generate
        generated = RouteCodeGenerator.generate(route_def)
        
        # Verify all files generated
        assert generated.route_code
        assert generated.requirements_txt
        assert generated.config_yaml
        assert generated.test_data_json
        
        # Verify metadata
        assert "supervisor-manager" in generated.metadata["pattern"]
        assert len(generated.metadata["agents"]) == 4

class TestFanOutFanIn:
    """Tests for fan-out/fan-in pattern"""

    def _make_route(self, catalog: AgentCatalog, name: str = "parallel-doc-processor") -> RouteDefinition:
        return RouteDefinition(
            name=name,
            pattern=RoutePattern.FAN_OUT_FAN_IN,
            agents={
                "processor_0": catalog.get_agent("document-processor"),
                "processor_1": catalog.get_agent("text-enricher"),
                "aggregator": catalog.get_agent("fan-in-aggregator"),
            },
            description="Parallel document processing",
            timeout_seconds=120,
            per_agent_timeout_seconds=60,
        )

    def test_generate_fan_out_fan_in(self):
        """Generate fan-out/fan-in route code"""
        catalog = AgentCatalog()
        route_def = self._make_route(catalog)
        generated = RouteCodeGenerator.generate(route_def)

        assert "class ParallelDocProcessorRoute:" in generated.route_code
        assert "asyncio.gather" in generated.route_code
        assert "processor_0" in generated.route_code
        assert "processor_1" in generated.route_code
        assert "aggregator" in generated.route_code
        assert "_validate_input" in generated.route_code
        assert "_validate_output" in generated.route_code

    def test_fan_out_fan_in_has_partial_failure_handling(self):
        """Generated code handles partial processor failures gracefully"""
        catalog = AgentCatalog()
        route_def = self._make_route(catalog)
        generated = RouteCodeGenerator.generate(route_def)

        assert "return_exceptions=True" in generated.route_code
        assert "isinstance(result, Exception)" in generated.route_code

    def test_fan_out_fan_in_validation_passes(self):
        """Valid fan-out/fan-in route has no contract errors"""
        catalog = AgentCatalog()
        route_def = self._make_route(catalog)
        errors = ContractValidator.validate_route(route_def)
        critical = [e for e in errors if e.error_type in ["contract_mismatch", "missing_agent"]]
        assert len(critical) == 0

    def test_fan_out_fan_in_missing_aggregator(self):
        """Missing aggregator produces a missing_agent error"""
        catalog = AgentCatalog()
        route_def = RouteDefinition(
            name="bad-fan-out",
            pattern=RoutePattern.FAN_OUT_FAN_IN,
            agents={
                "processor_0": catalog.get_agent("document-processor"),
            },
        )
        errors = ContractValidator.validate_agent_contracts(route_def.pattern, route_def.agents)
        assert any(e.error_type == "missing_agent" and "aggregator" in e.message for e in errors)

    def test_fan_out_fan_in_missing_processor(self):
        """No processor_* agents produces a missing_agent error"""
        catalog = AgentCatalog()
        route_def = RouteDefinition(
            name="bad-fan-out",
            pattern=RoutePattern.FAN_OUT_FAN_IN,
            agents={
                "aggregator": catalog.get_agent("fan-in-aggregator"),
            },
        )
        errors = ContractValidator.validate_agent_contracts(route_def.pattern, route_def.agents)
        assert any(e.error_type == "missing_agent" and "processor" in e.message.lower() for e in errors)

    def test_fan_out_test_data_json(self):
        """Generated test data is valid JSON suited for the pattern"""
        catalog = AgentCatalog()
        route_def = self._make_route(catalog)
        generated = RouteCodeGenerator.generate(route_def)
        data = json.loads(generated.test_data_json)
        assert isinstance(data, list)
        assert len(data) > 0


class TestMapReduce:
    """Tests for map-reduce pattern"""

    def _make_route(self, catalog: AgentCatalog, name: str = "batch-transform") -> RouteDefinition:
        return RouteDefinition(
            name=name,
            pattern=RoutePattern.MAP_REDUCE,
            agents={
                "splitter": catalog.get_agent("batch-splitter"),
                "mapper": catalog.get_agent("data-mapper"),
                "reducer": catalog.get_agent("data-reducer"),
            },
            description="Batch data transformation",
            timeout_seconds=180,
            per_agent_timeout_seconds=60,
        )

    def test_generate_map_reduce(self):
        """Generate map-reduce route code"""
        catalog = AgentCatalog()
        route_def = self._make_route(catalog)
        generated = RouteCodeGenerator.generate(route_def)

        assert "class BatchTransformRoute:" in generated.route_code
        assert "asyncio.gather" in generated.route_code
        assert "splitter" in generated.route_code
        assert "mapper" in generated.route_code
        assert "reducer" in generated.route_code
        assert "_validate_input" in generated.route_code
        assert "_validate_output" in generated.route_code

    def test_map_reduce_chunks_referenced(self):
        """Generated code uses 'chunks' from splitter output"""
        catalog = AgentCatalog()
        route_def = self._make_route(catalog)
        generated = RouteCodeGenerator.generate(route_def)
        assert '"chunks"' in generated.route_code or "'chunks'" in generated.route_code or "chunks" in generated.route_code

    def test_map_reduce_validation_passes(self):
        """Valid map-reduce route has no contract errors"""
        catalog = AgentCatalog()
        route_def = self._make_route(catalog)
        errors = ContractValidator.validate_route(route_def)
        critical = [e for e in errors if e.error_type in ["contract_mismatch", "missing_agent"]]
        assert len(critical) == 0

    def test_map_reduce_missing_splitter(self):
        """Missing splitter produces a missing_agent error"""
        catalog = AgentCatalog()
        route_def = RouteDefinition(
            name="bad-mr",
            pattern=RoutePattern.MAP_REDUCE,
            agents={
                "mapper": catalog.get_agent("data-mapper"),
                "reducer": catalog.get_agent("data-reducer"),
            },
        )
        errors = ContractValidator.validate_agent_contracts(route_def.pattern, route_def.agents)
        assert any(e.error_type == "missing_agent" and "splitter" in e.message for e in errors)

    def test_map_reduce_missing_reducer(self):
        """Missing reducer produces a missing_agent error"""
        catalog = AgentCatalog()
        route_def = RouteDefinition(
            name="bad-mr",
            pattern=RoutePattern.MAP_REDUCE,
            agents={
                "splitter": catalog.get_agent("batch-splitter"),
                "mapper": catalog.get_agent("data-mapper"),
            },
        )
        errors = ContractValidator.validate_agent_contracts(route_def.pattern, route_def.agents)
        assert any(e.error_type == "missing_agent" and "reducer" in e.message for e in errors)

    def test_map_reduce_test_data_json(self):
        """Generated test data is valid JSON suited for the pattern"""
        catalog = AgentCatalog()
        route_def = self._make_route(catalog)
        generated = RouteCodeGenerator.generate(route_def)
        data = json.loads(generated.test_data_json)
        assert isinstance(data, list)
        assert len(data) > 0


class TestSequentialPipeline:
    """Tests for sequential-pipeline pattern"""

    def _make_route(self, catalog: AgentCatalog, name: str = "doc-enrich-pipeline") -> RouteDefinition:
        return RouteDefinition(
            name=name,
            pattern=RoutePattern.SEQUENTIAL_PIPELINE,
            agents={
                "stage_0": catalog.get_agent("document-processor"),
                "stage_1": catalog.get_agent("text-enricher"),
                "stage_2": catalog.get_agent("data-formatter"),
            },
            description="Document enrichment pipeline",
            timeout_seconds=180,
            per_agent_timeout_seconds=60,
        )

    def test_generate_sequential_pipeline(self):
        """Generate sequential-pipeline route code"""
        catalog = AgentCatalog()
        route_def = self._make_route(catalog)
        generated = RouteCodeGenerator.generate(route_def)

        assert "class DocEnrichPipelineRoute:" in generated.route_code
        assert "stage_0" in generated.route_code
        assert "stage_1" in generated.route_code
        assert "stage_2" in generated.route_code
        assert "_validate_input" in generated.route_code
        assert "_validate_output" in generated.route_code

    def test_sequential_pipeline_no_asyncio_gather(self):
        """Sequential pipeline does not use parallel gather (it's sequential)"""
        catalog = AgentCatalog()
        route_def = self._make_route(catalog)
        generated = RouteCodeGenerator.generate(route_def)
        assert "asyncio.gather" not in generated.route_code

    def test_sequential_pipeline_stage_chaining(self):
        """Generated code chains stage output into next stage input via 'data' variable"""
        catalog = AgentCatalog()
        route_def = self._make_route(catalog)
        generated = RouteCodeGenerator.generate(route_def)
        assert "data = await self.stage_0.invoke(data)" in generated.route_code or \
               "data = await self.stage_0" in generated.route_code

    def test_sequential_pipeline_validation_too_few_stages(self):
        """Single stage produces a missing_agent error"""
        catalog = AgentCatalog()
        route_def = RouteDefinition(
            name="bad-pipeline",
            pattern=RoutePattern.SEQUENTIAL_PIPELINE,
            agents={
                "stage_0": catalog.get_agent("document-processor"),
            },
        )
        errors = ContractValidator.validate_agent_contracts(route_def.pattern, route_def.agents)
        assert any(e.error_type == "missing_agent" and "stage" in e.message.lower() for e in errors)

    def test_sequential_pipeline_test_data_json(self):
        """Generated test data is valid JSON suited for the pattern"""
        catalog = AgentCatalog()
        route_def = self._make_route(catalog)
        generated = RouteCodeGenerator.generate(route_def)
        data = json.loads(generated.test_data_json)
        assert isinstance(data, list)
        assert len(data) > 0


# P2 integration tests
class TestP2Integration:
    """End-to-end integration tests for all four patterns"""

    def test_all_patterns_generate_valid_files(self, tmp_path):
        """All four patterns produce saveable output files"""
        catalog = AgentCatalog()

        routes = [
            RouteDefinition(
                name="sup-mgr-route",
                pattern=RoutePattern.SUPERVISOR_MANAGER,
                agents={
                    "supervisor": catalog.get_agent("loan-supervisor-router"),
                    "specialist_0": catalog.get_agent("loan-specialist-mortgage"),
                    "aggregator": catalog.get_agent("standard-aggregator"),
                },
            ),
            RouteDefinition(
                name="fan-out-route",
                pattern=RoutePattern.FAN_OUT_FAN_IN,
                agents={
                    "processor_0": catalog.get_agent("document-processor"),
                    "processor_1": catalog.get_agent("text-enricher"),
                    "aggregator": catalog.get_agent("fan-in-aggregator"),
                },
            ),
            RouteDefinition(
                name="map-reduce-route",
                pattern=RoutePattern.MAP_REDUCE,
                agents={
                    "splitter": catalog.get_agent("batch-splitter"),
                    "mapper": catalog.get_agent("data-mapper"),
                    "reducer": catalog.get_agent("data-reducer"),
                },
            ),
            RouteDefinition(
                name="pipeline-route",
                pattern=RoutePattern.SEQUENTIAL_PIPELINE,
                agents={
                    "stage_0": catalog.get_agent("document-processor"),
                    "stage_1": catalog.get_agent("data-formatter"),
                },
            ),
        ]

        for route_def in routes:
            generated = RouteCodeGenerator.generate(route_def)
            route_dir = tmp_path / route_def.name
            generated.save_to_disk(str(route_dir))

            assert (route_dir / "route.py").exists(), f"{route_def.name}: route.py missing"
            assert (route_dir / "requirements.txt").exists(), f"{route_def.name}: requirements.txt missing"
            assert (route_dir / "config.yaml").exists(), f"{route_def.name}: config.yaml missing"
            assert (route_dir / "test_data.json").exists(), f"{route_def.name}: test_data.json missing"

    def test_all_patterns_metadata_correct(self):
        """Generated metadata contains correct pattern name"""
        catalog = AgentCatalog()

        cases = [
            (RoutePattern.SUPERVISOR_MANAGER, "supervisor-manager", {
                "supervisor": catalog.get_agent("loan-supervisor-router"),
                "specialist_0": catalog.get_agent("loan-specialist-mortgage"),
                "aggregator": catalog.get_agent("standard-aggregator"),
            }),
            (RoutePattern.FAN_OUT_FAN_IN, "fan-out-fan-in", {
                "processor_0": catalog.get_agent("document-processor"),
                "aggregator": catalog.get_agent("fan-in-aggregator"),
            }),
            (RoutePattern.MAP_REDUCE, "map-reduce", {
                "splitter": catalog.get_agent("batch-splitter"),
                "mapper": catalog.get_agent("data-mapper"),
                "reducer": catalog.get_agent("data-reducer"),
            }),
            (RoutePattern.SEQUENTIAL_PIPELINE, "sequential-pipeline", {
                "stage_0": catalog.get_agent("document-processor"),
                "stage_1": catalog.get_agent("data-formatter"),
            }),
        ]

        for pattern, expected_pattern_str, agents in cases:
            route_def = RouteDefinition(name="test", pattern=pattern, agents=agents)
            generated = RouteCodeGenerator.generate(route_def)
            assert expected_pattern_str in generated.metadata["pattern"], \
                f"Expected '{expected_pattern_str}' in metadata for {pattern}"

    def test_all_patterns_config_yaml_correct(self):
        """Config yaml includes pattern name for all four patterns"""
        catalog = AgentCatalog()

        cases = [
            (RoutePattern.SUPERVISOR_MANAGER, "supervisor-manager", {
                "supervisor": catalog.get_agent("loan-supervisor-router"),
                "specialist_0": catalog.get_agent("loan-specialist-mortgage"),
                "aggregator": catalog.get_agent("standard-aggregator"),
            }),
            (RoutePattern.FAN_OUT_FAN_IN, "fan-out-fan-in", {
                "processor_0": catalog.get_agent("document-processor"),
                "aggregator": catalog.get_agent("fan-in-aggregator"),
            }),
            (RoutePattern.MAP_REDUCE, "map-reduce", {
                "splitter": catalog.get_agent("batch-splitter"),
                "mapper": catalog.get_agent("data-mapper"),
                "reducer": catalog.get_agent("data-reducer"),
            }),
            (RoutePattern.SEQUENTIAL_PIPELINE, "sequential-pipeline", {
                "stage_0": catalog.get_agent("document-processor"),
                "stage_1": catalog.get_agent("data-formatter"),
            }),
        ]

        for pattern, expected_pattern_str, agents in cases:
            route_def = RouteDefinition(name="test", pattern=pattern, agents=agents)
            generated = RouteCodeGenerator.generate(route_def)
            assert expected_pattern_str in generated.config_yaml, \
                f"Expected '{expected_pattern_str}' in config.yaml for {pattern}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

