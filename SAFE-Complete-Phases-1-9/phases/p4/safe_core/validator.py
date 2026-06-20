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

        elif pattern == RoutePattern.FAN_OUT_FAN_IN:
            processor_keys = [k for k in agents if k.startswith("processor_")]
            if not processor_keys:
                errors.append(ValidationError(
                    error_type="missing_agent",
                    message="At least one processor_* agent is required for fan-out/fan-in pattern",
                    suggested_solutions=["Add processor agents with keys processor_0, processor_1, …"]
                ))

            aggregator = agents.get("aggregator")
            if not aggregator:
                errors.append(ValidationError(
                    error_type="missing_agent",
                    message="An 'aggregator' agent is required for fan-out/fan-in pattern",
                    suggested_solutions=["Add an aggregator agent with key 'aggregator'"]
                ))
            else:
                agg_input_props = aggregator.input_schema.get("properties", {})
                if "results" not in agg_input_props:
                    errors.append(ValidationError(
                        error_type="contract_mismatch",
                        message=f"Aggregator '{aggregator.name}' must accept a 'results' field in its input schema",
                        suggested_solutions=["Choose an aggregator that expects a 'results' array input"]
                    ))

        elif pattern == RoutePattern.MAP_REDUCE:
            for role in ("splitter", "mapper", "reducer"):
                if role not in agents:
                    errors.append(ValidationError(
                        error_type="missing_agent",
                        message=f"'{role}' agent is required for map-reduce pattern",
                        suggested_solutions=[f"Add an agent with key '{role}'"]
                    ))

            splitter = agents.get("splitter")
            if splitter:
                splitter_output_props = splitter.output_schema.get("properties", {})
                if "chunks" not in splitter_output_props:
                    errors.append(ValidationError(
                        error_type="contract_mismatch",
                        message=f"Splitter '{splitter.name}' must output a 'chunks' field",
                        suggested_solutions=["Choose a splitter whose output schema includes 'chunks'"]
                    ))

            mapper = agents.get("mapper")
            if mapper:
                mapper_input_props = mapper.input_schema.get("properties", {})
                mapper_output_props = mapper.output_schema.get("properties", {})
                if "data_chunk" not in mapper_input_props:
                    errors.append(ValidationError(
                        error_type="contract_mismatch",
                        message=f"Mapper '{mapper.name}' must accept a 'data_chunk' input field",
                        suggested_solutions=["Choose a mapper whose input schema includes 'data_chunk'"]
                    ))
                if "mapped_result" not in mapper_output_props:
                    errors.append(ValidationError(
                        error_type="contract_mismatch",
                        message=f"Mapper '{mapper.name}' must output a 'mapped_result' field",
                        suggested_solutions=["Choose a mapper whose output schema includes 'mapped_result'"]
                    ))

            reducer = agents.get("reducer")
            if reducer:
                reducer_input_props = reducer.input_schema.get("properties", {})
                if "mapped_results" not in reducer_input_props:
                    errors.append(ValidationError(
                        error_type="contract_mismatch",
                        message=f"Reducer '{reducer.name}' must accept a 'mapped_results' input field",
                        suggested_solutions=["Choose a reducer whose input schema includes 'mapped_results'"]
                    ))

        elif pattern == RoutePattern.SEQUENTIAL_PIPELINE:
            stage_keys = sorted(k for k in agents if k.startswith("stage_"))
            if len(stage_keys) < 2:
                errors.append(ValidationError(
                    error_type="missing_agent",
                    message="Sequential-pipeline pattern requires at least 2 stage_* agents",
                    suggested_solutions=["Add agents with keys stage_0, stage_1, …"]
                ))

            # Check each adjacent pair: stage[i] output must cover stage[i+1] required inputs
            for i in range(len(stage_keys) - 1):
                current = agents[stage_keys[i]]
                nxt = agents[stage_keys[i + 1]]
                current_output_props = current.output_schema.get("properties", {})
                next_required = nxt.input_schema.get("required", [])
                for field in next_required:
                    if field not in current_output_props:
                        errors.append(ValidationError(
                            error_type="contract_mismatch",
                            message=(
                                f"Stage '{current.name}' does not output '{field}' "
                                f"required by next stage '{nxt.name}'"
                            ),
                            suggested_solutions=[
                                f"Update '{current.name}' to output '{field}'",
                                f"Choose a different agent for stage {i + 1} that doesn't require '{field}'"
                            ]
                        ))

        return errors
    
    @staticmethod
    def validate_no_cycles(agents: Dict[str, Agent]) -> List[ValidationError]:
        """Validate no circular dependencies using depth-first search."""
        errors = []

        # Map agent names back to their dict keys for dependency resolution
        name_to_key = {agent.name: key for key, agent in agents.items()}

        # Build adjacency: key -> list of dependency keys (skip unknown deps)
        graph: Dict[str, List[str]] = {
            key: [name_to_key[dep] for dep in agent.dependencies if dep in name_to_key]
            for key, agent in agents.items()
        }

        visited: set = set()
        in_stack: set = set()

        def dfs(node: str) -> None:
            visited.add(node)
            in_stack.add(node)
            for neighbour in graph.get(node, []):
                if neighbour in in_stack:
                    errors.append(ValidationError(
                        error_type="circular_dependency",
                        message=f"Circular dependency: '{node}' -> '{neighbour}' forms a cycle",
                        suggested_solutions=[
                            f"Remove the dependency of '{node}' on '{neighbour}'",
                            "Restructure agent dependencies to eliminate the cycle",
                        ],
                    ))
                elif neighbour not in visited:
                    dfs(neighbour)
            in_stack.discard(node)

        for key in agents:
            if key not in visited:
                dfs(key)

        return errors

