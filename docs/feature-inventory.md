# APEX GP — Complete Feature Inventory & Master Traceability Matrix

> **Document Status:** LIVING / AUTHORITATIVE  
> **Last Updated:** 2026-10-12  
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
| Feature ID | Name / Description | Release Target | Status | Dependencies | Verification Criteria |
|---|---|---|---|---|---|
| A1-01 | Define APEX GP branding & logo / motorsport visual identity | R1 | [TODO] | None | Design tokens, visual assets in web/mobile |
| A1-02 | Color, typography, spacing, component tokens (Tailwind / NativeWind) | R1 | [TODO] | None | `design-tokens` package shared across platforms |
| A1-03 | Accessible reusable UI components (Buttons, Cards, Tables, Tabs, Dialogs) | R1 | [TODO] | A1-02 | Tested with keyboard & screen reader accessibility |
| A1-04 | Reusable status indicators and semantic badges | R1 | [TODO] | A1-02 | Live/stale/historical badge states |
| A1-05 | Standardized chart styles and tooltips (ECharts / Recharts) | R1 | [TODO] | A1-02 | Consistent palette across race charts |
| A1-06 | Loading skeletons, empty states, error boundaries, offline states | R1 | [TODO] | A1-03 | Graceful UI degradation under all states |
| A1-07 | Responsive desktop, tablet, mobile layouts & Dark / Light mode | R1 | [TODO] | A1-02 | Layout tested across breakpoints |
| A2-01 | Web Navigation (Home, Race Center, Championship, Drivers/Teams, Circuits, Race IQ, Strategy Lab, Archive, My Pit Wall, Settings) | R1 | [TODO] | A1-03 | Next.js App Router with active routes |
| A2-02 | Mobile Navigation (Expo / React Native tabs and native stack) | R1 | [TODO] | A1-03 | Expo Router matching web domain hierarchy |

---

### Module B: Home Dashboard & Calendar
| Feature ID | Name / Description | Release Target | Status | Dependencies | Verification Criteria |
|---|---|---|---|---|---|
| B1-01 | Next Grand Prix banner & session countdown clock | R1 | [TODO] | J3-02 | Countdown accurately computes to next session start |
| B1-02 | Race-weekend schedule (FP1, FP2, FP3, Sprint Shootout, Sprint, Quali, Race) | R1 | [TODO] | J3-02 | Correct weekend format shown (Standard vs Sprint) |
| B1-03 | Session status & latest verified session results | R1 | [TODO] | J3-03 | Provenance timestamped; no unverified results |
| B1-04 | Current Driver & Constructor Championship mini-standings | R1 | [TODO] | J3-06 | Live points gap and positions verified |
| B1-05 | Configurable dashboard panels & favorite driver/team highlights | R1 | [TODO] | I1-05 | Personalized widgets render based on user prefs |
| B1-06 | Historical fallback for off-season and off-weekends | R1 | [TODO] | J3-02 | Clear labeling of historical data |
| B2-01 | Official Season Calendar with meetings, tracks, round numbers | R1 | [TODO] | J1-01 | Full calendar loaded from official/verified source |
| B2-02 | Sprint-weekend format detection & multi-timezone scheduling | R1 | [TODO] | B2-01 | Timezone conversion tested across UTC/local |
| B2-03 | Calendar season filtering and historical season browsing | R1 | [TODO] | J3-01 | Query past seasons with race dates |
| B2-04 | Session reminders & ICS / iCal calendar export | R1 | [TODO] | B2-01 | .ics download generation tested |

---

### Module C: Drivers, Teams, and Historical Results
| Feature ID | Name / Description | Release Target | Status | Dependencies | Verification Criteria |
|---|---|---|---|---|---|
| C1-01 | Driver profile (bio, number, code, nationality, team, career stats) | R1 | [TODO] | J3-04 | Verified stats (wins, podiums, poles, championships) |
| C1-02 | Driver recent race performance, qualifying pace, head-to-head teammate comparison | R1 | [TODO] | J3-04 | Head-to-head metric calculations unit tested |
| C1-03 | Driver recent form charts and circuit-specific performance | R1 | [TODO] | C1-02 | Sparkline and position progression charts |
| C2-01 | Constructor profiles (history, current lineup, season results, points) | R1 | [TODO] | J3-05 | Historical constructor records verified |
| C2-02 | Constructor teammate comparison & rival team head-to-head | R1 | [TODO] | C2-01 | Point share and pace delta calculated |
| C3-01 | Driver & Constructor Standings tables with points gaps | R1 | [TODO] | J3-06 | Points gap to leader and ahead verified |
| C3-02 | Official race classifications with session-specific scoring | R1 | [TODO] | J3-03 | Correct points allocated (full, half, sprint, fastest lap) |
| C3-03 | Handling of revised classifications, penalties, and post-race disqualifications | R1 | [TODO] | C3-02 | Provenance audit trail preserved |
| C3-04 | Data provenance, update timestamps, and CSV export for standings/results | R1 | [TODO] | C3-01 | Export tested; timestamps rendered on every table |

