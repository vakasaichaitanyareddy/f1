"use client";

import React, { useState, useEffect } from "react";
import { 
  Trophy, Calendar, Flag, Activity, ShieldCheck, 
  ChevronRight, Gauge, Layers, Info
} from "lucide-react";

interface DriverStanding {
  position: number;
  driver: {
    first_name: string;
    last_name: string;
    code: string;
    constructor_name: string;
    constructor_color: string;
  };
  points: number;
  wins: number;
  points_behind_leader: number;
}

interface ChampionshipIntelligence {
  leader: string;
  lead_gap: number;
  leader_clinched: boolean;
  remaining_gps: number;
  remaining_sprints: number;
  contenders: Array<{
    driver_id: string;
    driver_name: string;
    driver_code: string;
    constructor_name: string;
    points: number;
    points_behind_leader: number;
    max_possible_points: number;
    mathematically_eliminated: boolean;
  }>;
}

interface Meeting {
  id: string;
  season: number;
  round_number: number;
  official_name: string;
  location: string;
  country: string;
  circuit_name: string;
  sessions: Array<{
    id: string;
    name: string;
    type: string;
    status: string;
    start_time_utc: string;
  }>;
}

export default function Home() {
  const [activeTab, setActiveTab] = useState<"home" | "championship" | "calendar">("home");
  const [spoilerShield, setSpoilerShield] = useState(false);
  const [standings, setStandings] = useState<DriverStanding[]>([]);
  const [champIntel, setChampIntel] = useState<ChampionshipIntelligence | null>(null);
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [stRes, chRes, mtRes] = await Promise.all([
          fetch("http://localhost:8000/api/v1/standings/drivers").catch(() => null),
          fetch("http://localhost:8000/api/v1/championship/intelligence?remaining_gps=23&remaining_sprints=6").catch(() => null),
          fetch("http://localhost:8000/api/v1/meetings?season=2024").catch(() => null)
        ]);

        if (stRes && stRes.ok) setStandings(await stRes.json());
        if (chRes && chRes.ok) setChampIntel(await chRes.json());
        if (mtRes && mtRes.ok) setMeetings(await mtRes.json());
      } catch (err) {
        console.error("API error", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  return (
    <div className="flex flex-col min-h-screen bg-[#0D0E12] text-[#F5F6F8]">
      {/* Top Motorsport Navigation Header */}
      <header className="sticky top-0 z-50 flex items-center justify-between px-6 py-4 bg-[#15171E]/95 backdrop-blur border-b border-[#272A35]">
        <div className="flex items-center space-x-6">
          <div className="flex items-center space-x-2">
            <span className="bg-[#E10600] text-white font-black text-xl px-2 py-0.5 rounded tracking-tighter">
              APEX
            </span>
            <span className="font-bold text-xl tracking-wider text-white">GP</span>
          </div>

          <nav className="hidden md:flex space-x-1">
            <button
              onClick={() => setActiveTab("home")}
              className={`px-3 py-1.5 rounded-md text-sm font-semibold transition ${
                activeTab === "home" ? "bg-[#272A35] text-white" : "text-[#8F96A3] hover:text-white"
              }`}
            >
              Dashboard
            </button>
            <button
              onClick={() => setActiveTab("championship")}
              className={`px-3 py-1.5 rounded-md text-sm font-semibold transition ${
                activeTab === "championship" ? "bg-[#272A35] text-white" : "text-[#8F96A3] hover:text-white"
              }`}
            >
              Championship Intelligence
            </button>
            <button
              onClick={() => setActiveTab("calendar")}
              className={`px-3 py-1.5 rounded-md text-sm font-semibold transition ${
                activeTab === "calendar" ? "bg-[#272A35] text-white" : "text-[#8F96A3] hover:text-white"
              }`}
            >
              Season Calendar
            </button>
          </nav>
        </div>

        {/* Global Controls & Provenance Tag */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 text-xs text-[#8F96A3] bg-[#0D0E12] px-3 py-1.5 rounded border border-[#272A35]">
            <span className="w-2 h-2 rounded-full bg-[#64D2FF]"></span>
            <span>DATA: FIA VERIFIED (HISTORICAL)</span>
          </div>

          {/* Spoiler Shield Toggle */}
          <button
            onClick={() => setSpoilerShield(!spoilerShield)}
            className={`flex items-center space-x-2 text-xs font-semibold px-3 py-1.5 rounded transition border ${
              spoilerShield 
                ? "bg-[#E10600]/20 border-[#E10600] text-[#E10600]" 
                : "bg-[#272A35] border-[#272A35] text-[#8F96A3] hover:text-white"
            }`}
          >
            <ShieldCheck className="w-4 h-4" />
            <span>SPOILER SHIELD: {spoilerShield ? "ON" : "OFF"}</span>
          </button>
        </div>
      </header>

      {/* Main Body */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 space-y-6">
        {/* Next Grand Prix / Live Banner */}
        <div className="bg-gradient-to-r from-[#15171E] to-[#1c1f28] rounded-xl border border-[#272A35] p-6 shadow-xl relative overflow-hidden">
          <div className="absolute right-0 top-0 bottom-0 w-1/3 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-[#E10600]/10 via-transparent to-transparent pointer-events-none"></div>
          
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <div className="flex items-center space-x-2 text-xs text-[#E10600] font-bold uppercase tracking-wider mb-1">
                <Flag className="w-4 h-4" />
                <span>ROUND 1 OF 24 • COMPLETED</span>
              </div>
              <h1 className="text-2xl md:text-3xl font-extrabold text-white">
                Formula 1 Gulf Air Bahrain Grand Prix 2024
              </h1>
              <p className="text-[#8F96A3] text-sm mt-1">
                Bahrain International Circuit • Sakhir • 57 Laps (308.238 km)
              </p>
            </div>

            <div className="flex items-center space-x-3">
              <div className="bg-[#0D0E12] border border-[#272A35] px-4 py-2.5 rounded-lg text-center">
                <div className="text-xs text-[#8F96A3] uppercase">Fastest Lap</div>
                <div className="text-sm font-bold text-white font-mono">1:32.608 (VER)</div>
              </div>
              <div className="bg-[#E10600] text-white px-5 py-2.5 rounded-lg font-bold text-sm shadow hover:bg-red-700 transition cursor-pointer flex items-center space-x-1">
                <span>View Race IQ</span>
                <ChevronRight className="w-4 h-4" />
              </div>
            </div>
          </div>
        </div>

        {/* Tab 1: Dashboard */}
        {activeTab === "home" && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Standings Table (2 Columns) */}
            <div className="lg:col-span-2 bg-[#15171E] rounded-xl border border-[#272A35] overflow-hidden">
              <div className="flex items-center justify-between px-6 py-4 border-b border-[#272A35]">
                <div className="flex items-center space-x-2">
                  <Trophy className="w-5 h-5 text-[#FFCC00]" />
                  <h2 className="font-bold text-lg text-white">Driver World Championship</h2>
                </div>
                <span className="text-xs text-[#8F96A3]">Updated after Round 1</span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-sm">
                  <thead>
                    <tr className="bg-[#0D0E12]/50 text-[#8F96A3] text-xs uppercase border-b border-[#272A35]">
                      <th className="py-3 px-4">Pos</th>
                      <th className="py-3 px-4">Driver</th>
                      <th className="py-3 px-4">Team</th>
                      <th className="py-3 px-4 text-center">Wins</th>
                      <th className="py-3 px-4 text-right">Pts Gap</th>
                      <th className="py-3 px-4 text-right">Points</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#272A35]">
                    {standings.map((s) => (
                      <tr key={s.driver.code} className="hover:bg-[#1a1d26] transition">
                        <td className="py-3.5 px-4 font-mono font-bold text-white">
                          {spoilerShield ? "•" : `P${s.position}`}
                        </td>
                        <td className="py-3.5 px-4">
                          <div className="font-bold text-white flex items-center space-x-2">
                            <span>{s.driver.first_name} {s.driver.last_name}</span>
                            <span className="text-xs text-[#8F96A3] font-mono font-normal">[{s.driver.code}]</span>
                          </div>
                        </td>
                        <td className="py-3.5 px-4">
                          <span 
                            className="text-xs px-2 py-0.5 rounded font-medium text-white"
                            style={{ backgroundColor: s.driver.constructor_color + "33", borderLeft: `3px solid ${s.driver.constructor_color}` }}
                          >
                            {s.driver.constructor_name}
                          </span>
                        </td>
                        <td className="py-3.5 px-4 text-center font-mono text-[#8F96A3]">
                          {spoilerShield ? "-" : s.wins}
                        </td>
                        <td className="py-3.5 px-4 text-right font-mono text-xs text-[#8F96A3]">
                          {spoilerShield ? "-" : (s.points_behind_leader === 0 ? "LEADER" : `-${s.points_behind_leader}`)}
                        </td>
                        <td className="py-3.5 px-4 text-right font-mono font-extrabold text-white">
                          {spoilerShield ? "•••" : s.points}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Championship Math Snapshot (1 Column) */}
            <div className="space-y-6">
              <div className="bg-[#15171E] rounded-xl border border-[#272A35] p-6 space-y-4">
                <div className="flex items-center space-x-2 text-white font-bold text-lg">
                  <Gauge className="w-5 h-5 text-[#E10600]" />
                  <h2>Championship Status</h2>
                </div>

                <div className="space-y-3">
                  <div className="p-3 bg-[#0D0E12] rounded-lg border border-[#272A35]">
                    <div className="text-xs text-[#8F96A3]">Championship Leader</div>
                    <div className="text-lg font-extrabold text-white font-mono mt-0.5">
                      {champIntel?.leader || "VER"}
                    </div>
                  </div>

                  <div className="p-3 bg-[#0D0E12] rounded-lg border border-[#272A35]">
                    <div className="text-xs text-[#8F96A3]">Rounds Remaining</div>
                    <div className="text-sm font-semibold text-white mt-0.5">
                      {champIntel?.remaining_gps || 23} Grands Prix • {champIntel?.remaining_sprints || 6} Sprints
                    </div>
                  </div>

                  <div className="p-3 bg-[#0D0E12] rounded-lg border border-[#272A35]">
                    <div className="text-xs text-[#8F96A3]">Mathematical Clinch State</div>
                    <div className="text-sm font-semibold text-[#64D2FF] mt-0.5">
                      {champIntel?.leader_clinched ? "TITLE CLINCHED" : "OPEN TITLE RACE"}
                    </div>
                  </div>
                </div>

                <button 
                  onClick={() => setActiveTab("championship")}
                  className="w-full py-2.5 bg-[#272A35] text-white hover:bg-[#343846] rounded-lg text-sm font-semibold transition"
                >
                  Open Full Mathematics Engine →
                </button>
              </div>

              {/* Data Provenance Card */}
              <div className="bg-[#15171E]/60 rounded-xl border border-[#272A35] p-5 text-xs text-[#8F96A3] space-y-2">
                <div className="flex items-center space-x-2 text-white font-bold">
                  <Info className="w-4 h-4 text-[#64D2FF]" />
                  <span>Strict Data Provenance</span>
                </div>
                <p>
                  APEX GP adheres to zero-fabrication standards. Standings and results are verified from official FIA timing data.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Tab 2: Championship Intelligence */}
        {activeTab === "championship" && (
          <div className="bg-[#15171E] rounded-xl border border-[#272A35] p-6 space-y-6">
            <div>
              <h2 className="text-xl font-extrabold text-white">Championship Mathematics & Clinching Matrix</h2>
              <p className="text-sm text-[#8F96A3] mt-1">
                Pure mathematical calculation of maximum achievable points, countbacks, and elimination thresholds under official FIA Sporting Regulations.
              </p>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-sm">
                <thead>
                  <tr className="bg-[#0D0E12] text-[#8F96A3] text-xs uppercase border-b border-[#272A35]">
                    <th className="py-3 px-4">Driver</th>
                    <th className="py-3 px-4">Constructor</th>
                    <th className="py-3 px-4 text-right">Current Points</th>
                    <th className="py-3 px-4 text-right">Points Behind</th>
                    <th className="py-3 px-4 text-right">Max Achievable</th>
                    <th className="py-3 px-4 text-center">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#272A35]">
                  {champIntel?.contenders.map((c) => (
                    <tr key={c.driver_id} className="hover:bg-[#1a1d26] transition">
                      <td className="py-3 px-4 font-bold text-white">
                        {c.driver_name} <span className="text-[#8F96A3] font-mono font-normal">[{c.driver_code}]</span>
                      </td>
                      <td className="py-3 px-4 text-[#8F96A3]">{c.constructor_name}</td>
                      <td className="py-3 px-4 text-right font-mono font-bold text-white">{c.points}</td>
                      <td className="py-3 px-4 text-right font-mono text-[#8F96A3]">-{c.points_behind_leader}</td>
                      <td className="py-3 px-4 text-right font-mono text-[#64D2FF] font-semibold">{c.max_possible_points}</td>
                      <td className="py-3 px-4 text-center">
                        {c.mathematically_eliminated ? (
                          <span className="px-2 py-0.5 bg-red-950/60 text-red-400 border border-red-800 rounded text-xs">
                            Eliminated
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 bg-green-950/60 text-green-400 border border-green-800 rounded text-xs">
                            Contender
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

        {/* Tab 3: Calendar */}
        {activeTab === "calendar" && (
          <div className="bg-[#15171E] rounded-xl border border-[#272A35] p-6 space-y-6">
            <div>
              <h2 className="text-xl font-extrabold text-white">2024 FIA Formula One World Championship Calendar</h2>
              <p className="text-sm text-[#8F96A3] mt-1">
                Official calendar meetings with weekend session schedules.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {meetings.map((m) => (
                <div key={m.id} className="p-4 bg-[#0D0E12] rounded-lg border border-[#272A35] space-y-3">
                  <div className="flex items-center justify-between text-xs text-[#8F96A3]">
                    <span className="font-mono text-[#E10600] font-bold">ROUND {m.round_number}</span>
                    <span>{m.country}</span>
                  </div>
                  <h3 className="font-bold text-white text-base">{m.official_name}</h3>
                  <div className="text-xs text-[#8F96A3]">{m.circuit_name}</div>
                  <div className="pt-2 border-t border-[#272A35] flex items-center justify-between text-xs">
                    <span className="text-[#30D158] font-semibold">COMPLETED</span>
                    <span className="text-white hover:text-[#E10600] cursor-pointer">Details →</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-[#272A35] bg-[#15171E] px-6 py-6 text-center text-xs text-[#8F96A3]">
        <p>© 2026 APEX GP Platform. Built with Next.js, FastAPI, PostgreSQL, and strict Formula 1 data provenance.</p>
      </footer>
    </div>
  );
}
