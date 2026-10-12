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
    UserProfile, UserPreferencesUpdate, TokenResponse
)
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

    meeting = (await db.execute(select(MeetingModel).where(MeetingModel.id == session.meeting_id))).scalar_one()

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
            source="FIA_OFFICIAL_CLASSIFICATION",
            retrieved_at=datetime.now(timezone.utc),
            data_state=DataStateEnum.HISTORICAL,
            verified=True,
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
            "verified": True
        }
    }
