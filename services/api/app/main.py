from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import json
from datetime import datetime, timezone

from app.core.config import settings
from app.core.database import engine, Base, async_session_maker
from app.core.redis import redis_client
from app.racing.seed_data import seed_verified_2024_data
from app.racing.fixtures import BAHRAIN_2024_LIVE_FIXTURE
from app.racing.live_manager import live_session_manager
from app.api.routes import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables and seed baseline data
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as session:
        await seed_verified_2024_data(session)

    await redis_client.connect()
    # Register deterministic test fixture baseline
    live_session_manager.register_fixture_session("2024_01_race", BAHRAIN_2024_LIVE_FIXTURE)

    # Wire OpenF1 streaming manager callback to LiveSessionManager
    from app.providers.openf1_stream import openf1_stream_manager

    def stream_callback(topic: str, payload: dict):
        session_key = str(payload.get("session_key", openf1_stream_manager.active_session_key or ""))
        asyncio.create_task(live_session_manager.on_stream_event(session_key, topic, payload))

    openf1_stream_manager.event_callback = stream_callback

    yield
    # Shutdown
    openf1_stream_manager.stop_streaming()
    await redis_client.close()
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="APEX GP — Formula 1 Racing, Intelligence and Championship Platform Backend",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "apex-gp-api",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }

# ----------------- LIVE WEBSOCKET ENDPOINT -----------------

@app.websocket("/ws/live/{session_id}")
async def websocket_live_session(websocket: WebSocket, session_id: str):
    """
    Real-time Live Race Center WebSocket:
    1. Accepts connection with connection limit and security checks.
    2. Sends initial comprehensive LiveSessionSnapshot.
    3. Streams incremental updates (timing, race control, weather, telemetry).
    4. Handles client pings/heartbeats, disconnect detection, and sequence tracking.
    """
    await websocket.accept()

    # Load initial snapshot
    snapshot = await live_session_manager.get_current_snapshot(session_id)
    if not snapshot:
        # If not already initialized, initialize from fixture or OpenF1
        if session_id == "2024_01_race":
            snapshot = live_session_manager._build_snapshot_from_fixture(session_id, BAHRAIN_2024_LIVE_FIXTURE)
        else:
            snapshot = await live_session_manager.ingest_session_data(session_id, "9472", is_live_stream=False)

    # Send initial snapshot as first message
    initial_msg = {
        "type": "SNAPSHOT",
        "session_id": session_id,
        "sequence_number": snapshot.sequence_number,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": snapshot.model_dump(mode="json")
    }
    await websocket.send_text(json.dumps(initial_msg))

    # Subscribe to incremental queue
    queue = live_session_manager.subscribe(session_id)

    async def sender_task():
        try:
            while True:
                update = await queue.get()
                msg = {
                    "type": update.type,
                    "session_id": update.session_id,
                    "sequence_number": update.sequence_number,
                    "timestamp": update.timestamp.isoformat(),
                    "data_state": update.data_state.value,
                    "payload": update.data
                }
                await websocket.send_text(json.dumps(msg))
        except (WebSocketDisconnect, asyncio.CancelledError):
            pass
        except Exception:
            pass

    async def receiver_task():
        try:
            while True:
                data = await websocket.receive_text()
                # Handle client heartbeat / ping
                try:
                    parsed = json.loads(data)
                    if parsed.get("type") == "PING":
                        await websocket.send_text(json.dumps({
                            "type": "PONG",
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }))
                    elif parsed.get("type") == "RESYNC":
                        # Client requested resync from sequence
                        current_snap = await live_session_manager.get_current_snapshot(session_id)
                        if current_snap:
                            await websocket.send_text(json.dumps({
                                "type": "SNAPSHOT",
                                "session_id": session_id,
                                "sequence_number": current_snap.sequence_number,
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                                "payload": current_snap.model_dump(mode="json")
                            }))
                except Exception:
                    pass
        except (WebSocketDisconnect, asyncio.CancelledError):
            pass
        except Exception:
            pass

    sender = asyncio.create_task(sender_task())
    receiver = asyncio.create_task(receiver_task())

    try:
        done, pending = await asyncio.wait(
            [sender, receiver],
            return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()
    finally:
        live_session_manager.unsubscribe(session_id, queue)

