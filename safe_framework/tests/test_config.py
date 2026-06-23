"""Tests for centralised SAFE configuration (safe_core/config.py)."""

import os
import pytest
from safe_core.config import SafeConfig


class TestSafeConfigDefaults:
    def test_default_execution_timeout(self):
        cfg = SafeConfig()
        assert cfg.execution_timeout_seconds == 300

    def test_default_agent_timeout(self):
        cfg = SafeConfig()
        assert cfg.agent_default_timeout_seconds == 3600

    def test_default_retry_loop(self):
        cfg = SafeConfig()
        assert cfg.retry_loop_max_retries == 3

    def test_default_spawn_budget(self):
        cfg = SafeConfig()
        assert cfg.loop_spawn_budget == 10

    def test_default_approver_emails(self):
        cfg = SafeConfig()
        assert "@" in cfg.approver_finance_lead
        assert "@" in cfg.approver_security_lead
        assert "@" in cfg.approver_team_lead

    def test_default_health_thresholds(self):
        cfg = SafeConfig()
        assert cfg.health_failure_threshold == 2
        assert cfg.health_slow_threshold_ms == 5000.0
        assert cfg.health_cost_threshold_usd == 1000.0
        assert cfg.health_frozen_threshold_seconds == 3600.0

    def test_frozen(self):
        cfg = SafeConfig()
        with pytest.raises((AttributeError, TypeError)):
            cfg.execution_timeout_seconds = 999  # type: ignore[misc]


class TestSafeConfigFromEnv:
    def test_reads_execution_timeout(self, monkeypatch):
        monkeypatch.setenv("SAFE_EXECUTION_DEFAULT_TIMEOUT_SECONDS", "600")
        cfg = SafeConfig.from_env()
        assert cfg.execution_timeout_seconds == 600

    def test_reads_agent_timeout(self, monkeypatch):
        monkeypatch.setenv("SAFE_AGENT_DEFAULT_TIMEOUT_SECONDS", "7200")
        cfg = SafeConfig.from_env()
        assert cfg.agent_default_timeout_seconds == 7200

    def test_reads_retry_loop(self, monkeypatch):
        monkeypatch.setenv("SAFE_RETRY_LOOP_MAX_RETRIES", "5")
        cfg = SafeConfig.from_env()
        assert cfg.retry_loop_max_retries == 5

    def test_reads_spawn_budget(self, monkeypatch):
        monkeypatch.setenv("SAFE_RALPH_LOOP_SPAWN_BUDGET", "20")
        cfg = SafeConfig.from_env()
        assert cfg.loop_spawn_budget == 20

    def test_reads_approver_emails(self, monkeypatch):
        monkeypatch.setenv("SAFE_APPROVER_FINANCE_LEAD", "cfo@acme.com")
        monkeypatch.setenv("SAFE_APPROVER_SECURITY_LEAD", "ciso@acme.com")
        monkeypatch.setenv("SAFE_APPROVER_TEAM_LEAD", "lead@acme.com")
        cfg = SafeConfig.from_env()
        assert cfg.approver_finance_lead == "cfo@acme.com"
        assert cfg.approver_security_lead == "ciso@acme.com"
        assert cfg.approver_team_lead == "lead@acme.com"

    def test_reads_health_thresholds(self, monkeypatch):
        monkeypatch.setenv("SAFE_HEALTH_FAILURE_THRESHOLD", "4")
        monkeypatch.setenv("SAFE_HEALTH_SLOW_THRESHOLD_MS", "2000.0")
        monkeypatch.setenv("SAFE_HEALTH_COST_THRESHOLD_USD", "500.0")
        monkeypatch.setenv("SAFE_HEALTH_FROZEN_THRESHOLD_SECONDS", "1800")
        cfg = SafeConfig.from_env()
        assert cfg.health_failure_threshold == 4
        assert cfg.health_slow_threshold_ms == 2000.0
        assert cfg.health_cost_threshold_usd == 500.0
        assert cfg.health_frozen_threshold_seconds == 1800.0

    def test_falls_back_to_defaults_when_unset(self, monkeypatch):
        for key in [
            "SAFE_EXECUTION_DEFAULT_TIMEOUT_SECONDS",
            "SAFE_AGENT_DEFAULT_TIMEOUT_SECONDS",
            "SAFE_RETRY_LOOP_MAX_RETRIES",
        ]:
            monkeypatch.delenv(key, raising=False)
        cfg = SafeConfig.from_env()
        assert cfg.execution_timeout_seconds == 300
        assert cfg.agent_default_timeout_seconds == 3600
        assert cfg.retry_loop_max_retries == 3

    def test_cost_threshold_factor(self, monkeypatch):
        monkeypatch.setenv("SAFE_HIGH_COST_APPROVER_THRESHOLD_FACTOR", "0.75")
        cfg = SafeConfig.from_env()
        assert cfg.high_cost_approver_threshold_factor == 0.75
