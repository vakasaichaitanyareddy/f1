import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from datetime import timedelta
import httpx
from unittest.mock import AsyncMock, patch

from app.main import app
from app.core.database import engine, Base, async_session_maker
from app.racing.seed_data import seed_verified_2024_data
from app.identity.security import create_access_token
from app.providers.openf1 import OpenF1Provider
from app.racing.models import DataStateEnum

@pytest_asyncio.fixture(scope="module", autouse=True)
async def setup_test_db():
    # Setup tables in SQLite
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed verified test data
    async with async_session_maker() as session:
        await seed_verified_2024_data(session)

    yield

    # Teardown
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# 1. Base Endpoint Tests
@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "apex-gp-api"

@pytest.mark.asyncio
async def test_get_meetings():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/meetings?season=2024")
        assert response.status_code == 200
        meetings = response.json()
        assert len(meetings) >= 1
        assert meetings[0]["round_number"] == 1
        assert meetings[0]["country"] == "Bahrain"

@pytest.mark.asyncio
async def test_get_meeting_detail_and_not_found():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Existing meeting
        res = await client.get("/api/v1/meetings/2024_01_bahrain")
        assert res.status_code == 200
        assert res.json()["circuit_id"] == "bahrain"

        # Missing meeting
        res_404 = await client.get("/api/v1/meetings/non_existent_round")
        assert res_404.status_code == 404
        assert res_404.json()["detail"] == "Meeting not found"

@pytest.mark.asyncio
async def test_get_standings():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/standings/drivers")
        assert response.status_code == 200
        standings = response.json()
        assert len(standings) >= 1
        # P1 is Max Verstappen with 26 points
        assert standings[0]["driver"]["code"] == "VER"
        assert standings[0]["points"] == 26.0
        assert standings[0]["points_behind_leader"] == 0.0

@pytest.mark.asyncio
async def test_session_classification_provenance():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/sessions/2024_01_race/classification")
        assert res.status_code == 200
        data = res.json()
        assert len(data["results"]) == 8
        # Provenance must be tagged as verified test fixture
        prov = data["provenance"]
        assert prov["verified"] is True
        assert prov["data_state"] == "HISTORICAL"
        assert prov["is_test_fixture"] is True
        assert "Development seed baseline" in prov["notes"]

@pytest.mark.asyncio
async def test_session_classification_not_found():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/sessions/invalid_session_id/classification")
        assert res.status_code == 404
        assert res.json()["detail"] == "Session not found"

@pytest.mark.asyncio
async def test_championship_intelligence_api():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/championship/intelligence?remaining_gps=23&remaining_sprints=6")
        assert response.status_code == 200
        data = response.json()
        assert data["leader"] == "VER"
        assert data["leader_clinched"] is False
        assert len(data["contenders"]) > 0
        prov = data["provenance"]
        assert prov["is_test_fixture"] is True

# 2. Authentication & Authorization Edge Cases
@pytest.mark.asyncio
async def test_auth_registration_and_duplicate():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register new
        reg_res = await client.post("/api/v1/auth/register", json={
            "email": "pilot1@apex-gp.internal",
            "password": "SecurePassword123!",
            "full_name": "Test Pilot"
        })
        assert reg_res.status_code == 200
        assert "access_token" in reg_res.json()

        # Duplicate email registration must return 400
        dup_res = await client.post("/api/v1/auth/register", json={
            "email": "pilot1@apex-gp.internal",
            "password": "OtherPassword456!",
            "full_name": "Another Pilot"
        })
        assert dup_res.status_code == 400
        assert dup_res.json()["detail"] == "Email already registered"

@pytest.mark.asyncio
async def test_auth_login_success_and_failure():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Invalid password
        fail_res = await client.post("/api/v1/auth/login", json={
            "email": "pilot1@apex-gp.internal",
            "password": "WrongPassword!"
        })
        assert fail_res.status_code == 401
        assert fail_res.json()["detail"] == "Invalid email or password"

        # Non-existent email
        notfound_res = await client.post("/api/v1/auth/login", json={
            "email": "ghost@apex-gp.internal",
            "password": "SomePassword"
        })
        assert notfound_res.status_code == 401

        # Valid login
        login_res = await client.post("/api/v1/auth/login", json={
            "email": "pilot1@apex-gp.internal",
            "password": "SecurePassword123!"
        })
        assert login_res.status_code == 200
        assert "access_token" in login_res.json()

@pytest.mark.asyncio
async def test_expired_or_invalid_jwt_token():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. No token
        res_no_token = await client.get("/api/v1/user/me")
        assert res_no_token.status_code == 401

        # 2. Malformed token
        res_malformed = await client.get(
            "/api/v1/user/me",
            headers={"Authorization": "Bearer malformed.jwt.token"}
        )
        assert res_malformed.status_code == 401

        # 3. Expired token
        expired_token = create_access_token(
            {"sub": "non_existent_id"},
            expires_delta=timedelta(seconds=-10)
        )
        res_expired = await client.get(
            "/api/v1/user/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        assert res_expired.status_code == 401

# 3. Provider Resilience & Error Behavior (OpenF1 Mocking)
@pytest.mark.asyncio
async def test_openf1_provider_success():
    from unittest.mock import MagicMock
    mock_client = AsyncMock()
    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = [{"session_key": "9150", "country_name": "Bahrain"}]
    mock_client.get.return_value = mock_res

    provider = OpenF1Provider(client=mock_client)
    result = await provider.get_latest_session(country_name="Bahrain")
    assert result["session"] is not None
    assert result["session"]["session_key"] == "9150"
    assert result["provenance"].verified is True
    assert result["provenance"].data_state == DataStateEnum.HISTORICAL

@pytest.mark.asyncio
async def test_openf1_provider_rate_limit_and_timeout():
    from unittest.mock import MagicMock
    mock_client = AsyncMock()

    # 1. HTTP 429 Rate Limit
    mock_res_429 = MagicMock()
    mock_res_429.status_code = 429
    mock_client.get.return_value = mock_res_429

    provider = OpenF1Provider(client=mock_client)
    res_429 = await provider.get_latest_session()
    assert res_429["session"] is None
    assert res_429["provenance"].data_state == DataStateEnum.UNAVAILABLE
    assert "rate limit" in res_429["provenance"].notes.lower()

    # 2. Timeout Exception
    mock_client.get.side_effect = httpx.TimeoutException("Connection timed out")
    res_timeout = await provider.get_latest_session()
    assert res_timeout["session"] is None
    assert res_timeout["provenance"].data_state == DataStateEnum.UNAVAILABLE
    assert "timed out" in res_timeout["provenance"].notes.lower()