---

### Module D: Live Race Center (Release 2)
| Feature ID | Name / Description | Release Target | Status | Dependencies | Verification Criteria |
|---|---|---|---|---|---|
| D1-01 | OpenF1 & FastF1 backend data adapter with quota & retry handling | R2 | [TODO] | J1-01 | Normalized schemas, deduplication, retry logic |
| D1-02 | Data freshness status indicator (LIVE, DELAYED, STALE, HISTORICAL, UNAVAILABLE) | R2 | [TODO] | D1-01 | Real-time staleness detector tested |
| D2-01 | Live Timing Tower (Position, Interval, Gap to Leader, Lap, S1/S2/S3, Best Lap) | R2 | [TODO] | D1-01 | Responsive sortable desktop/mobile table |
| D2-02 | Tire compound indicator and stint age tracker | R2 | [TODO] | D2-01 | Compound colors and lap counts verified |
| D3-01 | Live Race Control messages feed (Flags, VSC, SC, Red Flag, Penalties, Investigations) | R2 | [TODO] | D1-01 | Strict chronological ordering and driver tags |
| D4-01 | Interactive Track Map (SVG / Canvas circuit geometry, driver positions, sectors) | R2 | [TODO] | D1-01 | High-efficiency rendering with smooth interpolation |
| D5-01 | Telemetry overlay (Speed, Throttle, Brake, Gear, RPM, DRS status comparison) | R2 | [TODO] | D1-01 | Side-by-side driver telemetry traces |
| D6-01 | Real-time WebSocket streaming with snapshot + delta resynchronization | R2 | [TODO] | J2-04 | Reconnect without state corruption tested |

---

### Module E: Championship Intelligence (Release 3)
| Feature ID | Name / Description | Release Target | Status | Dependencies | Verification Criteria |
|---|---|---|---|---|---|
| E1-01 | Championship Dashboard (Current points, gap, remaining points available, title contenders) | R3 | [TODO] | C3-01 | Maximum possible points calculation |
| E2-01 | Exact Minimum-Points Engine (mathematical clinching conditions & elimination logic) | R3 | [TODO] | E1-01 | Formula 1 countback and tie-break rules tested |
| E2-02 | Rival-Points Cap Calculator (maximum permissible rival points for title preservation) | R3 | [TODO] | E2-01 | Mathematically verified against historical title races |
| E3-01 | Race-by-race Finishing Position Scenario Matrix with validation against contradictions | R3 | [TODO] | E2-01 | Impossible finishes (two drivers P1) rejected |
| E3-02 | Saved and shareable championship scenario URLs | R3 | [TODO] | E3-01 | Scenarios serializable into deep links |
| E4-01 | Monte Carlo Season Simulator (10,000+ runs with DNF, pace variance, grid penalties) | R3 | [TODO] | E1-01 | Empirical win probability & confidence intervals |
| E4-02 | Model calibration, error metrics (Brier score / log loss), and historical backtesting | R3 | [TODO] | E4-01 | Backtested against 2021, 2023, 2024 seasons |
| E5-01 | Championship Visualizations (Probability trend lines, Clinching combinations table) | R3 | [TODO] | E4-01 | Interactive charts with assumption callouts |

---

### Module F: Circuit & Driver Performance Analytics (Release 4)
| Feature ID | Name / Description | Release Target | Status | Dependencies | Verification Criteria |
|---|---|---|---|---|---|
| F1-01 | Historical circuit performance records (Finishing distribution, Qualifying delta) | R4 | [TODO] | C1-01 | Aggregated per-driver track statistics |
| F2-01 | Circuit characteristics model (High-speed, low-speed, traction, braking, straights) | R4 | [TODO] | J3-08 | Quantitative track profile classifications |
| F2-02 | Car / Driver Suitability Index with current-season pace weighting | R4 | [TODO] | F2-01 | Regression / pacing model combining track & car |
| F3-01 | Future-Race Predictions (Qualifying rank, finishing distribution, win/podium probability) | R4 | [TODO] | F2-02 | Model versioning, uncertainty intervals |
| F3-02 | Circuit Analytics Comparison Tables with CSV export | R4 | [TODO] | F3-01 | Sortable multi-driver track comparison |

---

