# APEX GP — Release Notes v1.1.2

> **Release Version:** `v1.1.2`  
> **Type:** Official Regulatory Scoring Patch & Audit Completion  
> **Date:** 2026-10-12  
> **Git Tag:** `v1.1.2` (following `v1.1.1` and `v1.1.0`)  

---

## 1. Scope & Overview

APEX GP v1.1.2 finalizes the complete, evidence-grounded scoring rules matrix and mathematical calculation engine according to official FIA Formula One Sporting Regulations spanning **1991 through 2026**.

This release preserves all existing architecture, database schemas, API endpoints, web/mobile applications, and previous release tags (`v1.1.0`, `v1.1.1`), with zero feature omissions or simplifications.

---

## 2. Key Enhancements & Regulatory Corrections

### 2.1. Complete 1991–2026 Season-by-Season Regulation Matrix
- Authored `docs/regulation-rules-matrix.md` detailing official document titles, issue numbers, WMSC ratification dates, document URLs, and exact articles for all historical and modern eras.
- Added direct regulatory provenance metadata tracking to `REGULATION_PROVENANCE_REGISTRY` in `services/api/app/championship/engine.py`.

### 2.2. 2014 Season Finale Double-Points Rule (Article 6.4)
- Implemented `is_final_event` evaluation in `calculate_grand_prix_points()`.
- When `season == 2014` and `is_final_event == True` (Abu Dhabi Grand Prix, Round 19), finishing position base points are doubled:
  - P1: 50 pts, P2: 36 pts, P3: 30 pts, P4: 24 pts, P5: 20 pts, P6: 16 pts, P7: 12 pts, P8: 8 pts, P9: 4 pts, P10: 2 pts.
- Normal 2014 races (Rounds 1–18) correctly award standard points.
- Factored into maximum remaining points calculations for drivers (up to 50 pts) and constructors (up to 86 pts).

### 2.3. Fastest-Lap Distance Distinction (2019–2021 vs 2022–2024 vs 2025+)
- **2019–2021:** Driver must finish in top 10 in a race where points are awarded. Pre-2022 regulations did **not** enforce a 50% distance threshold.
- **2022–2024:** Driver must finish in top 10 AND leader must complete $\ge 50\%$ distance. Bonus is awarded in full races and the 50%–<75% band, but suppressed in the <25% and 25%–<50% bands.
- **2025 Onward:** Fastest-lap bonus point completely abolished under amended Article 6.4.

### 2.4. Dead-Heat Tied Finishes & Split Points
- Implemented `calculate_shared_points()` for dead-heat finishes where multiple drivers tie for position(s).
- Sums the points across all tied finishing positions and divides equally (decimal points supported, e.g. 21.5 pts for tied P1).

### 2.5. Constructor Maximum Capacity & Sprint Separation in Countbacks
- `calculate_max_remaining_points()` now supports `is_constructor=True` accounting for two scoring cars per team (e.g. 44 pts per GP in 2024, 43 pts in 2025, 86 pts in 2014 finale).
- `evaluate_fia_countback()` distinguishes Grand Prix race wins from Sprint session wins per FIA Sporting Regulations Article 7.2.

---

## 3. Verification & Test Evidence

### 3.1. Automated Test Suite (Pytest)
Command executed: `$env:PYTHONPATH="e:\f1\services\api"; pytest services/api/tests`
- **Result:** **27 passed in 2.25s** (100% success rate, 0 failures, 0 errors).
  - 15 unit tests in `test_championship_engine.py` covering:
    - Standard modern GP points
    - Historical eras (1991–2002, 2003–2009)
    - Fastest lap top-10 conditions
    - Shortened race distance boundaries (below 50%, 50%, between 50% and 75%)
    - 2025+ fastest lap abolition
    - Provenance metadata inspection
    - Penalty deductions
    - Sprint points (2021 vs 2022+)
    - Countback resolution
    - Mathematical elimination & clinch boundaries
    - 2014 double points season finale
    - 2019–2021 vs 2022–2024 FL distance distinction
    - Dead heat shared points
    - Constructor maximum capacity
    - Countback sprint vs GP distinction
  - 12 integration tests in `test_api_endpoints.py` covering auth, registration, login, meetings, classifications, standings, preferences, and championship intelligence.

### 3.2. Web Production Build (Next.js 15)
Command executed: `npm run build` in `apps/web`
- **Result:** Compiled successfully in 1651ms; static pages generated; 0 TypeScript or linting errors.

### 3.3. Mobile Application Typecheck (Expo / React Native)
Command executed: `npx tsc --project apps/mobile/tsconfig.json --noEmit`
- **Result:** Exit code 0 (0 type errors, clean compilation).

### 3.4. Docker Compose & Container Runtime Environment
Command executed: `docker info`
- **Result:** Docker CLI v29.7.2 available, but connection to host daemon pipe (`npipe:////./pipe/dockerDesktopLinuxEngine`) failed because Docker Desktop is not running on the Windows host machine.
- **Operational Status:** Marked as `BLOCKED (Environmental: Docker Desktop daemon offline)`. Multi-container compose configuration (`docker-compose.yml`) was previously verified via `docker compose config`.
