# APEX GP — Private Friends-Only Beta & Release Plan

## Beta Schedule (4 Weeks)
- **Week 1: Functional Correctness**
  - Verify Web navigation, dark mode, responsive tables, countdown timers.
  - Verify Drivers, Constructors, Calendar, Standings, and historical results.
  - Test authentication and user preference persistence.
- **Week 2: Reliability & Error Handling**
  - Simulate provider downtime and verify fallback banners ("Historical/Unavailable").
  - Test data provenance displays and verify no fabricated entries exist.
  - Verify database migrations and Redis caching invalidation.
- **Week 3: Race-Weekend Simulation & Telemetry Stress**
  - Live timing replay and high-frequency WebSocket connection load test.
  - Reconnect test under packet drop.
  - Championship clinching calculation verification against FIA official rulings.
- **Week 4: Release Candidate Hardening**
  - WCAG AA contrast accessibility verification.
  - Security audit and zero-leak confirmation on secrets.
  - Public launch decision gate.
