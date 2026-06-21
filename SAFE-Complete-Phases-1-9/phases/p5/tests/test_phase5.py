"""Comprehensive tests for Phase 5: Health Registry"""

import pytest
import asyncio
from safe_core.health_models import (
    RouteHealth,
    RouteHealthStatus,
    HealthAlert,
    AlertSeverity,
    HealthMetric,
)
from safe_core.health_monitor import HealthMonitor
from safe_core.storage.semantic_kernel_store import SemanticKernelRouteHealthStore

class TestHealthModels:
    """Tests for health data models"""
    
    def test_route_health_initialization(self):
        """Test RouteHealth initialization"""
        health = RouteHealth(
            route_name="test-route",
            route_version="v1.0",
            status=RouteHealthStatus.READY,
        )
        
        assert health.route_name == "test-route"
        assert health.status == RouteHealthStatus.READY
        assert health.execution_count == 0
        assert health.success_rate == 100.0
    
    def test_route_health_success_rate(self):
        """Test success rate calculation"""
        health = RouteHealth(
            route_name="test",
            route_version="v1.0",
            status=RouteHealthStatus.READY,
            execution_count=10,
            success_count=8,
        )
        
        assert health.success_rate == 80.0
    
    def test_health_alert_creation(self):
        """Test HealthAlert creation"""
        alert = HealthAlert(
            route_name="test",
            severity=AlertSeverity.WARNING,
            message="Test alert",
            metric_name="test_metric",
            current_value=100.0,
            threshold=50.0,
            suggested_action="Do something",
        )
        
        assert alert.route_name == "test"
        assert alert.severity == AlertSeverity.WARNING
        
        alert_dict = alert.to_dict()
        assert "alert_id" in alert_dict
        assert alert_dict["severity"] == "warning"
    
    def test_health_metric_threshold(self):
        """Test HealthMetric threshold checking"""
        metric = HealthMetric(
            name="execution_time",
            value=1000.0,
            unit="ms",
            threshold=500.0,
        )
        
        assert metric.is_threshold_exceeded()
    
    def test_status_enum(self):
        """Test RouteHealthStatus enum"""
        statuses = [
            RouteHealthStatus.READY,
            RouteHealthStatus.WARN_SLOW,
            RouteHealthStatus.WARN_FAILING,
            RouteHealthStatus.WARN_COST,
            RouteHealthStatus.OFFLINE,
            RouteHealthStatus.FROZEN,
        ]
        
        assert len(statuses) == 6
        assert RouteHealthStatus.READY.value == "ready"


class TestStorageLayer:
    """Tests for storage abstraction"""
    
    @pytest.mark.asyncio
    async def test_save_and_retrieve_health(self):
        """Test saving and retrieving health"""
        storage = SemanticKernelRouteHealthStore()
        
        health = RouteHealth(
            route_name="test-route",
            route_version="v1.0",
            status=RouteHealthStatus.READY,
            execution_count=10,
            success_count=9,
        )
        
        # Save
        result = await storage.save_route_health(health)
        assert result is True
        
        # Retrieve
        retrieved = await storage.get_route_health("test-route", "v1.0")
        assert retrieved is not None
        assert retrieved.route_name == "test-route"
        assert retrieved.execution_count == 10
    
    @pytest.mark.asyncio
    async def test_save_and_retrieve_alert(self):
        """Test saving and retrieving alerts"""
        storage = SemanticKernelRouteHealthStore()
        
        alert = HealthAlert(
            route_name="test",
            severity=AlertSeverity.WARNING,
            message="Test alert",
            metric_name="test_metric",
            current_value=100.0,
            threshold=50.0,
            suggested_action="Test action",
        )
        
        # Save
        result = await storage.save_alert(alert)
        assert result is True
        
        # Retrieve
        alerts = await storage.get_alerts(route_name="test")
        assert len(alerts) > 0
        assert alerts[0].route_name == "test"
    
    @pytest.mark.asyncio
    async def test_list_all_routes(self):
        """Test listing all routes"""
        storage = SemanticKernelRouteHealthStore()
        
        # Register multiple routes
        for i in range(3):
            health = RouteHealth(
                route_name=f"route-{i}",
                route_version="v1.0",
                status=RouteHealthStatus.READY,
            )
            await storage.save_route_health(health)
        
        routes = await storage.list_all_routes()
        assert len(routes) == 3


