"""CLI commands for health monitoring"""

import asyncio
from typing import Optional
from safe_core.health_monitor import HealthMonitor
from safe_core.storage.semantic_kernel_store import SemanticKernelRouteHealthStore

class HealthCLI:
    """CLI for health registry operations"""
    
    def __init__(self):
        self.storage = SemanticKernelRouteHealthStore()
        self.monitor = HealthMonitor(self.storage)
    
    async def show_dashboard(self) -> None:
        """Show health dashboard"""
        dashboard = await self.monitor.get_health_dashboard()
        
        print("\n" + "="*70)
        print("SAFE Health Registry Dashboard")
        print("="*70)
        print(f"\nTimestamp: {dashboard['timestamp']}")
        print(f"Total Monitored Routes: {dashboard['total_routes']}")
        
        print("\nRoutes by Status:")
        for status, routes in dashboard['routes_by_status'].items():
            print(f"  {status}: {len(routes)} route(s)")
            for route in routes[:5]:
                print(f"    • {route}")
            if len(routes) > 5:
                print(f"    ... and {len(routes) - 5} more")
        
        if dashboard['recent_alerts']:
            print("\nRecent Alerts:")
            for alert in dashboard['recent_alerts'][:5]:
                print(f"  [{alert['severity'].upper()}] {alert['message']}")
                print(f"    Action: {alert['action']}")
        
        print("\n" + "="*70)
    
    async def show_route_health(self, route_name: str, version: str = "v1.0") -> None:
        """Show health for a specific route"""
        health = await self.storage.get_route_health(route_name, version)
        
        if not health:
            print(f"Route {route_name} not found")
            return
        
        print(f"\n{'='*70}")
        print(f"Health Report: {route_name} ({version})")
        print(f"{'='*70}")
        print(f"\nStatus: {health.status.value}")
        print(f"Last Check: {health.last_check.isoformat()}")
        
        print(f"\nExecution Metrics:")
        print(f"  Total Executions: {health.execution_count}")
        print(f"  Successes: {health.success_count}")
        print(f"  Failures: {health.failure_count}")
        print(f"  Success Rate: {health.success_rate:.1f}%")
        print(f"  Consecutive Failures: {health.consecutive_failures}")
        
        print(f"\nPerformance:")
        print(f"  Average Time: {health.avg_execution_time_ms:.2f}ms")
        print(f"  P95 Time: {health.p95_execution_time_ms:.2f}ms")
        print(f"  P99 Time: {health.p99_execution_time_ms:.2f}ms")
        print(f"  Slow Executions: {health.consecutive_slow_executions}")
        
        print(f"\nCost:")
        print(f"  Tokens Used: {health.tokens_used:,}")
        print(f"  Estimated Monthly Cost: ${health.estimated_monthly_cost_usd:.2f}")
        
        print(f"\n{'='*70}")
    
    async def show_alerts(self, route_name: Optional[str] = None, limit: int = 20) -> None:
        """Show recent alerts"""
        alerts = await self.storage.get_alerts(route_name=route_name, limit=limit)
        
        print(f"\n{'='*70}")
        print("Recent Alerts")
        if route_name:
            print(f"Route: {route_name}")
        print(f"{'='*70}\n")
        
        if not alerts:
            print("No alerts found")
            return
        
        for alert in alerts:
            severity_emoji = {
                "info": "ℹ️",
                "warning": "⚠️",
                "critical": "🚨"
            }.get(alert.severity, "•")
            
            print(f"{severity_emoji} [{alert.timestamp.isoformat()}]")
            print(f"   Route: {alert.route_name}")
            print(f"   Message: {alert.message}")
            print(f"   Metric: {alert.metric_name} ({alert.current_value:.2f} vs {alert.threshold:.2f})")
            print(f"   Action: {alert.suggested_action}")
            print()
        
        print(f"{'='*70}")
    
    async def register_route(self, route_name: str, version: str = "v1.0") -> None:
        """Register a route for monitoring"""
        await self.monitor.register_route(route_name, version)
        print(f"✓ Route {route_name} registered for monitoring")
    
    async def record_execution(
        self,
        route_name: str,
        success: bool,
        execution_time_ms: float,
        version: str = "v1.0",
        tokens_used: int = 0,
        cost_usd: float = 0.0,
    ) -> None:
        """Record a route execution"""
        await self.monitor.record_execution(
            route_name=route_name,
            version=version,
            success=success,
            execution_time_ms=execution_time_ms,
            tokens_used=tokens_used,
            estimated_cost_usd=cost_usd,
        )
    
    async def freeze_route(self, route_name: str, version: str = "v1.0") -> None:
        """Freeze a route"""
        success = await self.monitor.freeze_route(route_name, version)
        if success:
            print(f"✓ Route {route_name} frozen")
        else:
            print(f"✗ Failed to freeze route {route_name}")
    
    async def unfreeze_route(self, route_name: str, version: str = "v1.0") -> None:
        """Unfreeze a route"""
        success = await self.monitor.unfreeze_route(route_name, version)
        if success:
            print(f"✓ Route {route_name} unfrozen")
        else:
            print(f"✗ Failed to unfreeze route {route_name}")

async def main():
    """Example usage"""
    cli = HealthCLI()
    
    # Register a route
    await cli.register_route("loan-approval-v1")
    
    # Simulate some executions
    for i in range(10):
        success = i < 8  # 80% success rate
        time_ms = 2000 if i % 3 == 0 else 1000
        await cli.record_execution(
            "loan-approval-v1",
            success=success,
            execution_time_ms=float(time_ms),
            tokens_used=500 + i * 100,
            cost_usd=0.05 + i * 0.01,
        )
    
    # Show dashboard
    await cli.show_dashboard()
    
    # Show route health
    await cli.show_route_health("loan-approval-v1")
    
    # Show alerts
    await cli.show_alerts()

if __name__ == "__main__":
    asyncio.run(main())

