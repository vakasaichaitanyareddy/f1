import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import engine, Base, async_session_maker
from app.racing.seed_data import seed_verified_2024_data

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
async def test_championship_intelligence_api():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/championship/intelligence?remaining_gps=23&remaining_sprints=6")
        assert response.status_code == 200
        data = response.json()
        assert data["leader"] == "VER"
        assert data["leader_clinched"] is False
        assert len(data["contenders"]) > 0

@pytest.mark.asyncio
async def test_auth_and_user_preferences():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register
        reg_res = await client.post("/api/v1/auth/register", json={
            "email": "testracer@apex-gp.internal",
            "password": "SecurePassword123!",
            "full_name": "Apex Racer"
        })
        assert reg_res.status_code == 200
        token = reg_res.json()["access_token"]

        # Patch preferences (Enable spoiler shield)
        pref_res = await client.patch(
            "/api/v1/user/preferences",
            headers={"Authorization": f"Bearer {token}"},
            json={"spoiler_shield_enabled": True, "favorite_driver_id": "max_verstappen"}
        )
        assert pref_res.status_code == 200
        assert pref_res.json()["spoiler_shield_enabled"] is True
        assert pref_res.json()["favorite_driver_id"] == "max_verstappen"
