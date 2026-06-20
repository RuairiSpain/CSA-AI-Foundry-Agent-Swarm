"""Release manager"""
from typing import Dict, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

class ReleaseStatus(str, Enum):
    PLANNED = "planned"
    STAGING = "staging"
    TESTING = "testing"
    DEPLOYED = "deployed"

@dataclass
class Release:
    version: str
    status: ReleaseStatus
    components: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

class ReleaseManager:
    def __init__(self):
        self.releases: Dict[str, Release] = {}
    
    async def create_release(self, version: str, components: List[str]) -> Release:
        release = Release(version=version, status=ReleaseStatus.PLANNED, components=components)
        self.releases[version] = release
        return release
    
    async def transition_to_deployed(self, version: str) -> bool:
        if version in self.releases:
            self.releases[version].status = ReleaseStatus.DEPLOYED
            return True
        return False
