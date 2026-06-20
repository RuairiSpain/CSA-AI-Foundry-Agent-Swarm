"""CLI commands for governance and Agent 365 integration"""

import asyncio
from typing import Optional
from safe_core.governance.models import GovernancePolicy, ComplianceLevel, ApprovalStatus
from safe_core.governance.approval_engine import ApprovalEngine
from safe_core.lifecycle.manager import RouteLifecycleManager
from safe_core.audit.logger import AuditLogger, AuditEventType

class GovernanceCLI:
    """CLI for governance operations"""
    
    def __init__(self):
        self.policy = GovernancePolicy(
            name="Default Policy",
            compliance_level=ComplianceLevel.STANDARD,
            require_approval=True,
            approval_threshold=1,
            max_monthly_cost_usd=10000.0,
        )
        self.approval_engine = ApprovalEngine(self.policy)
        self.lifecycle = RouteLifecycleManager()
        self.audit = AuditLogger()
    
    async def request_approval(
        self,
        route_name: str,
        route_version: str,
        requester: str,
        agents: list,
        estimated_cost: float,
        estimated_volume: int,
    ) -> None:
        """Request approval for route deployment"""
        
        # Create approval request
        request = await self.approval_engine.create_approval_request(
            route_name=route_name,
            route_version=route_version,
            requester_email=requester,
            agents=agents,
            estimated_cost=estimated_cost,
            estimated_volume=estimated_volume,
        )
        
        # Log audit event
        await self.audit.log_event(
            event_type=AuditEventType.APPROVAL_REQUESTED,
            actor=requester,
            resource="route",
            resource_id=f"{route_name}:{route_version}",
            details={
                "request_id": request.request_id,
                "estimated_cost": estimated_cost,
                "agents": agents,
            },
            compliance_relevant=True,
        )
        
        print(f"\n✓ Approval request created: {request.request_id}")
        print(f"  Route: {route_name} {route_version}")
        print(f"  Requester: {requester}")
        print(f"  Approvers needed: {request.approvers}")
        print(f"  Estimated cost: ${estimated_cost:.2f}/month")
    
    async def approve_request(
        self,
        request_id: str,
        approver: str,
        comment: str = "",
    ) -> None:
        """Approve a route deployment request"""
        
        requests = await self.approval_engine.get_pending_requests()
        request = next((r for r in requests if r.request_id == request_id), None)
        
        if not request:
            print(f"✗ Request not found: {request_id}")
            return
        
        # Submit approval
        success = await self.approval_engine.submit_approval(
            request_id=request_id,
            approver_email=approver,
            approved=True,
            comment=comment,
        )
        
        if success:
            # Log approval
            await self.audit.log_event(
                event_type=AuditEventType.APPROVAL_GRANTED,
                actor=approver,
                resource="route",
                resource_id=f"{request.route_name}:{request.route_version}",
                details={"request_id": request_id, "comment": comment},
                compliance_relevant=True,
                severity="info",
            )
            
            print(f"✓ Approval granted by {approver}")
            
            if request.is_approved:
                print(f"✓ Request approved! Ready for deployment.")
    
    async def show_pending_approvals(self, approver: Optional[str] = None) -> None:
        """Show pending approval requests"""
        
        pending = await self.approval_engine.get_pending_requests(approver)
        
        if not pending:
            print("\nNo pending approvals")
            return
        
        print("\n" + "="*70)
        print("Pending Approval Requests")
        print("="*70)
        
        for req in pending:
            print(f"\nRequest ID: {req.request_id}")
            print(f"Route: {req.route_name} {req.route_version}")
            print(f"Requester: {req.requester_email}")
            print(f"Estimated Cost: ${req.estimated_monthly_cost_usd:.2f}/month")
            print(f"Agents: {', '.join(req.agents_involved)}")
            print(f"Status: {req.status.value}")
            print(f"Approvals: {req.approval_count}/{len(req.approvers)}")
            print(f"Approvers: {', '.join(req.approvers)}")
    
    async def show_audit_trail(self, resource: Optional[str] = None) -> None:
        """Show audit trail"""
        
        events = await self.audit.get_events(resource=resource, limit=20)
        
        if not events:
            print("\nNo audit events")
            return
        
        print("\n" + "="*70)
        print("Audit Trail")
        print("="*70)
        
        for event in events:
            print(f"\n[{event.timestamp.isoformat()}] {event.event_type.value}")
            print(f"  Actor: {event.actor}")
            print(f"  Resource: {event.resource} ({event.resource_id})")
            if event.details:
                print(f"  Details: {event.details}")
    
    async def check_compliance(
        self,
        route_name: str,
        agents: list,
        estimated_cost: float,
        data_sources: list,
    ) -> None:
        """Check route compliance"""
        
        result = await self.approval_engine.check_compliance(
            route_name=route_name,
            agents=agents,
            estimated_cost=estimated_cost,
            data_sources=data_sources,
        )
        
        print(f"\n{'='*70}")
        print(f"Compliance Check: {route_name}")
        print(f"{'='*70}")
        
        print(f"\nStatus: {'✓ PASSED' if result.passed else '✗ FAILED'}")
        print(f"Checks Passed: {result.checks_passed}")
        print(f"Checks Failed: {result.checks_failed}")
        
        if result.issues:
            print("\nIssues:")
            for issue in result.issues:
                print(f"  ✗ {issue}")
        
        if result.warnings:
            print("\nWarnings:")
            for warning in result.warnings:
                print(f"  ⚠ {warning}")
    
    async def export_compliance_report(self) -> None:
        """Export compliance audit report"""
        
        report = await self.audit.export_compliance_report()
        
        print(f"\n{'='*70}")
        print("Compliance Audit Report")
        print(f"{'='*70}")
        
        print(f"\nGenerated: {report['timestamp']}")
        print(f"Total Events: {report['total_events']}")
        print(f"Compliance Events: {report['compliance_events']}")
        print(f"Critical Events: {report['critical_events']}")
        print(f"Warning Events: {report['warning_events']}")
        
        if report['critical_events'] > 0:
            print("\n🚨 CRITICAL EVENTS DETECTED - Review required")

async def main():
    """Example usage"""
    cli = GovernanceCLI()
    
    # Request approval
    await cli.request_approval(
        route_name="loan-approval-v1",
        route_version="v1.0",
        requester="bea@microsoft.com",
        agents=["supervisor", "specialist-mortgage", "aggregator"],
        estimated_cost=500.00,
        estimated_volume=1000,
    )
    
    # Show pending
    await cli.show_pending_approvals()
    
    # Check compliance
    await cli.check_compliance(
        route_name="loan-approval-v1",
        agents=["supervisor", "specialist-mortgage", "aggregator"],
        estimated_cost=500.00,
        data_sources=["credit-bureau", "income-verification"],
    )
    
    # Export report
    await cli.export_compliance_report()

if __name__ == "__main__":
    asyncio.run(main())

