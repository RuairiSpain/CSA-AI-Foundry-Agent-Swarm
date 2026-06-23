"""Comprehensive test runner"""

from typing import Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

class RunStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"

# Backward-compat alias
TestStatus = RunStatus

@dataclass
class RunResult:
    test_name: str
    test_class: str
    status: RunStatus
    duration_ms: float = 0.0
    error_message: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class RunSuite:
    suite_name: str
    tests: List[RunResult] = field(default_factory=list)
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0

    @property
    def success_rate(self) -> float:
        return (self.passed / self.total_tests * 100) if self.total_tests > 0 else 0.0

class SuiteRunner:
    def __init__(self):
        self.suites: Dict[str, RunSuite] = {}

    async def add_test_result(
        self, suite_name: str, test_name: str, test_class: str,
        status: RunStatus, duration_ms: float = 0.0, error_msg: str = "",
    ) -> None:
        if suite_name not in self.suites:
            self.suites[suite_name] = RunSuite(suite_name=suite_name)

        result = RunResult(test_name, test_class, status, duration_ms, error_msg)
        suite = self.suites[suite_name]
        suite.tests.append(result)
        suite.total_tests += 1

        if status == RunStatus.PASSED:
            suite.passed += 1
        elif status == RunStatus.FAILED:
            suite.failed += 1

# Backward-compat aliases
TestRunner = SuiteRunner
TestResult = RunResult
TestSuite = RunSuite

