"""Approval workflow engine for Agent 365 integration"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from .models import (
    ApprovalRequest,
    ApprovalStatus,
    GovernancePolicy,
    ComplianceCheckResult,
)
from ..config import config

class ApprovalEngine:
    """Manages approval workflows for route deployment"""
    
    def __init__(self, policy: GovernancePolicy):
        self.policy = policy
        self.pending_requests: Dict[str, ApprovalRequest] = {}
        self.completed_requests: List[ApprovalRequest] = []
    
    async def create_approval_request(
        self,
        route_name: str,
        route_version: str,
        requester_email: str,
        agents: List[str],
        estimated_cost: float,
        estimated_volume: int,
        description: str = "",
    ) -> ApprovalRequest:
        """Create new approval request"""
        
        request_id = f"apr-{route_name}-{datetime.now(timezone.utc).timestamp()}"
        
        request = ApprovalRequest(
            request_id=request_id,
            route_name=route_name,
            route_version=route_version,
            requester_email=requester_email,
            agents_involved=agents,
            estimated_monthly_cost_usd=estimated_cost,
            estimated_daily_volume=estimated_volume,
            description=description,
        )
        
        # Set approvers based on policy
        if self.policy.require_approval:
            request.approvers = await self._assign_approvers(route_name, estimated_cost)
        
        self.pending_requests[request_id] = request
        return request
    
    async def _assign_approvers(self, route_name: str, cost: float) -> List[str]:
        """Assign approvers based on route and cost"""
        approvers = []
        
        # High-cost routes require more approvers
        if cost > self.policy.max_monthly_cost_usd * config.high_cost_approver_threshold_factor:
            approvers.extend([config.approver_finance_lead, config.approver_security_lead])
        else:
            approvers.extend([config.approver_team_lead])
        
        return approvers
    
    async def submit_approval(
        self,
        request_id: str,
        approver_email: str,
        approved: bool,
        comment: str = "",
    ) -> bool:
        """Submit approval or rejection"""
        
        if request_id not in self.pending_requests:
            return False
        
        request = self.pending_requests[request_id]
        
        if approver_email not in request.approvers:
            return False
        
        request.add_approval(approver_email, approved, comment)

        if not approved:
            request.status = ApprovalStatus.REJECTED
            request.rejection_reason = comment
            self.completed_requests.append(request)
            del self.pending_requests[request_id]
            return True

        if request.approval_count >= self.policy.approval_threshold:
            request.status = ApprovalStatus.APPROVED
            self.completed_requests.append(request)
            del self.pending_requests[request_id]

        return True
    
    async def get_pending_requests(self, approver_email: Optional[str] = None) -> List[ApprovalRequest]:
        """Get pending requests"""
        requests = list(self.pending_requests.values())
        
        if approver_email:
            requests = [r for r in requests if approver_email in r.approvers]
        
        return requests
    
    async def revoke_approval(self, request_id: str, reason: str) -> bool:
        """Revoke a previously approved request"""
        
        # Check both pending and completed
        if request_id in self.pending_requests:
            request = self.pending_requests[request_id]
        else:
            # Find in completed
            request = next((r for r in self.completed_requests if r.request_id == request_id), None)
            if not request:
                return False
        
        request.status = ApprovalStatus.REVOKED
        request.rejection_reason = reason
        
        return True
    
    async def check_compliance(
        self,
        route_name: str,
        agents: List[str],
        estimated_cost: float,
        data_sources: List[str],
    ) -> ComplianceCheckResult:
        """Check if route meets compliance requirements"""
        
        result = ComplianceCheckResult(
            passed=True,
            checks_passed=0,
            checks_failed=0,
        )
        
        # Check cost
        if estimated_cost > self.policy.max_monthly_cost_usd:
            result.add_issue(
                f"Monthly cost (${estimated_cost}) exceeds policy limit (${self.policy.max_monthly_cost_usd})"
            )
        else:
            result.checks_passed += 1
        
        # Check allowed data sources
        if self.policy.allowed_data_sources:
            for source in data_sources:
                if source not in self.policy.allowed_data_sources:
                    result.add_warning(f"Data source '{source}' not in approved list")
        else:
            result.checks_passed += 1
        
        # Check audit trail requirement
        if self.policy.require_audit_trail:
            result.checks_passed += 1
        
        return result

