"""Security validation — input schema checking, PII detection, prompt-injection heuristics."""

import re
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# PII patterns (regex-based; Presidio can replace these in production)
# ---------------------------------------------------------------------------
_PII_PATTERNS: Dict[str, re.Pattern] = {
    "email":        re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"),
    "phone_us":     re.compile(r"\b(\+?1[\s\-.]?)?\(?\d{3}\)?[\s\-.]?\d{3}[\s\-.]?\d{4}\b"),
    "ssn":          re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "credit_card":  re.compile(r"\b(?:4\d{3}|5[1-5]\d{2}|6011|3[47]\d{2})[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b"),
    "ipv4":         re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
}

# ---------------------------------------------------------------------------
# Prompt-injection heuristics
# ---------------------------------------------------------------------------
_INJECTION_PATTERNS: List[re.Pattern] = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?", re.I),
    re.compile(r"disregard\s+(all\s+)?(previous|prior|above)\s+instructions?", re.I),
    re.compile(r"forget\s+(everything|all)\s+(you|i)\s+(were|was|have been)\s+told", re.I),
    re.compile(r"you\s+are\s+now\s+(a|an)\s+\w+", re.I),
    re.compile(r"act\s+as\s+(if\s+)?(you\s+are\s+)?(a|an)\s+\w+", re.I),
    re.compile(r"(do not|don't)\s+(follow|obey)\s+(your|the)\s+(rules?|guidelines?|instructions?)", re.I),
    re.compile(r"<\s*(system|assistant|user)\s*>", re.I),
    re.compile(r"\[INST\]|\[/INST\]|<\|im_start\|>|<\|im_end\|>"),
]


@dataclass
class SecurityIssue:
    issue_id: str
    severity: str  # "low", "medium", "high", "critical"
    description: str
    affected_component: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class SecurityValidator:
    """Validates agent inputs for schema compliance, PII, and prompt injection."""

    def __init__(self):
        self.issues: List[SecurityIssue] = []
        self.checks_performed: Dict[str, bool] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def check_input_validation(
        self,
        component: str,
        data: Optional[Dict[str, Any]] = None,
        schema: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Validate *data* against *schema* (JSON Schema subset).

        Checks required fields and basic type correctness.  Returns True when
        all required fields are present and correctly typed; False otherwise,
        with issues recorded for `get_report()`.
        """
        key = f"{component}_input_validation"
        passed = True

        if data is None or schema is None:
            self.checks_performed[key] = True
            return True

        required = schema.get("required", [])
        properties = schema.get("properties", {})

        for field_name in required:
            if field_name not in data:
                self._add_issue(
                    f"{key}_missing_{field_name}",
                    severity="high",
                    description=f"Required field '{field_name}' missing from input",
                    component=component,
                )
                passed = False

        _TYPE_MAP = {"string": str, "integer": int, "number": (int, float), "boolean": bool, "array": list, "object": dict}
        for field_name, value in data.items():
            field_schema = properties.get(field_name, {})
            expected_type = field_schema.get("type")
            if expected_type and expected_type in _TYPE_MAP:
                if not isinstance(value, _TYPE_MAP[expected_type]):
                    self._add_issue(
                        f"{key}_type_{field_name}",
                        severity="medium",
                        description=(
                            f"Field '{field_name}' expected type '{expected_type}' "
                            f"but got '{type(value).__name__}'"
                        ),
                        component=component,
                    )
                    passed = False

        self.checks_performed[key] = passed
        return passed

    async def check_authentication(
        self,
        component: str,
        auth_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Verify that authentication credentials are present and non-empty."""
        key = f"{component}_authentication"

        if auth_data is None:
            self._add_issue(
                f"{key}_missing",
                severity="critical",
                description="No authentication data provided",
                component=component,
            )
            self.checks_performed[key] = False
            return False

        token = auth_data.get("token") or auth_data.get("api_key") or auth_data.get("key")
        if not token:
            self._add_issue(
                f"{key}_empty",
                severity="critical",
                description="Authentication token/api_key is absent or empty",
                component=component,
            )
            self.checks_performed[key] = False
            return False

        self.checks_performed[key] = True
        return True

    async def check_pii(self, component: str, text: str) -> bool:
        """Scan *text* for common PII patterns. Returns True if no PII found."""
        key = f"{component}_pii"
        found_types: List[str] = []

        for pii_type, pattern in _PII_PATTERNS.items():
            if pattern.search(text):
                found_types.append(pii_type)

        if found_types:
            self._add_issue(
                f"{key}_detected",
                severity="high",
                description=f"Potential PII detected in component input: {', '.join(found_types)}",
                component=component,
            )
            self.checks_performed[key] = False
            return False

        self.checks_performed[key] = True
        return True

    async def check_prompt_injection(self, component: str, text: str) -> bool:
        """Scan *text* for prompt-injection patterns. Returns True if no injection found."""
        key = f"{component}_prompt_injection"

        for pattern in _INJECTION_PATTERNS:
            if pattern.search(text):
                self._add_issue(
                    f"{key}_detected",
                    severity="critical",
                    description="Potential prompt-injection pattern detected in input",
                    component=component,
                )
                self.checks_performed[key] = False
                return False

        self.checks_performed[key] = True
        return True

    async def get_report(self) -> Dict[str, Any]:
        """Return a summary of all checks performed and issues found."""
        by_severity: Dict[str, int] = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for issue in self.issues:
            by_severity[issue.severity] = by_severity.get(issue.severity, 0) + 1

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_checks": len(self.checks_performed),
            "checks_passed": sum(1 for v in self.checks_performed.values() if v),
            "critical_issues": by_severity["critical"],
            "high_issues": by_severity["high"],
            "medium_issues": by_severity["medium"],
            "low_issues": by_severity["low"],
            "total_issues": len(self.issues),
            "issues": [
                {
                    "id": i.issue_id,
                    "severity": i.severity,
                    "description": i.description,
                    "component": i.affected_component,
                    "timestamp": i.timestamp.isoformat(),
                }
                for i in self.issues
            ],
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _add_issue(self, issue_id: str, severity: str, description: str, component: str) -> None:
        self.issues.append(SecurityIssue(
            issue_id=issue_id,
            severity=severity,
            description=description,
            affected_component=component,
        ))
