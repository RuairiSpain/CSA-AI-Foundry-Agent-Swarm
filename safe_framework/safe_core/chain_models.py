"""RouteChain data models — multi-pattern sequential workflows."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class RouteChainStep:
    """One step in a RouteChain — references an existing generated route."""

    route_name: str
    # Maps this step's input field → key in the running context (previous outputs).
    field_mapping: Dict[str, str] = field(default_factory=dict)
    # Fields always pulled from the original request into this step's input.
    pass_through_fields: List[str] = field(default_factory=list)
    # Python expression evaluated against context; step is skipped if falsy.
    condition: Optional[str] = None
    # Human label shown in logs (defaults to route_name).
    label: Optional[str] = None


@dataclass
class RouteChain:
    """Ordered sequence of RouteDefinitions executed with shared context."""

    name: str
    steps: List[RouteChainStep]
    description: str = ""
    timeout_seconds: int = 600
    # "halt" raises on any step failure; "skip" logs and continues.
    on_step_failure: str = "halt"
    # Opt-in: append full input/output trace to context["_chain_history"].
    include_chain_history: bool = False
    csa_email: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = "v1.0"
