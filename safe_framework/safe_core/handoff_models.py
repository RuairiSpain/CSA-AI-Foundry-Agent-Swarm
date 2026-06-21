"""HandoffPattern models — Azure AI Foundry ConnectedAgentTool delegation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List


class HandoffPattern(str, Enum):
    """Azure AI Foundry ConnectedAgentTool handoff topologies.

    These are fundamentally different from RoutePattern values: the execution
    graph is decided at runtime by the parent agent's LLM, not by a static
    wiring defined at authoring time.
    """
    DIRECT = "direct-handoff"
    SELECTIVE = "selective-handoff"
    SEQUENTIAL = "sequential-handoff"
    HIERARCHICAL = "hierarchical-handoff"
    RECURSIVE = "recursive-handoff"


@dataclass
class SubAgent:
    """Descriptor for one sub-agent available in a handoff pool.

    Restriction fields
    ------------------
    allowed_callers : list of role keys (e.g. ``["coordinator"]``) that may
        invoke this sub-agent.  When set, the code generator only includes
        this sub-agent's ``ConnectedAgentTool`` definition in the tool list
        of matching callers.  ``None`` / empty list = unrestricted.

    max_calls : maximum number of times this sub-agent may be invoked within
        a single ``invoke()`` call.  0 = unlimited.  Enforced via explicit
        instructions injected into the parent agent's system prompt; Azure AI
        Foundry does not expose per-tool call interception natively.
    """
    name: str
    description: str
    capability_tags: List[str] = field(default_factory=list)
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    allowed_callers: List[str] = field(default_factory=list)   # [] = unrestricted
    max_calls: int = 0                                          # 0 = unlimited


@dataclass
class HandoffDefinition:
    """Complete definition for a ConnectedAgentTool handoff flow.

    A HandoffDefinition can be used in two ways:
      1. Standalone — invoked directly via ``safe handoff run <name>`` or as a
         chain step (``route_name: "handoff:<name>"``).
      2. Embedded — referenced from an Agent inside a RouteDefinition via
         ``Agent.handoff_ref``. The route's deterministic path is preserved;
         the handoff is entirely contained within that one agent's execution.
    """
    name: str
    pattern: HandoffPattern
    sub_agents: Dict[str, SubAgent]
    description: str = ""
    max_depth: int = 3
    return_policy: str = "always"       # "always" | "on_partial" | "on_failure"
    timeout_seconds: int = 120
    csa_email: str = ""
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    version: str = "v1.0"


@dataclass
class GeneratedHandoff:
    """Output of HandoffCodeGenerator.generate()."""
    handoff_code: str
    requirements_txt: str
    config_yaml: str
    metadata: Dict[str, Any]

    def save_to_disk(self, handoff_dir: str) -> None:
        import os
        os.makedirs(handoff_dir, exist_ok=True)
        with open(f"{handoff_dir}/handoff.py", "w") as f:
            f.write(self.handoff_code)
        with open(f"{handoff_dir}/requirements.txt", "w") as f:
            f.write(self.requirements_txt)
        with open(f"{handoff_dir}/config.yaml", "w") as f:
            f.write(self.config_yaml)
