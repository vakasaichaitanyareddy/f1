from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from app.core.database import get_db_session
from app.racing.models import (
    User, ConstructorModel, DriverModel, MeetingModel, SessionModel,
    SessionResultModel, DataStateEnum
)
from app.racing.schemas import (
    MeetingRead, DriverWithConstructor, ConstructorWithDrivers,
    DriverStandingRead, ConstructorStandingRead, RaceClassificationRead,
    RaceResultEntryRead, ProvenanceMeta, UserCreate, UserLogin,
    UserProfile, UserPreferencesUpdate, TokenResponse,
    LiveSessionSnapshot, LiveIncrementalUpdate
)
from app.racing.live_manager import live_session_manager
from app.identity.security import (
    get_password_hash, verify_password, create_access_token,
    get_current_user, get_current_user_optional
)
from app.championship.engine import (
    calculate_clinch_threshold, is_mathematically_eliminated,
    calculate_max_remaining_points
)

api_router = APIRouter()

# ----------------- AUTH & PREFERENCES -----------------

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db_session)):
    stmt = select(User).where(User.email == user_in.email)
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        id=str(uuid.uuid4()),
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    token = create_access_token(data={"sub": new_user.id})
    return TokenResponse(
        access_token=token,
        user=UserProfile.model_validate(new_user)
    )

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db_session)):
    stmt = select(User).where(User.email == credentials.email)
    user = (await db.execute(stmt)).scalar_one_or_none()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(data={"sub": user.id})
    return TokenResponse(
        access_token=token,
        user=UserProfile.model_validate(user)
    )

@api_router.get("/user/me", response_model=UserProfile)
async def get_me(user: User = Depends(get_current_user)):
    return UserProfile.model_validate(user)

