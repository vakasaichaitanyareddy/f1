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

## 3. Live Race Center Ingestion & Delivery (Release 2)
1. **Live Provider Architecture**:
   - Upstream API: `https://api.openf1.org/v1` (Community timing provider)
   - Endpoints supported: `/sessions`, `/drivers`, `/position`, `/intervals`, `/laps`, `/pit`, `/stints`, `/weather`, `/race_control`, `/location`, `/car_data`.
   - Credentials & API calls: Retained strictly on backend; never exposed to web or mobile clients.
2. **WebSocket Real-Time Delivery (`/ws/live/{session_id}`)**:
   - Initial Message: Complete `SNAPSHOT` (`LiveSessionSnapshot`) containing timing tower, pit stops, stints, race control, track map coordinates, weather, and provenance.
   - Streaming Updates: Incremental deltas (`TIMING`, `RACE_CONTROL`, `WEATHER`, `MAP_POSITIONS`, `TELEMETRY`) with monotonic sequence numbers.
   - Heartbeat & Resync: Ping/Pong frame every 15 seconds; `RESYNC` request triggers full fresh snapshot.
   - Backpressure Protection: Max subscriber queue size of 100 with oldest-message eviction on slow clients.
3. **Circuit Geometry & Track Coordinates**:
   - Verified FIA track path coordinates for Bahrain International Circuit (`5.412 km`).
   - High-frequency car coordinates from `/location` normalized to track SVG viewport.

## 4. Known Limitations & Stabilization Notes (Release 2)
- **Local Development Database**: Uses `postgresql+asyncpg` in Docker Compose (loopback binding `127.0.0.1:8000`) and `sqlite+aiosqlite` for offline local unit test runs.
- **Upstream OpenF1 Quotas**: OpenF1 free tier applies rate limiting (HTTP 429). The backend caches full snapshots in Redis (1h TTL) to shield upstream endpoints and protect client streaming stability.
- **Sprint Schedule Scope**: Development seed includes Round 1 (Bahrain GP 2024 archive). Real-time live streaming activates automatically when an active Grand Prix session key is supplied.

