"""Comprehensive tests for Phase 4: Route Writer Agent"""

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

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

