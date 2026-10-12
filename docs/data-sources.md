# APEX GP — Data Sources, Contracts & Provenance Guide

## 1. Upstream Data Sources
1. **OpenF1 (Live & Real-Time Timing)**:
   - Base URL: `https://api.openf1.org/v1`
   - Scope: Session meetings, laps, intervals, stints, pit stops, car data, position, race control messages, weather.
   - Status: Permitted community use. Rate limits respected with backend caching.
2. **FastF1 & Ergast/Jolpica (Historical Racing Data)**:
   - Scope: Complete historical archives from 1950 to present.
   - Usage: Off-line ingestion and batch synchronization into durable PostgreSQL database.
3. **Internal Normalized Schemas**:
   - `Meeting`: Race weekends with sprint/standard format indicators.
   - `Session`: FP1, FP2, FP3, Sprint Shootout, Sprint, Qualifying, Race.
   - `Lap`: Lap number, sector 1, sector 2, sector 3, lap time, compound, is_pit_in, is_pit_out.
   - `Standing`: Driver and constructor championship points with countback positions.

## 2. Provenance Guarantees
- Every response from `/api/v1/...` contains a `_provenance` object:
  ```json
  {
    "source": "OPENF1" | "ERGASST_JOLPICA" | "LOCAL_FIXTURE",
    "retrieved_at": "2026-10-12T13:20:00Z",
    "data_state": "LIVE" | "DELAYED" | "STALE" | "HISTORICAL" | "UNAVAILABLE",
    "verified": true
  }
  ```
