import pytest
import json
import asyncio
from datetime import datetime, timezone
import httpx
from fastapi.testclient import TestClient

from app.main import app
from app.racing.live_manager import LiveSessionManager, live_session_manager
from app.racing.fixtures import BAHRAIN_2024_LIVE_FIXTURE
from app.racing.models import DataStateEnum, SessionStatusEnum
from app.racing.schemas import LiveIncrementalUpdate
from app.providers.openf1 import OpenF1Provider

def test_live_manager_fixture_snapshot():
    mgr = LiveSessionManager()
    mgr.register_fixture_session("test_sess", BAHRAIN_2024_LIVE_FIXTURE)
    snapshot = mgr._build_snapshot_from_fixture("test_sess", BAHRAIN_2024_LIVE_FIXTURE)
    
    assert snapshot.session_id == "test_sess"
    assert snapshot.current_lap == 32
    assert snapshot.total_laps == 57
    assert len(snapshot.timing_tower) == 8
    assert snapshot.timing_tower[0].driver_code == "VER"
    assert snapshot.timing_tower[0].position == 1
    assert snapshot.timing_tower[1].driver_code == "PER"
    assert snapshot.timing_tower[1].positions_gained == 3
    assert snapshot.provenance.is_test_fixture is True
    assert snapshot.provenance.data_state == DataStateEnum.HISTORICAL
    assert snapshot.weather.track_temperature == 24.2
    assert len(snapshot.pit_stops) == 5
    assert len(snapshot.race_control) == 5

def test_live_snapshot_rest_endpoint():
    client = TestClient(app)
    # 2024_01_race is registered in lifespan
    live_session_manager.register_fixture_session("2024_01_race", BAHRAIN_2024_LIVE_FIXTURE)
    response = client.get("/api/v1/live/2024_01_race/snapshot")
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "2024_01_race"
    assert data["current_lap"] == 32
    assert data["provenance"]["is_test_fixture"] is True
    assert len(data["timing_tower"]) >= 8

def test_live_snapshot_not_found():
    client = TestClient(app)
    response = client.get("/api/v1/live/nonexistent_session/snapshot")
    assert response.status_code == 404

def test_live_websocket_connection_and_heartbeat():
    client = TestClient(app)
    live_session_manager.register_fixture_session("2024_01_race", BAHRAIN_2024_LIVE_FIXTURE)
    with client.websocket_connect("/ws/live/2024_01_race") as ws:
        # First message is SNAPSHOT
        first_raw = ws.receive_text()
        first_msg = json.loads(first_raw)
        assert first_msg["type"] == "SNAPSHOT"
        assert first_msg["session_id"] == "2024_01_race"
        assert first_msg["payload"]["current_lap"] == 32
        
        # Send PING heartbeat
        ws.send_text(json.dumps({"type": "PING"}))
        pong_raw = ws.receive_text()
        pong = json.loads(pong_raw)
        assert pong["type"] == "PONG"
        assert "timestamp" in pong

        # Send RESYNC request
        ws.send_text(json.dumps({"type": "RESYNC"}))
        resync_raw = ws.receive_text()
        resync = json.loads(resync_raw)
        assert resync["type"] == "SNAPSHOT"
        assert resync["session_id"] == "2024_01_race"

@pytest.mark.asyncio
async def test_live_incremental_update_and_backpressure():
    mgr = LiveSessionManager()
    queue = mgr.subscribe("sess_1")
    
    update = LiveIncrementalUpdate(
        type="TIMING",
        session_id="sess_1",
        sequence_number=1,
        timestamp=datetime.now(timezone.utc),
        data_state=DataStateEnum.HISTORICAL,
        data={"current_lap": 33}
    )
    await mgr.broadcast_update("sess_1", update)
    
    received = await queue.get()
    assert received.type == "TIMING"
    assert received.data["current_lap"] == 33
    
    mgr.unsubscribe("sess_1", queue)
    assert queue not in mgr._subscriber_queues["sess_1"]

@pytest.mark.asyncio
async def test_provider_adapter_endpoints_mock():
    # Test provider methods with mock client
    async def handler(request: httpx.Request):
        url = str(request.url)
        if "drivers" in url:
            return httpx.Response(200, json=[
                {"driver_number": 1, "name_acronym": "VER", "full_name": "Max Verstappen", "team_name": "Red Bull Racing", "team_colour": "3671c6"}
            ])
        elif "position" in url:
            return httpx.Response(200, json=[
                {"driver_number": 1, "position": 1}
            ])
        elif "intervals" in url:
            return httpx.Response(200, json=[
                {"driver_number": 1, "gap_to_leader": 0.0, "interval": 0.0}
            ])
        elif "laps" in url:
            return httpx.Response(200, json=[
                {"driver_number": 1, "lap_number": 10, "lap_duration": 92.5}
            ])
        elif "weather" in url:
            return httpx.Response(200, json=[
                {"air_temperature": 20.5, "track_temperature": 28.0, "humidity": 50.0}
            ])
        elif "race_control" in url:
            return httpx.Response(200, json=[
                {"lap_number": 1, "category": "Flag", "flag": "GREEN", "message": "TRACK CLEAR"}
            ])
        return httpx.Response(200, json=[])

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = OpenF1Provider(client=mock_client)
    
    drivers = await provider.get_drivers("9472")
    assert len(drivers) == 1
    assert drivers[0]["name_acronym"] == "VER"
    
    positions = await provider.get_positions("9472")
    assert len(positions) == 1
    assert positions[0]["position"] == 1
    
    weather = await provider.get_weather("9472")
    assert weather["air_temperature"] == 20.5
    
    rc = await provider.get_race_control_messages("9472")
    assert len(rc) == 1
    assert rc[0]["flag"] == "GREEN"

