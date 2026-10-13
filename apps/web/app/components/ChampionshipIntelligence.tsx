"use client";

import React, { useState, useEffect } from "react";
import { 
  Trophy, Calculator, ShieldAlert, Award, ChevronRight, 
  HelpCircle, CheckCircle2, XCircle, ArrowRight, Gauge, Info
} from "lucide-react";

interface Contender {
  driver_id: string;
  driver_name: string;
  driver_code: string;
  constructor_name: string;
  points: number;
  points_behind_leader: number;
  max_possible_points: number;
  mathematically_eliminated: boolean;
  can_clinch_next?: boolean;
}

interface ScenarioData {
  status: string;
  season: number;
  target: {
    driver_code: string;
    driver_name: string;
    constructor_name: string;
    current_points: number;
    current_position: number;
  };
  rival: {
    driver_code: string;
    driver_name: string;
    constructor_name: string;
    current_points: number;
    current_position: number;
  };
  calculation: {
    target_driver: string;
    target_points: number;
    rival_driver: string;
    rival_points: number;
    point_gap: number;
    remaining_gps: number;
    remaining_sprints: number;
    max_remaining_capacity: number;
    max_possible_target_points: number;
    is_eliminated: boolean;
    clinched_now: boolean;
    min_points_needed_if_rival_zero: number | null;
    min_points_to_clinch?: number | null;
    max_rival_points_allowed: number;
    countback_tie_advantage: boolean;
    scenarios: Array<{
      name: string;
      description: string;
      target_score: number;
      rival_max_allowed: number;
      clinch_feasible: boolean;
    }>;
  };
  provenance: {
    source: string;
    retrieved_at: string;
    data_state: string;
    notes: string;
  };
}

interface Props {
  spoilerShield: boolean;
}