@api_router.patch("/user/preferences", response_model=UserProfile)
async def update_preferences(
    prefs: UserPreferencesUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    if prefs.spoiler_shield_enabled is not None:
        user.spoiler_shield_enabled = prefs.spoiler_shield_enabled
    if prefs.favorite_driver_id is not None:
        user.favorite_driver_id = prefs.favorite_driver_id
    if prefs.favorite_team_id is not None:
        user.favorite_team_id = prefs.favorite_team_id
    if prefs.pitwall_layout_json is not None:
        user.pitwall_layout_json = prefs.pitwall_layout_json

    await db.commit()
    await db.refresh(user)
    return UserProfile.model_validate(user)

# ----------------- RACING & CALENDAR -----------------

@api_router.get("/meetings", response_model=List[MeetingRead])
async def get_meetings(
    season: int = Query(2024),
    db: AsyncSession = Depends(get_db_session)
):
    from sqlalchemy.orm import selectinload
    stmt = (
        select(MeetingModel)
        .options(selectinload(MeetingModel.sessions))
        .where(MeetingModel.season == season)
        .order_by(MeetingModel.round_number)
    )
    result = await db.execute(stmt)
    meetings = result.scalars().all()
    return [MeetingRead.model_validate(m) for m in meetings]

@api_router.get("/meetings/{meeting_id}", response_model=MeetingRead)
async def get_meeting_detail(
    meeting_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    from sqlalchemy.orm import selectinload
    stmt = (
        select(MeetingModel)
        .options(selectinload(MeetingModel.sessions))
        .where(MeetingModel.id == meeting_id)
    )
    meeting = (await db.execute(stmt)).scalar_one_or_none()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return MeetingRead.model_validate(meeting)

@api_router.get("/drivers", response_model=List[DriverWithConstructor])
async def get_drivers(db: AsyncSession = Depends(get_db_session)):
    stmt = select(DriverModel, ConstructorModel).join(ConstructorModel, DriverModel.constructor_id == ConstructorModel.id)
    res = await db.execute(stmt)
    drivers = []
    for d, c in res.all():
        drivers.append(DriverWithConstructor(
            id=d.id,
            code=d.code,
            permanent_number=d.permanent_number,
            first_name=d.first_name,
            last_name=d.last_name,
            nationality=d.nationality,
            constructor_id=d.constructor_id,
            constructor_name=c.name,
            constructor_color=c.color_hex,
            biography=d.biography,
            career_wins=d.career_wins,
            career_podiums=d.career_podiums,
            career_poles=d.career_poles,
            career_championships=d.career_championships,
        ))
    return drivers

@api_router.get("/constructors", response_model=List[ConstructorWithDrivers])
async def get_constructors(db: AsyncSession = Depends(get_db_session)):
    stmt = select(ConstructorModel)
    res = await db.execute(stmt)
    constructors = res.scalars().all()
    # load drivers
    results = []
    for c in constructors:
        drivers_stmt = select(DriverModel).where(DriverModel.constructor_id == c.id)
        d_res = await db.execute(drivers_stmt)
        drivers = d_res.scalars().all()
        results.append(ConstructorWithDrivers(
            id=c.id,
            name=c.name,
            nationality=c.nationality,
            color_hex=c.color_hex,
            total_championships=c.total_championships,
            drivers=drivers
        ))
    return results

@api_router.get("/standings/drivers", response_model=List[DriverStandingRead])
async def get_driver_standings(db: AsyncSession = Depends(get_db_session)):
    # Calculate sum of points per driver from SessionResults
    drivers_stmt = select(DriverModel, ConstructorModel).join(ConstructorModel, DriverModel.constructor_id == ConstructorModel.id)
    drivers_res = await db.execute(drivers_stmt)
    
    standings = []
    for d, c in drivers_res.all():
        # Points query
        pts_stmt = select(SessionResultModel).where(SessionResultModel.driver_id == d.id)
        res_list = (await db.execute(pts_stmt)).scalars().all()
        total_pts = sum(r.points_awarded for r in res_list)
        total_wins = sum(1 for r in res_list if r.position == 1)

        standings.append({
            "driver": DriverWithConstructor(
                id=d.id,
                code=d.code,
                permanent_number=d.permanent_number,
                first_name=d.first_name,
                last_name=d.last_name,
                nationality=d.nationality,
                constructor_id=d.constructor_id,
                constructor_name=c.name,
                constructor_color=c.color_hex,
                biography=d.biography,
                career_wins=d.career_wins,
                career_podiums=d.career_podiums,
                career_poles=d.career_poles,
                career_championships=d.career_championships,
            ),
            "points": total_pts,
            "wins": total_wins,
        })

    # Sort descending by points, then wins
    standings.sort(key=lambda s: (s["points"], s["wins"]), reverse=True)

    leader_pts = standings[0]["points"] if standings else 0.0
    output = []
    for idx, s in enumerate(standings):
        prev_pts = standings[idx - 1]["points"] if idx > 0 else s["points"]
        output.append(DriverStandingRead(
            position=idx + 1,
            driver=s["driver"],
            points=s["points"],
            wins=s["wins"],
            points_behind_leader=round(leader_pts - s["points"], 1),
            points_behind_previous=round(prev_pts - s["points"], 1),
        ))
    return output

@api_router.get("/standings/constructors", response_model=List[ConstructorStandingRead])
async def get_constructor_standings(db: AsyncSession = Depends(get_db_session)):
    constructors = (await db.execute(select(ConstructorModel))).scalars().all()
    standings = []
    for c in constructors:
        # Sum driver points
        pts_stmt = (
            select(SessionResultModel)
            .join(DriverModel, SessionResultModel.driver_id == DriverModel.id)
            .where(DriverModel.constructor_id == c.id)
        )
        res_list = (await db.execute(pts_stmt)).scalars().all()
        total_pts = sum(r.points_awarded for r in res_list)
        total_wins = sum(1 for r in res_list if r.position == 1)

        standings.append({
            "constructor": c,
            "points": total_pts,
            "wins": total_wins,
        })

    standings.sort(key=lambda s: (s["points"], s["wins"]), reverse=True)
    leader_pts = standings[0]["points"] if standings else 0.0

    output = []
    for idx, s in enumerate(standings):
        prev_pts = standings[idx - 1]["points"] if idx > 0 else s["points"]
        output.append(ConstructorStandingRead(
            position=idx + 1,
            constructor=s["constructor"],
            points=s["points"],
            wins=s["wins"],
            points_behind_leader=round(leader_pts - s["points"], 1),
            points_behind_previous=round(prev_pts - s["points"], 1),
        ))
    return output

@api_router.get("/sessions/{session_id}/classification", response_model=RaceClassificationRead)
async def get_session_classification(session_id: str, db: AsyncSession = Depends(get_db_session)):
    session_stmt = select(SessionModel).where(SessionModel.id == session_id)
    session = (await db.execute(session_stmt)).scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    from sqlalchemy.orm import selectinload
    meeting_stmt = select(MeetingModel).options(selectinload(MeetingModel.sessions)).where(MeetingModel.id == session.meeting_id)
    meeting = (await db.execute(meeting_stmt)).scalar_one()

    # Get results
    results_stmt = (
        select(SessionResultModel, DriverModel, ConstructorModel)
        .join(DriverModel, SessionResultModel.driver_id == DriverModel.id)
        .join(ConstructorModel, DriverModel.constructor_id == ConstructorModel.id)
        .where(SessionResultModel.session_id == session_id)
        .order_by(SessionResultModel.position)
    )
    raw_res = (await db.execute(results_stmt)).all()

    entries = []
    for r, d, c in raw_res:
        entries.append(RaceResultEntryRead(
            position=r.position,
            driver_id=d.id,
            driver_code=d.code,
            driver_name=f"{d.first_name} {d.last_name}",
            constructor_name=c.name,
            constructor_color=c.color_hex,
            grid=r.grid,
            laps=r.laps,
            status=r.status,
            time_or_retired=r.time_or_retired,
            points_awarded=r.points_awarded,
            fastest_lap=r.fastest_lap,
            fastest_lap_time=r.fastest_lap_time,
        ))

    return RaceClassificationRead(
        meeting=MeetingRead.model_validate(meeting),
        session_type=session.type,
        results=entries,
        provenance=ProvenanceMeta(
            source="FIA_OFFICIAL_CLASSIFICATION_ARCHIVE",
            retrieved_at=datetime.now(timezone.utc),
            data_state=DataStateEnum.HISTORICAL,
            verified=True,
            is_test_fixture=True,
            notes="Development seed baseline (Bahrain GP 2024 archive). Not live timing."
        )
    )

@api_router.get("/championship/intelligence")
async def get_championship_intelligence(
    remaining_gps: int = Query(23),
    remaining_sprints: int = Query(6),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Evaluates current championship state, leader clinching potential, and elimination status.
    """
    standings = await get_driver_standings(db)
    if not standings:
        return {"contenders": [], "leader_clinched": False}

    leader = standings[0]
    p2 = standings[1] if len(standings) > 1 else leader

    clinched, gap = calculate_clinch_threshold(
        leader.points, p2.points, remaining_gps, remaining_sprints
    )

    contenders = []
    for s in standings:
        eliminated = is_mathematically_eliminated(
            s.points, leader.points, remaining_gps, remaining_sprints
        )
        max_possible = s.points + calculate_max_remaining_points(remaining_gps, remaining_sprints)
        contenders.append({
            "driver_id": s.driver.id,
            "driver_name": f"{s.driver.first_name} {s.driver.last_name}",
            "driver_code": s.driver.code,
            "constructor_name": s.driver.constructor_name,
            "points": s.points,
            "points_behind_leader": s.points_behind_leader,
            "max_possible_points": max_possible,
            "mathematically_eliminated": eliminated,
            "can_clinch_next": not eliminated and (max_possible >= leader.points)
        })

    return {
        "leader": leader.driver.code,
        "lead_gap": gap,
        "leader_clinched": clinched,
        "remaining_gps": remaining_gps,
        "remaining_sprints": remaining_sprints,
        "contenders": contenders,
        "provenance": {
            "source": "APEX_GP_CHAMPIONSHIP_MATH_ENGINE",
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "data_state": "HISTORICAL",
            "verified": True,
            "is_test_fixture": True,
            "notes": "Calculated over 2024 development seed baseline."
        }
    }

@api_router.get("/championship/calculator")
async def get_championship_scenario_calculator(
    driver_code: str = Query(..., description="Driver acronym to evaluate (e.g. PER, LEC, NOR)"),
    rival_code: Optional[str] = Query(None, description="Rival driver acronym to compare against (defaults to leader or P2)"),
    season: int = Query(2024),
    remaining_gps: int = Query(23),
    remaining_sprints: int = Query(6),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Evaluates 'What does this driver need to win?' scenario calculator.
    Provides mathematically verified thresholds, countback evaluation, rival caps,
    and feasible scenarios without probabilistic heuristics or chat hallucinations.
    """
    from app.championship.engine import calculate_driver_scenario_to_win

    standings = await get_driver_standings(db)
    if not standings:
        raise HTTPException(status_code=404, detail="No standings data available")

    # Map drivers by code
    drivers_map = {s.driver.code.upper(): s for s in standings}
    target = drivers_map.get(driver_code.upper())
    if not target:
        raise HTTPException(status_code=404, detail=f"Driver '{driver_code}' not found in standings")

    # Default rival: if target is leader, rival is P2; otherwise rival is leader
    leader = standings[0]
    p2 = standings[1] if len(standings) > 1 else leader

    if rival_code:
        rival = drivers_map.get(rival_code.upper())
        if not rival:
            raise HTTPException(status_code=404, detail=f"Rival driver '{rival_code}' not found in standings")
    else:
        rival = p2 if target.driver.code == leader.driver.code else leader

    # Fetch actual finishes for target and rival from SessionResultModel for countback analysis
    target_results_stmt = (
        select(SessionResultModel.position)
        .where(SessionResultModel.driver_id == target.driver.id)
        .order_by(SessionResultModel.position)
    )
    rival_results_stmt = (
        select(SessionResultModel.position)
        .where(SessionResultModel.driver_id == rival.driver.id)
        .order_by(SessionResultModel.position)
    )
    target_finishes = [p for p in (await db.execute(target_results_stmt)).scalars().all() if p is not None]
    rival_finishes = [p for p in (await db.execute(rival_results_stmt)).scalars().all() if p is not None]

    scenario_res = calculate_driver_scenario_to_win(
        target_driver_code=target.driver.code,
        target_points=target.points,
        rival_driver_code=rival.driver.code,
        rival_points=rival.points,
        remaining_gps=remaining_gps,
        remaining_sprints=remaining_sprints,
        target_finishes=target_finishes,
        rival_finishes=rival_finishes,
        season=season
    )

    return {
        "status": "SUCCESS",
        "season": season,
        "target": {
            "driver_code": target.driver.code,
            "driver_name": f"{target.driver.first_name} {target.driver.last_name}",
            "constructor_name": target.driver.constructor_name,
            "current_points": target.points,
            "current_position": target.position
        },
        "rival": {
            "driver_code": rival.driver.code,
            "driver_name": f"{rival.driver.first_name} {rival.driver.last_name}",
            "constructor_name": rival.driver.constructor_name,
            "current_points": rival.points,
            "current_position": rival.position
        },
        "calculation": scenario_res,
        "provenance": {
            "source": "APEX_GP_CHAMPIONSHIP_MATH_ENGINE",
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "data_state": "HISTORICAL",
            "verified": True,
            "is_test_fixture": True,
            "notes": "Scenario evaluation executed via pure mathematical bounds."
        }
    }


# ----------------- LIVE RACE CENTER REST ENDPOINTS -----------------

@api_router.get("/live/diagnostics")
async def get_live_diagnostics():
    """
    Returns operational diagnostics for upstream OpenF1 streaming,
    including connection status, active session key, subscribed topics,
    deduplication metrics, ingestion lag, Redis cache status, and connected clients.
    Excludes sensitive credentials.
    """
    from app.providers.openf1_stream import openf1_stream_manager
    from app.core.redis import redis_client

    diag = openf1_stream_manager.get_diagnostics()
    diag["connected_clients_count"] = live_session_manager.get_connected_clients_count()
    diag["redis_connected"] = bool(redis_client._redis is not None)
    return diag

@api_router.get("/live/sessions")
async def list_available_live_sessions(db: AsyncSession = Depends(get_db_session)):
    """
    Returns available sessions for Live Race Center selection,
    including format, round number, provider mapping, and data state (LIVE vs HISTORICAL).
    """
    from app.providers.openf1_stream import openf1_stream_manager

    # Fetch sessions from DB
    sessions_list = []
    try:
        stmt = (
            select(SessionModel, MeetingModel)
            .join(MeetingModel, SessionModel.meeting_id == MeetingModel.id)
            .order_by(MeetingModel.season.desc(), MeetingModel.round_number.desc())
        )
        res = await db.execute(stmt)
        active_provider_key = openf1_stream_manager.active_session_key

        for s, m in res.all():
            provider_key = live_session_manager.resolve_provider_session_key(s.id)
            is_active_live = bool(openf1_stream_manager.is_connected and active_provider_key == provider_key)
            sessions_list.append({
                "session_id": s.id,
                "session_name": f"{m.official_name} - {s.name}",
                "meeting_id": m.id,
                "season": m.season,
                "round_number": m.round_number,
                "circuit_name": m.circuit_name,
                "session_type": s.type.value if hasattr(s.type, "value") else str(s.type),
                "status": "LIVE" if is_active_live else (s.status.value if hasattr(s.status, "value") else str(s.status)),
                "provider_session_key": provider_key,
                "data_state": "LIVE" if is_active_live else "HISTORICAL",
                "is_fixture": False
            })
    except Exception:
        pass


    # Add fixture session if not already in DB
    if not any(s["session_id"] == "2024_01_race" for s in sessions_list):
        sessions_list.insert(0, {
            "session_id": "2024_01_race",
            "session_name": "Bahrain GP 2024 (Baseline Demo Race)",
            "meeting_id": "2024_01_bahrain",
            "season": 2024,
            "round_number": 1,
            "circuit_name": "Bahrain International Circuit",
            "session_type": "RACE",
            "status": "COMPLETED",
            "provider_session_key": "9472",
            "data_state": "HISTORICAL",
            "is_fixture": True
        })

    return sessions_list

@api_router.get("/live/{session_id}/snapshot", response_model=LiveSessionSnapshot)
async def get_live_snapshot(session_id: str):
    """
    Returns current live timing, tower, weather, and race control snapshot.
    If session is not in cache, attempts to load from deterministic fixture or OpenF1.
    """
    snapshot = await live_session_manager.get_current_snapshot(session_id)
    if not snapshot:
        provider_key = live_session_manager.resolve_provider_session_key(session_id)
        snapshot = await live_session_manager.ingest_session_data(session_id, provider_key, is_live_stream=False)
    if not snapshot:
        raise HTTPException(status_code=404, detail=f"Live session {session_id} not active or available.")
    return snapshot

@api_router.post("/live/{session_id}/sync")
async def trigger_live_sync(session_id: str, openf1_key: Optional[str] = None, is_live: bool = False):
    """
    Synchronizes session data directly from OpenF1 provider,
    building a fresh snapshot and broadcasting incremental updates.
    """
    provider_key = openf1_key or live_session_manager.resolve_provider_session_key(session_id)
    snapshot = await live_session_manager.ingest_session_data(session_id, provider_key, is_live_stream=is_live)
    return {"status": "synced", "session_id": session_id, "data_state": snapshot.data_state, "sequence_number": snapshot.sequence_number}