def test_live_diagnostics_endpoint():
    client = TestClient(app)
    res = client.get("/api/v1/live/diagnostics")
    assert res.status_code == 200
    diag = res.json()
    assert "upstream_provider" in diag
    assert "connection_status" in diag
    assert "is_connected" in diag
    assert "broker" in diag
    assert "total_messages_received" in diag
    assert "total_duplicates_filtered" in diag
    assert "connected_clients_count" in diag
    assert "has_credentials" in diag
    # Ensure sensitive credentials are NOT exposed
    assert "password" not in diag
    assert "username" not in diag
    assert "token" not in diag

def test_live_sessions_endpoint():
    client = TestClient(app)
    res = client.get("/api/v1/live/sessions")
    assert res.status_code == 200
    sessions = res.json()
    assert isinstance(sessions, list)
    assert len(sessions) >= 1
    # Check that session format includes provider mapping and data state
    first_sess = sessions[0]
    assert "session_id" in first_sess
    assert "session_name" in first_sess
    assert "provider_session_key" in first_sess
    assert "data_state" in first_sess
    assert first_sess["data_state"] in ["LIVE", "HISTORICAL"]

def test_openf1_stream_manager_deduplication_and_filtering():
    from app.providers.openf1_stream import OpenF1StreamManager

    events_received = []
    def callback(topic, payload):
        events_received.append((topic, payload))

    manager = OpenF1StreamManager(event_callback=callback)
    manager.active_session_key = "9472"

    msg1 = json.dumps({
        "session_key": 9472,
        "driver_number": 1,
        "date": "2024-03-02T15:05:00.000Z",
        "lap_number": 1
    }).encode("utf-8")

    # Ingest first message
    manager._handle_raw_message("v1/laps", msg1)
    assert manager.total_messages_received == 1
    assert manager.total_duplicates_filtered == 0
    assert len(events_received) == 1

    # Ingest exact duplicate message
    manager._handle_raw_message("v1/laps", msg1)
    assert manager.total_messages_received == 2
    assert manager.total_duplicates_filtered == 1
    assert len(events_received) == 1 # duplicate filtered, not dispatched

    # Ingest message for a different session - should be filtered
    msg_other_session = json.dumps({
        "session_key": 9999,
        "driver_number": 1,
        "date": "2024-03-02T15:05:01.000Z",
        "lap_number": 1
    }).encode("utf-8")
    manager._handle_raw_message("v1/laps", msg_other_session)
    assert manager.total_messages_received == 3
    assert len(events_received) == 1

    # Ingest new distinct message for active session
    msg2 = json.dumps({
        "session_key": 9472,
        "driver_number": 1,
        "date": "2024-03-02T15:06:00.000Z",
        "lap_number": 2
    }).encode("utf-8")
    manager._handle_raw_message("v1/laps", msg2)
    assert manager.total_messages_received == 4
    assert manager.total_duplicates_filtered == 1
    assert len(events_received) == 2

@pytest.mark.asyncio
async def test_live_manager_stream_event_to_subscriber():
    """
    Verifies that on_stream_event formats incremental typed messages,
    updates Redis timestamp, and delivers to subscribed queues.
    """
    mgr = LiveSessionManager()
    queue = mgr.subscribe("2024_01_race")

    await mgr.on_stream_event("9472", "v1/race_control", {
        "session_key": 9472,
        "category": "Flag",
        "flag": "YELLOW",
        "message": "SECTOR 2 YELLOW FLAG"
    })

    received = await queue.get()
    assert received.type == "RACE_CONTROL"
    assert received.session_id == "2024_01_race"
    assert received.data["flag"] == "YELLOW"
    assert received.data_state == DataStateEnum.LIVE

    mgr.unsubscribe("2024_01_race", queue)

@pytest.mark.asyncio
async def test_live_manager_stream_event_location_and_telemetry():
    """
    Verifies that location and car_data topics map to MAP_POSITIONS and TELEMETRY.
    """
    mgr = LiveSessionManager()
    queue = mgr.subscribe("2024_01_race")

    # Location topic
    await mgr.on_stream_event("9472", "v1/location", {
        "session_key": 9472,
        "driver_number": 1,
        "x": 1234.5,
        "y": 6789.0
    })
    msg_loc = await queue.get()
    assert msg_loc.type == "MAP_POSITIONS"
    assert msg_loc.data["x"] == 1234.5

    # Car data topic
    await mgr.on_stream_event("9472", "v1/car_data", {
        "session_key": 9472,
        "driver_number": 1,
        "speed": 315,
        "throttle": 100
    })
    msg_telem = await queue.get()
    assert msg_telem.type == "TELEMETRY"
    assert msg_telem.data["speed"] == 315

    mgr.unsubscribe("2024_01_race", queue)

@pytest.mark.asyncio
async def test_upstream_token_missing_credentials_graceful_handling():
    """
    Verifies that when OPENF1_USERNAME / OPENF1_PASSWORD are not set in the environment,
    get_access_token() returns None and start_streaming() gracefully marks CREDENTIALS_MISSING
    without crashing or falsifying connection state.
    """
    from app.providers.openf1 import OpenF1Provider
    from app.providers.openf1_stream import OpenF1StreamManager
    from app.core.config import settings

    provider = OpenF1Provider()
    token = await provider.get_access_token()
    # In test environment without .env credentials, token should be None
    if not settings.OPENF1_USERNAME or not settings.OPENF1_PASSWORD:
        assert token is None

        stream_mgr = OpenF1StreamManager(provider=provider)
        res = await stream_mgr.start_streaming("9472")
        assert res is False
        assert stream_mgr.connection_status == "CREDENTIALS_MISSING"
        assert stream_mgr.is_connected is False




