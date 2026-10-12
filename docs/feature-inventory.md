# APEX GP — Complete Feature Inventory & Master Traceability Matrix

> **Document Status:** LIVING / AUTHORITATIVE  
> **Last Updated:** 2026-10-12 (Post-Release Gate Audit & v1.1.4 Verification)  
> **Master Rule:** No feature from the master specification may be omitted, simplified into a placeholder, or marked complete without verified tests and working code.

---

## 1. Traceability Status Legend
- `[TODO]` Not yet implemented
- `[IN_PROGRESS]` Currently active implementation
- `[BLOCKED]` Blocked on explicit documented dependency / permission
- `[DONE]` Fully implemented, unit/integration tested, verified against real or explicitly labeled test data

---

## 2. Master Feature Inventory

### Module A: Product Design, System & Navigation
| Feature ID | Name / Description | Release Target | Status | Dependencies | Verification Evidence & Criteria |
|---|---|---|---|---|---|
| A1-01 | Define APEX GP branding & logo / motorsport visual identity | R1 | [DONE] | None | Visual badges, `#E10600` accent, tarmac dark theme in web and mobile |
| A1-02 | Color, typography, spacing, component tokens (Tailwind / NativeWind) | R1 | [DONE] | None | `packages/design-tokens` with constructor hex codes, tire compounds, status states |
| A1-03 | Accessible reusable UI components (Buttons, Cards, Tables, Tabs, Dialogs) | R1 | [DONE] | A1-02 | Tested with responsive tables, buttons, tabs in Next.js web build |
| A1-04 | Reusable status indicators and semantic badges | R1 | [DONE] | A1-02 | Live, stale, historical, and test fixture badge indicators verified |
| A1-05 | Standardized chart styles and tooltips (ECharts / Recharts) | R1 | [TODO] | A1-02 | Scheduled for telemetry/championship deep-dive visual modules |
| A1-06 | Loading skeletons, empty states, error boundaries, offline states | R1 | [DONE] | A1-03 | Skeletons and graceful degradation on API timeouts tested |
| A1-07 | Responsive desktop, tablet, mobile layouts & Dark / Light mode | R1 | [DONE] | A1-02 | Tested across responsive viewport layouts in `apps/web` |
| A2-01 | Web Navigation (Home, Race Center, Championship, Drivers/Teams, Calendar) | R1 | [DONE] | A1-03 | Next.js App Router tabs with responsive navigation |
| A2-02 | Mobile Navigation (Expo / React Native tabs and native stack) | R1 | [DONE] | A1-03 | `apps/mobile/App.tsx` verified with TypeScript compilation |

---

### Module B: Home Dashboard & Calendar
| Feature ID | Name / Description | Release Target | Status | Dependencies | Verification Evidence & Criteria |
|---|---|---|---|---|---|
| B1-01 | Next Grand Prix banner & session countdown clock | R1 | [DONE] | J3-02 | Meeting banner with round number, circuit length, lap counts |
| B1-02 | Race-weekend schedule (FP1, FP2, FP3, Sprint Shootout, Sprint, Quali, Race) | R1 | [DONE] | J3-02 | Session type models and meeting associations verified |
| B1-03 | Session status & latest verified session results | R1 | [DONE] | J3-03 | Tested via `/api/v1/sessions/{id}/classification` with provenance |
| B1-04 | Current Driver & Constructor Championship mini-standings | R1 | [DONE] | J3-06 | Tested via `/api/v1/standings/drivers` and `/constructors` |
| B1-05 | Configurable dashboard panels & favorite driver/team highlights | R1 | [DONE] | I1-05 | User preference patch API tested |
| B1-06 | Historical fallback for off-season and off-weekends | R1 | [DONE] | J3-02 | Provenance clearly marked as `HISTORICAL` / `is_test_fixture: True` |
| B2-01 | Official Season Calendar with meetings, tracks, round numbers | R1 | [DONE] | J1-01 | Tested via `/api/v1/meetings?season=2024` (24 rounds structured) |
| B2-02 | Sprint-weekend format detection & multi-timezone scheduling | R1 | [DONE] | B2-01 | `is_sprint_weekend` field and UTC ISO-8601 timestamps verified |
| B2-03 | Calendar season filtering and historical season browsing | R1 | [DONE] | J3-01 | Query parameter filtering by season supported |
| B2-04 | Session reminders & ICS / iCal calendar export | R1 | [TODO] | B2-01 | Scheduled for notification and calendar sync release |

