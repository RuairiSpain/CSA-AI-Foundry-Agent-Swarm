"""Tests for ReleaseManager.promote() and transition validation."""
import pytest
from safe_core.release.manager import ReleaseManager, ReleaseStatus


@pytest.fixture
async def mgr_with_release():
    mgr = ReleaseManager()
    await mgr.create_release("v1.0", ["route-a", "route-b"])
    return mgr


class TestPromote:
    @pytest.mark.asyncio
    async def test_dev_to_staging_succeeds(self, mgr_with_release):
        mgr = mgr_with_release
        result = await mgr.promote("v1.0", from_env="dev", to_env="staging", approver="alice@example.com")
        assert result is True

    @pytest.mark.asyncio
    async def test_staging_to_prod_succeeds(self, mgr_with_release):
        mgr = mgr_with_release
        await mgr.promote("v1.0", from_env="dev", to_env="staging", approver="alice@example.com")
        result = await mgr.promote("v1.0", from_env="staging", to_env="prod", approver="bob@example.com")
        assert result is True
        assert mgr.releases["v1.0"].status == ReleaseStatus.DEPLOYED

    @pytest.mark.asyncio
    async def test_dev_to_prod_skipping_staging_fails(self, mgr_with_release):
        mgr = mgr_with_release
        result = await mgr.promote("v1.0", from_env="dev", to_env="prod", approver="alice@example.com")
        assert result is False

    @pytest.mark.asyncio
    async def test_unknown_version_fails(self):
        mgr = ReleaseManager()
        result = await mgr.promote("nonexistent", from_env="dev", to_env="staging", approver="x")
        assert result is False

    @pytest.mark.asyncio
    async def test_promotion_records_approver(self, mgr_with_release):
        mgr = mgr_with_release
        await mgr.promote("v1.0", from_env="dev", to_env="staging", approver="alice@example.com")
        assert mgr.releases["v1.0"].promotions[0]["approver"] == "alice@example.com"

    @pytest.mark.asyncio
    async def test_promotion_records_environments(self, mgr_with_release):
        mgr = mgr_with_release
        await mgr.promote("v1.0", from_env="dev", to_env="staging", approver="alice@example.com")
        p = mgr.releases["v1.0"].promotions[0]
        assert p["from_env"] == "dev"
        assert p["to_env"] == "staging"

    @pytest.mark.asyncio
    async def test_invalid_from_env_fails(self, mgr_with_release):
        mgr = mgr_with_release
        result = await mgr.promote("v1.0", from_env="unknown-env", to_env="prod", approver="x")
        assert result is False


class TestCreateAndTransition:
    @pytest.mark.asyncio
    async def test_create_release(self):
        mgr = ReleaseManager()
        release = await mgr.create_release("v2.0", ["comp-a"])
        assert release.version == "v2.0"
        assert release.status == ReleaseStatus.PLANNED

    @pytest.mark.asyncio
    async def test_transition_to_deployed(self):
        mgr = ReleaseManager()
        await mgr.create_release("v2.0", [])
        result = await mgr.transition_to_deployed("v2.0")
        assert result is True
        assert mgr.releases["v2.0"].status == ReleaseStatus.DEPLOYED

    @pytest.mark.asyncio
    async def test_release_timestamp_is_utc_aware(self):
        mgr = ReleaseManager()
        release = await mgr.create_release("v3.0", [])
        assert release.created_at.tzinfo is not None
