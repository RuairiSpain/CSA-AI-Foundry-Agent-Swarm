"""Release manager with environment-promotion gates."""
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class ReleaseStatus(str, Enum):
    PLANNED = "planned"
    STAGING = "staging"
    TESTING = "testing"
    DEPLOYED = "deployed"


# Valid environment promotion paths (from → allowed-tos)
_VALID_TRANSITIONS: Dict[str, List[str]] = {
    "dev":     ["staging"],
    "staging": ["prod"],
    "prod":    [],
}


@dataclass
class Release:
    version: str
    status: ReleaseStatus
    components: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    promotions: List[Dict] = field(default_factory=list)


class ReleaseManager:
    def __init__(self):
        self.releases: Dict[str, Release] = {}

    async def create_release(self, version: str, components: List[str]) -> Release:
        release = Release(version=version, status=ReleaseStatus.PLANNED, components=components)
        self.releases[version] = release
        return release

    async def promote(
        self,
        version: str,
        from_env: str,
        to_env: str,
        approver: str,
    ) -> bool:
        """Promote *version* from *from_env* to *to_env* with an approver gate.

        Valid paths: dev → staging → prod.
        Returns False for unknown versions or invalid environment transitions.
        """
        if version not in self.releases:
            return False

        allowed = _VALID_TRANSITIONS.get(from_env, [])
        if to_env not in allowed:
            return False

        release = self.releases[version]
        release.promotions.append({
            "from_env": from_env,
            "to_env": to_env,
            "approver": approver,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        if to_env == "prod":
            release.status = ReleaseStatus.DEPLOYED

        return True

    async def transition_to_deployed(self, version: str) -> bool:
        if version in self.releases:
            self.releases[version].status = ReleaseStatus.DEPLOYED
            return True
        return False