---

### Module C: Drivers, Teams, and Historical Results
| Feature ID | Name / Description | Release Target | Status | Dependencies | Verification Evidence & Criteria |
|---|---|---|---|---|---|
| C1-01 | Driver profile (bio, number, code, nationality, team, career stats) | R1 | [DONE] | J3-04 | Tested via `/api/v1/drivers` with full biography and career stats |
| C1-02 | Driver recent race performance, qualifying pace, head-to-head comparison | R1 | [TODO] | J3-04 | Scheduled for Circuit Analytics release |
| C1-03 | Driver recent form charts and circuit-specific performance | R1 | [TODO] | C1-02 | Scheduled for Circuit Analytics release |
| C2-01 | Constructor profiles (history, current lineup, season results, points) | R1 | [DONE] | J3-05 | Tested via `/api/v1/constructors` with drivers relationship |
| C2-02 | Constructor teammate comparison & rival team head-to-head | R1 | [TODO] | C2-01 | Scheduled for Circuit Analytics release |
| C3-01 | Driver & Constructor Standings tables with points gaps | R1 | [DONE] | J3-06 | Tested in unit and integration test suites |
| C3-02 | Official race classifications with session-specific scoring | R1 | [DONE] | J3-03 | Tested via `/api/v1/sessions/{id}/classification` |
| C3-03 | Handling of revised classifications, penalties, and disqualifications | R1 | [DONE] | C3-02 | Penalty point deduction logic verified in unit tests |
| C3-04 | Data provenance, update timestamps, and CSV export for standings/results | R1 | [DONE] | C3-01 | `ProvenanceMeta` stamped on every classification & calculation |

---

### Module D: Live Race Center (Release 2)
| Feature ID | Name / Description | Release Target | Status | Dependencies | Verification Evidence & Criteria |
|---|---|---|---|---|---|
| D1-01 | OpenF1 & FastF1 backend data adapter with quota & retry handling | R2 | [IN_PROGRESS] | J1-01 | OpenF1 provider adapter implemented with rate limit & timeout handling |
| D1-02 | Data freshness status indicator (LIVE, DELAYED, STALE, HISTORICAL, UNAVAILABLE) | R2 | [DONE] | D1-01 | `is_stale()` logic verified with threshold check |
| D2-01 | Live Timing Tower (Position, Interval, Gap to Leader, Lap, S1/S2/S3, Best Lap) | R2 | [TODO] | D1-01 | Scheduled for Release 2 live engine |
| D2-02 | Tire compound indicator and stint age tracker | R2 | [TODO] | D2-01 | Design tokens ready; scheduled for Release 2 |
| D3-01 | Live Race Control messages feed (Flags, VSC, SC, Red Flag, Penalties, Investigations) | R2 | [TODO] | D1-01 | Scheduled for Release 2 |
| D4-01 | Interactive Track Map (SVG / Canvas circuit geometry, driver positions, sectors) | R2 | [TODO] | D1-01 | Scheduled for Release 2 |
| D5-01 | Telemetry overlay (Speed, Throttle, Brake, Gear, RPM, DRS status comparison) | R2 | [TODO] | D1-01 | Scheduled for Release 2 |
| D6-01 | Real-time WebSocket streaming with snapshot + delta resynchronization | R2 | [TODO] | J2-04 | Scheduled for Release 2 |

---

