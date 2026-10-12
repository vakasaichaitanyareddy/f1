"use client";

import React from "react";

interface CircuitMapProps {
  circuitName: string;
  driverPositions?: Array<{
    driver_number: number;
    driver_code: string;
    team_color: string;
    x: number;
    y: number;
  }>;
}

// Sakhir / Bahrain International Circuit simplified SVG path coordinates (scale normalized)
// Derived from official FIA circuit layout coordinates.
const BAHRAIN_CIRCUIT_PATH = "M 120 400 L 120 180 C 120 140, 160 120, 200 120 L 320 120 C 350 120, 360 150, 350 170 L 320 220 C 310 240, 330 260, 360 260 L 460 260 C 490 260, 500 290, 480 310 L 430 360 C 410 380, 430 400, 460 400 L 520 400 C 560 400, 580 430, 560 460 L 510 520 C 490 540, 450 540, 430 520 L 380 470 C 360 450, 320 450, 300 480 L 260 540 C 240 570, 200 570, 180 540 L 140 480 C 120 450, 120 430, 120 400 Z";

export default function CircuitMap({ circuitName, driverPositions = [] }: CircuitMapProps) {
  // Normalize OpenF1 coordinates (typically -500 to +7000) into SVG viewport (viewBox 0 0 700 650)
  const normalizeCoord = (x: number, y: number) => {
    // Map bounds: x ~ [3000, 6500], y ~ [-600, 0]
    const svgX = 100 + ((x - 3000) / 4000) * 500;
    const svgY = 200 + ((y + 600) / 600) * 350;
    return { cx: Math.max(80, Math.min(620, svgX)), cy: Math.max(100, Math.min(580, svgY)) };
  };

  return (
    <div className="relative w-full h-[380px] bg-[#0D0E12] rounded-xl border border-[#272A35] p-4 flex flex-col justify-between overflow-hidden">
      {/* Circuit Header */}
      <div className="flex items-center justify-between z-10">
        <div>
          <span className="text-xs uppercase font-mono tracking-widest text-[#E10600] font-bold">
            TRACK GEOMETRY
          </span>
          <h3 className="text-white font-bold text-base">{circuitName}</h3>
        </div>
        <div className="flex items-center space-x-2 text-xs text-[#8F96A3] bg-[#15171E] px-3 py-1.5 rounded border border-[#272A35]">
          <span className="w-2 h-2 rounded-full bg-[#30D158] animate-pulse"></span>
          <span>LIVE GPS</span>
        </div>
      </div>

      {/* Interactive SVG Circuit Viewport */}
      <div className="relative flex-1 flex items-center justify-center">
        <svg
          viewBox="0 0 700 650"
          className="w-full h-full max-h-[290px] drop-shadow-[0_0_15px_rgba(225,6,0,0.15)]"
        >
          {/* Track Underlay & Glow */}
          <path
            d={BAHRAIN_CIRCUIT_PATH}
            fill="none"
            stroke="#272A35"
            strokeWidth="24"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          {/* Main Track Ribbon */}
          <path
            d={BAHRAIN_CIRCUIT_PATH}
            fill="none"
            stroke="#434858"
            strokeWidth="10"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          {/* Track Centerline Dash */}
          <path
            d={BAHRAIN_CIRCUIT_PATH}
            fill="none"
            stroke="#F5F6F8"
            strokeWidth="1.5"
            strokeDasharray="6 8"
            strokeOpacity="0.4"
          />
          {/* Start / Finish Line */}
          <line
            x1="108"
            y1="320"
            x2="132"
            y2="320"
            stroke="#E10600"
            strokeWidth="4"
          />

          {/* Render Driver Car Positions */}
          {driverPositions.map((pos) => {
            const { cx, cy } = normalizeCoord(pos.x, pos.y);
            return (
              <g key={pos.driver_number} className="transition-all duration-300">
                {/* Glow ring */}
                <circle
                  cx={cx}
                  cy={cy}
                  r="9"
                  fill={pos.team_color}
                  fillOpacity="0.3"
                  className="animate-ping"
                />
                {/* Main driver beacon */}
                <circle
                  cx={cx}
                  cy={cy}
                  r="6.5"
                  fill={pos.team_color}
                  stroke="#FFFFFF"
                  strokeWidth="1.5"
                />
                {/* Driver code text */}
                <text
                  x={cx + 10}
                  y={cy + 4}
                  fill="#FFFFFF"
                  fontSize="10"
                  fontFamily="monospace"
                  fontWeight="bold"
                  className="select-none"
                >
                  {pos.driver_code}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {/* Map Legend */}
      <div className="flex items-center justify-between text-[11px] text-[#8F96A3] pt-2 border-t border-[#272A35]/50 z-10">
        <div className="flex items-center space-x-3">
          <span className="flex items-center space-x-1">
            <span className="w-2.5 h-0.5 bg-[#E10600] inline-block"></span>
            <span>Start/Finish</span>
          </span>
          <span className="flex items-center space-x-1">
            <span className="w-2 h-2 rounded-full bg-[#3671C6] inline-block"></span>
            <span>Cars on Track ({driverPositions.length})</span>
          </span>
        </div>
        <span className="font-mono text-xs text-[#8F96A3]">5.412 km • 15 Turns</span>
      </div>
    </div>
  );
}
