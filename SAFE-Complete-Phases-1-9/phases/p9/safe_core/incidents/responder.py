"""Incident responder"""
from typing import Dict, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

class IncidentSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class IncidentStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"

@dataclass
class Incident:
    incident_id: str
    title: str
    severity: IncidentSeverity
    status: IncidentStatus
    affected_routes: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

class IncidentResponder:
    def __init__(self):
        self.incidents: Dict[str, Incident] = {}
    
    async def create_incident(
        self, incident_id: str, title: str,
        severity: IncidentSeverity, routes: List[str]
    ) -> Incident:
        incident = Incident(
            incident_id=incident_id, title=title,
            severity=severity, status=IncidentStatus.OPEN,
            affected_routes=routes
        )
        self.incidents[incident_id] = incident
        return incident
    
    async def resolve_incident(self, incident_id: str) -> bool:
        if incident_id in self.incidents:
            self.incidents[incident_id].status = IncidentStatus.RESOLVED
            return True
        return False
