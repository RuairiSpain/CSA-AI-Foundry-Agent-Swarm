"""Comprehensive tests for Phase 6: Agent 365 Integration"""

import pytest
import asyncio
from safe_core.governance.models import (
    GovernancePolicy,
    ComplianceLevel,
    ApprovalRequest,
    ApprovalStatus,
    RouteLifecycleState,
)
from safe_core.governance.approval_engine import ApprovalEngine
from safe_core.lifecycle.manager import RouteLifecycleManager
from safe_core.audit.logger import AuditLogger, AuditEventType

class TestGovernanceModels:
    """Tests for governance data models"""

    def test_governance_policy_creation(self):
        """Test creating governance policy"""
        policy = GovernancePolicy(
            name="Test Policy",
            compliance_level=ComplianceLevel.STRICT,
            require_approval=True,
            max_monthly_cost_usd=5000.0,
        )

        assert policy.name == "Test Policy"
        assert policy.compliance_level == ComplianceLevel.STRICT
        assert policy.require_approval is True

    def test_approval_request_creation(self):
        """Test creating approval request"""
        request = ApprovalRequest(
            request_id="apr-test-001",
            route_name="test-route",
            route_version="v1.0",
            requester_email="user@example.com",
            status=ApprovalStatus.PENDING,
            estimated_monthly_cost_usd=1000.0,
        )

        assert request.request_id == "apr-test-001"
        assert request.status == ApprovalStatus.PENDING

    def test_approval_submission(self):
        """Test submitting approval"""
        request = ApprovalRequest(
            request_id="apr-test-001",
            route_name="test-route",
            route_version="v1.0",
            requester_email="user@example.com",
            approvers=["approver@example.com"],
        )

        # Add approval
        request.add_approval("approver@example.com", True, "Looks good")

        assert request.approval_count == 1
        assert request.is_approved


