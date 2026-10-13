"use client";

import React, { useState, useEffect, useRef } from "react";
import { 
  Radio, Gauge, ShieldAlert, Flag, CloudSun, 
  RotateCw, RefreshCw, AlertTriangle, ArrowUp, ArrowDown, 
  Minus, Fuel, Disc, Wrench
} from "lucide-react";
import CircuitMap from "./CircuitMap";

interface LiveSessionProps {
  sessionId?: string;
  spoilerShield?: boolean;
  onSessionChange?: (sessionId: string) => void;
}

interface AvailableSession {
  session_id: string;
  session_name: string;
  meeting_id: string;
  season: number;
  round_number: number;
  circuit_name: string;
  session_type: string;
  status: string;
  provider_session_key: string;
  data_state: string;
  is_fixture: boolean;
}

interface DiagnosticsData {
  upstream_provider: string;
  connection_status: string;
  is_connected: boolean;
  broker: string;
  active_session_key?: string;
  subscribed_topics: string[];
  last_upstream_message_time?: string;
  last_normalized_event_time?: string;
  last_redis_update_time?: string;
  ingestion_lag_seconds?: number;
  total_messages_received: number;
  total_duplicates_filtered: number;
  has_credentials: boolean;
  connected_clients_count: number;
  redis_connected: boolean;
}

interface SectorTimes {

  sector_1?: number;
  sector_2?: number;
  sector_3?: number;
}

interface DriverTiming {
  driver_number: number;
  driver_code: string;
  driver_name: string;
  team_name: string;
  team_color: string;
  position: number;
  grid: number;
  gap_to_leader?: number;
  interval?: number;
  last_lap_time?: number;
  best_lap_time?: number;
  sectors: SectorTimes;
  current_lap: number;
  in_pit: boolean;
  pit_stops_count: number;
  tire_compound?: string;
  stint_lap_count: number;
  status: string;
  positions_gained: number;
}

interface PitStop {
  driver_number: number;
  lap_number: number;
  pit_duration?: number;
  lane_duration?: number;
  timestamp: string;
}

interface Stint {
  driver_number: number;
  stint_number: number;
  compound: string;
  lap_start: number;
  lap_end?: number;
  tyre_age_at_start: number;
}

interface RaceControl {
  date: string;
  lap_number?: number;
  category: string;
  message: string;
  flag?: string;
  scope?: string;
  sector?: number;
}

interface Weather {
  air_temperature: number;
  track_temperature: number;
  humidity: number;
  pressure: number;
  wind_speed: number;
  wind_direction: number;
  rainfall: number;
}

interface DriverMapPosition {
  driver_number: number;
  driver_code: string;
  team_color: string;
  x: number;
  y: number;
}

interface TelemetryItem {
  driver_number: number;
  speed: number;
  throttle: number;
  brake: number;
  n_gear: number;
  drs: number;
  rpm: number;
}

interface Snapshot {
  session_id: string;
  session_name: string;
  circuit_name: string;
  total_laps: number;
  current_lap: number;
  status: string;
  data_state: string;
  track_status: string;
  weather?: Weather;
  timing_tower: DriverTiming[];
  pit_stops: PitStop[];
  stints: Stint[];
  race_control: RaceControl[];
  driver_map_positions: DriverMapPosition[];
  telemetry: TelemetryItem[];
  sequence_number: number;
  provenance: {
    source: string;
    retrieved_at: string;
    data_state: string;
    verified: boolean;
    is_test_fixture: boolean;
    notes?: string;
  };
}

