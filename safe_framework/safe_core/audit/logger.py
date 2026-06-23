"""Append-only audit trail with JSONL persistence and hash-chain integrity."""

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
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
    """Single audit event (append-only)."""
    event_id: str
    event_type: AuditEventType
    actor: str
    resource: str
    resource_id: str
    timestamp: datetime
    correlation_id: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    severity: str = "info"
    compliance_relevant: bool = False
    prev_hash: str = ""  # SHA-256 of previous event's canonical JSON
    event_hash: str = ""  # SHA-256 of this event's canonical JSON (set after creation)

    def to_dict(self) -> Dict[str, Any]:
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
            "prev_hash": self.prev_hash,
            "event_hash": self.event_hash,
        }

    def _canonical_json(self) -> str:
        """Deterministic JSON for hashing (excludes event_hash field itself)."""
        d = self.to_dict()
        d.pop("event_hash", None)
        return json.dumps(d, sort_keys=True, ensure_ascii=True)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


class AuditLogger:
    """Append-only audit trail with JSONL persistence and hash-chain integrity.

    If *log_path* is provided, every event is appended to a JSONL file so the
    trail survives process restarts.  Each event carries the SHA-256 hash of
    the previous event, forming a tamper-evident chain.
    """

    def __init__(self, log_path: Optional[str] = None):
        env_path = os.environ.get("SAFE_AUDIT_LOG_PATH")
        resolved = log_path or env_path
        self._log_path: Optional[Path] = Path(resolved) if resolved else None
        self.events: List[AuditEvent] = []
        self.compliance_events: List[AuditEvent] = []

        if self._log_path:
            self._log_path.parent.mkdir(parents=True, exist_ok=True)
            self._load_from_disk()

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

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
        event_id = f"evt-{resource}-{len(self.events)}"
        prev_hash = self.events[-1].event_hash if self.events else ""

        event = AuditEvent(
            event_id=event_id,
            event_type=event_type,
            actor=actor,
            resource=resource,
            resource_id=resource_id,
            timestamp=datetime.now(timezone.utc),
            correlation_id=correlation_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            severity=severity,
            compliance_relevant=compliance_relevant,
            prev_hash=prev_hash,
        )
        event.event_hash = _sha256(event._canonical_json())

        self.events.append(event)
        if compliance_relevant:
            self.compliance_events.append(event)

        if self._log_path:
            self._append_to_disk(event)

        return event_id

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    async def get_events(
        self,
        resource: Optional[str] = None,
        actor: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        limit: int = 100,
    ) -> List[AuditEvent]:
        events = self.events
        if resource:
            events = [e for e in events if e.resource == resource]
        if actor:
            events = [e for e in events if e.actor == actor]
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return sorted(events, key=lambda e: e.timestamp, reverse=True)[:limit]

    async def get_compliance_events(
        self,
        severity: Optional[str] = None,
        limit: int = 100,
    ) -> List[AuditEvent]:
        events = self.compliance_events
        if severity:
            events = [e for e in events if e.severity == severity]
        return sorted(events, key=lambda e: e.timestamp, reverse=True)[:limit]

    async def get_event(self, event_id: str) -> Optional[AuditEvent]:
        return next((e for e in self.events if e.event_id == event_id), None)

    # ------------------------------------------------------------------
    # Integrity
    # ------------------------------------------------------------------

    async def verify_integrity(self) -> bool:
        """Verify the hash chain — detects both deletion and tampering.

        Each event's stored prev_hash must match the SHA-256 of the previous
        event's canonical JSON, and each event_hash must match a fresh hash of
        the event's own canonical JSON.
        """
        prev_hash = ""
        for event in self.events:
            if event.prev_hash != prev_hash:
                return False
            expected_hash = _sha256(event._canonical_json())
            if event.event_hash != expected_hash:
                return False
            prev_hash = event.event_hash
        return True

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    async def export_compliance_report(self) -> Dict[str, Any]:
        critical_events = [e for e in self.compliance_events if e.severity == "critical"]
        warning_events = [e for e in self.compliance_events if e.severity == "warning"]
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_events": len(self.events),
            "compliance_events": len(self.compliance_events),
            "critical_events": len(critical_events),
            "warning_events": len(warning_events),
            "events": [e.to_dict() for e in self.compliance_events[-50:]],
        }

    # ------------------------------------------------------------------
    # Disk helpers
    # ------------------------------------------------------------------

    def _append_to_disk(self, event: AuditEvent) -> None:
        with self._log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event.to_dict()) + "\n")

    def _load_from_disk(self) -> None:
        if not self._log_path.exists():
            return
        with self._log_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                    event = AuditEvent(
                        event_id=d["event_id"],
                        event_type=AuditEventType(d["event_type"]),
                        actor=d["actor"],
                        resource=d["resource"],
                        resource_id=d["resource_id"],
                        timestamp=datetime.fromisoformat(d["timestamp"]),
                        correlation_id=d.get("correlation_id", ""),
                        details=d.get("details", {}),
                        ip_address=d.get("ip_address"),
                        user_agent=d.get("user_agent"),
                        severity=d.get("severity", "info"),
                        prev_hash=d.get("prev_hash", ""),
                        event_hash=d.get("event_hash", ""),
                    )
                    self.events.append(event)
                    if event.compliance_relevant:
                        self.compliance_events.append(event)
                except (KeyError, ValueError):
                    pass
