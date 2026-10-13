/**
 * APEX GP — Design Tokens
 * Formula 1 Motorsport System Colors, Compounds, and Semantic Badges
 */

export const colors = {
  // Brand
  apexRed: '#E10600',       // Official motorsport red accent
  apexDark: '#0D0E12',      // Deep tarmac black
  apexCharcoal: '#15171E',  // Card and surface dark
  apexBorder: '#272A35',    // High-contrast subtle boundary
  apexMuted: '#8F96A3',     // Secondary reading contrast
  apexText: '#F5F6F8',      // Crisp white text

  // Tire Compounds
  tires: {
    soft: '#FF3B30',        // Red
    medium: '#FFCC00',      // Yellow
    hard: '#FFFFFF',        // White
    intermediate: '#34C759',// Green
    wet: '#007AFF',         // Blue
    unknown: '#8E8E93',
  },

  // Flags & Track Status
  trackStatus: {
    green: '#30D158',
    yellow: '#FFD60A',
    safetyCar: '#FF9F0A',
    vsc: '#FF9F0A',
    red: '#FF453A',
    chequered: '#FFFFFF',
  },

  // Provenance / Data State
  provenance: {
    live: '#30D158',
    delayed: '#FF9F0A',
    stale: '#FF453A',
    historical: '#64D2FF',
    unavailable: '#8E8E93',
  },

  // Formula 1 Constructors (2024/2026 Grid)
  constructors: {
    red_bull: '#3671C6',
    ferrari: '#E80020',
    mclaren: '#FF8000',
    mercedes: '#27F4D2',
    aston_martin: '#229971',
    alpine: '#0093CC',
    williams: '#64C4FF',
    rb: '#6692FF',
    sauber: '#52E252',
    haas: '#B6BABD',
  }
};

export const typography = {
  fontFamily: {
    display: ['Formula1', 'system-ui', 'sans-serif'],
    sans: ['Inter', 'system-ui', 'sans-serif'],
    mono: ['JetBrains Mono', 'monospace'],
  }
};
