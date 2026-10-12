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

## 3. Known Limitations & Stabilization Notes (Release 1.1)
- **Local Development Database**: Defaults to `sqlite+aiosqlite` for lightweight, zero-dependency local runs and unit testing. Production and Docker Compose use `postgresql+asyncpg` with Alembic migration versioning (`b1af478a9ca2`).
- **Redis Cache Fallback**: When Redis is unavailable locally, `RedisClient` degrades gracefully without throwing unhandled exceptions.
- **Sprint Schedule Scope**: Current development seed includes round 1 (Bahrain GP 2024). Full 24-round calendar session ingestion from FastF1/Jolpica is scheduled for subsequent data pipelines.
