"""Code generation from route definitions"""

import json
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from .models import RouteDefinition, GeneratedRoute, RoutePattern

_PATTERNS_DIR = Path(__file__).parent.parent / "agents" / "patterns"

_PATTERN_TEMPLATE_DIRS = {
    RoutePattern.SUPERVISOR_MANAGER: _PATTERNS_DIR / "supervisor-manager",
    RoutePattern.FAN_OUT_FAN_IN:     _PATTERNS_DIR / "fan-out-fan-in",
    RoutePattern.MAP_REDUCE:         _PATTERNS_DIR / "map-reduce",
    RoutePattern.SEQUENTIAL_PIPELINE: _PATTERNS_DIR / "sequential-pipeline",
}

def _get_template(pattern: RoutePattern):
    template_dir = _PATTERN_TEMPLATE_DIRS[pattern]
    env = Environment(loader=FileSystemLoader(str(template_dir)), keep_trailing_newline=True)
    return env.get_template("route.py.jinja2")


class RouteCodeGenerator:
    """Generates production-ready route code from definitions"""

    @staticmethod
    def generate(route_def: RouteDefinition) -> GeneratedRoute:
        """Generate complete route from definition"""
        if route_def.pattern == RoutePattern.SUPERVISOR_MANAGER:
            return RouteCodeGenerator._generate_supervisor_manager(route_def)
        elif route_def.pattern == RoutePattern.FAN_OUT_FAN_IN:
            return RouteCodeGenerator._generate_fan_out_fan_in(route_def)
        elif route_def.pattern == RoutePattern.MAP_REDUCE:
            return RouteCodeGenerator._generate_map_reduce(route_def)
        elif route_def.pattern == RoutePattern.SEQUENTIAL_PIPELINE:
            return RouteCodeGenerator._generate_sequential_pipeline(route_def)
        else:
            raise NotImplementedError(f"Pattern {route_def.pattern} not yet implemented")

    @staticmethod
    def _class_name(route_name: str) -> str:
        return "".join(w.capitalize() for w in route_name.replace("-", "_").split("_"))

    @staticmethod
    def _generate_supervisor_manager(route_def: RouteDefinition) -> GeneratedRoute:
        supervisor_key = "supervisor"
        specialists = {k: v for k, v in route_def.agents.items() if k.startswith("specialist_")}
        aggregator_key = "aggregator"

        supervisor = route_def.agents[supervisor_key]
        input_required = supervisor.input_schema.get("required", [])
        aggregator = route_def.agents[aggregator_key]
        output_required = aggregator.output_schema.get("required", [])

        context = {
            "route_name": route_def.name,
            "class_name": RouteCodeGenerator._class_name(route_def.name),
            "description": route_def.description,
            "pattern": route_def.pattern.value,
            "agent_names": ", ".join(route_def.agents.keys()),
            "created_at": datetime.now().strftime("%Y-%m-%d"),
            "agents": route_def.agents,
            "supervisor_key": supervisor_key,
            "specialists": specialists,
            "aggregator_key": aggregator_key,
            "routing_field": route_def.routing_field or "specialist",
            "required_input_fields": json.dumps(input_required),
            "required_output_fields": json.dumps(output_required),
        }

        route_code = _get_template(RoutePattern.SUPERVISOR_MANAGER).render(**context)
        return GeneratedRoute(
            route_code=route_code,
            requirements_txt=RouteCodeGenerator._generate_requirements(route_def),
            config_yaml=RouteCodeGenerator._generate_config(route_def),
            test_data_json=RouteCodeGenerator._generate_test_data(route_def),
            metadata={
                "pattern": route_def.pattern.value,
                "agents": list(route_def.agents.keys()),
                "created_at": datetime.now().isoformat(),
                "version": "v1.0",
            }
        )

    @staticmethod
    def _generate_fan_out_fan_in(route_def: RouteDefinition) -> GeneratedRoute:
        processor_keys = sorted(k for k in route_def.agents if k.startswith("processor_"))
        aggregator_key = "aggregator"

        first_processor = route_def.agents.get(processor_keys[0]) if processor_keys else None
        input_required = first_processor.input_schema.get("required", []) if first_processor else []
        aggregator = route_def.agents.get(aggregator_key)
        output_required = aggregator.output_schema.get("required", []) if aggregator else []

        context = {
            "route_name": route_def.name,
            "class_name": RouteCodeGenerator._class_name(route_def.name),
            "description": route_def.description,
            "pattern": route_def.pattern.value,
            "agent_names": ", ".join(route_def.agents.keys()),
            "created_at": datetime.now().strftime("%Y-%m-%d"),
            "agents": route_def.agents,
            "processor_keys": processor_keys,
            "processor_count": len(processor_keys),
            "aggregator_key": aggregator_key,
            "required_input_fields": json.dumps(input_required),
            "required_output_fields": json.dumps(output_required),
        }

        route_code = _get_template(RoutePattern.FAN_OUT_FAN_IN).render(**context)
        return GeneratedRoute(
            route_code=route_code,
            requirements_txt=RouteCodeGenerator._generate_requirements(route_def),
            config_yaml=RouteCodeGenerator._generate_config(route_def),
            test_data_json=RouteCodeGenerator._generate_test_data(route_def),
            metadata={
                "pattern": route_def.pattern.value,
                "agents": list(route_def.agents.keys()),
                "created_at": datetime.now().isoformat(),
                "version": "v1.0",
            }
        )

    @staticmethod
    def _generate_map_reduce(route_def: RouteDefinition) -> GeneratedRoute:
        splitter_key = "splitter"
        mapper_key = "mapper"
        reducer_key = "reducer"

        splitter = route_def.agents.get(splitter_key)
        input_required = splitter.input_schema.get("required", []) if splitter else []
        reducer = route_def.agents.get(reducer_key)
        output_required = reducer.output_schema.get("required", []) if reducer else []

        context = {
            "route_name": route_def.name,
            "class_name": RouteCodeGenerator._class_name(route_def.name),
            "description": route_def.description,
            "pattern": route_def.pattern.value,
            "agent_names": ", ".join(route_def.agents.keys()),
            "created_at": datetime.now().strftime("%Y-%m-%d"),
            "agents": route_def.agents,
            "splitter_key": splitter_key,
            "mapper_key": mapper_key,
            "reducer_key": reducer_key,
            "required_input_fields": json.dumps(input_required),
            "required_output_fields": json.dumps(output_required),
        }

        route_code = _get_template(RoutePattern.MAP_REDUCE).render(**context)
        return GeneratedRoute(
            route_code=route_code,
            requirements_txt=RouteCodeGenerator._generate_requirements(route_def),
            config_yaml=RouteCodeGenerator._generate_config(route_def),
            test_data_json=RouteCodeGenerator._generate_test_data(route_def),
            metadata={
                "pattern": route_def.pattern.value,
                "agents": list(route_def.agents.keys()),
                "created_at": datetime.now().isoformat(),
                "version": "v1.0",
            }
        )

    @staticmethod
    def _generate_sequential_pipeline(route_def: RouteDefinition) -> GeneratedRoute:
        stage_keys = sorted(k for k in route_def.agents if k.startswith("stage_"))

        first_stage = route_def.agents.get(stage_keys[0]) if stage_keys else None
        input_required = first_stage.input_schema.get("required", []) if first_stage else []
        last_stage = route_def.agents.get(stage_keys[-1]) if stage_keys else None
        output_required = last_stage.output_schema.get("required", []) if last_stage else []

        context = {
            "route_name": route_def.name,
            "class_name": RouteCodeGenerator._class_name(route_def.name),
            "description": route_def.description,
            "pattern": route_def.pattern.value,
            "agent_names": ", ".join(route_def.agents.keys()),
            "created_at": datetime.now().strftime("%Y-%m-%d"),
            "agents": route_def.agents,
            "stage_keys": stage_keys,
            "stage_count": len(stage_keys),
            "required_input_fields": json.dumps(input_required),
            "required_output_fields": json.dumps(output_required),
        }

        route_code = _get_template(RoutePattern.SEQUENTIAL_PIPELINE).render(**context)
        return GeneratedRoute(
            route_code=route_code,
            requirements_txt=RouteCodeGenerator._generate_requirements(route_def),
            config_yaml=RouteCodeGenerator._generate_config(route_def),
            test_data_json=RouteCodeGenerator._generate_test_data(route_def),
            metadata={
                "pattern": route_def.pattern.value,
                "agents": list(route_def.agents.keys()),
                "created_at": datetime.now().isoformat(),
                "version": "v1.0",
            }
        )

    @staticmethod
    def _generate_requirements(route_def: RouteDefinition) -> str:
        requirements = [
            "semantic-kernel>=0.4.0",
            "azure-ai>=1.0.0",
            "pydantic>=2.0.0",
            "python-dateutil>=2.8.0",
        ]
        return "\n".join(requirements) + "\n"

    @staticmethod
    def _generate_config(route_def: RouteDefinition) -> str:
        config = f"""# {route_def.name} - v1.0

name: {route_def.name}
version: v1.0
pattern: {route_def.pattern.value}
description: {route_def.description}

agents:
"""
        for key, agent in route_def.agents.items():
            config += f"  {key}: {agent.name}\n"

        config += f"""
timeouts:
  total_seconds: {route_def.timeout_seconds}
  per_agent_seconds: {route_def.per_agent_timeout_seconds}

metadata:
  created_at: {datetime.now().isoformat()}
  created_by: {route_def.csa_email}
"""
        return config

    @staticmethod
    def _generate_test_data(route_def: RouteDefinition) -> str:
        pattern = route_def.pattern

        if pattern == RoutePattern.SUPERVISOR_MANAGER:
            test_data = [
                {
                    "name": "test_case_1",
                    "input": {"amount": 100000, "loan_type": "mortgage", "credit_score": 750},
                    "expected": {"decision": "approved"},
                },
                {
                    "name": "test_case_2",
                    "input": {"amount": 30000, "loan_type": "auto", "credit_score": 680},
                    "expected": {"decision": "approved"},
                },
            ]
        elif pattern == RoutePattern.FAN_OUT_FAN_IN:
            test_data = [
                {
                    "name": "test_case_1",
                    "input": {"data": {"id": 1, "payload": "sample"}},
                    "expected": {"combined_result": {}},
                },
            ]
        elif pattern == RoutePattern.MAP_REDUCE:
            test_data = [
                {
                    "name": "test_case_1",
                    "input": {"data": [{"item": i} for i in range(5)], "chunk_size": 2},
                    "expected": {"reduced_result": {}},
                },
            ]
        elif pattern == RoutePattern.SEQUENTIAL_PIPELINE:
            test_data = [
                {
                    "name": "test_case_1",
                    "input": {"input_data": {"field": "value"}},
                    "expected": {"output_data": {}},
                },
            ]
        else:
            test_data = [{"name": "test_case_1", "input": {}, "expected": {}}]

        return json.dumps(test_data, indent=2) + "\n"
