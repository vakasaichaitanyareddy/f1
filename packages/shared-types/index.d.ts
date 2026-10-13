/**
 * APEX GP — Shared Domain Models & Contracts
 * Strictly mirrors backend Pydantic models for absolute type safety across web & mobile.
 */

export type DataState = 'LIVE' | 'DELAYED' | 'STALE' | 'HISTORICAL' | 'UNAVAILABLE';

export interface ProvenanceMeta {
  source: string;
  retrieved_at: string;
  data_state: DataState;
  verified: boolean;
}

export type SessionType =
  | 'FP1'
  | 'FP2'
  | 'FP3'
  | 'SPRINT_SHOOTOUT'
  | 'SPRINT'
  | 'QUALIFYING'
  | 'RACE';

export type SessionStatus = 'SCHEDULED' | 'LIVE' | 'DELAYED' | 'SUSPENDED' | 'COMPLETED' | 'CANCELLED';

export interface Driver {
  id: string;
  code: string;
  permanent_number: number;
  first_name: string;
  last_name: string;
  nationality: string;
  constructor_id: string;
  constructor_name: string;
  constructor_color: string;
  biography?: string;
  career_wins: number;
  career_podiums: number;
  career_poles: number;
  career_championships: number;
}

export interface Constructor {
  id: string;
  name: string;
  nationality: string;
  color_hex: string;
  drivers: Driver[];
  total_championships: number;
}

export interface Session {
  id: string;
  meeting_id: string;
  name: string;
  type: SessionType;
  start_time_utc: string;
  status: SessionStatus;
}

export interface Meeting {
  id: string;
  season: number;
  round_number: number;
  official_name: string;
  location: string;
  country: string;
  circuit_id: string;
  circuit_name: string;
  circuit_length_km: number;
  laps_total: number;
  is_sprint_weekend: boolean;
  sessions: Session[];
}

export interface DriverStanding {
  position: number;
  driver: Driver;
  points: number;
  wins: number;
  points_behind_leader: number;
  points_behind_previous: number;
}

export interface ConstructorStanding {
  position: number;
  constructor: Constructor;
  points: number;
  wins: number;
  points_behind_leader: number;
  points_behind_previous: number;
}

export interface RaceResultEntry {
  position: number;
  driver_id: string;
  driver_code: string;
  driver_name: string;
  constructor_name: string;
  grid: number;
  laps: number;
  status: string; // Finished, +1 Lap, DNF, DSQ
  time_or_retired: string;
  points_awarded: number;
  fastest_lap: boolean;
  fastest_lap_time?: string;
}

export interface RaceClassification {
  meeting: Meeting;
  session_type: SessionType;
  results: RaceResultEntry[];
  provenance: ProvenanceMeta;
}

export interface TimingTowerRow {
  position: number;
  driver_number: number;
  driver_code: string;
  driver_name: string;
  gap_to_leader: string;
  interval: string;
  current_lap: number;
  last_lap_time?: string;
  best_lap_time?: string;
  sector_1?: string;
  sector_2?: string;
  sector_3?: string;
  tire_compound: 'SOFT' | 'MEDIUM' | 'HARD' | 'INTERMEDIATE' | 'WET' | 'UNKNOWN';
  tire_stint_laps: number;
  in_pit: boolean;
  pit_stop_count: number;
  position_change: number;
}

export interface LiveRaceCenterState {
  meeting_id: string;
  session_name: string;
  session_status: SessionStatus;
  lap_current: number;
  laps_total: number;
  track_status: 'GREEN' | 'YELLOW' | 'SC' | 'VSC' | 'RED';
  timing_tower: TimingTowerRow[];
  provenance: ProvenanceMeta;
}