class TestHealthMonitor:
    """Tests for health monitoring"""
    
    @pytest.mark.asyncio
    async def test_register_route(self):
        """Test registering a route"""
        storage = SemanticKernelRouteHealthStore()
        monitor = HealthMonitor(storage)
        
        await monitor.register_route("test-route", "v1.0")
        
        health = await storage.get_route_health("test-route", "v1.0")
        assert health is not None
        assert health.route_name == "test-route"
    
    @pytest.mark.asyncio
    async def test_record_successful_execution(self):
        """Test recording successful execution"""
        storage = SemanticKernelRouteHealthStore()
        monitor = HealthMonitor(storage)
        
        await monitor.register_route("test-route", "v1.0")
        
        await monitor.record_execution(
            route_name="test-route",
            version="v1.0",
            success=True,
            execution_time_ms=1000.0,
            tokens_used=500,
            estimated_cost_usd=0.05,
        )
        
        health = await storage.get_route_health("test-route", "v1.0")
        assert health.execution_count == 1
        assert health.success_count == 1
        assert health.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_record_failed_execution(self):
        """Test recording failed execution"""
        storage = SemanticKernelRouteHealthStore()
        monitor = HealthMonitor(storage)
        
        await monitor.register_route("test-route", "v1.0")
        
        await monitor.record_execution(
            route_name="test-route",
            version="v1.0",
            success=False,
            execution_time_ms=500.0,
        )
        
        health = await storage.get_route_health("test-route", "v1.0")
        assert health.failure_count == 1
        assert health.consecutive_failures == 1
    
    @pytest.mark.asyncio
    async def test_two_strike_failure_detection(self):
        """Test two-strike rule for failures"""
        storage = SemanticKernelRouteHealthStore()
        monitor = HealthMonitor(storage)
        
        await monitor.register_route("test-route", "v1.0")
        
        # First failure
        await monitor.record_execution(
            route_name="test-route",
            version="v1.0",
            success=False,
            execution_time_ms=500.0,
        )
        
        health = await storage.get_route_health("test-route", "v1.0")
        assert health.status == RouteHealthStatus.READY  # Not triggered yet
        
        # Second failure
        await monitor.record_execution(
            route_name="test-route",
            version="v1.0",
            success=False,
            execution_time_ms=500.0,
        )
        
        health = await storage.get_route_health("test-route", "v1.0")
        assert health.status == RouteHealthStatus.WARN_FAILING  # Triggered!
    
    @pytest.mark.asyncio
    async def test_slow_execution_detection(self):
        """Test detection of slow executions"""
        storage = SemanticKernelRouteHealthStore()
        monitor = HealthMonitor(storage)
        
        await monitor.register_route("test-route", "v1.0")
        
        health = await storage.get_route_health("test-route", "v1.0")
        original_threshold = health.slow_execution_threshold_ms
        
        # Record slow executions
        for _ in range(2):
            await monitor.record_execution(
                route_name="test-route",
                version="v1.0",
                success=True,
                execution_time_ms=original_threshold + 1000,
            )
        
        health = await storage.get_route_health("test-route", "v1.0")
        assert health.status == RouteHealthStatus.WARN_SLOW
    
    @pytest.mark.asyncio
    async def test_cost_alert_generation(self):
        """Test cost threshold alerts"""
        storage = SemanticKernelRouteHealthStore()
        monitor = HealthMonitor(storage)
        
        await monitor.register_route("test-route", "v1.0")
        
        health = await storage.get_route_health("test-route", "v1.0")
        health.estimated_monthly_cost_usd = health.cost_threshold_usd + 100
        await storage.save_route_health(health)
        
        await monitor.record_execution(
            route_name="test-route",
            version="v1.0",
            success=True,
            execution_time_ms=500.0,
            estimated_cost_usd=50.0,
        )
        
        health = await storage.get_route_health("test-route", "v1.0")
        assert health.status == RouteHealthStatus.WARN_COST
    
    @pytest.mark.asyncio
    async def test_freeze_unfreeze_route(self):
        """Test freezing and unfreezing routes"""
        storage = SemanticKernelRouteHealthStore()
        monitor = HealthMonitor(storage)
        
        await monitor.register_route("test-route", "v1.0")
        
        # Freeze
        result = await monitor.freeze_route("test-route", "v1.0")
        assert result is True
        
        health = await storage.get_route_health("test-route", "v1.0")
        assert health.status == RouteHealthStatus.FROZEN
        
        # Unfreeze
        result = await monitor.unfreeze_route("test-route", "v1.0")
        assert result is True
        
        health = await storage.get_route_health("test-route", "v1.0")
        assert health.status == RouteHealthStatus.READY
    
    @pytest.mark.asyncio
    async def test_get_health_dashboard(self):
        """Test dashboard generation"""
        storage = SemanticKernelRouteHealthStore()
        monitor = HealthMonitor(storage)
        
        # Register and simulate routes
        for i in range(3):
            await monitor.register_route(f"route-{i}", "v1.0")
        
        dashboard = await monitor.get_health_dashboard()
        
        assert "timestamp" in dashboard
        assert "total_routes" in dashboard
        assert "routes_by_status" in dashboard
        assert dashboard["total_routes"] == 3


class TestPhase5Integration:
    """Integration tests for Phase 5"""
    
    @pytest.mark.asyncio
    async def test_complete_monitoring_workflow(self):
        """Test complete monitoring workflow"""
        storage = SemanticKernelRouteHealthStore()
        monitor = HealthMonitor(storage)
        
        # 1. Register route
        await monitor.register_route("integration-test-route", "v1.0")
        
        # 2. Simulate 20 executions (80% success, 50% slow)
        for i in range(20):
            success = i < 16
            time_ms = 6000 if i % 2 == 0 else 1000
            
            await monitor.record_execution(
                route_name="integration-test-route",
                version="v1.0",
                success=success,
                execution_time_ms=float(time_ms),
                tokens_used=500,
                estimated_cost_usd=0.05,
            )
        
        # 3. Verify health
        health = await storage.get_route_health("integration-test-route", "v1.0")
        assert health.execution_count == 20
        assert health.success_rate == 80.0
        
        # 4. Get dashboard
        dashboard = await monitor.get_health_dashboard()
        assert dashboard["total_routes"] >= 1

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