class TestApprovalEngine:
    """Tests for approval workflow engine"""

    @pytest.mark.asyncio
    async def test_create_approval_request(self):
        """Test creating approval request"""
        policy = GovernancePolicy(
            name="Test",
            compliance_level=ComplianceLevel.STANDARD,
        )
        engine = ApprovalEngine(policy)

        request = await engine.create_approval_request(
            route_name="test-route",
            route_version="v1.0",
            requester_email="user@example.com",
            agents=["agent-1", "agent-2"],
            estimated_cost=500.0,
            estimated_volume=1000,
        )

        assert request.route_name == "test-route"
        assert request.status == ApprovalStatus.PENDING

    @pytest.mark.asyncio
    async def test_submit_approval(self):
        """Test submitting approval"""
        policy = GovernancePolicy(
            name="Test",
            compliance_level=ComplianceLevel.STANDARD,
            approval_threshold=1,
        )
        engine = ApprovalEngine(policy)

        # Create request
        request = await engine.create_approval_request(
            route_name="test-route",
            route_version="v1.0",
            requester_email="user@example.com",
            agents=["agent-1"],
            estimated_cost=500.0,
            estimated_volume=1000,
        )

        # Submit approval
        result = await engine.submit_approval(
            request_id=request.request_id,
            approver_email=request.approvers[0],
            approved=True,
            comment="Approved",
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_compliance_check_pass(self):
        """Test passing compliance check"""
        policy = GovernancePolicy(
            name="Test",
            max_monthly_cost_usd=10000.0,
        )
        engine = ApprovalEngine(policy)

        result = await engine.check_compliance(
            route_name="test-route",
            agents=["agent-1"],
            estimated_cost=5000.0,
            data_sources=[],
        )

        assert result.passed is True

    @pytest.mark.asyncio
    async def test_compliance_check_fail(self):
        """Test failing compliance check"""
        policy = GovernancePolicy(
            name="Test",
            max_monthly_cost_usd=1000.0,
        )
        engine = ApprovalEngine(policy)

        result = await engine.check_compliance(
            route_name="test-route",
            agents=["agent-1"],
            estimated_cost=5000.0,
            data_sources=[],
        )

        assert result.passed is False
        assert len(result.issues) > 0


class TestLifecycleManager:
    """Tests for route lifecycle management"""

    @pytest.mark.asyncio
    async def test_create_route_entry(self):
        """Test creating route lifecycle entry"""
        manager = RouteLifecycleManager()

        await manager.create_route_entry("test-route", "v1.0")

        state = await manager.get_route_state("test-route", "v1.0")
        assert state == RouteLifecycleState.DRAFT

    @pytest.mark.asyncio
    async def test_state_transition(self):
        """Test state transitions"""
        manager = RouteLifecycleManager()

        await manager.create_route_entry("test-route", "v1.0")

        # Transition to pending approval
        result = await manager.transition_state(
            "test-route",
            "v1.0",
            RouteLifecycleState.PENDING_APPROVAL,
            actor="user",
            reason="Submitted for approval",
        )

        assert result is True

        state = await manager.get_route_state("test-route", "v1.0")
        assert state == RouteLifecycleState.PENDING_APPROVAL

    @pytest.mark.asyncio
    async def test_full_lifecycle(self):
        """Test complete lifecycle flow"""
        manager = RouteLifecycleManager()

        await manager.create_route_entry("test-route", "v1.0")

        # Draft -> Pending Approval -> Approved -> Deployed -> Active
        transitions = [
            RouteLifecycleState.PENDING_APPROVAL,
            RouteLifecycleState.APPROVED,
            RouteLifecycleState.DEPLOYED,
            RouteLifecycleState.ACTIVE,
        ]

        for target_state in transitions:
            result = await manager.transition_state(
                "test-route",
                "v1.0",
                target_state,
                actor="system",
            )
            assert result is True

        # Verify final state
        final_state = await manager.get_route_state("test-route", "v1.0")
        assert final_state == RouteLifecycleState.ACTIVE

    @pytest.mark.asyncio
    async def test_invalid_transition(self):
        """Test invalid state transitions"""
        manager = RouteLifecycleManager()

        await manager.create_route_entry("test-route", "v1.0")

        # Try invalid transition: DRAFT -> ACTIVE (should fail)
        result = await manager.transition_state(
            "test-route",
            "v1.0",
            RouteLifecycleState.ACTIVE,
        )

        assert result is False


class TestAuditLogger:
    """Tests for audit trail logging"""

    @pytest.mark.asyncio
    async def test_log_event(self):
        """Test logging audit event"""
        logger = AuditLogger()

        event_id = await logger.log_event(
            event_type=AuditEventType.ROUTE_CREATED,
            actor="user@example.com",
            resource="route",
            resource_id="test-route:v1.0",
            details={"created_by": "user"},
        )

        assert event_id is not None

        # Retrieve event
        event = await logger.get_event(event_id)
        assert event is not None
        assert event.event_type == AuditEventType.ROUTE_CREATED

    @pytest.mark.asyncio
    async def test_filter_events(self):
        """Test filtering audit events"""
        logger = AuditLogger()

        # Log multiple events
        for i in range(5):
            await logger.log_event(
                event_type=AuditEventType.ROUTE_CREATED,
                actor="user@example.com",
                resource="route",
                resource_id=f"test-route-{i}:v1.0",
                details={},
            )

        # Get events for specific resource
        events = await logger.get_events(resource="route")
        assert len(events) == 5

    @pytest.mark.asyncio
    async def test_compliance_events(self):
        """Test compliance event tracking"""
        logger = AuditLogger()

        # Log compliance event
        await logger.log_event(
            event_type=AuditEventType.APPROVAL_GRANTED,
            actor="approver@example.com",
            resource="route",
            resource_id="test-route:v1.0",
            details={},
            compliance_relevant=True,
            severity="info",
        )

        # Get compliance events
        events = await logger.get_compliance_events()
        assert len(events) > 0

    @pytest.mark.asyncio
    async def test_audit_integrity(self):
        """Test audit log integrity"""
        logger = AuditLogger()

        # Log events
        for i in range(3):
            await logger.log_event(
                event_type=AuditEventType.ROUTE_CREATED,
                actor="user@example.com",
                resource="route",
                resource_id=f"test-route-{i}",
                details={},
            )

        # Verify integrity
        is_valid = await logger.verify_integrity()
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_export_compliance_report(self):
        """Test exporting compliance report"""
        logger = AuditLogger()

        # Log compliance events
        for i in range(3):
            await logger.log_event(
                event_type=AuditEventType.APPROVAL_GRANTED,
                actor="approver@example.com",
                resource="route",
                resource_id=f"test-route-{i}",
                details={},
                compliance_relevant=True,
            )

        # Export report
        report = await logger.export_compliance_report()

        assert "timestamp" in report
        assert "total_events" in report
        assert "compliance_events" in report


class TestApprovalEngineEdgeCases:
    """Tests for approval engine branches not covered by the happy-path tests."""

    @pytest.mark.asyncio
    async def test_high_cost_route_assigns_finance_and_security_approvers(self):
        policy = GovernancePolicy(
            name="Test",
            compliance_level=ComplianceLevel.STRICT,
            require_approval=True,
            max_monthly_cost_usd=1000.0,
        )
        engine = ApprovalEngine(policy)
        # cost > 1000 * 0.5 = 500 → finance + security leads
        request = await engine.create_approval_request(
            route_name="expensive-route",
            route_version="v1.0",
            requester_email="user@example.com",
            agents=["agent-1"],
            estimated_cost=900.0,
            estimated_volume=500,
        )
        assert len(request.approvers) == 2

    @pytest.mark.asyncio
    async def test_low_cost_route_assigns_single_team_lead(self):
        policy = GovernancePolicy(
            name="Test",
            compliance_level=ComplianceLevel.STANDARD,
            require_approval=True,
            max_monthly_cost_usd=1000.0,
        )
        engine = ApprovalEngine(policy)
        # cost <= 1000 * 0.5 = 500 → team lead only
        request = await engine.create_approval_request(
            route_name="cheap-route",
            route_version="v1.0",
            requester_email="user@example.com",
            agents=["agent-1"],
            estimated_cost=100.0,
            estimated_volume=500,
        )
        assert len(request.approvers) == 1

    @pytest.mark.asyncio
    async def test_submit_approval_unknown_request_returns_false(self):
        policy = GovernancePolicy(name="Test")
        engine = ApprovalEngine(policy)
        result = await engine.submit_approval(
            request_id="nonexistent-id",
            approver_email="anyone@example.com",
            approved=True,
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_submit_approval_unauthorised_approver_returns_false(self):
        policy = GovernancePolicy(
            name="Test",
            compliance_level=ComplianceLevel.STANDARD,
            require_approval=True,
            approval_threshold=1,
        )
        engine = ApprovalEngine(policy)
        request = await engine.create_approval_request(
            route_name="test-route",
            route_version="v1.0",
            requester_email="user@example.com",
            agents=["agent-1"],
            estimated_cost=50.0,
            estimated_volume=100,
        )
        result = await engine.submit_approval(
            request_id=request.request_id,
            approver_email="intruder@example.com",
            approved=True,
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_get_pending_requests_filtered_by_approver(self):
        policy = GovernancePolicy(
            name="Test",
            compliance_level=ComplianceLevel.STANDARD,
            require_approval=True,
            max_monthly_cost_usd=1000.0,
        )
        engine = ApprovalEngine(policy)
        # Create a low-cost request (team-lead approver)
        await engine.create_approval_request(
            route_name="route-a",
            route_version="v1.0",
            requester_email="user@example.com",
            agents=["agent-1"],
            estimated_cost=50.0,
            estimated_volume=10,
        )
        # Create a high-cost request (finance + security approvers)
        await engine.create_approval_request(
            route_name="route-b",
            route_version="v1.0",
            requester_email="user@example.com",
            agents=["agent-1"],
            estimated_cost=900.0,
            estimated_volume=10,
        )
        all_requests = await engine.get_pending_requests()
        assert len(all_requests) == 2

        import os
        team_lead = os.environ.get("SAFE_APPROVER_TEAM_LEAD", "team-lead@company.com")
        team_lead_requests = await engine.get_pending_requests(approver_email=team_lead)
        assert len(team_lead_requests) == 1
        assert team_lead_requests[0].route_name == "route-a"

    @pytest.mark.asyncio
    async def test_revoke_pending_approval(self):
        policy = GovernancePolicy(name="Test", require_approval=True)
        engine = ApprovalEngine(policy)
        request = await engine.create_approval_request(
            route_name="route-x",
            route_version="v1.0",
            requester_email="user@example.com",
            agents=["agent-1"],
            estimated_cost=50.0,
            estimated_volume=10,
        )
        result = await engine.revoke_approval(request.request_id, reason="Policy violation")
        assert result is True
        assert request.status == ApprovalStatus.REVOKED

    @pytest.mark.asyncio
    async def test_revoke_nonexistent_request_returns_false(self):
        policy = GovernancePolicy(name="Test")
        engine = ApprovalEngine(policy)
        result = await engine.revoke_approval("does-not-exist", reason="test")
        assert result is False

    @pytest.mark.asyncio
    async def test_compliance_disallowed_data_source_adds_warning(self):
        policy = GovernancePolicy(
            name="Test",
            max_monthly_cost_usd=10000.0,
            allowed_data_sources=["approved-db"],
        )
        engine = ApprovalEngine(policy)
        result = await engine.check_compliance(
            route_name="test-route",
            agents=["agent-1"],
            estimated_cost=100.0,
            data_sources=["unapproved-source"],
        )
        assert result.passed is True
        assert len(result.warnings) > 0


class TestPhase6Integration:
    """Integration tests for Phase 6"""

    @pytest.mark.asyncio
    async def test_complete_governance_workflow(self):
        """Test complete governance workflow"""

        # Setup
        policy = GovernancePolicy(
            name="Test Policy",
            compliance_level=ComplianceLevel.STANDARD,
            require_approval=True,
            approval_threshold=1,
        )

        approval_engine = ApprovalEngine(policy)
        lifecycle = RouteLifecycleManager()
        audit = AuditLogger()

        # 1. Create route
        await lifecycle.create_route_entry("test-route", "v1.0")
        await audit.log_event(
            event_type=AuditEventType.ROUTE_CREATED,
            actor="user@example.com",
            resource="route",
            resource_id="test-route:v1.0",
            details={},
            compliance_relevant=True,
        )

        # 2. Request approval
        request = await approval_engine.create_approval_request(
            route_name="test-route",
            route_version="v1.0",
            requester_email="user@example.com",
            agents=["agent-1"],
            estimated_cost=500.0,
            estimated_volume=1000,
        )

        await audit.log_event(
            event_type=AuditEventType.APPROVAL_REQUESTED,
            actor="user@example.com",
            resource="route",
            resource_id="test-route:v1.0",
            details={"request_id": request.request_id},
            compliance_relevant=True,
        )

        # 3. Submit approval
        await approval_engine.submit_approval(
            request_id=request.request_id,
            approver_email=request.approvers[0],
            approved=True,
        )

        # 4. Transition lifecycle
        await lifecycle.transition_state(
            "test-route",
            "v1.0",
            RouteLifecycleState.APPROVED,
        )

        await lifecycle.transition_state(
            "test-route",
            "v1.0",
            RouteLifecycleState.DEPLOYED,
        )

        # 5. Verify audit trail
        events = await audit.get_compliance_events()
        assert len(events) > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
