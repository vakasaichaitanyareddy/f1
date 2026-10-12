from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime
from app.racing.models import DataStateEnum, SessionTypeEnum, SessionStatusEnum

class ProvenanceMeta(BaseModel):
    source: str
    retrieved_at: datetime
    data_state: DataStateEnum
    verified: bool
    is_test_fixture: bool = False
    notes: Optional[str] = None

class ConstructorBase(BaseModel):
    id: str
    name: str
    nationality: str
    color_hex: str
    total_championships: int = 0
    model_config = ConfigDict(from_attributes=True)

class DriverBase(BaseModel):
    id: str
    code: str
    permanent_number: int
    first_name: str
    last_name: str
    nationality: str
    constructor_id: str
    biography: Optional[str] = None
    career_wins: int = 0
    career_podiums: int = 0
    career_poles: int = 0
    career_championships: int = 0
    model_config = ConfigDict(from_attributes=True)

class DriverWithConstructor(DriverBase):
    constructor_name: str
    constructor_color: str

class ConstructorWithDrivers(ConstructorBase):
    drivers: List[DriverBase] = []

class SessionRead(BaseModel):
    id: str
    meeting_id: str
    name: str
    type: SessionTypeEnum
    start_time_utc: datetime
    status: SessionStatusEnum
    model_config = ConfigDict(from_attributes=True)

class MeetingRead(BaseModel):
    id: str
    season: int
    round_number: int
    official_name: str
    location: str
    country: str
    circuit_id: str
    circuit_name: str
    circuit_length_km: float
    laps_total: int
    is_sprint_weekend: bool
    sessions: List[SessionRead] = []
    model_config = ConfigDict(from_attributes=True)

class DriverStandingRead(BaseModel):
    position: int
    driver: DriverWithConstructor
    points: float
    wins: int
    points_behind_leader: float
    points_behind_previous: float

class ConstructorStandingRead(BaseModel):
    position: int
    constructor: ConstructorBase
    points: float
    wins: int
    points_behind_leader: float
    points_behind_previous: float

class RaceResultEntryRead(BaseModel):
    position: int
    driver_id: str
    driver_code: str
    driver_name: str
    constructor_name: str
    constructor_color: str
    grid: int
    laps: int
    status: str
    time_or_retired: str
    points_awarded: float
    fastest_lap: bool
    fastest_lap_time: Optional[str] = None

class RaceClassificationRead(BaseModel):
    meeting: MeetingRead
    session_type: SessionTypeEnum
    results: List[RaceResultEntryRead]
    provenance: ProvenanceMeta

# Identity Schemas
class UserCreate(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class UserProfile(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    spoiler_shield_enabled: bool = False
    favorite_driver_id: Optional[str] = None
    favorite_team_id: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class UserPreferencesUpdate(BaseModel):
    spoiler_shield_enabled: Optional[bool] = None
    favorite_driver_id: Optional[str] = None
    favorite_team_id: Optional[str] = None
    pitwall_layout_json: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile
