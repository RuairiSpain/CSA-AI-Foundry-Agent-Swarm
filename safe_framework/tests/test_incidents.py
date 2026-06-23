"""Tests for IncidentResponder — create, resolve, and status transitions."""
import pytest
from safe_core.incidents.responder import (
    Incident,
    IncidentResponder,
    IncidentSeverity,
    IncidentStatus,
)


@pytest.fixture
async def responder():
    return IncidentResponder()


@pytest.fixture
async def responder_with_incident():
    r = IncidentResponder()
    await r.create_incident("inc-1", "High CPU", IncidentSeverity.HIGH, ["route-a"])
    return r


class TestCreateIncident:
    @pytest.mark.asyncio
    async def test_create_returns_incident(self, responder):
        inc = await responder.create_incident(
            "inc-1", "DB timeout", IncidentSeverity.CRITICAL, ["db-route"]
        )
        assert isinstance(inc, Incident)

    @pytest.mark.asyncio
    async def test_create_sets_open_status(self, responder):
        inc = await responder.create_incident(
            "inc-2", "Latency spike", IncidentSeverity.MEDIUM, []
        )
        assert inc.status == IncidentStatus.OPEN

    @pytest.mark.asyncio
    async def test_create_stores_incident(self, responder):
        await responder.create_incident("inc-3", "Auth failure", IncidentSeverity.LOW, [])
        assert "inc-3" in responder.incidents

    @pytest.mark.asyncio
    async def test_create_stores_affected_routes(self, responder):
        routes = ["route-x", "route-y"]
        inc = await responder.create_incident(
            "inc-4", "Multi-route failure", IncidentSeverity.HIGH, routes
        )
        assert inc.affected_routes == routes

    @pytest.mark.asyncio
    async def test_create_uses_utc_timestamp(self, responder):
        inc = await responder.create_incident(
            "inc-5", "Clock check", IncidentSeverity.LOW, []
        )
        assert inc.created_at.tzinfo is not None

    @pytest.mark.asyncio
    async def test_create_severity_critical(self, responder):
        inc = await responder.create_incident(
            "inc-6", "Complete outage", IncidentSeverity.CRITICAL, ["all"]
        )
        assert inc.severity == IncidentSeverity.CRITICAL


class TestResolveIncident:
    @pytest.mark.asyncio
    async def test_resolve_existing_returns_true(self, responder_with_incident):
        result = await responder_with_incident.resolve_incident("inc-1")
        assert result is True

    @pytest.mark.asyncio
    async def test_resolve_sets_resolved_status(self, responder_with_incident):
        await responder_with_incident.resolve_incident("inc-1")
        assert responder_with_incident.incidents["inc-1"].status == IncidentStatus.RESOLVED

    @pytest.mark.asyncio
    async def test_resolve_unknown_returns_false(self, responder):
        result = await responder.resolve_incident("does-not-exist")
        assert result is False

    @pytest.mark.asyncio
    async def test_resolve_does_not_remove_incident(self, responder_with_incident):
        await responder_with_incident.resolve_incident("inc-1")
        assert "inc-1" in responder_with_incident.incidents

    @pytest.mark.asyncio
    async def test_multiple_incidents_resolve_independently(self, responder):
        await responder.create_incident("a", "A", IncidentSeverity.LOW, [])
        await responder.create_incident("b", "B", IncidentSeverity.HIGH, [])
        await responder.resolve_incident("a")
        assert responder.incidents["a"].status == IncidentStatus.RESOLVED
        assert responder.incidents["b"].status == IncidentStatus.OPEN
