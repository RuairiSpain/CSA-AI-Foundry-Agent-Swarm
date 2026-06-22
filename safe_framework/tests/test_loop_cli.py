"""Tests for the `safe loop` CLI sub-commands."""

import pytest
from typer.testing import CliRunner
from safe_cli.main import app, _parse_interval

runner = CliRunner()


# ---------------------------------------------------------------------------
# _parse_interval helper
# ---------------------------------------------------------------------------

class TestParseInterval:
    def test_seconds(self):
        assert _parse_interval("30s") == 30.0

    def test_minutes(self):
        assert _parse_interval("5m") == 300.0

    def test_hours(self):
        assert _parse_interval("2h") == 7200.0

    def test_days(self):
        assert _parse_interval("1d") == 86400.0

    def test_plain_number(self):
        assert _parse_interval("120") == 120.0

    def test_fractional(self):
        assert _parse_interval("0.5m") == 30.0


# ---------------------------------------------------------------------------
# safe loop run
# ---------------------------------------------------------------------------

class TestLoopRunCommand:
    def test_run_exits_cleanly(self):
        result = runner.invoke(app, ["loop", "run", "my-route", "--max-iter", "1", "--interval", "0s"])
        assert result.exit_code == 0

    def test_run_shows_finish_message(self):
        result = runner.invoke(app, ["loop", "run", "test-route", "--max-iter", "1", "--interval", "0s"])
        assert "Loop finished" in result.output

    def test_run_default_interval(self):
        result = runner.invoke(app, ["loop", "run", "any-route", "--max-iter", "1"])
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# safe loop goal
# ---------------------------------------------------------------------------

class TestLoopGoalCommand:
    def test_goal_exits_cleanly(self):
        result = runner.invoke(app, [
            "loop", "goal", "my-route",
            "--condition", "output.get('done', False)",
            "--max-iter", "1",
        ])
        assert result.exit_code == 0

    def test_goal_shows_iteration_info(self):
        result = runner.invoke(app, [
            "loop", "goal", "my-route",
            "--max-iter", "1",
        ])
        assert "iteration" in result.output.lower() or "reason" in result.output

    def test_goal_no_condition_still_runs(self):
        result = runner.invoke(app, ["loop", "goal", "bare-route", "--max-iter", "1"])
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# safe loop sched
# ---------------------------------------------------------------------------

class TestLoopSchedCommand:
    def test_sched_creates_schedule_yaml(self, tmp_path):
        result = runner.invoke(app, [
            "loop", "sched", "my-route",
            "--cron", "0 9 * * *",
            "--routes-dir", str(tmp_path),
        ])
        assert result.exit_code == 0
        schedule_file = tmp_path / "my-route" / "schedule.yaml"
        assert schedule_file.exists()

    def test_sched_yaml_content(self, tmp_path):
        import yaml
        runner.invoke(app, [
            "loop", "sched", "report-route",
            "--cron", "0 8 * * 1",
            "--routes-dir", str(tmp_path),
        ])
        data = yaml.safe_load((tmp_path / "report-route" / "schedule.yaml").read_text())
        assert data["cron"] == "0 8 * * 1"
        assert data["route"] == "report-route"
        assert data["type"] == "interval-loop"

    def test_sched_shows_registered_message(self, tmp_path):
        result = runner.invoke(app, [
            "loop", "sched", "x", "--cron", "* * * * *",
            "--routes-dir", str(tmp_path),
        ])
        assert "Schedule registered" in result.output


# ---------------------------------------------------------------------------
# safe loop status
# ---------------------------------------------------------------------------

class TestLoopStatusCommand:
    def test_status_exits_cleanly(self):
        result = runner.invoke(app, ["loop", "status", "run-abc123"])
        assert result.exit_code == 0

    def test_status_shows_run_id(self):
        result = runner.invoke(app, ["loop", "status", "run-abc123"])
        assert "run-abc123" in result.output


# ---------------------------------------------------------------------------
# safe loop stop
# ---------------------------------------------------------------------------

class TestLoopStopCommand:
    def test_stop_exits_cleanly(self):
        result = runner.invoke(app, ["loop", "stop", "run-xyz"])
        assert result.exit_code == 0

    def test_stop_shows_run_id(self):
        result = runner.invoke(app, ["loop", "stop", "run-xyz"])
        assert "run-xyz" in result.output

    def test_stop_shows_confirmation(self):
        result = runner.invoke(app, ["loop", "stop", "run-xyz"])
        assert "Stop signal sent" in result.output or "stop" in result.output.lower()
