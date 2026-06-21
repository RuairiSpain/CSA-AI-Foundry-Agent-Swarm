"""Contract validation for routes and agents"""

from typing import List, Dict, Any
from .models import RouteDefinition, Agent, ValidationError, RoutePattern

class ContractValidator:
    """Validates route and agent contracts"""
    
    @staticmethod
    def validate_route(
        route_def: RouteDefinition,
        *,
        ignore_handoff_refs: bool = True,
    ) -> List[ValidationError]:
        """Validate complete route definition.

        Args:
            route_def: The route to validate.
            ignore_handoff_refs: When True (default), agents that declare a
                ``handoff_ref`` are excluded from input/output contract checks.
                Their declared output schema is taken at face value. Set to
                False to also run HandoffValidator on each referenced handoff
                (requires the handoff config.yaml to be on disk).
        """
        errors = []

        agents_to_validate = (
            {k: v for k, v in route_def.agents.items() if not v.handoff_ref}
            if ignore_handoff_refs
            else route_def.agents
        )

        # Validate timeouts
        timeout_errors = ContractValidator.validate_timeouts(
            route_def.timeout_seconds,
            route_def.per_agent_timeout_seconds
        )
        errors.extend(timeout_errors)

        # Validate agent contracts match pattern (using filtered agent set)
        contract_errors = ContractValidator.validate_agent_contracts(
            route_def.pattern,
            agents_to_validate
        )
        errors.extend(contract_errors)

        # Validate no circular dependencies (full agent set — handoff agents
        # still participate in the route dependency graph)
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

        elif pattern == RoutePattern.ROUND_ROBIN:
            if "dispatcher" not in agents:
                errors.append(ValidationError(
                    error_type="missing_agent",
                    message="'dispatcher' agent is required for round-robin pattern",
                    suggested_solutions=["Add an agent with key 'dispatcher'"]
                ))
            worker_keys = [k for k in agents if k.startswith("worker_")]
            if len(worker_keys) < 2:
                errors.append(ValidationError(
                    error_type="missing_agent",
                    message="Round-robin pattern requires at least 2 worker_* agents",
                    suggested_solutions=["Add agents with keys worker_0, worker_1, …"]
                ))

        elif pattern == RoutePattern.MIXTURE_OF_EXPERTS:
            if "router" not in agents:
                errors.append(ValidationError(
                    error_type="missing_agent",
                    message="'router' agent is required for mixture-of-experts pattern",
                    suggested_solutions=["Add an agent with key 'router'"]
                ))
            expert_keys = [k for k in agents if k.startswith("expert_")]
            if not expert_keys:
                errors.append(ValidationError(
                    error_type="missing_agent",
                    message="At least one expert_* agent is required for mixture-of-experts pattern",
                    suggested_solutions=["Add agents with keys expert_0, expert_1, …"]
                ))
            aggregator = agents.get("aggregator")
            if not aggregator:
                errors.append(ValidationError(
                    error_type="missing_agent",
                    message="'aggregator' agent is required for mixture-of-experts pattern",
                    suggested_solutions=["Add an aggregator agent with key 'aggregator'"]
                ))
            else:
                agg_input_props = aggregator.input_schema.get("properties", {})
                if "expert_outputs" not in agg_input_props:
                    errors.append(ValidationError(
                        error_type="contract_mismatch",
                        message=f"Aggregator '{aggregator.name}' must accept 'expert_outputs' in its input schema",
                        suggested_solutions=["Choose an aggregator that expects an 'expert_outputs' input field"]
                    ))

        elif pattern == RoutePattern.HIERARCHICAL_TEAMS:
            if "coordinator" not in agents:
                errors.append(ValidationError(
                    error_type="missing_agent",
                    message="'coordinator' agent is required for hierarchical-teams pattern",
                    suggested_solutions=["Add an agent with key 'coordinator'"]
                ))
            team_keys = [k for k in agents if k.startswith("team_")]
            if len(team_keys) < 2:
                errors.append(ValidationError(
                    error_type="missing_agent",
                    message="Hierarchical-teams pattern requires at least 2 team_* agents",
                    suggested_solutions=["Add agents with keys team_0, team_1, …"]
                ))
            aggregator = agents.get("aggregator")
            if not aggregator:
                errors.append(ValidationError(
                    error_type="missing_agent",
                    message="'aggregator' agent is required for hierarchical-teams pattern",
                    suggested_solutions=["Add an aggregator agent with key 'aggregator'"]
                ))
            else:
                agg_input_props = aggregator.input_schema.get("properties", {})
                if "team_results" not in agg_input_props:
                    errors.append(ValidationError(
                        error_type="contract_mismatch",
                        message=f"Aggregator '{aggregator.name}' must accept 'team_results' in its input schema",
                        suggested_solutions=["Choose an aggregator that expects a 'team_results' input field"]
                    ))

        elif pattern == RoutePattern.FALLBACK_CHAIN:
            if "primary" not in agents:
                errors.append(ValidationError(
                    error_type="missing_agent",
                    message="'primary' agent is required for fallback-chain pattern",
                    suggested_solutions=["Add an agent with key 'primary'"]
                ))
            fallback_keys = [k for k in agents if k.startswith("fallback_")]
            if not fallback_keys:
                errors.append(ValidationError(
                    error_type="missing_agent",
                    message="At least one fallback_* agent is required for fallback-chain pattern",
                    suggested_solutions=["Add agents with keys fallback_0, fallback_1, …"]
                ))

        elif pattern == RoutePattern.RETRY_LOOP:
            if "worker" not in agents:
                errors.append(ValidationError(
                    error_type="missing_agent",
                    message="'worker' agent is required for retry-loop pattern",
                    suggested_solutions=["Add an agent with key 'worker'"]
                ))
            validator_agent = agents.get("validator")
            if not validator_agent:
                errors.append(ValidationError(
                    error_type="missing_agent",
                    message="'validator' agent is required for retry-loop pattern",
                    suggested_solutions=["Add an agent with key 'validator'"]
                ))
            else:
                validator_output_props = validator_agent.output_schema.get("properties", {})
                if "valid" not in validator_output_props:
                    errors.append(ValidationError(
                        error_type="contract_mismatch",
                        message=f"Validator '{validator_agent.name}' must output a 'valid' field",
                        suggested_solutions=["Choose a validator whose output schema includes 'valid'"]
                    ))

        elif pattern == RoutePattern.DIAMOND:
            splitter = agents.get("splitter")
            if not splitter:
                errors.append(ValidationError(
                    error_type="missing_agent",
                    message="'splitter' agent is required for diamond pattern",
                    suggested_solutions=["Add an agent with key 'splitter'"]
                ))
            else:
                splitter_output_props = splitter.output_schema.get("properties", {})
                for required_field in ("left", "right"):
                    if required_field not in splitter_output_props:
                        errors.append(ValidationError(
                            error_type="contract_mismatch",
                            message=f"Splitter '{splitter.name}' must output '{required_field}' field",
                            suggested_solutions=[f"Choose a splitter whose output schema includes '{required_field}'"]
                        ))
            for role in ("left_processor", "right_processor"):
                if role not in agents:
                    errors.append(ValidationError(
                        error_type="missing_agent",
                        message=f"'{role}' agent is required for diamond pattern",
                        suggested_solutions=[f"Add an agent with key '{role}'"]
                    ))
            merger = agents.get("merger")
            if not merger:
                errors.append(ValidationError(
                    error_type="missing_agent",
                    message="'merger' agent is required for diamond pattern",
                    suggested_solutions=["Add an agent with key 'merger'"]
                ))
            else:
                merger_input_props = merger.input_schema.get("properties", {})
                for required_field in ("left_result", "right_result"):
                    if required_field not in merger_input_props:
                        errors.append(ValidationError(
                            error_type="contract_mismatch",
                            message=f"Merger '{merger.name}' must accept '{required_field}' in its input schema",
                            suggested_solutions=[f"Choose a merger whose input schema includes '{required_field}'"]
                        ))

        elif pattern == RoutePattern.CONDITIONAL_BRANCHING:
            if "evaluator" not in agents:
                errors.append(ValidationError(
                    error_type="missing_agent",
                    message="'evaluator' agent is required for conditional-branching pattern",
                    suggested_solutions=["Add an agent with key 'evaluator'"]
                ))
            branch_keys = [k for k in agents if k.startswith("branch_")]
            if len(branch_keys) < 2:
                errors.append(ValidationError(
                    error_type="missing_agent",
                    message="Conditional-branching pattern requires at least 2 branch_* agents",
                    suggested_solutions=["Add agents with keys branch_0, branch_1, …"]
                ))

        elif pattern == RoutePattern.TREE_REDUCE:
            leaf_keys = [k for k in agents if k.startswith("leaf_")]
            if len(leaf_keys) < 2:
                errors.append(ValidationError(
                    error_type="missing_agent",
                    message="Tree-reduce pattern requires at least 2 leaf_* agents",
                    suggested_solutions=["Add agents with keys leaf_0, leaf_1, …"]
                ))
            reducer = agents.get("reducer")
            if not reducer:
                errors.append(ValidationError(
                    error_type="missing_agent",
                    message="'reducer' agent is required for tree-reduce pattern",
                    suggested_solutions=["Add an agent with key 'reducer'"]
                ))
            else:
                reducer_input_props = reducer.input_schema.get("properties", {})
                reducer_output_props = reducer.output_schema.get("properties", {})
                for required_field in ("left", "right"):
                    if required_field not in reducer_input_props:
                        errors.append(ValidationError(
                            error_type="contract_mismatch",
                            message=f"Reducer '{reducer.name}' must accept '{required_field}' in its input schema",
                            suggested_solutions=[f"Choose a reducer whose input schema includes '{required_field}'"]
                        ))
                if "result" not in reducer_output_props:
                    errors.append(ValidationError(
                        error_type="contract_mismatch",
                        message=f"Reducer '{reducer.name}' must output a 'result' field",
                        suggested_solutions=["Choose a reducer whose output schema includes 'result'"]
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

