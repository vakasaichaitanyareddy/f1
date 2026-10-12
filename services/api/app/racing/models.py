from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base

class DataStateEnum(str, enum.Enum):
    LIVE = "LIVE"
    DELAYED = "DELAYED"
    STALE = "STALE"
    HISTORICAL = "HISTORICAL"
    UNAVAILABLE = "UNAVAILABLE"

class SessionTypeEnum(str, enum.Enum):
    FP1 = "FP1"
    FP2 = "FP2"
    FP3 = "FP3"
    SPRINT_SHOOTOUT = "SPRINT_SHOOTOUT"
    SPRINT = "SPRINT"
    QUALIFYING = "QUALIFYING"
    RACE = "RACE"

class SessionStatusEnum(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    LIVE = "LIVE"
    DELAYED = "DELAYED"
    SUSPENDED = "SUSPENDED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    spoiler_shield_enabled = Column(Boolean, default=False)
    favorite_driver_id = Column(String, nullable=True)
    favorite_team_id = Column(String, nullable=True)
    pitwall_layout_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ConstructorModel(Base):
    __tablename__ = "constructors"

    id = Column(String, primary_key=True) # e.g. "red_bull", "ferrari"
    name = Column(String, nullable=False)
    nationality = Column(String, nullable=False)
    color_hex = Column(String, nullable=False)
    total_championships = Column(Integer, default=0)

    drivers = relationship("DriverModel", back_populates="constructor")

class DriverModel(Base):
    __tablename__ = "drivers"

    id = Column(String, primary_key=True) # e.g. "max_verstappen"
    code = Column(String(3), nullable=False, index=True)
    permanent_number = Column(Integer, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    nationality = Column(String, nullable=False)
    constructor_id = Column(String, ForeignKey("constructors.id"), nullable=False)
    biography = Column(Text, nullable=True)
    career_wins = Column(Integer, default=0)
    career_podiums = Column(Integer, default=0)
    career_poles = Column(Integer, default=0)
    career_championships = Column(Integer, default=0)

    constructor = relationship("ConstructorModel", back_populates="drivers")

class MeetingModel(Base):
    __tablename__ = "meetings"

    id = Column(String, primary_key=True) # e.g. "2024_01_bahrain"
    season = Column(Integer, nullable=False, index=True)
    round_number = Column(Integer, nullable=False)
    official_name = Column(String, nullable=False)
    location = Column(String, nullable=False)
    country = Column(String, nullable=False)
    circuit_id = Column(String, nullable=False)
    circuit_name = Column(String, nullable=False)
    circuit_length_km = Column(Float, nullable=False)
    laps_total = Column(Integer, nullable=False)
    is_sprint_weekend = Column(Boolean, default=False)

    sessions = relationship("SessionModel", back_populates="meeting", cascade="all, delete-orphan")

class SessionModel(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True) # e.g. "2024_01_race"
    meeting_id = Column(String, ForeignKey("meetings.id"), nullable=False)
    name = Column(String, nullable=False)
    type = Column(SQLEnum(SessionTypeEnum), nullable=False)
    start_time_utc = Column(DateTime, nullable=False)
    status = Column(SQLEnum(SessionStatusEnum), default=SessionStatusEnum.SCHEDULED)

    meeting = relationship("MeetingModel", back_populates="sessions")
    results = relationship("SessionResultModel", back_populates="session", cascade="all, delete-orphan")

class SessionResultModel(Base):
    __tablename__ = "session_results"

    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    driver_id = Column(String, ForeignKey("drivers.id"), nullable=False)
    position = Column(Integer, nullable=False)
    grid = Column(Integer, nullable=False)
    laps = Column(Integer, nullable=False)
    status = Column(String, nullable=False) # "Finished", "+1 Lap", "DNF", "DSQ"
    time_or_retired = Column(String, nullable=False)
    points_awarded = Column(Float, default=0.0)
    fastest_lap = Column(Boolean, default=False)
    fastest_lap_time = Column(String, nullable=True)

    session = relationship("SessionModel", back_populates="results")
