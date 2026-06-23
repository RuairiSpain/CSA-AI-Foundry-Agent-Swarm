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
    loop_default_max_iterations: int = 10

    # Pattern-specific defaults used by code generator
    evaluator_optimizer_max_iterations: int = 3
    evaluator_optimizer_quality_threshold: float = 0.85
    reflection_max_reflections: int = 2
    lats_max_iterations: int = 20
    lats_branching_factor: int = 3
    lats_exploration_constant: float = 1.414
    lats_success_threshold: float = 0.8
    lats_max_depth: int = 10
    pge_max_sprint_iterations: int = 5
    pge_max_interview_turns: int = 10

    # Execution retry defaults
    execution_max_retries: int = 3
    execution_base_backoff_seconds: float = 2.0

    # Governance cost defaults
    governance_max_monthly_cost_usd: float = 10000.0

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
            loop_default_max_iterations=int(
                os.environ.get("SAFE_LOOP_DEFAULT_MAX_ITERATIONS", "10")
            ),
            evaluator_optimizer_max_iterations=int(
                os.environ.get("SAFE_EVALUATOR_OPTIMIZER_MAX_ITERATIONS", "3")
            ),
            evaluator_optimizer_quality_threshold=float(
                os.environ.get("SAFE_EVALUATOR_OPTIMIZER_QUALITY_THRESHOLD", "0.85")
            ),
            reflection_max_reflections=int(
                os.environ.get("SAFE_REFLECTION_MAX_REFLECTIONS", "2")
            ),
            lats_max_iterations=int(
                os.environ.get("SAFE_LATS_MAX_ITERATIONS", "20")
            ),
            lats_branching_factor=int(
                os.environ.get("SAFE_LATS_BRANCHING_FACTOR", "3")
            ),
            lats_exploration_constant=float(
                os.environ.get("SAFE_LATS_EXPLORATION_CONSTANT", "1.414")
            ),
            lats_success_threshold=float(
                os.environ.get("SAFE_LATS_SUCCESS_THRESHOLD", "0.8")
            ),
            lats_max_depth=int(
                os.environ.get("SAFE_LATS_MAX_DEPTH", "10")
            ),
            pge_max_sprint_iterations=int(
                os.environ.get("SAFE_PGE_MAX_SPRINT_ITERATIONS", "5")
            ),
            pge_max_interview_turns=int(
                os.environ.get("SAFE_PGE_MAX_INTERVIEW_TURNS", "10")
            ),
            execution_max_retries=int(
                os.environ.get("SAFE_EXECUTION_MAX_RETRIES", "3")
            ),
            execution_base_backoff_seconds=float(
                os.environ.get("SAFE_EXECUTION_BASE_BACKOFF_SECONDS", "2.0")
            ),
            governance_max_monthly_cost_usd=float(
                os.environ.get("SAFE_GOVERNANCE_MAX_MONTHLY_COST_USD", "10000.0")
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
