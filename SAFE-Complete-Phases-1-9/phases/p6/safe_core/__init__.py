"""
SAFE Framework Phase 6: Agent 365 Integration
Governance, approval workflows, and lifecycle management
"""

__version__ = "1.0.0"
__author__ = "Microsoft CSA Team"

from .governance.models import (
    GovernancePolicy,
    ApprovalRequest,
    ApprovalStatus,
)
from .lifecycle.manager import RouteLifecycleManager
from .audit.logger import AuditLogger

__all__ = [
    "GovernancePolicy",
    "ApprovalRequest",
    "ApprovalStatus",
    "RouteLifecycleManager",
    "AuditLogger",
]