export default function LiveRaceCenter({ sessionId = "2024_01_race", spoilerShield = false, onSessionChange }: LiveSessionProps) {
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [connectionState, setConnectionState] = useState<"CONNECTING" | "CONNECTED" | "DISCONNECTED" | "ERROR">("CONNECTING");
  const [selectedDriver, setSelectedDriver] = useState<number | null>(1); // Default Max Verstappen
  const [activeView, setActiveView] = useState<"TIMING" | "PIT_STINTS" | "RACE_CONTROL" | "TELEMETRY">("TIMING");
  const [availableSessions, setAvailableSessions] = useState<AvailableSession[]>([]);
  const [showDiagnostics, setShowDiagnostics] = useState<boolean>(false);
  const [diagnosticsData, setDiagnosticsData] = useState<DiagnosticsData | null>(null);
  const [loadingDiag, setLoadingDiag] = useState<boolean>(false);
  const wsRef = useRef<WebSocket | null>(null);
  const heartbeatTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Format seconds to mm:ss.sss
  const formatLapTime = (timeInSeconds?: number) => {
    if (!timeInSeconds) return "-:--.---";
    const minutes = Math.floor(timeInSeconds / 60);
    const seconds = (timeInSeconds % 60).toFixed(3);
    return `${minutes}:${seconds.padStart(6, "0")}`;
  };

  // Load available sessions for session switcher
  useEffect(() => {
    fetch("http://localhost:8000/api/v1/live/sessions")
      .then((res) => res.json())
      .then((data) => {
        if (Array.isArray(data)) setAvailableSessions(data);
      })
      .catch((err) => console.error("Error loading available sessions", err));
  }, []);

  // Fetch operational diagnostics
  const fetchDiagnostics = async () => {
    setLoadingDiag(true);
    try {
      const res = await fetch("http://localhost:8000/api/v1/live/diagnostics");
      if (res.ok) {
        setDiagnosticsData(await res.json());
      }
    } catch (err) {
      console.error("Diagnostics fetch error", err);
    } finally {
      setLoadingDiag(false);
    }
  };

  useEffect(() => {
    // Clear snapshot on session change so old data cannot linger
    setSnapshot(null);
    setConnectionState("CONNECTING");

    let currentActiveSession = sessionId;

    // 1. Initial REST fetch for snapshot fallback
    fetch(`http://localhost:8000/api/v1/live/${sessionId}/snapshot`)
      .then((res) => res.json())
      .then((data) => {
        if (currentActiveSession === sessionId && data && data.session_id) setSnapshot(data);
      })
      .catch((err) => console.error("Snapshot fetch error", err));

    let isSubscribed = true;

    // 2. WebSocket setup
    const wsUrl = `ws://localhost:8000/ws/live/${sessionId}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      if (!isSubscribed) return;
      setConnectionState("CONNECTED");
      // Setup heartbeat every 15s
      heartbeatTimerRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: "PING" }));
        }
      }, 15000);
    };

    ws.onmessage = (event) => {
      if (!isSubscribed) return;
      try {
        const msg = JSON.parse(event.data);
        // Pass control messages (PING / PONG)
        if (msg.type === "PING" || msg.type === "PONG") {
          return;
        }
        // Data-bearing events must belong strictly to the active sessionId.
        // Reject any data-bearing message with mismatched or absent session_id.
        if (!msg.session_id || msg.session_id !== sessionId) {
          return;
        }
        if (msg.type === "SNAPSHOT") {
          setSnapshot(msg.payload);
        } else if (msg.type === "TIMING") {
          setSnapshot((prev) => {
            if (!prev) return prev;
            return {
              ...prev,
              current_lap: msg.payload?.current_lap ?? prev.current_lap,
              track_status: msg.payload?.track_status ?? prev.track_status,
              timing_tower: msg.payload?.timing_tower ?? prev.timing_tower,
              weather: msg.payload?.weather ?? prev.weather,
              data_state: msg.data_state ?? prev.data_state,
            };
          });
        } else if (msg.type === "RACE_CONTROL") {
          setSnapshot((prev) => {
            if (!prev) return prev;
            const updatedRc = [...(prev.race_control || []), msg.payload].slice(-30);
            return {
              ...prev,
              race_control: updatedRc,
              track_status: msg.payload?.flag === "RED" ? "RED" : (msg.payload?.flag?.includes("YELLOW") ? "YELLOW" : prev.track_status)
            };
          });
        } else if (msg.type === "WEATHER") {
          setSnapshot((prev) => {
            if (!prev) return prev;
            return { ...prev, weather: msg.payload };
          });
        } else if (msg.type === "MAP_POSITIONS") {
          setSnapshot((prev) => {
            if (!prev) return prev;
            return { ...prev, driver_map_positions: msg.payload };
          });
        } else if (msg.type === "TELEMETRY") {
          setSnapshot((prev) => {
            if (!prev) return prev;
            return { ...prev, telemetry: msg.payload };
          });
        }
      } catch (err) {
        console.error("WS Parse error", err);
      }
    };

    ws.onclose = () => {
      if (isSubscribed) setConnectionState("DISCONNECTED");
      if (heartbeatTimerRef.current) clearInterval(heartbeatTimerRef.current);
    };

    ws.onerror = () => {
      if (isSubscribed) setConnectionState("ERROR");
    };

    return () => {
      isSubscribed = false;
      if (heartbeatTimerRef.current) clearInterval(heartbeatTimerRef.current);
      ws.onopen = null;
      ws.onmessage = null;
      ws.onclose = null;
      ws.onerror = null;
      ws.close();
    };
  }, [sessionId]);

  const triggerResync = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "RESYNC" }));
    } else {
      // Re-fetch via REST
      fetch(`http://localhost:8000/api/v1/live/${sessionId}/snapshot`)
        .then((res) => res.json())
        .then((data) => setSnapshot(data));
    }
  };

  const getTireBadgeColor = (compound?: string) => {
    switch (compound?.toUpperCase()) {
      case "SOFT": return "bg-red-600 text-white border-red-500";
      case "MEDIUM": return "bg-yellow-500 text-black border-yellow-400";
      case "HARD": return "bg-white text-black border-gray-300";
      case "INTERMEDIATE": return "bg-green-600 text-white border-green-500";
      case "WET": return "bg-blue-600 text-white border-blue-500";
      default: return "bg-gray-700 text-gray-300 border-gray-600";
    }
  };

  const getTrackStatusBadge = (status?: string) => {
    switch (status) {
      case "SAFETY_CAR":
        return <span className="px-2 py-0.5 rounded text-xs font-bold bg-amber-500 text-black flex items-center gap-1 animate-pulse"><AlertTriangle className="w-3 h-3"/> SAFETY CAR</span>;
      case "VSC":
        return <span className="px-2 py-0.5 rounded text-xs font-bold bg-amber-600 text-white flex items-center gap-1"><AlertTriangle className="w-3 h-3"/> VIRTUAL SAFETY CAR</span>;
      case "YELLOW":
        return <span className="px-2 py-0.5 rounded text-xs font-bold bg-yellow-400 text-black flex items-center gap-1"><Flag className="w-3 h-3"/> YELLOW FLAG</span>;
      case "RED":
        return <span className="px-2 py-0.5 rounded text-xs font-bold bg-red-600 text-white flex items-center gap-1 animate-pulse"><ShieldAlert className="w-3 h-3"/> RED FLAG</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-xs font-bold bg-green-500 text-black flex items-center gap-1"><Flag className="w-3 h-3"/> TRACK CLEAR (GREEN)</span>;
    }
  };

  const selectedDriverTelemetry = snapshot?.telemetry.find(t => t.driver_number === selectedDriver);
  const selectedDriverTiming = snapshot?.timing_tower.find(t => t.driver_number === selectedDriver);

  return (
    <div className="space-y-6">
      {/* Top Session Bar */}
      <div className="bg-[#15171E] rounded-xl border border-[#272A35] p-5 shadow-lg flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex flex-wrap items-center gap-3">
            <span className="flex items-center space-x-1.5 text-xs font-black uppercase tracking-wider px-2 py-0.5 rounded bg-[#E10600] text-white">
              <Radio className="w-3 h-3 animate-pulse" />
              <span>LIVE RACE CENTER</span>
            </span>
            {getTrackStatusBadge(snapshot?.track_status)}
            <div className="flex items-center space-x-1 text-xs px-2 py-0.5 rounded bg-[#0D0E12] border border-[#272A35] text-[#8F96A3]">
              <span className={`w-2 h-2 rounded-full ${connectionState === "CONNECTED" ? "bg-[#30D158]" : "bg-red-500"}`}></span>
              <span>WS: {connectionState}</span>
            </div>

            {/* Dynamic Session Switcher Dropdown */}
            {availableSessions.length > 0 && onSessionChange && (
              <select
                aria-label="Active Racing Session"
                value={sessionId}
                onChange={(e) => onSessionChange(e.target.value)}
                className="bg-[#0D0E12] border border-[#272A35] text-xs font-semibold text-white px-2.5 py-1 rounded focus:outline-none focus:border-[#E10600]"
              >
                {availableSessions.map((s) => (
                  <option key={s.session_id} value={s.session_id}>
                    {s.data_state === "LIVE" ? "🔴 [LIVE] " : "[HISTORICAL] "}
                    {s.session_name}
                  </option>
                ))}
              </select>
            )}
          </div>
          <h2 className="text-xl md:text-2xl font-black text-white">{snapshot?.session_name || "Formula 1 Grand Prix"}</h2>
          <div className="text-xs text-[#8F96A3] flex flex-wrap items-center gap-2">
            <span>{snapshot?.circuit_name}</span>
            <span>•</span>
            <span className="font-mono text-white font-bold">LAP {snapshot?.current_lap} / {snapshot?.total_laps}</span>
            <span>•</span>
            <span className={`font-semibold px-1.5 py-0.2 rounded text-[11px] ${
              snapshot?.data_state === "LIVE" ? "bg-red-900/40 text-red-400 border border-red-700/50" : "bg-blue-900/40 text-blue-400 border border-blue-700/50"
            }`}>
              FEED: {snapshot?.data_state || "HISTORICAL"}
            </span>
            <span>•</span>
            <span className="text-[#64D2FF]">SRC: {snapshot?.provenance?.source}</span>
          </div>
        </div>

        {/* Weather & Re-sync / Diagnostics Controls */}
        <div className="flex items-center space-x-3">
          {snapshot?.weather && (
            <div className="hidden sm:flex items-center space-x-4 bg-[#0D0E12] border border-[#272A35] px-4 py-2 rounded-lg text-xs">
              <div className="flex items-center space-x-1.5 text-white">
                <CloudSun className="w-4 h-4 text-amber-400" />
                <span className="font-mono font-bold">{snapshot.weather.track_temperature}°C</span>
                <span className="text-[#8F96A3]">TRACK</span>
              </div>
              <div className="text-white border-l border-[#272A35] pl-3">
                <span className="font-mono font-bold">{snapshot.weather.air_temperature}°C</span>
                <span className="text-[#8F96A3] ml-1">AIR</span>
              </div>
              <div className="text-white border-l border-[#272A35] pl-3">
                <span className="font-mono font-bold">{snapshot.weather.wind_speed} m/s</span>
                <span className="text-[#8F96A3] ml-1">WIND</span>
              </div>
            </div>
          )}

          <button
            onClick={() => {
              setShowDiagnostics(true);
              fetchDiagnostics();
            }}
            className="flex items-center space-x-1 bg-[#1a1d26] hover:bg-[#272A35] border border-[#272A35] text-[#8F96A3] hover:text-white px-3 py-2 rounded-lg text-xs font-semibold transition"
            title="Operational Stream Diagnostics"
          >
            <Gauge className="w-3.5 h-3.5" />
            <span>DIAGNOSTICS</span>
          </button>

          <button
            onClick={triggerResync}
            className="flex items-center space-x-1 bg-[#272A35] hover:bg-[#343846] text-white px-3 py-2 rounded-lg text-xs font-semibold transition"
            title="Resynchronize stream"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>RESYNC</span>
          </button>
        </div>
      </div>

      {/* Operational Diagnostics Modal */}
      {showDiagnostics && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#15171E] border border-[#272A35] rounded-xl max-w-xl w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-[#272A35] pb-3">
              <div className="flex items-center space-x-2">
                <Gauge className="w-5 h-5 text-[#64D2FF]" />
                <h3 className="font-bold text-white text-base">Upstream Feed Operational Diagnostics</h3>
              </div>
              <button
                onClick={() => setShowDiagnostics(false)}
                className="text-[#8F96A3] hover:text-white text-sm font-bold px-2 py-1"
              >
                ✕
              </button>
            </div>

            {loadingDiag ? (
              <div className="py-8 text-center text-sm text-[#8F96A3]">Loading operational diagnostics...</div>
            ) : diagnosticsData ? (
              <div className="space-y-3 text-xs font-mono">
                <div className="grid grid-cols-2 gap-2 bg-[#0D0E12] p-3 rounded border border-[#272A35]">
                  <div>
                    <span className="text-[#8F96A3] block">Upstream Provider:</span>
                    <span className="text-white font-bold">{diagnosticsData.upstream_provider}</span>
                  </div>
                  <div>
                    <span className="text-[#8F96A3] block">Connection Status:</span>
                    <span className={`font-bold ${diagnosticsData.is_connected ? "text-[#30D158]" : "text-amber-400"}`}>
                      {diagnosticsData.connection_status}
                    </span>
                  </div>
                  <div>
                    <span className="text-[#8F96A3] block">Broker:</span>
                    <span className="text-white">{diagnosticsData.broker}</span>
                  </div>
                  <div>
                    <span className="text-[#8F96A3] block">Active Provider Key:</span>
                    <span className="text-white">{diagnosticsData.active_session_key || "None (Idle)"}</span>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2 bg-[#0D0E12] p-3 rounded border border-[#272A35]">
                  <div>
                    <span className="text-[#8F96A3] block">Ingestion Lag:</span>
                    <span className="text-white">{diagnosticsData.ingestion_lag_seconds !== null ? `${diagnosticsData.ingestion_lag_seconds}s` : "N/A"}</span>
                  </div>
                  <div>
                    <span className="text-[#8F96A3] block">WebSocket Clients:</span>
                    <span className="text-white">{diagnosticsData.connected_clients_count} connected</span>
                  </div>
                  <div>
                    <span className="text-[#8F96A3] block">Messages Received:</span>
                    <span className="text-white">{diagnosticsData.total_messages_received}</span>
                  </div>
                  <div>
                    <span className="text-[#8F96A3] block">Duplicates Filtered:</span>
                    <span className="text-white">{diagnosticsData.total_duplicates_filtered}</span>
                  </div>
                </div>

                <div className="bg-[#0D0E12] p-3 rounded border border-[#272A35] space-y-1">
                  <div>
                    <span className="text-[#8F96A3]">Subscribed Topics: </span>
                    <span className="text-white">{diagnosticsData.subscribed_topics.join(", ") || "None"}</span>
                  </div>
                  <div>
                    <span className="text-[#8F96A3]">OAuth2 Credentials Present: </span>
                    <span className={diagnosticsData.has_credentials ? "text-[#30D158]" : "text-amber-400"}>
                      {diagnosticsData.has_credentials ? "YES" : "NO (Unauthenticated mode)"}
                    </span>
                  </div>
                  <div>
                    <span className="text-[#8F96A3]">Redis Cache Connected: </span>
                    <span className={diagnosticsData.redis_connected ? "text-[#30D158]" : "text-red-400"}>
                      {diagnosticsData.redis_connected ? "YES" : "NO"}
                    </span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-red-400 text-sm">Failed to load diagnostics.</div>
            )}

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setShowDiagnostics(false)}
                className="bg-[#272A35] hover:bg-[#343846] text-white px-4 py-2 rounded text-xs font-semibold"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main Split Layout: Timing Tower (Left 60%) + Circuit Map & Telemetry (Right 40%) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Timing Tower & Sub-Views */}
        <div className="lg:col-span-7 space-y-4">
          {/* Sub-view Navigation Tabs */}
          <div className="flex items-center space-x-2 border-b border-[#272A35] pb-2">
            <button
              onClick={() => setActiveView("TIMING")}
              className={`px-3 py-1.5 rounded text-xs font-bold transition ${activeView === "TIMING" ? "bg-[#E10600] text-white" : "text-[#8F96A3] hover:text-white"}`}
            >
              TIMING TOWER
            </button>
            <button
              onClick={() => setActiveView("PIT_STINTS")}
              className={`px-3 py-1.5 rounded text-xs font-bold transition ${activeView === "PIT_STINTS" ? "bg-[#E10600] text-white" : "text-[#8F96A3] hover:text-white"}`}
            >
              PIT STOPS & STINTS ({snapshot?.pit_stops.length || 0})
            </button>
            <button
              onClick={() => setActiveView("RACE_CONTROL")}
              className={`px-3 py-1.5 rounded text-xs font-bold transition ${activeView === "RACE_CONTROL" ? "bg-[#E10600] text-white" : "text-[#8F96A3] hover:text-white"}`}
            >
              RACE CONTROL ({snapshot?.race_control.length || 0})
            </button>
            <button
              onClick={() => setActiveView("TELEMETRY")}
              className={`px-3 py-1.5 rounded text-xs font-bold transition ${activeView === "TELEMETRY" ? "bg-[#E10600] text-white" : "text-[#8F96A3] hover:text-white"}`}
            >
              LIVE TELEMETRY
            </button>
          </div>

          {/* VIEW 1: TIMING TOWER */}
          {activeView === "TIMING" && (
            <div className="bg-[#15171E] rounded-xl border border-[#272A35] overflow-hidden shadow">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="bg-[#0D0E12] text-[#8F96A3] uppercase border-b border-[#272A35]">
                      <th className="py-2.5 px-3">Pos</th>
                      <th className="py-2.5 px-2">Driver</th>
                      <th className="py-2.5 px-2">Tire</th>
                      <th className="py-2.5 px-3 text-right">Gap</th>
                      <th className="py-2.5 px-3 text-right">Int</th>
                      <th className="py-2.5 px-3 text-right">Last Lap</th>
                      <th className="py-2.5 px-3 text-right">Best Lap</th>
                      <th className="py-2.5 px-2 text-center">S1 / S2 / S3</th>
                      <th className="py-2.5 px-2 text-center">Gain</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#272A35]">
                    {snapshot?.timing_tower.map((row) => (
                      <tr
                        key={row.driver_number}
                        onClick={() => setSelectedDriver(row.driver_number)}
                        className={`cursor-pointer transition hover:bg-[#1C1F28] ${selectedDriver === row.driver_number ? "bg-[#1E222D]" : ""}`}
                      >
                        {/* Position */}
                        <td className="py-2.5 px-3 font-mono font-black text-white">
                          {spoilerShield ? "•" : `P${row.position}`}
                        </td>
                        {/* Driver Code & Color Accent */}
                        <td className="py-2.5 px-2">
                          <div className="flex items-center space-x-1.5">
                            <span className="w-1.5 h-4 rounded-full" style={{ backgroundColor: row.team_color }}></span>
                            <span className="font-bold text-white font-mono">{row.driver_code}</span>
                            <span className="text-[10px] text-[#8F96A3] hidden sm:inline">{row.driver_name.split(" ")[1]}</span>
                          </div>
                        </td>
                        {/* Tire Compound & Stint Age */}
                        <td className="py-2.5 px-2">
                          <div className="flex items-center space-x-1">
                            <span className={`px-1.5 py-0.2 rounded text-[9px] font-black border ${getTireBadgeColor(row.tire_compound)}`}>
                              {row.tire_compound?.[0] || "?"}
                            </span>
                            <span className="font-mono text-[10px] text-[#8F96A3]">L{row.stint_lap_count}</span>
                          </div>
                        </td>
                        {/* Gap to Leader */}
                        <td className="py-2.5 px-3 text-right font-mono text-white">
                          {spoilerShield ? "-" : (row.gap_to_leader === 0 ? "LEAD" : `+${row.gap_to_leader?.toFixed(3)}`)}
                        </td>
                        {/* Interval */}
                        <td className="py-2.5 px-3 text-right font-mono text-[#8F96A3]">
                          {spoilerShield ? "-" : (row.interval === 0 ? "-" : `+${row.interval?.toFixed(3)}`)}
                        </td>
                        {/* Last Lap */}
                        <td className="py-2.5 px-3 text-right font-mono text-white">
                          {spoilerShield ? "-:--.---" : formatLapTime(row.last_lap_time)}
                        </td>
                        {/* Best Lap */}
                        <td className="py-2.5 px-3 text-right font-mono font-bold text-[#64D2FF]">
                          {spoilerShield ? "-:--.---" : formatLapTime(row.best_lap_time)}
                        </td>
                        {/* Sectors */}
                        <td className="py-2.5 px-2 text-center font-mono text-[10px] text-[#8F96A3]">
                          {row.sectors.sector_1?.toFixed(1) || "-"} / {row.sectors.sector_2?.toFixed(1) || "-"} / {row.sectors.sector_3?.toFixed(1) || "-"}
                        </td>
                        {/* Position Gain */}
                        <td className="py-2.5 px-2 text-center font-mono">
                          {row.positions_gained > 0 ? (
                            <span className="text-[#30D158] flex items-center justify-center font-bold">
                              <ArrowUp className="w-3 h-3 mr-0.5" />+{row.positions_gained}
                            </span>
                          ) : row.positions_gained < 0 ? (
                            <span className="text-[#E10600] flex items-center justify-center font-bold">
                              <ArrowDown className="w-3 h-3 mr-0.5" />{row.positions_gained}
                            </span>
                          ) : (
                            <span className="text-[#8F96A3] flex items-center justify-center">
                              <Minus className="w-3 h-3" />
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* VIEW 2: PIT STOPS & STINTS */}
          {activeView === "PIT_STINTS" && (
            <div className="bg-[#15171E] rounded-xl border border-[#272A35] p-4 space-y-4">
              <h3 className="font-bold text-white text-sm flex items-center gap-2">
                <Wrench className="w-4 h-4 text-[#FFCC00]" />
                Recent Pit Stops
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {snapshot?.pit_stops.map((p, idx) => (
                  <div key={idx} className="bg-[#0D0E12] border border-[#272A35] p-3 rounded-lg flex items-center justify-between">
                    <div>
                      <span className="text-xs font-mono font-bold text-white">Car #{p.driver_number}</span>
                      <span className="text-xs text-[#8F96A3] ml-2">Lap {p.lap_number}</span>
                    </div>
                    <div className="text-right font-mono">
                      <span className="text-xs font-bold text-[#30D158]">{p.pit_duration}s stop</span>
                      <span className="text-[10px] text-[#8F96A3] block">{p.lane_duration}s in lane</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* VIEW 3: RACE CONTROL */}
          {activeView === "RACE_CONTROL" && (
            <div className="bg-[#15171E] rounded-xl border border-[#272A35] p-4 space-y-3">
              <h3 className="font-bold text-white text-sm flex items-center gap-2">
                <Flag className="w-4 h-4 text-[#E10600]" />
                Official Race Control Timeline
              </h3>
              <div className="space-y-2 max-h-[350px] overflow-y-auto">
                {snapshot?.race_control.map((rc, idx) => (
                  <div key={idx} className="bg-[#0D0E12] border border-[#272A35] p-3 rounded-lg flex items-start justify-between">
                    <div>
                      <div className="flex items-center space-x-2">
                        {rc.flag && (
                          <span className={`px-1.5 py-0.5 rounded text-[10px] font-black uppercase ${rc.flag === "GREEN" ? "bg-green-600 text-white" : rc.flag === "YELLOW" ? "bg-yellow-400 text-black" : "bg-red-600 text-white"}`}>
                            {rc.flag}
                          </span>
                        )}
                        <span className="text-xs font-bold text-[#E10600] uppercase font-mono">{rc.category}</span>
                        {rc.lap_number && <span className="text-xs text-[#8F96A3]">Lap {rc.lap_number}</span>}
                      </div>
                      <p className="text-xs text-white mt-1 font-mono">{rc.message}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* VIEW 4: LIVE TELEMETRY */}
          {activeView === "TELEMETRY" && (
            <div className="bg-[#15171E] rounded-xl border border-[#272A35] p-5 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-white text-sm flex items-center gap-2">
                  <Gauge className="w-4 h-4 text-[#64D2FF]" />
                  Telemetry Inspector — Car #{selectedDriver} ({selectedDriverTiming?.driver_code || "DRIVER"})
                </h3>
              </div>
              {selectedDriverTelemetry ? (
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                  <div className="bg-[#0D0E12] border border-[#272A35] p-4 rounded-lg text-center">
                    <span className="text-xs text-[#8F96A3]">SPEED</span>
                    <div className="text-2xl font-black text-white font-mono mt-1">{selectedDriverTelemetry.speed} <span className="text-xs font-normal">km/h</span></div>
                  </div>
                  <div className="bg-[#0D0E12] border border-[#272A35] p-4 rounded-lg text-center">
                    <span className="text-xs text-[#8F96A3]">GEAR</span>
                    <div className="text-2xl font-black text-[#64D2FF] font-mono mt-1">{selectedDriverTelemetry.n_gear}</div>
                  </div>
                  <div className="bg-[#0D0E12] border border-[#272A35] p-4 rounded-lg text-center">
                    <span className="text-xs text-[#8F96A3]">THROTTLE</span>
                    <div className="text-2xl font-black text-[#30D158] font-mono mt-1">{selectedDriverTelemetry.throttle}%</div>
                  </div>
                  <div className="bg-[#0D0E12] border border-[#272A35] p-4 rounded-lg text-center">
                    <span className="text-xs text-[#8F96A3]">DRS STATUS</span>
                    <div className={`text-2xl font-black font-mono mt-1 ${selectedDriverTelemetry.drs ? "text-[#30D158]" : "text-[#8F96A3]"}`}>
                      {selectedDriverTelemetry.drs ? "OPEN" : "CLOSED"}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-xs text-[#8F96A3] p-4 text-center">Select a driver from the timing tower to inspect live speed, throttle, and gear telemetry.</div>
              )}
            </div>
          )}
        </div>

        {/* Right Column: Interactive Circuit Map & Driver Focus */}
        <div className="lg:col-span-5 space-y-4">
          <CircuitMap
            circuitName={snapshot?.circuit_name || "Bahrain International Circuit"}
            driverPositions={snapshot?.driver_map_positions || []}
          />

          {/* Selected Driver Focus Card */}
          {selectedDriverTiming && (
            <div className="bg-[#15171E] rounded-xl border border-[#272A35] p-5 space-y-3">
              <div className="flex items-center justify-between border-b border-[#272A35] pb-3">
                <div className="flex items-center space-x-2">
                  <span className="w-2.5 h-6 rounded" style={{ backgroundColor: selectedDriverTiming.team_color }}></span>
                  <div>
                    <h4 className="font-extrabold text-white text-base">{selectedDriverTiming.driver_name}</h4>
                    <span className="text-xs text-[#8F96A3]">{selectedDriverTiming.team_name}</span>
                  </div>
                </div>
                <div className="text-right font-mono">
                  <span className="text-lg font-black text-white">P{selectedDriverTiming.position}</span>
                  <span className="text-[10px] text-[#8F96A3] block">GRID P{selectedDriverTiming.grid}</span>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-2 text-center text-xs">
                <div className="bg-[#0D0E12] p-2 rounded border border-[#272A35]">
                  <span className="text-[10px] text-[#8F96A3]">LAST LAP</span>
                  <div className="font-mono font-bold text-white mt-0.5">{formatLapTime(selectedDriverTiming.last_lap_time)}</div>
                </div>
                <div className="bg-[#0D0E12] p-2 rounded border border-[#272A35]">
                  <span className="text-[10px] text-[#8F96A3]">BEST LAP</span>
                  <div className="font-mono font-bold text-[#64D2FF] mt-0.5">{formatLapTime(selectedDriverTiming.best_lap_time)}</div>
                </div>
                <div className="bg-[#0D0E12] p-2 rounded border border-[#272A35]">
                  <span className="text-[10px] text-[#8F96A3]">TIRE STINT</span>
                  <div className="font-mono font-bold text-white mt-0.5">{selectedDriverTiming.tire_compound} (L{selectedDriverTiming.stint_lap_count})</div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