export default function ChampionshipIntelligenceView({ spoilerShield }: Props) {
  const [contenders, setContenders] = useState<Contender[]>([]);
  const [selectedDriver, setSelectedDriver] = useState<string>("PER");
  const [selectedRival, setSelectedRival] = useState<string>("VER");
  const [scenarioData, setScenarioData] = useState<ScenarioData | null>(null);
  const [remainingGps, setRemainingGps] = useState<number>(23);
  const [remainingSprints, setRemainingSprints] = useState<number>(6);
  const [loading, setLoading] = useState<boolean>(true);
  const [calculating, setCalculating] = useState<boolean>(false);

  // Load baseline intelligence
  useEffect(() => {
    fetch(`http://localhost:8000/api/v1/championship/intelligence?remaining_gps=${remainingGps}&remaining_sprints=${remainingSprints}`)
      .then((res) => res.json())
      .then((data) => {
        if (data.contenders) {
          setContenders(data.contenders);
          if (data.contenders.length > 1 && selectedDriver === "PER") {
            // Default: P2 driver vs P1 driver
            setSelectedDriver(data.contenders[1]?.driver_code || "PER");
            setSelectedRival(data.contenders[0]?.driver_code || "VER");
          }
        }
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [remainingGps, remainingSprints]);

  // Load calculator scenario for selected driver and rival
  useEffect(() => {
    if (!selectedDriver) return;
    setCalculating(true);
    const rivalParam = selectedRival ? `&rival_code=${selectedRival}` : "";
    fetch(
      `http://localhost:8000/api/v1/championship/calculator?driver_code=${selectedDriver}${rivalParam}&remaining_gps=${remainingGps}&remaining_sprints=${remainingSprints}`
    )
      .then((res) => res.json())
      .then((data) => {
        if (data.status === "SUCCESS") {
          setScenarioData(data);
        }
        setCalculating(false);
      })
      .catch(() => setCalculating(false));
  }, [selectedDriver, selectedRival, remainingGps, remainingSprints]);

  // URL Syncing & Shareable Scenario Link (E3-02)
  const [copiedLink, setCopiedLink] = useState(false);
  useEffect(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      const urlDriver = params.get("driver")?.trim().toUpperCase();
      const urlRival = params.get("rival")?.trim().toUpperCase();
      // Validate sanitized 2-4 char alphanumeric driver codes
      if (urlDriver && /^[A-Z0-9]{2,4}$/.test(urlDriver)) {
        setSelectedDriver(urlDriver);
      }
      if (urlRival && /^[A-Z0-9]{2,4}$/.test(urlRival)) {
        setSelectedRival(urlRival);
      }
    }
  }, []);

  const handleShareLink = () => {
    if (typeof window !== "undefined") {
      const url = `${window.location.origin}${window.location.pathname}?tab=championship&driver=${selectedDriver}&rival=${selectedRival}`;
      navigator.clipboard.writeText(url);
      setCopiedLink(true);
      setTimeout(() => setCopiedLink(false), 2500);
    }
  };

  // Monte Carlo Simulation State (E4-01, E4-02)
  const [simulationData, setSimulationData] = useState<any>(null);
  const [simulating, setSimulating] = useState(false);

  const runSimulation = (runs: number = 1000) => {
    setSimulating(true);
    fetch(`http://localhost:8000/api/v1/championship/simulate?iterations=${runs}&remaining_gps=${remainingGps}&remaining_sprints=${remainingSprints}`)
      .then((res) => res.json())
      .then((data) => {
        setSimulationData(data);
        setSimulating(false);
      })
      .catch(() => setSimulating(false));
  };

  const calc = scenarioData?.calculation;

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="bg-[#15171E] rounded-xl border border-[#272A35] p-6 shadow-lg">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 text-xs text-[#FFCC00] font-bold uppercase tracking-wider mb-1">
              <Trophy className="w-4 h-4" />
              <span>FIA SPORTING REGULATIONS MATHEMATICS</span>
            </div>
            <h2 className="text-2xl font-black text-white">Championship Intelligence & Scenario Engine</h2>
            <p className="text-sm text-[#8F96A3] mt-1 max-w-2xl">
              Pure mathematical evaluation of clinch thresholds, mathematical elimination, rival point allowances, and Monte Carlo stochastic probabilities under official FIA Sporting Regulations.
            </p>
          </div>

          <div className="flex items-center space-x-3">
            {/* Share Scenario Button (E3-02) */}
            <button
              onClick={handleShareLink}
              className="flex items-center space-x-1.5 px-3 py-2 bg-[#272A35] hover:bg-[#E10600] text-white rounded-lg text-xs font-bold transition cursor-pointer"
            >
              <Info className="w-4 h-4" />
              <span>{copiedLink ? "Link Copied!" : "Share Scenario URL"}</span>
            </button>

            {/* Quick Round Configuration */}
            <div className="flex items-center space-x-3 bg-[#0D0E12] border border-[#272A35] p-2.5 rounded-lg text-xs">
              <div>
                <span className="text-[#8F96A3] block">Remaining GPs:</span>
                <span className="font-mono font-bold text-white text-sm">{remainingGps}</span>
              </div>
              <div className="h-6 w-[1px] bg-[#272A35]" />
              <div>
                <span className="text-[#8F96A3] block">Remaining Sprints:</span>
                <span className="font-mono font-bold text-white text-sm">{remainingSprints}</span>
              </div>
              <div className="h-6 w-[1px] bg-[#272A35]" />
              <div>
                <span className="text-[#8F96A3] block">Max Available Pts:</span>
                <span className="font-mono font-bold text-[#64D2FF] text-sm">
                  {calc?.max_remaining_capacity ?? remainingGps * 26 + remainingSprints * 8}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Interactive Scenario Calculator: "What does this driver need to win?" */}
      <div className="bg-gradient-to-br from-[#15171E] to-[#1a1d26] rounded-xl border border-[#272A35] p-6 shadow-xl relative overflow-hidden">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2 text-white font-bold text-lg">
            <Calculator className="w-5 h-5 text-[#E10600]" />
            <h3>Interactive Scenario Calculator: What Does This Driver Need to Win?</h3>
          </div>
          <button
            onClick={() => runSimulation(1000)}
            disabled={simulating}
            className="flex items-center space-x-1.5 px-3.5 py-1.5 bg-[#E10600] hover:bg-red-700 disabled:opacity-50 text-white rounded-lg text-xs font-bold transition shadow cursor-pointer"
          >
            <Gauge className="w-4 h-4" />
            <span>{simulating ? "Simulating 1,000 Seasons..." : "Run Monte Carlo Sim (1,000x)"}</span>
          </button>
        </div>


        {/* Contender & Rival Selection Controls */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div>
            <label className="block text-xs uppercase tracking-wider text-[#8F96A3] font-bold mb-2">
              Select Contender
            </label>
            <select
              value={selectedDriver}
              onChange={(e) => setSelectedDriver(e.target.value)}
              className="w-full bg-[#0D0E12] border border-[#272A35] rounded-lg px-3 py-2 text-white font-medium focus:outline-none focus:border-[#E10600] transition"
            >
              {contenders.map((c) => (
                <option key={c.driver_code} value={c.driver_code}>
                  {c.driver_name} ({c.driver_code}) — {c.points} pts
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs uppercase tracking-wider text-[#8F96A3] font-bold mb-2">
              Compare Against Rival
            </label>
            <select
              value={selectedRival}
              onChange={(e) => setSelectedRival(e.target.value)}
              className="w-full bg-[#0D0E12] border border-[#272A35] rounded-lg px-3 py-2 text-white font-medium focus:outline-none focus:border-[#E10600] transition"
            >
              {contenders.map((c) => (
                <option key={c.driver_code} value={c.driver_code} disabled={c.driver_code === selectedDriver}>
                  {c.driver_name} ({c.driver_code}) — {c.points} pts
                </option>
              ))}
            </select>
          </div>

          {/* Quick Stats Pill 1 */}
          <div className="bg-[#0D0E12] border border-[#272A35] rounded-lg p-3 flex flex-col justify-center">
            <span className="text-xs text-[#8F96A3] uppercase">Point Gap</span>
            <div className="flex items-baseline space-x-2 mt-0.5">
              <span className={`text-xl font-mono font-extrabold ${calc && calc.point_gap > 0 ? "text-red-400" : calc && calc.point_gap < 0 ? "text-green-400" : "text-white"}`}>
                {calc ? (spoilerShield ? "••" : (calc.point_gap > 0 ? `-${calc.point_gap}` : `+${Math.abs(calc.point_gap)}`)) : "-"}
              </span>
              <span className="text-xs text-[#8F96A3]">PTS</span>
            </div>
          </div>

          {/* Quick Stats Pill 2 */}
          <div className="bg-[#0D0E12] border border-[#272A35] rounded-lg p-3 flex flex-col justify-center">
            <span className="text-xs text-[#8F96A3] uppercase">Mathematical Status</span>
            <div className="mt-0.5">
              {calc?.is_eliminated ? (
                <span className="inline-flex items-center text-xs font-bold text-red-400 bg-red-950/60 border border-red-800/80 px-2 py-0.5 rounded">
                  <XCircle className="w-3.5 h-3.5 mr-1" /> Eliminated
                </span>
              ) : calc?.clinched_now ? (
                <span className="inline-flex items-center text-xs font-bold text-yellow-400 bg-yellow-950/60 border border-yellow-800/80 px-2 py-0.5 rounded">
                  <Award className="w-3.5 h-3.5 mr-1" /> Champion Clinched
                </span>
              ) : (
                <span className="inline-flex items-center text-xs font-bold text-green-400 bg-green-950/60 border border-green-800/80 px-2 py-0.5 rounded">
                  <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Title Eligible
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Calculated Results Card */}
        {calc && (
          <div className="bg-[#0D0E12] rounded-xl border border-[#272A35] p-5 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="border-r border-[#272A35]/60 pr-4">
                <span className="text-xs text-[#8F96A3] block uppercase">
                  {calc.point_gap < 0 ? "Min Pts to Clinch Title" : "Min Pts Needed (Rival = 0)"}
                </span>
                <span className="text-2xl font-mono font-bold text-[#64D2FF] mt-1 block">
                  {calc.point_gap < 0 && calc.min_points_to_clinch !== undefined && calc.min_points_to_clinch !== null
                    ? `${calc.min_points_to_clinch} pts`
                    : (calc.min_points_needed_if_rival_zero !== null ? `${calc.min_points_needed_if_rival_zero} pts` : "N/A")}
                </span>
                <span className="text-xs text-[#8F96A3] mt-1 block">
                  {calc.point_gap < 0
                    ? `Points required to mathematically clinch over ${calc.rival_driver} irrespective of rival finishes.`
                    : `Points required to surpass ${calc.rival_driver} if rival scores zero.`}
                </span>
              </div>

              <div className="border-r border-[#272A35]/60 pr-4">
                <span className="text-xs text-[#8F96A3] block uppercase">Rival Maximum Allowed</span>
                <span className="text-2xl font-mono font-bold text-amber-400 mt-1 block">
                  {calc.max_rival_points_allowed} pts
                </span>
                <span className="text-xs text-[#8F96A3] mt-1 block">
                  Max points {calc.rival_driver} can score before {calc.target_driver} is mathematically locked out.
                </span>
              </div>

              <div>
                <span className="text-xs text-[#8F96A3] block uppercase">FIA Countback Advantage</span>
                <span className="text-sm font-semibold text-white mt-1 block flex items-center space-x-1.5">
                  {calc.countback_tie_advantage ? (
                    <span className="text-green-400 flex items-center">
                      <CheckCircle2 className="w-4 h-4 mr-1" /> Wins countback on ties
                    </span>
                  ) : (
                    <span className="text-[#8F96A3]">Rival holds or leads tie-break</span>
                  )}
                </span>
                <span className="text-xs text-[#8F96A3] mt-1 block">
                  Evaluated using statutory race finishing position hierarchy.
                </span>
              </div>
            </div>

            {/* Feasible Scenarios Table */}
            {calc.scenarios && calc.scenarios.length > 0 && (
              <div className="mt-4 pt-4 border-t border-[#272A35]">
                <h4 className="text-xs font-bold uppercase text-[#8F96A3] tracking-wider mb-3">
                  Mathematically Verified Pathways for [{calc.target_driver}] to Win:
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {calc.scenarios.map((sc, idx) => (
                    <div key={idx} className="bg-[#15171E] border border-[#272A35] rounded-lg p-3.5 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-bold text-white">{sc.name}</span>
                        {sc.clinch_feasible ? (
                          <span className="text-[11px] px-2 py-0.5 rounded bg-green-950/60 text-green-400 border border-green-800">
                            Achievable
                          </span>
                        ) : (
                          <span className="text-[11px] px-2 py-0.5 rounded bg-red-950/60 text-red-400 border border-red-800">
                            Requires Rival Drop
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-[#8F96A3]">{sc.description}</p>
                      <div className="flex items-center justify-between text-xs font-mono pt-1 border-t border-[#272A35]/50">
                        <span className="text-[#64D2FF]">Target Score: +{sc.target_score} pts</span>
                        <span className="text-amber-400">Rival Cap: ≤ {sc.rival_max_allowed} pts</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Monte Carlo Simulation Probability Results (E4-01, E4-02, E5-01) */}
        {simulationData && (
          <div className="mt-5 pt-5 border-t border-[#272A35] bg-[#0D0E12] rounded-xl p-5 border">
            <div className="flex items-center justify-between mb-3">
              <div>
                <span className="text-xs uppercase font-mono tracking-wider text-[#FFCC00] font-bold">
                  STOCHASTIC GAUSSIAN SIMULATION
                </span>
                <h4 className="text-white font-bold text-base">
                  Monte Carlo Season Forecast ({simulationData.iterations.toLocaleString()} Runs)
                </h4>
              </div>
              <span className="text-xs text-[#8F96A3] font-mono">
                Model: Pace-Weighted Stochastic
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-[#15171E] text-[#8F96A3] uppercase border-b border-[#272A35]">
                    <th className="py-2.5 px-3">Driver</th>
                    <th className="py-2.5 px-3">Current Pts</th>
                    <th className="py-2.5 px-3 text-right">Expected Total Pts</th>
                    <th className="py-2.5 px-3 text-right">Expected Wins</th>
                    <th className="py-2.5 px-3 text-right">Title Probability</th>
                    <th className="py-2.5 px-3 text-center">Probability Bar</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#272A35]/60 font-mono">
                  {simulationData.probabilities.map((p: any) => (
                    <tr key={p.driver_code} className="hover:bg-[#1a1d26]">
                      <td className="py-2 px-3 font-sans font-bold text-white flex items-center space-x-1.5">
                        <span>{p.driver_name}</span>
                        <span className="text-[#8F96A3] text-[11px] font-mono">[{p.driver_code}]</span>
                      </td>
                      <td className="py-2 px-3 text-[#8F96A3]">{p.current_points}</td>
                      <td className="py-2 px-3 text-right text-white font-bold">{p.expected_final_points}</td>
                      <td className="py-2 px-3 text-right text-[#8F96A3]">{p.expected_total_wins}</td>
                      <td className="py-2 px-3 text-right font-bold text-[#64D2FF]">
                        {p.championship_probability_pct}%
                      </td>
                      <td className="py-2 px-3">
                        <div className="w-24 bg-[#15171E] rounded-full h-2 mx-auto overflow-hidden border border-[#272A35]">
                          <div
                            className="bg-[#E10600] h-full rounded-full"
                            style={{ width: `${Math.min(100, Math.max(0, p.championship_probability_pct))}%` }}
                          />
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Provenance & Forecast Transparency Note */}
            <div className="mt-3 pt-3 border-t border-[#272A35]/60 flex flex-col sm:flex-row items-start sm:items-center justify-between text-[11px] text-[#8F96A3] gap-2">
              <div className="flex items-center space-x-1.5">
                <Info className="w-3.5 h-3.5 text-[#64D2FF]" />
                <span>
                  <strong>Stochastic Forecast Notice:</strong> Simulated distributions are probabilistic model forecasts based on current season standings, calibrated pace weights, and 7.5% baseline DNF rate. Not guaranteed or verified race outcomes.
                </span>
              </div>
              <span className="font-mono text-[#64D2FF] shrink-0">
                PROVENANCE: {simulationData?.provenance?.source || "APEX_GP_MONTE_CARLO_SIMULATOR"}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Contenders Table */}

      <div className="bg-[#15171E] rounded-xl border border-[#272A35] overflow-hidden shadow-lg">
        <div className="px-6 py-4 border-b border-[#272A35] flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Trophy className="w-5 h-5 text-[#FFCC00]" />
            <h3 className="font-bold text-lg text-white">Full Contender Roster & Elimination Status</h3>
          </div>
          <span className="text-xs text-[#8F96A3]">Sorted by Current Championship Order</span>
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
                <th className="py-3 px-4 text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#272A35]">
              {contenders.map((c) => (
                <tr key={c.driver_code} className={`hover:bg-[#1a1d26] transition ${selectedDriver === c.driver_code ? "bg-[#1a1d26]/60 border-l-2 border-l-[#E10600]" : ""}`}>
                  <td className="py-3.5 px-4 font-bold text-white flex items-center space-x-2">
                    <span>{c.driver_name}</span>
                    <span className="text-xs text-[#8F96A3] font-mono font-normal">[{c.driver_code}]</span>
                  </td>
                  <td className="py-3.5 px-4 text-[#8F96A3]">{c.constructor_name}</td>
                  <td className="py-3.5 px-4 text-right font-mono font-bold text-white">
                    {spoilerShield ? "••" : c.points}
                  </td>
                  <td className="py-3.5 px-4 text-right font-mono text-[#8F96A3]">
                    {spoilerShield ? "-" : `-${c.points_behind_leader}`}
                  </td>
                  <td className="py-3.5 px-4 text-right font-mono text-[#64D2FF] font-semibold">
                    {spoilerShield ? "•••" : c.max_possible_points}
                  </td>
                  <td className="py-3.5 px-4 text-center">
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
                  <td className="py-3.5 px-4 text-center">
                    <button
                      onClick={() => setSelectedDriver(c.driver_code)}
                      className="text-xs font-semibold px-2.5 py-1 rounded bg-[#272A35] hover:bg-[#E10600] text-white transition cursor-pointer"
                    >
                      Calculate
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
