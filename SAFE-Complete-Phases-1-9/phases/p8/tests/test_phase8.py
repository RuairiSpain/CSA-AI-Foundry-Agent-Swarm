"""Phase 8: Testing & QA tests"""

import pytest
import asyncio
from safe_core.testing.test_runner import TestRunner, TestStatus
from safe_core.performance.benchmark import PerformanceBenchmark
from safe_core.security.validator import SecurityValidator

class TestTestRunner:
    @pytest.mark.asyncio
    async def test_add_test_result(self):
        runner = TestRunner()
        await runner.add_test_result("suite1", "test1", "Test", TestStatus.PASSED, 125.5)
        assert "suite1" in runner.suites
        assert runner.suites["suite1"].passed == 1
    
    @pytest.mark.asyncio
    async def test_success_rate(self):
        runner = TestRunner()
        await runner.add_test_result("s1", "t1", "T", TestStatus.PASSED)
        await runner.add_test_result("s1", "t2", "T", TestStatus.FAILED)
        suite = runner.suites["s1"]
        assert suite.success_rate == 50.0

class TestPerformanceBenchmark:
    @pytest.mark.asyncio
    async def test_measure(self):
        benchmark = PerformanceBenchmark()
        def fn(): return "ok"
        duration = await benchmark.measure("test", fn)
        assert duration >= 0
    
    @pytest.mark.asyncio
    async def test_stats(self):
        benchmark = PerformanceBenchmark()
        def fn(): return "ok"
        await benchmark.measure("test", fn)
        await benchmark.measure("test", fn)
        stats = await benchmark.get_stats("test")
        assert "avg_ms" in stats
        assert stats["count"] == 2

class TestSecurityValidator:
    @pytest.mark.asyncio
    async def test_input_validation(self):
        validator = SecurityValidator()
        result = await validator.check_input_validation("phase4")
        assert result is True
    
    @pytest.mark.asyncio
    async def test_report(self):
        validator = SecurityValidator()
        await validator.check_input_validation("phase4")
        report = await validator.get_report()
        assert report["total_checks"] == 1

