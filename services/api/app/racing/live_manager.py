import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from collections import defaultdict

from app.core.redis import redis_client
from app.racing.models import DataStateEnum, SessionStatusEnum
from app.racing.schemas import (
    LiveSessionSnapshot, LiveIncrementalUpdate, DriverTimingEntry,
    SectorTimes, PitStopEvent, StintInfo, RaceControlMessage,
    TrackWeather, DriverMapPosition, TelemetryEntry, ProvenanceMeta
)
from app.providers.openf1 import OpenF1Provider

logger = logging.getLogger("apex_gp.live_ingestion")

# Color map fallback by constructor / team name
TEAM_COLORS: Dict[str, str] = {
    "Red Bull Racing": "#3671C6",
    "Ferrari": "#E80020",
    "Mercedes": "#27F4D2",
    "Mercedes-AMG": "#27F4D2",
    "McLaren": "#FF8000",
    "Aston Martin": "#229971",
    "Alpine": "#0093CC",
    "Williams": "#64C4FF",
    "RB": "#6692FF",
    "Kick Sauber": "#52E252",
    "Sauber": "#52E252",
    "Haas F1 Team": "#B6BABD",
    "Haas": "#B6BABD"
}

def get_team_color(team_name: Optional[str]) -> str:
    if not team_name:
        return "#FFFFFF"
    for k, v in TEAM_COLORS.items():
        if k.lower() in team_name.lower():
            return v
    return "#E10600"

