"""Contract validation for routes and agents"""

from typing import List, Dict, Any
from .models import RouteDefinition, Agent, ValidationError, RoutePattern

class ContractValidator:
    """Validates route and agent contracts"""
    
    @staticmethod
    def validate_route(route_def: RouteDefinition) -> List[ValidationError]:
        """Validate complete route definition"""
        errors = []
        
        # Validate timeouts
        timeout_errors = ContractValidator.validate_timeouts(
            route_def.timeout_seconds,
            route_def.per_agent_timeout_seconds
        )
        errors.extend(timeout_errors)
        
        # Validate agent contracts match pattern
        contract_errors = ContractValidator.validate_agent_contracts(
            route_def.pattern,
            route_def.agents
        )
        errors.extend(contract_errors)
        
        # Validate no circular dependencies
        circular_errors = ContractValidator.validate_no_cycles(route_def.agents)
        errors.extend(circular_errors)
        
        return errors
    
    @staticmethod
    def validate_timeouts(total: int, per_agent: int) -> List[ValidationError]:
        """Validate timeout configuration"""
        errors = []
        
        if total < per_agent:
            errors.append(ValidationError(
                error_type="timeout_mismatch",
                message=f"Total timeout ({total}s) < per-agent timeout ({per_agent}s)",
                suggested_solutions=[
                    f"Increase total timeout to at least {per_agent * 2}s",
                    f"Decrease per-agent timeout to {total // 2}s"
                ]
            ))
        
        if total < 10:
            errors.append(ValidationError(
                error_type="timeout_too_low",
                message=f"Total timeout too low: {total}s",
                suggested_solutions=["Increase timeout to at least 30s"]
            ))
        
        return errors
    
    @staticmethod
    def validate_agent_contracts(pattern: RoutePattern, agents: Dict[str, Agent]) -> List[ValidationError]:
        """Validate that agent contracts match the pattern"""
        errors = []
        
        if pattern == RoutePattern.SUPERVISOR_MANAGER:
            # Supervisor output must match specialist inputs
            supervisor = agents.get("supervisor")
            if not supervisor:
                errors.append(ValidationError(
                    error_type="missing_agent",
                    message="Supervisor agent is required for supervisor-manager pattern"
                ))
                return errors
            
            supervisor_output = supervisor.output_schema.get("properties", {})
            
            for key, specialist in agents.items():
                if key.startswith("specialist_"):
                    specialist_input = specialist.input_schema.get("properties", {})
                    
                    # Check if supervisor outputs match specialist inputs
                    for input_field in specialist_input:
                        if input_field not in supervisor_output:
                            errors.append(ValidationError(
                                error_type="contract_mismatch",
                                message=f"{specialist.name} expects input field '{input_field}' that supervisor doesn't provide",
                                suggested_solutions=[
                                    f"Update supervisor prompt to output '{input_field}'",
                                    f"Select different specialist that doesn't require '{input_field}'"
                                ]
                            ))
        
        return errors
    
    @staticmethod
    def validate_no_cycles(agents: Dict[str, Agent]) -> List[ValidationError]:
        """Validate no circular dependencies"""
        # In a real implementation, would build DAG and check for cycles
        # For now, just check basic structure
        errors = []
        
        return errors

