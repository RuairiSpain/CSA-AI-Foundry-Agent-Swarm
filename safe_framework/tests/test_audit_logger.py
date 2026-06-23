"""Tests for audit logger persistence, hash-chain integrity, and tamper detection."""
import json
import pytest
import tempfile
from pathlib import Path
from safe_core.audit.logger import AuditLogger, AuditEventType


async def _log(logger, n=3):
    for i in range(n):
        await logger.log_event(
            event_type=AuditEventType.ROUTE_CREATED,
            actor="user@example.com",
            resource="route",
            resource_id=f"r-{i}",
            details={"i": i},
        )


class TestHashChain:
    @pytest.mark.asyncio
    async def test_empty_log_is_valid(self):
        logger = AuditLogger()
        assert await logger.verify_integrity() is True

    @pytest.mark.asyncio
    async def test_chain_valid_after_writes(self):
        logger = AuditLogger()
        await _log(logger, 5)
        assert await logger.verify_integrity() is True

    @pytest.mark.asyncio
    async def test_tampered_event_fails_integrity(self):
        logger = AuditLogger()
        await _log(logger, 3)
        logger.events[1].details["tampered"] = True
        assert await logger.verify_integrity() is False

    @pytest.mark.asyncio
    async def test_deleted_event_fails_integrity(self):
        logger = AuditLogger()
        await _log(logger, 3)
        del logger.events[1]
        assert await logger.verify_integrity() is False

    @pytest.mark.asyncio
    async def test_prev_hash_links_correctly(self):
        logger = AuditLogger()
        await _log(logger, 2)
        assert logger.events[1].prev_hash == logger.events[0].event_hash


class TestPersistence:
    @pytest.mark.asyncio
    async def test_events_survive_restart(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            log_path = f.name

        logger1 = AuditLogger(log_path=log_path)
        await _log(logger1, 3)

        logger2 = AuditLogger(log_path=log_path)
        assert len(logger2.events) == 3
        assert logger2.events[0].resource_id == "r-0"

    @pytest.mark.asyncio
    async def test_integrity_holds_after_reload(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            log_path = f.name

        logger1 = AuditLogger(log_path=log_path)
        await _log(logger1, 3)

        logger2 = AuditLogger(log_path=log_path)
        assert await logger2.verify_integrity() is True

    @pytest.mark.asyncio
    async def test_in_memory_logger_has_no_log_path(self):
        logger = AuditLogger()
        assert logger._log_path is None

    @pytest.mark.asyncio
    async def test_disk_file_is_valid_jsonl(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            log_path = f.name

        logger = AuditLogger(log_path=log_path)
        await _log(logger, 2)

        lines = Path(log_path).read_text().strip().splitlines()
        assert len(lines) == 2
        for line in lines:
            obj = json.loads(line)
            assert "event_id" in obj
            assert "event_hash" in obj
            assert "prev_hash" in obj


class TestTimestamps:
    @pytest.mark.asyncio
    async def test_timestamps_are_utc_aware(self):
        logger = AuditLogger()
        await _log(logger, 1)
        ts = logger.events[0].timestamp
        assert ts.tzinfo is not None
