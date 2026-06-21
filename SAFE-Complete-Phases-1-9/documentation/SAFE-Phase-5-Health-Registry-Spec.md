# SAFE Phase 5: Health Registry - Detailed Specification

**Real-Time Monitoring with Auto-Detection & Governance**

**Weeks:** 6-7  
**Effort:** 10 engineer-days  
**Status:** Specification

---

## OVERVIEW

The Health Registry tracks route execution metrics, detects issues automatically, and integrates with governance systems.

**Core Responsibilities:**
1. **Metrics Collection** — Record execution time, cost, success rate
2. **Auto-Detection** — Flag routes when thresholds breached
3. **Status Management** — ready | warn-slow | warn-failing | warn-cost | offline | frozen
4. **Alerting** — Notify admins when status changes
5. **Dashboard** — Real-time visibility into all routes

---

## REQUIREMENTS

### Functional Requirements

| ID | Requirement | Acceptance Criteria |
|----|-------------|-------------------|
| R1 | Metrics collection | Every execution recorded: time, cost, success, errors |
| R2 | Auto-detection | Status flags trigger within 1 min of threshold |
| R3 | Status persistence | Status survives service restart |
| R4 | Alert system | Admins notified of status changes |
| R5 | Admin override | Admins can manually freeze/unfreeze routes |
| R6 | Time-series data | Metrics queryable by time window (1h, 24h, 7d) |
| R7 | Percentile calculations | P50, P95, P99 latencies available |
| R8 | Cost tracking | Token count + model cost calculated per execution |
| R9 | Dashboard integration | Status visible in M365/Agent 365 dashboard |
| R10 | Audit trail | All status changes logged with reason |

### Non-Functional Requirements

| ID | Requirement | Acceptance Criteria |
|----|-------------|-------------------|
| NF1 | Detection latency | Status updated within 1 minute of threshold |
| NF2 | Query performance | Metrics queries complete in <100ms |
| NF3 | Storage overhead | <100MB per 10K routes per 30 days |
| NF4 | Write throughput | Handle 1000 concurrent route executions |
| NF5 | False positive rate | 0% false positives in 48h test period |
| NF6 | Scalability | Support 10K routes, 1M executions/day |

---

## DATA MODEL

### RouteExecution

```python
@dataclass
class RouteExecution:
    # Identification
    route_id: str                    # "loan-approval-v1"
    version: str                     # "v1.0"
    execution_id: str                # UUID for this execution
    
    # Timing
    timestamp: datetime              # When execution started
    duration_seconds: float          # How long it took
    start_time: datetime
    end_time: datetime
    
    # Status
    success: bool                    # True/False
    error: Optional[str]             # Error message if failed
    error_type: Optional[str]        # "timeout", "validation", "contract", "agent"
    
    # Cost
    tokens_used: int                 # LLM tokens
    model_cost: float                # $ for this execution
    
    # Details
    input_size: int                  # Bytes of input
    output_size: int                 # Bytes of output
    agent_timings: Dict[str, float]  # Per-agent execution times
    
    # Metadata
    user_email: str                  # Who triggered this
    trace_id: str                    # For distributed tracing
    metadata: Dict[str, Any]         # Custom data
```

### HealthMetrics (Aggregated)

```python
@dataclass
class HealthMetrics:
    route_id: str
    time_window: str                 # "1h", "24h", "7d"
    
    # Count
    total_executions: int
    successful_executions: int
    failed_executions: int
    
    # Rates
    success_rate: float              # % (0-100)
    error_rate: float                # % (0-100)
    
    # Latency
    avg_duration: float              # seconds
    median_duration: float           # P50
    p95_duration: float              # P95
    p99_duration: float              # P99
    min_duration: float
    max_duration: float
    
    # Cost
    total_cost: float                # $
    avg_cost: float                  # $ per execution
    max_cost: float
    
    # Errors
    error_types: Dict[str, int]      # {"timeout": 5, "validation": 2}
    recent_errors: List[str]         # Last 10 errors
```

### RouteHealth (Status)

```python
@dataclass
class RouteHealth:
    route_id: str
    version: str
    status: str                      # ready | warn-slow | warn-failing | warn-cost | offline | frozen
    
    # Thresholds
    p95_threshold: float             # seconds (e.g., 60)
    error_rate_threshold: float      # % (e.g., 5)
    cost_threshold: float            # $ (e.g., 1.0)
    
    # Current metrics
    current_p95: float
    current_error_rate: float
    current_cost: float
    
    # Status details
    reasons: List[str]               # Why status is set (may have multiple)
    triggered_at: datetime
    
    # Admin actions
    is_frozen: bool
    frozen_by: Optional[str]         # Admin email
    frozen_reason: Optional[str]
    frozen_at: Optional[datetime]
    
    # Remediation
    suggested_actions: List[str]     # What to do about it
```

