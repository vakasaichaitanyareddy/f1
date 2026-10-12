# APEX GP — Release Notes v1.1.6

> **Release Version:** `v1.1.6`  
> **Type:** Targeted Correctness Patch & 2026 Sprint Scoring Correction  
> **Date:** 2026-10-12  
> **Status:** PASSED & STABILIZED  
> **Preceding Tags:** `v1.1.0`, `v1.1.1`, `v1.1.2`, `v1.1.3`, `v1.1.4`, `v1.1.5` (All preserved intact)

---

## 1. Executive Summary

Release `v1.1.6` corrects the sprint scoring table for the **2026 Formula 1 World Championship** in accordance with the official FIA Technical & Sporting Regulations, Section A, Issue 03, Article A2.2.2 (ratified June 25, 2026 / published October 1, 2026).

Under Article A2.2.2, sprint points are awarded exclusively to the **top 7 finishers** according to the scale **8, 7, 6, 5, 4, 3, 2**. Eighth place and below receive zero points.

The engine now cleanly differentiates all three sprint scoring eras:
1. **2021:** Inaugural Sprint Qualifying scale: 3–2–1 (Top 3).
2. **2022–2025:** Top 8 scale: 8–7–6–5–4–3–2–1 (Article 6.5).
3. **2026 Onward:** Top 7 scale: 8–7–6–5–4–3–2 (Section A, Article A2.2.2). Eighth place receives 0 points.

All downstream calculations—including maximum remaining points, title eliminations, clinching thresholds, and session results—have been audited and confirmed to consume the season-specific scoring table.

---

## 2. Key Regulatory Details & Changes Implemented

### 2.1 Season-Specific Sprint Points Table
- **`SPRINT_POINTS_2026`:** `{1: 8.0, 2: 7.0, 3: 6.0, 4: 5.0, 5: 4.0, 6: 3.0, 7: 2.0}` (P8+ awards 0.0).
- **`SPRINT_POINTS_2022_2025`:** `{1: 8.0, 2: 7.0, 3: 6.0, 4: 5.0, 5: 4.0, 6: 3.0, 7: 2.0, 8: 1.0}`.
- **`SPRINT_POINTS_2021`:** `{1: 3.0, 2: 2.0, 3: 1.0}`.
- **`calculate_sprint_points()`:** Dynamically dispatches between 2021, 2022–2025, and 2026+ based on the `season` argument while strictly enforcing the 2026 two-consecutive-green-laps and 50%-distance gates.

### 2.2 Maximum Remaining Points & Constructor Capacity Audit
- **Driver Sprint Maximum:** P1 awards 8 points across 2022–2025 and 2026, so single-driver max sprint score remains 8 points.
- **Constructor Sprint Maximum:** In 2026, the constructor's two cars can finish P1 and P2 ($8 + 7 = 15$ points), identical to the 2022–2025 capacity. The reduction of 8th place from 1 point to 0 points does not affect maximum theoretical constructor scoring capacity.
- **Season Dispatched Capacity:** `calculate_max_remaining_points()` explicitly references `SPRINT_POINTS_2026` for `season >= 2026`.

### 2.3 Regression Tests
- **`test_2026_sprint_scoring_gates`:** Corrected to expect P8 = 0.0 points and P7 = 2.0 points for 2026.
- **`test_sprint_points_regulations`:** Expanded to directly verify all eight finishing positions across 2022, 2023, 2024, 2025, and 2026.

---

## 3. Test & Verification Evidence

| Verification Target | Command Executed | Outcome | Details |
|---|---|---|---|
| Backend Pytest Suite | `pytest services/api/tests -v` | **PASSED (36/36)** | 24 championship arithmetic unit tests + 12 API integration tests passed in 2.32s |
| Web Production Build | `npm run build` in `apps/web` | **PASSED (Exit 0)** | Next.js 15.5.27 production build compiled in 2.0s with zero errors; static pages generated |
| Mobile TypeScript Validation | `npx tsc --project apps/mobile/tsconfig.json --noEmit` | **PASSED (Exit 0)** | Zero TypeScript diagnostics across React Native / Expo codebase |
| Docker Daemon | `docker compose config` | **BLOCKED (Environmental)** | Docker Desktop offline on Windows host (`//./pipe/dockerDesktopLinuxEngine`) |

---

## 4. Documentation & Git Artifacts

- **Commit:** To be tagged as `v1.1.6`
- **Preceding Tags:** `v1.1.0`, `v1.1.1`, `v1.1.2`, `v1.1.3`, `v1.1.4`, `v1.1.5` preserved intact.
- **Documentation Updated:**
  - [`docs/regulation-rules-matrix.md`](file:///e:/f1/docs/regulation-rules-matrix.md): Table and Section 3.7 updated with Article A2.2.2 Top 7 sprint scoring scale.
  - [`docs/feature-inventory.md`](file:///e:/f1/docs/feature-inventory.md): L1-01 updated with Top 7 sprint scale evidence; all future items preserved as `[TODO]`.
  - [`docs/release-notes-v1.1.6.md`](file:///e:/f1/docs/release-notes-v1.1.6.md): Complete release documentation.

---

## 5. Scope Governance & Remaining Blockers

- **Docker Runtime Verification:** Explicitly marked **`BLOCKED (Environmental)`**. Docker Desktop is offline on the host system. Production readiness is not claimed without live container integration.
- **Scope Discipline:** No Release 2–8 functionality was initiated, removed, or simplified during this targeted patch.
