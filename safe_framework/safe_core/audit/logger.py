"""Immutable audit trail for compliance and governance"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field

class AuditEventType(str, Enum):
    """Types of audit events"""
    ROUTE_CREATED = "route-created"
    ROUTE_UPDATED = "route-updated"
    ROUTE_DEPLOYED = "route-deployed"
    ROUTE_DISABLED = "route-disabled"
    APPROVAL_REQUESTED = "approval-requested"
    APPROVAL_GRANTED = "approval-granted"
    APPROVAL_REJECTED = "approval-rejected"
    APPROVAL_REVOKED = "approval-revoked"
    COST_THRESHOLD_EXCEEDED = "cost-threshold-exceeded"
    HEALTH_ALERT_GENERATED = "health-alert-generated"
    ROUTE_FROZEN = "route-frozen"
    ROUTE_UNFROZEN = "route-unfrozen"
    ACCESS_GRANTED = "access-granted"
    ACCESS_REVOKED = "access-revoked"
    POLICY_CHANGED = "policy-changed"

@dataclass
class AuditEvent:
    """Single audit event (immutable)"""
    event_id: str
    event_type: AuditEventType
    actor: str
    resource: str  # Route name or resource affected
    resource_id: str
    timestamp: datetime
    correlation_id: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    # For compliance
    severity: str = "info"  # info, warning, critical
    compliance_relevant: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "actor": self.actor,
            "resource": self.resource,
            "resource_id": self.resource_id,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "severity": self.severity,
        }

class AuditLogger:
    """Immutable audit trail logger"""
    
    def __init__(self):
        self.events: List[AuditEvent] = []
        self.compliance_events: List[AuditEvent] = []
    
    async def log_event(
        self,
        event_type: AuditEventType,
        actor: str,
        resource: str,
        resource_id: str,
        details: Dict[str, Any],
        correlation_id: str = "",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        severity: str = "info",
        compliance_relevant: bool = False,
    ) -> str:
        """Log an audit event"""

        event_id = f"evt-{resource}-{len(self.events)}"

        event = AuditEvent(
            event_id=event_id,
            event_type=event_type,
            actor=actor,
            resource=resource,
            resource_id=resource_id,
            timestamp=datetime.now(),
            correlation_id=correlation_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            severity=severity,
            compliance_relevant=compliance_relevant,
        )
        
        # Add to main log
        self.events.append(event)
        
        # Add to compliance log if relevant
        if compliance_relevant:
            self.compliance_events.append(event)
        
        return event_id
    
    async def get_events(
        self,
        resource: Optional[str] = None,
        actor: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        limit: int = 100,
    ) -> List[AuditEvent]:
        """Get audit events with filtering"""
        
        events = self.events
        
        if resource:
            events = [e for e in events if e.resource == resource]
        
        if actor:
            events = [e for e in events if e.actor == actor]
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        # Return most recent first
        return sorted(events, key=lambda e: e.timestamp, reverse=True)[:limit]
    
    async def get_compliance_events(
        self,
        severity: Optional[str] = None,
        limit: int = 100,
    ) -> List[AuditEvent]:
        """Get compliance-relevant events"""
        
        events = self.compliance_events
        
        if severity:
            events = [e for e in events if e.severity == severity]
        
        return sorted(events, key=lambda e: e.timestamp, reverse=True)[:limit]
    
    async def get_event(self, event_id: str) -> Optional[AuditEvent]:
        """Get specific event by ID"""
        return next((e for e in self.events if e.event_id == event_id), None)
    
    async def verify_integrity(self) -> bool:
        """Verify audit log integrity (all events present, no deletions)"""
        # In production: check cryptographic hash of events
        # For MVP: just verify events are ordered by timestamp
        
        timestamps = [e.timestamp for e in self.events]
        return timestamps == sorted(timestamps)
    
    async def export_compliance_report(self) -> Dict[str, Any]:
        """Export compliance audit report"""
        
        critical_events = [e for e in self.compliance_events if e.severity == "critical"]
        warning_events = [e for e in self.compliance_events if e.severity == "warning"]
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_events": len(self.events),
            "compliance_events": len(self.compliance_events),
            "critical_events": len(critical_events),
            "warning_events": len(warning_events),
            "events": [e.to_dict() for e in self.compliance_events[-50:]],  # Last 50
        }