---

## STATUS FLAGS

### ready
**Meaning:** All metrics within normal thresholds

**Trigger:** Every metric < threshold
```python
if (p95_duration < threshold_time and
    error_rate < threshold_error and
    cost < threshold_cost):
    status = "ready"
```

**Actions:** None needed, route operating normally

---

### warn-slow
**Meaning:** Route execution time exceeds threshold

**Trigger:**
```python
if p95_duration > 60 seconds:  # Default threshold
    add_status("warn-slow")
```

**Suggested Actions:**
1. Increase timeout (currently {timeout}s, might need {recommended}s)
2. Optimize agents (check which step is slow)
3. Cache results from previous executions
4. Move blocking operations to background

**Example Dashboard Alert:**
```
⚠️ Route loan-approval-v1 is SLOW
   P95: 85s (threshold: 60s)
   Recommendation: Increase timeout from 120s to 180s
   Agent causing slowness: specialist-mortgage (average 72s)
   [View logs] [Increase timeout] [Ignore]
```

---

### warn-failing
**Meaning:** Error rate exceeds threshold

**Trigger:**
```python
if error_rate > 5%:  # Default threshold
    add_status("warn-failing")
```

**Error Rate Calculation:**
```
error_rate = (failed_executions / total_executions) * 100

Example:
  Failed: 5 out of 100 = 5% (exactly at threshold)
  Failed: 6 out of 100 = 6% (exceeds, triggers flag)
```

**Two-Strike Rule:**
```
First threshold breach: Warning (don't flag yet)
Second consecutive check with breach: Flag as warn-failing
This prevents false positives from temporary spikes
```

**Suggested Actions:**
1. Review recent error logs
2. Check if specific error type is common
3. Try fallback agent
4. Update route logic or agent prompts
5. Increase model temperature for more variation

**Error Types Tracked:**
- `timeout` — Agent didn't respond in time
- `validation` — Input/output contract violation
- `contract_mismatch` — Agent output format unexpected
- `agent_error` — Agent threw exception
- `parsing_error` — Couldn't parse agent output

---

### warn-cost
**Meaning:** Cost per execution exceeds budget

**Trigger:**
```python
if cost > cost_threshold:  # e.g., $1.0
    add_status("warn-cost")
```

**Cost Calculation:**
```python
cost = (tokens_used / 1000) * token_price

Example:
  gpt-4o-mini: $0.15 per M input tokens
  5000 tokens * 0.00015 = $0.75
```

**Suggested Actions:**
1. Use cheaper model (gpt-4o-mini instead of gpt-4)
2. Reduce prompt length (fewer examples, shorter context)
3. Use prompt caching (cache common prompts)
4. Rate limit to once per hour instead of on-demand

---

### offline
**Meaning:** Route not responding to requests

**Trigger:**
```python
if not_responding_for > 5_minutes:
    status = "offline"
```

**Detection:**
```python
# Every minute, try health check
async def health_check(route_id):
    try:
        result = await invoke_route_with_timeout(
            route_id, 
            {"test": "data"}, 
            timeout=10s
        )
        record_health_check(route_id, success=True)
    except Timeout:
        record_health_check(route_id, success=False)

# After 5 consecutive failures
if consecutive_failures > 5:
    status = "offline"
```

**Suggested Actions:**
1. Check if route service is running
2. Check network connectivity
3. Verify route exists in routing table
4. Check for out-of-memory or resource exhaustion

---

### frozen
**Meaning:** Admin manually blocked route

**Trigger:** Admin action only
```bash
safe route freeze loan-approval-v1 "Performance issues being investigated"
```

**Storage:**
```python
route_health.is_frozen = True
route_health.frozen_by = "admin@example.com"
route_health.frozen_reason = "Performance issues being investigated"
route_health.frozen_at = datetime.now()
```

**What Happens:**
- Route will not execute (requests rejected)
- Admin action logged in audit trail
- Incident ticket created in Agent 365
- CSA team notified

**Unfreeze:**
```bash
safe route unfreeze loan-approval-v1 "Issues resolved, performance confirmed"
```

---

## AUTO-DETECTION ALGORITHM

### Metric Calculation

Every 5 minutes, calculate metrics from last 1 hour of executions:

```python
async def update_metrics():
    for route_id in all_routes:
        # Get recent executions
        executions = await storage.get_executions(
            route_id=route_id,
            hours=1
        )
        
        if len(executions) == 0:
            continue  # No data yet
        
        # Calculate metrics
        metrics = HealthMetrics(
            route_id=route_id,
            time_window="1h",
            total_executions=len(executions),
            successful_executions=sum(1 for e in executions if e.success),
            failed_executions=sum(1 for e in executions if not e.success),
            success_rate=(successful / total) * 100,
            error_rate=((total - successful) / total) * 100,
            avg_duration=mean([e.duration_seconds for e in executions]),
            p95_duration=percentile([e.duration_seconds for e in executions], 0.95),
            p99_duration=percentile([e.duration_seconds for e in executions], 0.99),
            total_cost=sum(e.model_cost for e in executions),
            avg_cost=total_cost / len(executions),
            error_types=count_error_types(executions),
        )
        
        # Store metrics
        await storage.set_metrics(route_id, metrics)
        
        # Determine status
        status = await determine_status(route_id, metrics)
        await update_status(route_id, status)
```

### Status Determination

```python
async def determine_status(route_id: str, metrics: HealthMetrics) -> str:
    # Get thresholds
    config = await get_route_config(route_id)
    
    statuses = []
    
    # Check each threshold
    if metrics.p95_duration > config.p95_threshold:
        statuses.append("warn-slow")
    
    if metrics.error_rate > config.error_rate_threshold:
        statuses.append("warn-failing")
    
    if metrics.avg_cost > config.cost_threshold:
        statuses.append("warn-cost")
    
    # Check if offline (health check failures)
    if await is_offline(route_id):
        statuses.append("offline")
    
    # Check if frozen (admin action)
    if (await get_route_health(route_id)).is_frozen:
        statuses = ["frozen"]  # Frozen overrides all else
    
    # Determine final status
    if "frozen" in statuses:
        return "frozen"
    elif "offline" in statuses:
        return "offline"
    elif len(statuses) > 0:
        return statuses[0]  # Multiple warnings, pick first
    else:
        return "ready"
```

### Threshold Configuration

Default thresholds (configurable per route):

```yaml
health_registry:
  p95_latency_threshold_seconds: 60      # Alert if P95 > 60s
  error_rate_threshold_percent: 5        # Alert if error rate > 5%
  cost_threshold_dollars: 1.0            # Alert if cost > $1.0
  offline_threshold_minutes: 5           # Mark offline after 5 min of failures
  
  # Two-strike rule
  strikes_before_flag: 2                 # Require 2 consecutive breaches
  
  # Auto-recovery
  auto_recovery_enabled: true            # Try to recover automatically
  auto_recovery_max_attempts: 3
```

---

## STORAGE ABSTRACTION

### Interface Definition

```python
from abc import ABC, abstractmethod

class IRouteHealthStore(ABC):
    """Abstract interface for route health storage"""
    
    @abstractmethod
    async def record_execution(
        self,
        execution: RouteExecution
    ) → None:
        """Record a route execution"""
        pass
    
    @abstractmethod
    async def get_metrics(
        self,
        route_id: str,
        hours: int = 1
    ) → HealthMetrics:
        """Get metrics for a route in past N hours"""
        pass
    
    @abstractmethod
    async def get_health(
        self,
        route_id: str
    ) → RouteHealth:
        """Get current health status"""
        pass
    
    @abstractmethod
    async def set_status(
        self,
        route_id: str,
        status: str,
        reasons: List[str]
    ) → None:
        """Set route status"""
        pass
    
    @abstractmethod
    async def freeze_route(
        self,
        route_id: str,
        admin_email: str,
        reason: str
    ) → None:
        """Freeze a route (admin action)"""
        pass
    
    @abstractmethod
    async def unfreeze_route(
        self,
        route_id: str,
        admin_email: str,
        evidence: str
    ) → None:
        """Unfreeze a route (admin action)"""
        pass
    
    @abstractmethod
    async def get_audit_log(
        self,
        route_id: str
    ) → List[AuditEvent]:
        """Get audit log of status changes"""
        pass
```

### MVP Implementation: SemanticKernelRouteHealthStore

In-memory storage, optimized for single deployment:

```python
class SemanticKernelRouteHealthStore(IRouteHealthStore):
    """Fast, in-memory storage for route health metrics"""
    
    def __init__(self):
        self.executions: Dict[str, List[RouteExecution]] = {}
        self.health: Dict[str, RouteHealth] = {}
        self.audit_log: List[AuditEvent] = []
    
    async def record_execution(self, execution: RouteExecution):
        """Record execution and update metrics"""
        route_id = execution.route_id
        
        # Store execution
        if route_id not in self.executions:
            self.executions[route_id] = []
        self.executions[route_id].append(execution)
        
        # Keep only last 24 hours
        cutoff = datetime.now() - timedelta(hours=24)
        self.executions[route_id] = [
            e for e in self.executions[route_id]
            if e.timestamp > cutoff
        ]
    
    async def get_metrics(self, route_id: str, hours: int = 1) -> HealthMetrics:
        """Calculate metrics from stored executions"""
        executions = self.executions.get(route_id, [])
        
        # Filter by time window
        cutoff = datetime.now() - timedelta(hours=hours)
        recent = [e for e in executions if e.timestamp > cutoff]
        
        if not recent:
            return HealthMetrics(
                route_id=route_id,
                time_window=f"{hours}h",
                total_executions=0,
                success_rate=100,
                error_rate=0,
                # ... all zeros
            )
        
        # Calculate metrics
        successful = sum(1 for e in recent if e.success)
        durations = [e.duration_seconds for e in recent]
        costs = [e.model_cost for e in recent]
        
        return HealthMetrics(
            route_id=route_id,
            time_window=f"{hours}h",
            total_executions=len(recent),
            successful_executions=successful,
            failed_executions=len(recent) - successful,
            success_rate=(successful / len(recent)) * 100,
            error_rate=((len(recent) - successful) / len(recent)) * 100,
            avg_duration=mean(durations),
            p95_duration=percentile(durations, 0.95),
            total_cost=sum(costs),
            avg_cost=mean(costs),
        )
    
    async def get_health(self, route_id: str) -> RouteHealth:
        """Get current health status"""
        return self.health.get(route_id, RouteHealth(route_id=route_id, status="unknown"))
    
    async def set_status(self, route_id: str, status: str, reasons: List[str]):
        """Update health status"""
        old_status = self.health.get(route_id, {}).status if route_id in self.health else None
        
        health = RouteHealth(
            route_id=route_id,
            status=status,
            reasons=reasons,
            triggered_at=datetime.now(),
        )
        self.health[route_id] = health
        
        # Log audit event
        if old_status != status:
            self.audit_log.append(AuditEvent(
                route_id=route_id,
                action="status_change",
                old_status=old_status,
                new_status=status,
                timestamp=datetime.now(),
            ))
```

### Future Implementation: CosmosDbRouteHealthStore

Persistent, scalable storage:

```python
class CosmosDbRouteHealthStore(IRouteHealthStore):
    """
    Cosmos DB storage for route health metrics
    
    Schema:
    - Table: route_executions
      Partition: route_id
      Rows: execution records (time-series)
    
    - Table: route_health
      Partition: route_id
      Rows: current health status per route
    
    - Table: audit_log
      Partition: timestamp
      Rows: audit events
    """
    
    def __init__(self, cosmos_client):
        self.client = cosmos_client
        self.db = client.get_database_client("safe_framework")
        self.executions_container = self.db.get_container_client("route_executions")
        self.health_container = self.db.get_container_client("route_health")
        self.audit_container = self.db.get_container_client("audit_log")
    
    async def record_execution(self, execution: RouteExecution):
        """Store execution in Cosmos"""
        # Implement Cosmos write
        pass
    
    # ... etc
```

---

## ALERTING SYSTEM

### Alert Channels

```python
class AlertChannel(ABC):
    @abstractmethod
    async def send(self, alert: Alert) → None:
        pass

class EmailAlertChannel(AlertChannel):
    async def send(self, alert: Alert):
        # Send email to alert.recipients
        pass

class SlackAlertChannel(AlertChannel):
    async def send(self, alert: Alert):
        # Post to Slack channel
        pass

class PagerDutyAlertChannel(AlertChannel):
    async def send(self, alert: Alert):
        # Create PagerDuty incident
        pass

class DashboardAlertChannel(AlertChannel):
    async def send(self, alert: Alert):
        # Display on M365/Agent 365 dashboard
        pass
```

### Alert Generation

```python
async def send_alerts(route_id: str, old_status: str, new_status: str):
    """Send alerts when status changes"""
    
    if old_status == new_status:
        return  # No change, no alert
    
    # Build alert
    alert = Alert(
        route_id=route_id,
        old_status=old_status,
        new_status=new_status,
        timestamp=datetime.now(),
        recipients=get_alert_recipients(route_id),
        channels=get_alert_channels(route_id),  # email, slack, pagerduty
    )
    
    # Send to all channels
    for channel in alert.channels:
        await channel.send(alert)
```

