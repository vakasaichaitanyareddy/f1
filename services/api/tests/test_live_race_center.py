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

def test_openf1_stream_incremental_updates_and_out_of_order():
    from app.providers.openf1_stream import OpenF1StreamManager

    events = []
    manager = OpenF1StreamManager(event_callback=lambda t, p: events.append((t, p)))
    manager.active_session_key = "9472"

    # 1. Lap sector 1 completion
    msg_s1 = json.dumps({
        "session_key": 9472,
        "_id": "lap_1_d1",
        "driver_number": 1,
        "lap_number": 10,
        "date": "2024-03-02T15:20:00.000Z",
        "duration_sector_1": 28.5
    }).encode("utf-8")
    manager._handle_raw_message("v1/laps", msg_s1)
    assert len(events) == 1
    assert events[-1][1]["duration_sector_1"] == 28.5

    # 2. Duplicate delivery of exact same message - filtered!
    manager._handle_raw_message("v1/laps", msg_s1)
    assert len(events) == 1
    assert manager.total_duplicates_filtered == 1

    # 3. Incremental update for same record key (_id: lap_1_d1) with Sector 2 completed
    msg_s2 = json.dumps({
        "session_key": 9472,
        "_id": "lap_1_d1",
        "driver_number": 1,
        "lap_number": 10,
        "date": "2024-03-02T15:20:30.000Z",
        "duration_sector_2": 39.1
    }).encode("utf-8")
    manager._handle_raw_message("v1/laps", msg_s2)
    assert len(events) == 2
    # Ensure previous sector 1 is preserved via enrichment
    assert events[-1][1]["duration_sector_1"] == 28.5
    assert events[-1][1]["duration_sector_2"] == 39.1

    # 4. Out-of-order message with older timestamp for driver 1
    msg_stale = json.dumps({
        "session_key": 9472,
        "driver_number": 1,
        "date": "2024-03-02T15:19:00.000Z",
        "lap_number": 9
    }).encode("utf-8")
    manager._handle_raw_message("v1/laps", msg_stale)
    assert len(events) == 2 # Stale message rejected
    assert manager.total_out_of_order_filtered == 1

    # 5. Malformed payload handled safely without crash
    manager._handle_raw_message("v1/laps", b"invalid json content{{{")
    manager._handle_raw_message("v1/laps", b"")
    assert len(events) == 2 # Safely ignored

def test_openf1_stream_diagnostics_states():
    from app.providers.openf1_stream import OpenF1StreamManager

    manager = OpenF1StreamManager()
    diag = manager.get_diagnostics()
    assert diag["upstream_provider"] == "OpenF1_MQTT_Stream"
    assert "total_duplicates_filtered" in diag
    assert "total_out_of_order_filtered" in diag

    # Simulate connected receiving
    manager.is_connected = True
    manager.last_upstream_timestamp = datetime.now(timezone.utc)
    diag_receiving = manager.get_diagnostics()
    assert diag_receiving["connection_status"] == "CONNECTED_RECEIVING"
    assert diag_receiving["ingestion_lag_seconds"] is not None
    assert diag_receiving["ingestion_lag_seconds"] <= 1.0


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

@pytest.mark.asyncio
async def test_multi_client_multi_session_isolation():
    """
    Verifies that multiple clients subscribing to distinct sessions
    receive only updates corresponding to their specific subscribed session.
    """
    mgr = LiveSessionManager()
    queue_session_a = mgr.subscribe("session_alpha")
    queue_session_b = mgr.subscribe("session_beta")

    # Broadcast update to session_alpha only
    update_a = LiveIncrementalUpdate(
        type="TIMING",
        session_id="session_alpha",
        sequence_number=1,
        timestamp=datetime.now(timezone.utc),
        data_state=DataStateEnum.LIVE,
        data={"current_lap": 12, "leader": "VER"}
    )
    await mgr.broadcast_update("session_alpha", update_a)

    # Queue A should receive the update
    received_a = await queue_session_a.get()
    assert received_a.session_id == "session_alpha"
    assert received_a.data["leader"] == "VER"

    # Queue B must NOT receive any message
    assert queue_session_b.empty()

    # Now broadcast to session_beta
    update_b = LiveIncrementalUpdate(
        type="RACE_CONTROL",
        session_id="session_beta",
        sequence_number=1,
        timestamp=datetime.now(timezone.utc),
        data_state=DataStateEnum.LIVE,
        data={"flag": "YELLOW"}
    )
    await mgr.broadcast_update("session_beta", update_b)

    # Queue B receives update, Queue A remains unaffected
    received_b = await queue_session_b.get()
    assert received_b.session_id == "session_beta"
    assert received_b.data["flag"] == "YELLOW"
    assert queue_session_a.empty()

    mgr.unsubscribe("session_alpha", queue_session_a)
    mgr.unsubscribe("session_beta", queue_session_b)

@pytest.mark.asyncio
async def test_cross_session_stream_event_isolation():
    """
    Verifies that on_stream_event filters events by provider session key
    and dispatches only to subscribers of the matching mapped internal session.
    """
    mgr = LiveSessionManager()
    mgr.map_session_to_provider("sess_alpha", "8881")
    mgr.map_session_to_provider("sess_beta", "8882")

    queue_alpha = mgr.subscribe("sess_alpha")
    queue_beta = mgr.subscribe("sess_beta")

    # Ingest event for Alpha (key 8881)
    await mgr.on_stream_event("8881", "v1/timing", {"session_key": 8881, "lap": 25})

    msg_alpha = await queue_alpha.get()
    assert msg_alpha.session_id == "sess_alpha"
    assert queue_beta.empty()

    # Ingest event for Beta (key 8882)
    await mgr.on_stream_event("8882", "v1/timing", {"session_key": 8882, "lap": 5})

    msg_beta = await queue_beta.get()
    assert msg_beta.session_id == "sess_beta"
    assert queue_alpha.empty()

    mgr.unsubscribe("sess_alpha", queue_alpha)
    mgr.unsubscribe("sess_beta", queue_beta)





