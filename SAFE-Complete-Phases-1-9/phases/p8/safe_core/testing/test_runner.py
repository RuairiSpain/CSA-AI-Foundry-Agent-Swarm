"""Comprehensive test runner"""

from typing import Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

class TestStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"

@dataclass
class TestResult:
    test_name: str
    test_class: str
    status: TestStatus
    duration_ms: float = 0.0
    error_message: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class TestSuite:
    suite_name: str
    tests: List[TestResult] = field(default_factory=list)
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    
    @property
    def success_rate(self) -> float:
        return (self.passed / self.total_tests * 100) if self.total_tests > 0 else 0.0

class TestRunner:
    def __init__(self):
        self.suites: Dict[str, TestSuite] = {}
    
    async def add_test_result(
        self, suite_name: str, test_name: str, test_class: str,
        status: TestStatus, duration_ms: float = 0.0, error_msg: str = "",
    ) -> None:
        if suite_name not in self.suites:
            self.suites[suite_name] = TestSuite(suite_name=suite_name)
        
        result = TestResult(test_name, test_class, status, duration_ms, error_msg)
        suite = self.suites[suite_name]
        suite.tests.append(result)
        suite.total_tests += 1
        
        if status == TestStatus.PASSED:
            suite.passed += 1
        elif status == TestStatus.FAILED:
            suite.failed += 1