### Example Alert

```
ALERT: Route loan-approval-v1 status changed

From: ready
To: warn-slow

Metrics:
  P95 Latency: 85s (threshold: 60s)
  Error Rate: 2% (within threshold)
  Cost: $0.50 (within threshold)

Recent Issues:
  - Last 3 executions all took >70s
  - Agent specialist-mortgage averaging 72s

Suggested Actions:
  1. Increase timeout from 120s to 180s
  2. Review specialist-mortgage logs for slowness
  3. Consider caching mortgage data

Dashboard: [View Route] [View Logs] [Increase Timeout]

Escalation: If not resolved in 1 hour, ticket will be escalated to engineering.
```

---

## CLI INTEGRATION

### Commands

```bash
# View current health
safe route health loan-approval-v1

# View metrics
safe route metrics loan-approval-v1 --period 24h

# Set alert thresholds
safe route alerts loan-approval-v1 \
  --warn-time 60s \
  --warn-error 5% \
  --warn-cost $1.0

# Freeze route (admin)
safe route freeze loan-approval-v1 "Performance issues"

# Unfreeze route (admin)
safe route unfreeze loan-approval-v1 "Issues resolved, performance verified"

# View audit log
safe route audit loan-approval-v1

# View all route statuses
safe route status --filter=warn-*

# Dashboard
safe dashboard  # Opens M365 dashboard with all routes
```

---

## TESTING

### Unit Tests

```python
class TestHealthRegistry:
    async def test_metrics_calculation():
        """Metrics calculated correctly"""
        executions = [
            RouteExecution(duration=5, success=True, cost=0.1),
            RouteExecution(duration=10, success=True, cost=0.1),
            RouteExecution(duration=15, success=False, cost=0.15),
        ]
        metrics = calculate_metrics(executions)
        assert metrics.avg_duration == 10
        assert metrics.success_rate == 66.7
        assert metrics.error_rate == 33.3
    
    async def test_status_determination():
        """Status determined correctly based on thresholds"""
        metrics = HealthMetrics(p95_duration=85, error_rate=2)
        config = RouteConfig(p95_threshold=60, error_threshold=5)
        
        status = determine_status(metrics, config)
        assert status == "warn-slow"
    
    async def test_two_strike_rule():
        """Two-strike rule prevents false positives"""
        # First threshold breach
        update_status("warn-slow")
        status1 = get_status()
        assert status1 == "ready"  # No flag yet
        
        # Second consecutive breach
        update_status("warn-slow")
        status2 = get_status()
        assert status2 == "warn-slow"  # Now flagged
    
    async def test_alert_sent_on_status_change():
        """Alert sent when status changes"""
        send_status_update("route-1", "ready", "warn-slow")
        
        # Verify alert sent
        assert len(mock_email_channel.calls) == 1
        assert mock_slack_channel.calls[0].text.contains("warn-slow")
    
    async def test_freeze_unfreeze():
        """Admin can freeze/unfreeze routes"""
        freeze_route("route-1", admin_email, reason)
        health = get_health("route-1")
        assert health.is_frozen == True
        
        unfreeze_route("route-1", admin_email)
        health = get_health("route-1")
        assert health.is_frozen == False

class TestAutoDetection:
    async def test_detects_slow_routes():
        """Detects routes exceeding latency threshold"""
        # Record 10 executions, all > 60s
        for i in range(10):
            record_execution(RouteExecution(
                route_id="route-1",
                duration=70,
                success=True
            ))
        
        # Update metrics
        await update_metrics()
        
        # Should be flagged as warn-slow
        health = await get_health("route-1")
        assert health.status == "warn-slow"
    
    async def test_detects_failing_routes():
        """Detects routes with high error rate"""
        # Record 10 executions, 6 failing
        for i in range(10):
            record_execution(RouteExecution(
                route_id="route-2",
                success=(i < 4)  # 4/10 = 40% error rate
            ))
        
        await update_metrics()
        health = await get_health("route-2")
        assert health.status == "warn-failing"
    
    async def test_no_false_positives_48h():
        """Zero false positives over 48 hours"""
        # Simulate 48 hours of normal operation
        # with occasional spikes
        
        # Record 1000 executions with metrics
        # Normal: 95% success, 5s avg latency
        # Spike: 1-2 executions with 70s latency
        
        # Verify no false flags
        for route in all_routes:
            health = await get_health(route)
            assert health.status == "ready"
```

---

**SAFE Phase 5: Health Registry Specification**  
**Real-Time Monitoring & Auto-Detection**  
**Weeks 6-7 | 10 Engineer-Days**

