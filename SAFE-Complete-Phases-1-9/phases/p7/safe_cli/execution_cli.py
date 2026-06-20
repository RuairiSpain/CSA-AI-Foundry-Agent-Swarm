"""CLI for workflow execution"""

import asyncio
from safe_core.invocation.engine import RouteInvocationEngine, ExecutionStatus
from safe_core.execution.executor import ExecutionEngine, RetryPolicy
from safe_core.results.tracker import ResultTracker

class ExecutionCLI:
    def __init__(self):
        self.invocation = RouteInvocationEngine()
        self.executor = ExecutionEngine(RetryPolicy(max_retries=3))
        self.tracker = ResultTracker()
    
    async def invoke_route(self, route_name: str, version: str, input_data: dict) -> None:
        """Invoke a route"""
        request = await self.invocation.create_execution_request(
            route_name=route_name,
            route_version=version,
            input_data=input_data,
        )
        print(f"✓ Execution request created: {request.request_id}")
        print(f"  Route: {route_name} {version}")
        print(f"  Input: {input_data}")
    
    async def execute_pending(self) -> None:
        """Execute pending requests"""
        pending = await self.invocation.get_pending_requests()
        print(f"\n📋 Executing {len(pending)} pending requests...\n")
        
        for i, request in enumerate(pending, 1):
            print(f"[{i}/{len(pending)}] {request.route_name}:{request.request_id[:8]}")
            
            # Dequeue
            exec_req = await self.invocation.dequeue_request()
            if not exec_req:
                break
            
            # Create result
            from safe_core.invocation.engine import ExecutionResult
            result = ExecutionResult(
                request_id=exec_req.request_id,
                route_name=exec_req.route_name,
                route_version=exec_req.route_version,
                status=ExecutionStatus.RUNNING,
                input_data=exec_req.input_data,
            )
            
            # Execute (with mock data)
            async def mock_route(data):
                await asyncio.sleep(0.1)
                return {"status": "processed", "input": data}
            
            result = await self.executor.execute_with_retry(result, mock_route)
            
            # Save result
            await self.invocation.save_result(result)
            await self.tracker.track_result(result)
            
            status_str = "✓" if result.is_successful else "✗"
            print(f"  {status_str} {result.status.value} ({result.execution_time_ms:.0f}ms)")
    
    async def show_results(self, route_name: str, version: str) -> None:
        """Show results for route"""
        results = await self.invocation.get_results_for_route(route_name, version, limit=10)
        stats = await self.tracker.get_route_stats(route_name, version)
        
        if not stats:
            print(f"No results for {route_name} {version}")
            return
        
        print(f"\n{'='*70}")
        print(f"Results: {route_name} {version}")
        print(f"{'='*70}\n")
        
        print(f"Total Executions: {stats['total_executions']}")
        print(f"Successful: {stats['successful']}")
        print(f"Failed: {stats['failed']}")
        print(f"Success Rate: {stats['success_rate']:.1f}%")
        print(f"Avg Execution Time: {stats['avg_execution_time_ms']:.0f}ms")

async def main():
    cli = ExecutionCLI()
    
    # Invoke routes
    await cli.invoke_route("loan-approval-v1", "v1.0", {"loan_amount": 50000})
    await cli.invoke_route("document-processor", "v1.0", {"file_path": "/docs/invoice.pdf"})
    
    # Show pending
    pending = await cli.invocation.get_pending_requests()
    print(f"\n⏳ Pending executions: {len(pending)}")
    
    # Execute
    await cli.execute_pending()
    
    # Show results
    await cli.show_results("loan-approval-v1", "v1.0")

if __name__ == "__main__":
    asyncio.run(main())