class LiveSessionManager:
    """
    Manages live session state in Redis and memory.
    Supports snapshot generation, sequence-tracked incremental updates,
    heartbeats, reconnect resynchronization, and deterministic test fixture playback.
    """
    def __init__(self, provider: Optional[OpenF1Provider] = None):
        self.provider = provider or OpenF1Provider()
        self._sequence_numbers: Dict[str, int] = defaultdict(int)
        self._snapshots: Dict[str, LiveSessionSnapshot] = {}
        self._fixture_sessions: Dict[str, Dict[str, Any]] = {}
        self._subscriber_queues: Dict[str, List[asyncio.Queue]] = defaultdict(list)
        self._lock = asyncio.Lock()

    def register_fixture_session(self, session_id: str, fixture_data: Dict[str, Any]):
        """Registers a deterministic test fixture session with explicit test labelling."""
        self._fixture_sessions[session_id] = fixture_data

    def get_next_sequence(self, session_id: str) -> int:
        self._sequence_numbers[session_id] += 1
        return self._sequence_numbers[session_id]

    async def get_current_snapshot(self, session_id: str) -> Optional[LiveSessionSnapshot]:
        # Try local cache first
        if session_id in self._snapshots:
            return self._snapshots[session_id]

        # Check Redis
        if redis_client._redis:
            raw = await redis_client.get(f"apex:live:snapshot:{session_id}")
            if raw:
                try:
                    return LiveSessionSnapshot.model_validate(raw)
                except Exception:
                    pass

        # If fixture registered
        if session_id in self._fixture_sessions:
            snapshot = self._build_snapshot_from_fixture(session_id, self._fixture_sessions[session_id])
            self._snapshots[session_id] = snapshot
            return snapshot

        return None

    def _build_snapshot_from_fixture(self, session_id: str, fixture: Dict[str, Any]) -> LiveSessionSnapshot:
        seq = self.get_next_sequence(session_id)
        prov = ProvenanceMeta(
            source=fixture.get("provenance_source", "DETERMINISTIC_TEST_FIXTURE"),
            retrieved_at=datetime.now(timezone.utc),
            data_state=fixture.get("data_state", DataStateEnum.HISTORICAL),
            verified=True,
            is_test_fixture=True,
            notes=fixture.get("notes", "Verified deterministic test fixture for Live Race Center.")
        )

        weather = None
        if "weather" in fixture:
            w_dict = fixture["weather"]
            weather = TrackWeather(
                air_temperature=w_dict.get("air_temperature", 25.0),
                track_temperature=w_dict.get("track_temperature", 32.0),
                humidity=w_dict.get("humidity", 45.0),
                pressure=w_dict.get("pressure", 1015.0),
                wind_speed=w_dict.get("wind_speed", 2.1),
                wind_direction=w_dict.get("wind_direction", 180),
                rainfall=w_dict.get("rainfall", 0),
                timestamp=datetime.now(timezone.utc)
            )

        timing_tower: List[DriverTimingEntry] = []
        for idx, row in enumerate(fixture.get("timing_tower", [])):
            timing_tower.append(DriverTimingEntry(
                driver_number=row.get("driver_number", idx + 1),
                driver_code=row.get("driver_code", f"D{idx+1}"),
                driver_name=row.get("driver_name", f"Driver {idx+1}"),
                team_name=row.get("team_name", "Team"),
                team_color=row.get("team_color", "#FFFFFF"),
                position=row.get("position", idx + 1),
                grid=row.get("grid", idx + 1),
                gap_to_leader=row.get("gap_to_leader", 0.0 if idx == 0 else round(idx * 2.345, 3)),
                interval=row.get("interval", 0.0 if idx == 0 else 2.345),
                last_lap_time=row.get("last_lap_time", 92.5),
                best_lap_time=row.get("best_lap_time", 91.8),
                sectors=SectorTimes(**row.get("sectors", {"sector_1": 29.1, "sector_2": 38.2, "sector_3": 24.5})),
                current_lap=row.get("current_lap", fixture.get("current_lap", 1)),
                in_pit=row.get("in_pit", False),
                pit_stops_count=row.get("pit_stops_count", 0),
                tire_compound=row.get("tire_compound", "MEDIUM"),
                stint_lap_count=row.get("stint_lap_count", 5),
                status=row.get("status", "ON_TRACK"),
                positions_gained=row.get("positions_gained", 0)
            ))

        pit_stops = [
            PitStopEvent(
                driver_number=p["driver_number"],
                lap_number=p["lap_number"],
                pit_duration=p.get("pit_duration", 24.5),
                lane_duration=p.get("lane_duration", 22.0),
                timestamp=datetime.now(timezone.utc)
            )
            for p in fixture.get("pit_stops", [])
        ]

        stints = [
            StintInfo(
                driver_number=s["driver_number"],
                stint_number=s["stint_number"],
                compound=s["compound"],
                lap_start=s["lap_start"],
                lap_end=s.get("lap_end"),
                tyre_age_at_start=s.get("tyre_age_at_start", 0)
            )
            for s in fixture.get("stints", [])
        ]

        race_control = [
            RaceControlMessage(
                date=datetime.now(timezone.utc),
                lap_number=rc.get("lap_number"),
                category=rc.get("category", "Flag"),
                message=rc.get("message", "TRACK CLEAR"),
                flag=rc.get("flag", "GREEN"),
                scope=rc.get("scope"),
                sector=rc.get("sector")
            )
            for rc in fixture.get("race_control", [])
        ]

        map_pos = [
            DriverMapPosition(
                driver_number=m["driver_number"],
                driver_code=m.get("driver_code", f"D{m['driver_number']}"),
                team_color=m.get("team_color", "#FFFFFF"),
                x=m["x"],
                y=m["y"],
                date=datetime.now(timezone.utc)
            )
            for m in fixture.get("map_positions", [])
        ]

        telemetry = [
            TelemetryEntry(
                driver_number=t["driver_number"],
                speed=t.get("speed", 280),
                throttle=t.get("throttle", 100),
                brake=t.get("brake", 0),
                n_gear=t.get("n_gear", 7),
                drs=t.get("drs", 1),
                rpm=t.get("rpm", 11500),
                timestamp=datetime.now(timezone.utc)
            )
            for t in fixture.get("telemetry", [])
        ]

        return LiveSessionSnapshot(
            session_id=session_id,
            session_name=fixture.get("session_name", "Bahrain Grand Prix Race"),
            circuit_name=fixture.get("circuit_name", "Bahrain International Circuit"),
            total_laps=fixture.get("total_laps", 57),
            current_lap=fixture.get("current_lap", 1),
            status=SessionStatusEnum(fixture.get("status", SessionStatusEnum.LIVE)),
            data_state=DataStateEnum(fixture.get("data_state", DataStateEnum.HISTORICAL)),
            track_status=fixture.get("track_status", "GREEN"),
            weather=weather,
            timing_tower=timing_tower,
            pit_stops=pit_stops,
            stints=stints,
            race_control=race_control,
            driver_map_positions=map_pos,
            telemetry=telemetry,
            sequence_number=seq,
            provenance=prov
        )

    async def ingest_session_data(
        self,
        session_id: str,
        openf1_session_key: str,
        is_live_stream: bool = False
    ) -> LiveSessionSnapshot:
        """
        Polls or fetches fresh session data from OpenF1 provider,
        normalizes entities, calculates intervals, gaps, and builds state snapshot.
        Caches in Redis and broadcasts incremental updates to subscribers.
        """
        drivers_raw = await self.provider.get_drivers(openf1_session_key)
        positions_raw = await self.provider.get_positions(openf1_session_key)
        intervals_res = await self.provider.get_live_timing_snapshot(openf1_session_key)
        laps_raw = await self.provider.get_laps(openf1_session_key)
        pit_raw = await self.provider.get_pit_stops(openf1_session_key)
        stints_raw = await self.provider.get_stints(openf1_session_key)
        weather_raw = await self.provider.get_weather(openf1_session_key)
        rc_raw = await self.provider.get_race_control_messages(openf1_session_key)

        data_state = DataStateEnum.LIVE if is_live_stream else DataStateEnum.HISTORICAL
        if not drivers_raw and not positions_raw:
            data_state = DataStateEnum.UNAVAILABLE

        # Build driver lookup table
        drivers_by_num: Dict[int, Dict[str, Any]] = {}
        for d in drivers_raw:
            num = d.get("driver_number")
            if num is not None:
                drivers_by_num[num] = d

        # Build interval lookup
        intervals_by_num: Dict[int, Dict[str, Any]] = {}
        for row in intervals_res.get("intervals", []):
            num = row.get("driver_number")
            if num is not None:
                intervals_by_num[num] = row

        # Build laps lookup (latest lap & fastest lap per driver)
        latest_lap_by_driver: Dict[int, Dict[str, Any]] = {}
        best_lap_by_driver: Dict[int, float] = {}
        for row in laps_raw:
            num = row.get("driver_number")
            if num is None:
                continue
            lap_num = row.get("lap_number", 0)
            lap_dur = row.get("lap_duration")
            if num not in latest_lap_by_driver or lap_num > latest_lap_by_driver[num].get("lap_number", 0):
                latest_lap_by_driver[num] = row
            if lap_dur and (num not in best_lap_by_driver or lap_dur < best_lap_by_driver[num]):
                best_lap_by_driver[num] = lap_dur

        # Build stints lookup (latest stint per driver)
        latest_stint_by_driver: Dict[int, Dict[str, Any]] = {}
        stint_objects: List[StintInfo] = []
        for s in stints_raw:
            num = s.get("driver_number")
            if num is not None:
                latest_stint_by_driver[num] = s
                stint_objects.append(StintInfo(
                    driver_number=num,
                    stint_number=s.get("stint_number", 1),
                    compound=s.get("compound", "UNKNOWN"),
                    lap_start=s.get("lap_start", 1),
                    lap_end=s.get("lap_end"),
                    tyre_age_at_start=s.get("tyre_age_at_start", 0)
                ))

        # Build pit stops count
        pit_counts: Dict[int, int] = defaultdict(int)
        pit_objects: List[PitStopEvent] = []
        for p in pit_raw:
            num = p.get("driver_number")
            if num is not None:
                pit_counts[num] += 1
                pit_objects.append(PitStopEvent(
                    driver_number=num,
                    lap_number=p.get("lap_number", 0),
                    pit_duration=p.get("pit_duration"),
                    lane_duration=p.get("lane_duration"),
                    timestamp=datetime.now(timezone.utc)
                ))

        # Position ranking
        sorted_positions = sorted(positions_raw, key=lambda x: x.get("position", 999))
        timing_tower: List[DriverTimingEntry] = []
        max_lap = 0

        for pos_data in sorted_positions:
            num = pos_data.get("driver_number")
            if num is None:
                continue
            driver_info = drivers_by_num.get(num, {})
            int_info = intervals_by_num.get(num, {})
            last_lap_data = latest_lap_by_driver.get(num, {})
            stint_info = latest_stint_by_driver.get(num, {})

            pos = pos_data.get("position", 99)
            grid = driver_info.get("grid_position", pos)
            cur_lap = last_lap_data.get("lap_number", 0)
            if cur_lap > max_lap:
                max_lap = cur_lap

            team_name = driver_info.get("team_name", "Unknown Team")
            team_color = f"#{driver_info.get('team_colour', 'FFFFFF')}" if driver_info.get("team_colour") else get_team_color(team_name)

            sectors = SectorTimes(
                sector_1=last_lap_data.get("duration_sector_1"),
                sector_2=last_lap_data.get("duration_sector_2"),
                sector_3=last_lap_data.get("duration_sector_3")
            )

            stint_start = stint_info.get("lap_start", 1)
            stint_laps = max(0, cur_lap - stint_start + 1) if cur_lap >= stint_start else 0

            timing_tower.append(DriverTimingEntry(
                driver_number=num,
                driver_code=driver_info.get("name_acronym", f"D{num}"),
                driver_name=driver_info.get("full_name", f"Driver {num}"),
                team_name=team_name,
                team_color=team_color,
                position=pos,
                grid=grid,
                gap_to_leader=int_info.get("gap_to_leader"),
                interval=int_info.get("interval"),
                last_lap_time=last_lap_data.get("lap_duration"),
                best_lap_time=best_lap_by_driver.get(num),
                sectors=sectors,
                current_lap=cur_lap,
                in_pit=last_lap_data.get("is_pit_out_lap", False),
                pit_stops_count=pit_counts[num],
                tire_compound=stint_info.get("compound", "UNKNOWN"),
                stint_lap_count=stint_laps,
                status="ON_TRACK",
                positions_gained=grid - pos
            ))

        # Weather
        weather_obj = None
        if weather_raw:
            weather_obj = TrackWeather(
                air_temperature=weather_raw.get("air_temperature", 0.0),
                track_temperature=weather_raw.get("track_temperature", 0.0),
                humidity=weather_raw.get("humidity", 0.0),
                pressure=weather_raw.get("pressure", 1013.0),
                wind_speed=weather_raw.get("wind_speed", 0.0),
                wind_direction=weather_raw.get("wind_direction", 0),
                rainfall=weather_raw.get("rainfall", 0),
                timestamp=datetime.now(timezone.utc)
            )

        # Race Control
        rc_objects: List[RaceControlMessage] = []
        track_status = "GREEN"
        for rc in rc_raw:
            flag = rc.get("flag")
            if flag in ["YELLOW", "DOUBLE YELLOW"]:
                track_status = "YELLOW"
            elif flag == "RED":
                track_status = "RED"
            cat = rc.get("category", "")
            if "Safety Car" in cat or "SAFETY CAR" in rc.get("message", ""):
                track_status = "SAFETY_CAR"
            elif "VSC" in cat or "VIRTUAL SAFETY CAR" in rc.get("message", ""):
                track_status = "VSC"

            rc_objects.append(RaceControlMessage(
                date=datetime.now(timezone.utc),
                lap_number=rc.get("lap_number"),
                category=rc.get("category", "General"),
                message=rc.get("message", ""),
                flag=flag,
                scope=rc.get("scope"),
                sector=rc.get("sector")
            ))

        seq = self.get_next_sequence(session_id)
        prov = ProvenanceMeta(
            source="OPENF1_REST_API",
            retrieved_at=datetime.now(timezone.utc),
            data_state=data_state,
            verified=True,
            is_test_fixture=False,
            notes=f"Live session {session_id} synced from OpenF1 key {openf1_session_key}."
        )

        snapshot = LiveSessionSnapshot(
            session_id=session_id,
            session_name=f"Session {session_id}",
            circuit_name="Grand Prix Circuit",
            total_laps=57,
            current_lap=max_lap,
            status=SessionStatusEnum.LIVE if is_live_stream else SessionStatusEnum.COMPLETED,
            data_state=data_state,
            track_status=track_status,
            weather=weather_obj,
            timing_tower=timing_tower,
            pit_stops=pit_objects[-20:], # Latest 20 pit stops
            stints=stint_objects,
            race_control=rc_objects[-30:], # Latest 30 race control messages
            driver_map_positions=[],
            telemetry=[],
            sequence_number=seq,
            provenance=prov
        )

        self._snapshots[session_id] = snapshot

        # Cache in Redis with 1 hour TTL
        if redis_client._redis:
            try:
                await redis_client.set(
                    f"apex:live:snapshot:{session_id}",
                    snapshot.model_dump(mode="json"),
                    ttl_seconds=3600
                )
            except Exception as e:
                logger.warning(f"Failed to cache snapshot in Redis: {e}")

        # Broadcast incremental update to connected WebSocket clients
        await self.broadcast_update(session_id, LiveIncrementalUpdate(
            type="TIMING",
            session_id=session_id,
            sequence_number=seq,
            timestamp=datetime.now(timezone.utc),
            data_state=data_state,
            data={
                "current_lap": max_lap,
                "track_status": track_status,
                "timing_tower": [t.model_dump(mode="json") for t in timing_tower],
                "weather": weather_obj.model_dump(mode="json") if weather_obj else None,
            }
        ))

        return snapshot

    async def broadcast_update(self, session_id: str, update: LiveIncrementalUpdate):
        """Broadcasts an incremental message to all active subscriber queues for a session."""
        queues = self._subscriber_queues.get(session_id, [])
        dead_queues = []
        for q in queues:
            try:
                # Discard oldest message if queue is full (backpressure defense)
                if q.full():
                    try:
                        q.get_nowait()
                    except asyncio.QueueEmpty:
                        pass
                q.put_nowait(update)
            except Exception:
                dead_queues.append(q)

        for dead in dead_queues:
            if dead in self._subscriber_queues[session_id]:
                self._subscriber_queues[session_id].remove(dead)

    def subscribe(self, session_id: str) -> asyncio.Queue:
        """Subscribes a client to incremental updates with backpressure protection."""
        q: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._subscriber_queues[session_id].append(q)
        return q

    def unsubscribe(self, session_id: str, q: asyncio.Queue):
        """Unsubscribes a client queue."""
        if q in self._subscriber_queues[session_id]:
            self._subscriber_queues[session_id].remove(q)

# Global LiveSessionManager singleton
live_session_manager = LiveSessionManager()
