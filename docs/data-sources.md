# APEX GP — Data Sources, Contracts & Provenance Guide

## 1. Upstream Data Sources
1. **OpenF1 (Live & Real-Time Timing)**:
   - Base URL: `https://api.openf1.org/v1`
   - Scope: Session meetings, laps, intervals, stints, pit stops, car data, position, race control messages, weather.
   - Status: Permitted community use. Rate limits (HTTP 429) respected with backend caching and graceful fallback.
   - Staleness Threshold: > 30 seconds since last heartbeat transitions state to `STALE`.
2. **FastF1 & Ergast/Jolpica (Historical Racing Data)**:
   - Scope: Complete historical archives from 1950 to present.
   - Usage: Offline ingestion and batch synchronization into durable PostgreSQL database.
3. **Internal Normalized Schemas**:
   - `Meeting`: Race weekends with sprint/standard format indicators.
   - `Session`: FP1, FP2, FP3, Sprint Shootout, Sprint, Qualifying, Race.
   - `SessionResult`: Official classification results, points, grid, laps, fastest lap, status.
   - `Driver` & `Constructor`: Normalized profiles with permanent numbers, nationality, constructor colors.
   - `Standing`: Driver and constructor championship points with countback positions.

## 2. Provenance Guarantees & Test Fixture Transparency
Every response from `/api/v1/...` that supplies session results or championship calculations contains a `provenance` metadata object:
```json
{
  "source": "OPENF1_REST_API" | "FIA_OFFICIAL_CLASSIFICATION_ARCHIVE" | "APEX_GP_CHAMPIONSHIP_MATH_ENGINE",
  "retrieved_at": "2026-10-12T13:20:00Z",
  "data_state": "LIVE" | "DELAYED" | "STALE" | "HISTORICAL" | "UNAVAILABLE",
  "verified": true,
  "is_test_fixture": false,
  "notes": "Optional provenance notes or fixture context"
}
```

### Strict Non-Fabrication Rules:
1. **Seed Data Transparency**: All development fixture seed records are strictly marked with `"is_test_fixture": true` and `"notes": "Development seed baseline (...). Not live timing."`
2. **Live Data Transparency**: Historical sessions are never labeled `LIVE`. If an active session timing feed stops transmitting for > 30 seconds, it is immediately labeled `STALE`.
3. **Provider Outages**: When upstream providers return HTTP 429 (rate limited), HTTP 5xx, or network timeouts, the system returns an empty payload with `data_state: "UNAVAILABLE"` and descriptive failure notes rather than synthesized placeholder data.

## 3. Live Race Center Ingestion & Delivery (Release 2 & Release 2.1)
1. **Upstream Streaming & Authentication Architecture (Release 2.1)**:
   - Upstream MQTT Broker: `mqtt.openf1.org:8883` (TLS) or WebSocket `wss://mqtt.openf1.org:8084/mqtt`.
   - Server-Side OAuth2 Token Refresh: `POST https://api.openf1.org/token` (`username`, `password`, `expires_in=3600`).
   - Token & Credential Security: Credentials are kept strictly on the server backend (`.env`). No OpenF1 credentials or tokens are ever sent to web or mobile clients.
   - Topics Subscribed: `v1/position`, `v1/intervals`, `v1/laps`, `v1/pit`, `v1/weather`, `v1/race_control`.
   - Deduplication: In-memory sliding cache based on topic, driver number, ISO timestamp, and lap number prevents duplicate event dispatch.
   - Stream Diagnostics (`GET /api/v1/live/diagnostics`): Reports operational status (`CONNECTED`, `CONNECTING`, `DISCONNECTED`, `CREDENTIALS_MISSING`), broker address, subscribed topics, deduplication stats, connected client count, and ingestion lag.
2. **Dynamic Session Selection & Data States**:
   - Sessions Endpoint (`GET /api/v1/live/sessions`): Dynamically resolves internal IDs to upstream session keys (e.g. `2024_01_race` $\to$ `9472`), indicating active data state (`LIVE` vs `HISTORICAL`).
   - Web & Mobile Dynamic Selectors: Allows users to seamlessly switch between active live sessions and historical/demo sessions without hardcoded routes.
   - Non-Fabrication Rule: Historical or offline sessions are never labeled `LIVE`. If credentials or live sessions are absent, status is honestly displayed as `HISTORICAL` or `CREDENTIALS_MISSING`.
3. **WebSocket Real-Time Delivery (`/ws/live/{session_id}`)**:
   - Initial Message: Complete `SNAPSHOT` (`LiveSessionSnapshot`) containing timing tower, pit stops, stints, race control, track map coordinates, weather, and provenance.
   - Streaming Updates: Incremental deltas (`TIMING`, `RACE_CONTROL`, `WEATHER`, `MAP_POSITIONS`, `TELEMETRY`) with monotonic sequence numbers.
   - Heartbeat & Resync: Ping/Pong frame every 15 seconds; `RESYNC` request triggers full fresh snapshot.
   - Backpressure Protection: Max subscriber queue size of 100 with oldest-message eviction on slow clients.
4. **Circuit Geometry & Track Coordinates**:
   - Verified FIA track path coordinates for Bahrain International Circuit (`5.412 km`).
   - High-frequency car coordinates from `/location` normalized to track SVG viewport.

## 4. Known Limitations & Stabilization Notes (Release 2.1)
- **Local Development Database**: Uses `postgresql+asyncpg` in Docker Compose (loopback binding `127.0.0.1:8000`) and `sqlite+aiosqlite` for offline local unit test runs.
- **Upstream OpenF1 Credentials**: Genuine real-time MQTT streaming requires paid/sponsored OAuth2 credentials from OpenF1. When credentials are not configured in `.env`, the stream manager operates in unauthenticated REST fallback mode and explicitly reports `CREDENTIALS_MISSING` in the diagnostics endpoint without falsifying live stream status.
- **Upstream OpenF1 Quotas**: OpenF1 free tier applies rate limiting (HTTP 429). The backend caches full snapshots in Redis (1h TTL) to shield upstream endpoints and protect client streaming stability.