### Module G: Race IQ — Historical Replay (Release 5)
| Feature ID | Name / Description | Release Target | Status | Dependencies | Verification Criteria |
|---|---|---|---|---|---|
| G1-01 | Race Time Machine (Play, pause, scrub, rewind, seek to lap, variable speed 0.5x-10x) | R5 | [TODO] | J3-10 | State reconstruction at arbitrary timestamps |
| G1-02 | Synchronized replay of Timing Tower, Race Control, and Track Positions | R5 | [TODO] | G1-01 | Synchronized multi-panel replay clock |
| G1-03 | Replay bookmarking and shareable timestamp links | R5 | [TODO] | G1-01 | Deep linking to exact lap/session moment |
| G2-01 | "Explain This Battle" multi-driver telemetry, tire age, and pit delta analyzer | R5 | [TODO] | G1-01 | Gap delta analysis with DRS / pit influence |

---

### Module H: Strategy Lab (Release 5)
| Feature ID | Name / Description | Release Target | Status | Dependencies | Verification Criteria |
|---|---|---|---|---|---|
| H1-01 | Pit-Stop Strategy Simulator (1-stop vs 2-stop vs 3-stop race time modeling) | R5 | [TODO] | J3-11 | Tire degradation polynomial modeling |
| H1-02 | Undercut / Overcut tactical window calculator | R5 | [TODO] | H1-01 | Pit lane delta + out-lap pace comparison |
| H1-03 | Safety Car / VSC pit delta advantage calculator | R5 | [TODO] | H1-01 | Delta under neutralized conditions tested |
| H2-01 | Strategy scenario saving, comparison and sharing | R5 | [TODO] | H1-01 | Deep link and saved strategy state |

---

### Module I: Personalization, Spoiler Shield & Accounts (Release 6)
| Feature ID | Name / Description | Release Target | Status | Dependencies | Verification Criteria |
|---|---|---|---|---|---|
| I1-01 | User authentication (JWT, secure registration, password hashing, recovery) | R1 | [TODO] | J2-02 | Secure auth flow with bcrypt & JWT tokens |
| I1-02 | Cross-device profile, favorite drivers and constructor management | R1 | [TODO] | I1-01 | Synchronized between web and mobile |
| I2-01 | Spoiler Shield Global Mode (masks results, positions, podiums, standings until unmasked) | R6 | [TODO] | I1-02 | Zero-leak guarantee across search, cards, alerts |
| I2-02 | Push and in-app session notifications with quiet hours & spoiler safety | R6 | [TODO] | I1-02 | Notification payload filters spoilers |
| I3-01 | "My Pit Wall" customizable multi-widget race dashboard | R6 | [TODO] | I1-02 | Reorderable grid with persisted layouts |

---

### Module J: Data Infrastructure, APIs & Operations
| Feature ID | Name / Description | Release Target | Status | Dependencies | Verification Criteria |
|---|---|---|---|---|---|
| J1-01 | Provider abstraction layer with resilient caching and schemas | R1 | [TODO] | None | Clean domain separation from external APIs |
| J2-01 | PostgreSQL relational schema & Alembic migrations | R1 | [TODO] | None | Tested schema migrations forward and back |
| J2-02 | Redis caching layer with TTL, cache invalidation & session store | R1 | [TODO] | None | Sub-millisecond reads for warm endpoints |
| J3-01 | Fast, typed REST API endpoints for Seasons, Meetings, Sessions, Results | R1 | [TODO] | J2-01 | OpenAPI 3.1 documentation & schema validation |
| J3-02 | OpenAPI TypeScript client auto-generation | R1 | [TODO] | J3-01 | End-to-end type safety in web & mobile |
| J4-01 | Docker Compose orchestration for local development & testing | R1 | [TODO] | None | Clean spin-up of API, Postgres, Redis, Web |
| J4-02 | CI/CD GitHub Actions workflows for linting, testing, and builds | R1 | [TODO] | None | Automated green build verification |

---

### Module K & L: Verification, Testing & Release Governance
| Feature ID | Name / Description | Release Target | Status | Dependencies | Verification Criteria |
|---|---|---|---|---|---|
| L1-01 | Unit test suite for championship points and tie-breaking arithmetic | R1 | [TODO] | J3-01 | 100% test pass on countback & scoring edge cases |
| L1-02 | Integration test suite for REST API endpoints and data validation | R1 | [TODO] | J3-01 | Pytest suite covering all routes |
| L1-03 | Web e2e and accessibility audit (WCAG AA, dark/light contrast) | R1 | [TODO] | A1-03 | Automated accessibility checks passing |
| N1-01 | Private Friends-Only Beta infrastructure & feedback tracking | R7 | [TODO] | All R1-R6 | 30-day stability verification |
| P1-01 | Production deployment checklist, observability & runbooks | R8 | [TODO] | N1-01 | Zero critical CVEs, full metrics, error logging |