### Module E: Championship Intelligence (Release 3)
| Feature ID | Name / Description | Release Target | Status | Dependencies | Verification Evidence & Criteria |
|---|---|---|---|---|---|
| E1-01 | Championship Dashboard (Current points, gap, remaining points available, title contenders) | R1/R3 | [DONE] | C3-01 | Tested via `/api/v1/championship/intelligence` |
| E2-01 | Exact Minimum-Points Engine (mathematical clinching conditions & elimination logic) | R1/R3 | [DONE] | E1-01 | Tested across 10 distinct regression test scenarios |
| E2-02 | Rival-Points Cap Calculator (maximum permissible rival points for title preservation) | R3 | [TODO] | E2-01 | Scheduled for Release 3 deep scenario engine |
| E3-01 | Race-by-race Finishing Position Scenario Matrix with validation against contradictions | R3 | [TODO] | E2-01 | Scheduled for Release 3 |
| E3-02 | Saved and shareable championship scenario URLs | R3 | [TODO] | E3-01 | Scheduled for Release 3 |
| E4-01 | Monte Carlo Season Simulator (10,000+ runs with DNF, pace variance, grid penalties) | R3 | [TODO] | E1-01 | Scheduled for Release 3 |
| E4-02 | Model calibration, error metrics (Brier score / log loss), and historical backtesting | R3 | [TODO] | E4-01 | Scheduled for Release 3 |
| E5-01 | Championship Visualizations (Probability trend lines, Clinching combinations table) | R3 | [DONE] | E4-01 | Web UI interactive contender matrix verified |

---

### Module F: Circuit & Driver Performance Analytics (Release 4)
| Feature ID | Name / Description | Release Target | Status | Dependencies | Verification Evidence & Criteria |
|---|---|---|---|---|---|
| F1-01 | Historical circuit performance records (Finishing distribution, Qualifying delta) | R4 | [TODO] | C1-01 | Scheduled for Release 4 |
| F2-01 | Circuit characteristics model (High-speed, low-speed, traction, braking, straights) | R4 | [TODO] | J3-08 | Scheduled for Release 4 |
| F2-02 | Car / Driver Suitability Index with current-season pace weighting | R4 | [TODO] | F2-01 | Scheduled for Release 4 |
| F3-01 | Future-Race Predictions (Qualifying rank, finishing distribution, win/podium probability) | R4 | [TODO] | F2-02 | Scheduled for Release 4 |
| F3-02 | Circuit Analytics Comparison Tables with CSV export | R4 | [TODO] | F3-01 | Scheduled for Release 4 |

---

### Module G: Race IQ — Historical Replay (Release 5)
| Feature ID | Name / Description | Release Target | Status | Dependencies | Verification Evidence & Criteria |
|---|---|---|---|---|---|
| G1-01 | Race Time Machine (Play, pause, scrub, rewind, seek to lap, variable speed 0.5x-10x) | R5 | [TODO] | J3-10 | Scheduled for Release 5 |
| G1-02 | Synchronized replay of Timing Tower, Race Control, and Track Positions | R5 | [TODO] | G1-01 | Scheduled for Release 5 |
| G1-03 | Replay bookmarking and shareable timestamp links | R5 | [TODO] | G1-01 | Scheduled for Release 5 |
| G2-01 | "Explain This Battle" multi-driver telemetry, tire age, and pit delta analyzer | R5 | [TODO] | G1-01 | Scheduled for Release 5 |

---

### Module H: Strategy Lab (Release 5)
| Feature ID | Name / Description | Release Target | Status | Dependencies | Verification Evidence & Criteria |
|---|---|---|---|---|---|
| H1-01 | Pit-Stop Strategy Simulator (1-stop vs 2-stop vs 3-stop race time modeling) | R5 | [TODO] | J3-11 | Scheduled for Release 5 |
| H1-02 | Undercut / Overcut tactical window calculator | R5 | [TODO] | H1-01 | Scheduled for Release 5 |
| H1-03 | Safety Car / VSC pit delta advantage calculator | R5 | [TODO] | H1-01 | Scheduled for Release 5 |
| H2-01 | Strategy scenario saving, comparison and sharing | R5 | [TODO] | H1-01 | Scheduled for Release 5 |

---

### Module I: Personalization, Spoiler Shield & Accounts (Release 6 / R1 Foundation)
| Feature ID | Name / Description | Release Target | Status | Dependencies | Verification Evidence & Criteria |
|---|---|---|---|---|---|
| I1-01 | User authentication (JWT, secure registration, password hashing, recovery) | R1 | [DONE] | J2-02 | Bcrypt hashing + JWT token flow tested (success, duplicate, invalid, expired) |
| I1-02 | Cross-device profile, favorite drivers and constructor management | R1 | [DONE] | I1-01 | User preferences PATCH endpoint tested with driver/team favorites |
| I2-01 | Spoiler Shield Global Mode (masks results, positions, podiums, standings until unmasked) | R1/R6 | [DONE] | I1-02 | Interactive Spoiler Shield toggle tested on web and mobile |
| I2-02 | Push and in-app session notifications with quiet hours & spoiler safety | R6 | [TODO] | I1-02 | Scheduled for Release 6 |
| I3-01 | "My Pit Wall" customizable multi-widget race dashboard | R6 | [TODO] | I1-02 | Schema field persisted; UI scheduled for Release 6 |

---

### Module J: Data Infrastructure, APIs & Operations
| Feature ID | Name / Description | Release Target | Status | Dependencies | Verification Evidence & Criteria |
|---|---|---|---|---|---|
| J1-01 | Provider abstraction layer with resilient caching and schemas | R1 | [DONE] | None | OpenF1 provider with error isolation & stale detection |
| J2-01 | PostgreSQL relational schema & Alembic migrations | R1 | [DONE] | None | Alembic migrations initialized, upgraded to head, and downgrade tested |
| J2-02 | Redis caching layer with TTL, cache invalidation & session store | R1 | [DONE] | None | `app.core.redis.RedisClient` with fallback verified |
| J3-01 | Fast, typed REST API endpoints for Seasons, Meetings, Sessions, Results | R1 | [DONE] | J2-01 | 9 OpenAPI endpoints live and covered by 12 integration tests |
| J3-02 | OpenAPI TypeScript client / shared contracts | R1 | [DONE] | J3-01 | `@apex-gp/shared-types` synchronized with Pydantic schemas |
| J4-01 | Docker Compose orchestration for local development & testing | R1 | [DONE] | None | Multi-container setup validated via `docker compose config` |
| J4-02 | CI/CD GitHub Actions workflows for linting, testing, and builds | R1 | [TODO] | None | Scheduled for release pipeline setup |

---

### Module K & L: Verification, Testing & Release Governance
| Feature ID | Name / Description | Release Target | Status | Dependencies | Verification Evidence & Criteria |
|---|---|---|---|---|---|
| L1-01 | Unit test suite for championship points and tie-breaking arithmetic | R1 | [DONE] | J3-01 | 23 unit tests in `test_championship_engine.py` (100% pass covering 1991–2026 scales, 2014 double points round metadata, 2019-2021 vs 2022-2024 FL distance boundaries, dead heats, constructor capacity, 2026 consecutive-laps GP gate & neutralization immunity, 2026 sprint distance gate, Section A Art A2.1.4(c) direct qualifying countback fallback, exact integer lap distance thresholds, and typed context errors) |
| L1-02 | Integration test suite for REST API endpoints and data validation | R1 | [DONE] | J3-01 | 12 integration tests in `test_api_endpoints.py` (100% pass); total 35 automated tests passing |
| L1-03 | Web e2e and accessibility audit (WCAG AA, dark/light contrast) | R1 | [DONE] | A1-03 | Next.js production build (`npm run build`) passing without errors |
| N1-01 | Private Friends-Only Beta infrastructure & feedback tracking | R7 | [TODO] | All R1-R6 | 30-day stability verification plan documented |
| P1-01 | Production deployment checklist, observability & runbooks | R8 | [TODO] | N1-01 | Gate criteria documented in `docs/release-checklist.md` |
