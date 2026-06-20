"""Governance models for Agent 365 integration"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime

class ApprovalStatus(str, Enum):
    """Approval request status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVOKED = "revoked"

class RouteLifecycleState(str, Enum):
    """Route lifecycle states"""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending-approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEPLOYED = "deployed"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"
    DISABLED = "disabled"

class ComplianceLevel(str, Enum):
    """Compliance requirements"""
    BASIC = "basic"
    STANDARD = "standard"
    STRICT = "strict"
    REGULATED = "regulated"

@dataclass
class GovernancePolicy:
    """Organization governance policy"""
    name: str
    compliance_level: ComplianceLevel
    require_approval: bool = True
    approval_threshold: int = 1  # Number of approvers needed
    max_monthly_cost_usd: float = 10000.0
    allowed_model_types: List[str] = field(default_factory=list)
    allowed_data_sources: List[str] = field(default_factory=list)
    require_pii_handling: bool = False
    require_audit_trail: bool = True
    
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""

@dataclass
class ApprovalRequest:
    """Approval request for route deployment"""
    request_id: str
    route_name: str
    route_version: str
    requester_email: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    
    # Route details
    description: str = ""
    agents_involved: List[str] = field(default_factory=list)
    estimated_monthly_cost_usd: float = 0.0
    estimated_daily_volume: int = 0
    
    # Approval details
    approvers: List[str] = field(default_factory=list)
    approvals: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    rejection_reason: Optional[str] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    deployed_at: Optional[datetime] = None
    
    def add_approval(self, approver_email: str, approved: bool, comment: str = "") -> None:
        """Record approval/rejection from approver"""
        self.approvals[approver_email] = {
            "approved": approved,
            "comment": comment,
            "timestamp": datetime.now().isoformat(),
        }
        
        if approved:
            self.status = ApprovalStatus.APPROVED
        else:
            self.status = ApprovalStatus.REJECTED
            self.rejection_reason = comment
    
    @property
    def approval_count(self) -> int:
        """Get number of approvals received"""
        return sum(1 for a in self.approvals.values() if a.get("approved"))
    
    @property
    def is_approved(self) -> bool:
        """Check if request is approved"""
        return self.status == ApprovalStatus.APPROVED

@dataclass
class ComplianceCheckResult:
    """Result of compliance check"""
    passed: bool
    checks_passed: int
    checks_failed: int
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def add_issue(self, issue: str) -> None:
        """Add compliance issue"""
        self.issues.append(issue)
        self.checks_failed += 1
        self.passed = False
    
    def add_warning(self, warning: str) -> None:
        """Add compliance warning"""
        self.warnings.append(warning)

