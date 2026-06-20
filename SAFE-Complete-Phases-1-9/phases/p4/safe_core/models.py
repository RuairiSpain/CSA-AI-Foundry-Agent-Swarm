"""Data models for Route Writer Agent"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime

class RoutePattern(str, Enum):
    """Supported route patterns"""
    SUPERVISOR_MANAGER = "supervisor-manager"
    FAN_OUT_FAN_IN = "fan-out-fan-in"
    MAP_REDUCE = "map-reduce"
    SEQUENTIAL_PIPELINE = "sequential-pipeline"

@dataclass
class Agent:
    """Agent definition from catalog"""
    name: str
    category: str
    version: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    description: str = ""
    example_usage: str = ""

@dataclass
class RouteDefinition:
    """Complete route definition"""
    name: str
    pattern: RoutePattern
    agents: Dict[str, Agent]
    description: str = ""
    timeout_seconds: int = 120
    per_agent_timeout_seconds: int = 60
    csa_email: str = ""
    tags: List[str] = field(default_factory=list)
    
    # Pattern-specific config
    routing_field: Optional[str] = None  # For supervisor-manager
    routing_rules: Dict[str, str] = field(default_factory=dict)  # value -> agent_key
    fallback_agent: Optional[str] = None
    
    created_at: datetime = field(default_factory=datetime.now)
    version: str = "v1.0"

@dataclass
class ValidationError:
    """Validation error details"""
    error_type: str  # "contract_mismatch", "circular_dependency", "timeout", etc
    message: str
    suggested_solutions: List[str] = field(default_factory=list)

@dataclass
class GeneratedRoute:
    """Output of code generation"""
    route_code: str  # Generated Python code
    requirements_txt: str
    config_yaml: str
    test_data_json: str
    metadata: Dict[str, Any]
    
    def save_to_disk(self, route_dir: str) -> None:
        """Save generated files to disk"""
        import os
        os.makedirs(route_dir, exist_ok=True)
        
        with open(f"{route_dir}/route.py", "w") as f:
            f.write(self.route_code)
        with open(f"{route_dir}/requirements.txt", "w") as f:
            f.write(self.requirements_txt)
        with open(f"{route_dir}/config.yaml", "w") as f:
            f.write(self.config_yaml)
        with open(f"{route_dir}/test_data.json", "w") as f:
            f.write(self.test_data_json)

@dataclass
class TestResult:
    """Route test result"""
    success: bool
    test_cases_passed: int
    test_cases_failed: int
    errors: List[str] = field(default_factory=list)
    execution_times: Dict[str, float] = field(default_factory=dict)

