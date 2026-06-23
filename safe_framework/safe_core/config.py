"""Centralised environment configuration for the SAFE framework.

All SAFE_ environment variables are read here. Other modules import the
module-level ``config`` singleton rather than calling ``os.environ`` directly.
Call ``SafeConfig.from_env()`` to get a fresh instance (useful in tests).
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class SafeConfig:
    # Runtime timeouts
    execution_timeout_seconds: int = 300
    agent_default_timeout_seconds: int = 3600

    # Code-generator loop controls
    retry_loop_max_retries: int = 3
    loop_spawn_budget: int = 10

    # Governance approvers
    approver_finance_lead: str = "finance-lead@company.com"
    approver_security_lead: str = "security-lead@company.com"
    approver_team_lead: str = "team-lead@company.com"
    high_cost_approver_threshold_factor: float = 0.5

    # Health thresholds
    health_failure_threshold: int = 2
    health_slow_threshold_ms: float = 5000.0
    health_cost_threshold_usd: float = 1000.0
    health_frozen_threshold_seconds: float = 3600.0

    @classmethod
    def from_env(cls) -> "SafeConfig":
        return cls(
            execution_timeout_seconds=int(
                os.environ.get("SAFE_EXECUTION_DEFAULT_TIMEOUT_SECONDS", "300")
            ),
            agent_default_timeout_seconds=int(
                os.environ.get("SAFE_AGENT_DEFAULT_TIMEOUT_SECONDS", "3600")
            ),
            retry_loop_max_retries=int(
                os.environ.get("SAFE_RETRY_LOOP_MAX_RETRIES", "3")
            ),
            loop_spawn_budget=int(
                os.environ.get("SAFE_RALPH_LOOP_SPAWN_BUDGET", "10")
            ),
            approver_finance_lead=os.environ.get(
                "SAFE_APPROVER_FINANCE_LEAD", "finance-lead@company.com"
            ),
            approver_security_lead=os.environ.get(
                "SAFE_APPROVER_SECURITY_LEAD", "security-lead@company.com"
            ),
            approver_team_lead=os.environ.get(
                "SAFE_APPROVER_TEAM_LEAD", "team-lead@company.com"
            ),
            high_cost_approver_threshold_factor=float(
                os.environ.get("SAFE_HIGH_COST_APPROVER_THRESHOLD_FACTOR", "0.5")
            ),
            health_failure_threshold=int(
                os.environ.get("SAFE_HEALTH_FAILURE_THRESHOLD", "2")
            ),
            health_slow_threshold_ms=float(
                os.environ.get("SAFE_HEALTH_SLOW_THRESHOLD_MS", "5000.0")
            ),
            health_cost_threshold_usd=float(
                os.environ.get("SAFE_HEALTH_COST_THRESHOLD_USD", "1000.0")
            ),
            health_frozen_threshold_seconds=float(
                os.environ.get("SAFE_HEALTH_FROZEN_THRESHOLD_SECONDS", "3600")
            ),
        )


config = SafeConfig.from_env()
