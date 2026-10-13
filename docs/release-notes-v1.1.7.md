# APEX GP — Release Notes v1.1.7

> **Release Version:** `v1.1.7`  
> **Type:** Targeted Correctness Patch & Downstream Audit  
> **Date:** 2026-10-12  
> **Status:** PASSED & STABILIZED  
> **Preceding Tags:** `v1.1.0`, `v1.1.1`, `v1.1.2`, `v1.1.3`, `v1.1.4`, `v1.1.5`, `v1.1.6` (All preserved intact)

---

## 1. Executive Summary

Release `v1.1.7` rectifies the sprint scoring scale for the **2026 Formula 1 World Championship** and completes an exhaustive downstream calculation audit.

In v1.1.6, an erroneous interpretation of Section A, Article A2.2.2 was introduced that restricted sprint scoring to the top 7 finishers (8–7–6–5–4–3–2) with zero points awarded to 8th place. 

Official verification against governing FIA Sporting Regulations (Section A, Issue 03, Article A2.2.2) and authoritative official session classifications confirms that **the standard sprint scoring scale awards points to the top 8 finishers: 8, 7, 6, 5, 4, 3, 2, 1**. Eighth place earns 1 point; ninth place and below earn 0 points.

All downstream consumers—including standings calculations, constructor maximum capacity, mathematical elimination, title-clinching thresholds, and dead-heat allocations (including P8/P9 boundary ties)—have been audited, updated, and validated against regression test suites.

---

## 2. Definitive Sprint Points Matrix Across All Eras

| Season / Era | Governing FIA Regulation | Finishing Positions Awarding Points | Points Allocation Scale | P8 Points | P9+ Points |
|---|---|---|---|---|---|
| **2021** | 2021 F1 Sporting Regulations, Art. 6.4/6.5 | Top 3 (Sprint Qualifying) | 3, 2, 1 | 0.0 | 0.0 |
| **2022–2025** | 2022–2025 F1 Sporting Regulations, Art. 6.4/6.5 | Top 8 | 8, 7, 6, 5, 4, 3, 2, 1 | 1.0 | 0.0 |
| **2026** | 2026 Technical & Sporting Regulations, Section A, Art. A2.2.2 | Top 8 (subject to eligibility gates) | 8, 7, 6, 5, 4, 3, 2, 1 | 1.0 | 0.0 |

---

## 3. Key Implementations & Downstream Audit

### 3.1 Sprint Scoring Scale Correction
- In [`services/api/app/championship/engine.py`](file:///e:/f1/services/api/app/championship/engine.py):
  - Updated `SPRINT_POINTS_2026`: `{1: 8.0, 2: 7.0, 3: 6.0, 4: 5.0, 5: 4.0, 6: 3.0, 7: 2.0, 8: 1.0}`.
  - P8 explicitly earns 1.0 point; P9+ earns 0.0 points.
  - Updated `REGULATION_PROVENANCE_REGISTRY["2026"]` provenance documentation to record the official top 8 scale.

### 3.2 Preservation of 2026 Eligibility Gates
- Preserved the dual statutory eligibility conditions under Article A2.2:
  1. At least two complete, consecutive laps without Safety Car (SC) or Virtual Safety Car (VSC).
  2. At least 50% of the scheduled sprint distance completed.
  3. Typed `InsufficientContextError` raised when required session context is missing or unknown.

### 3.3 Dead-Heat Support for Sprints & P8/P9 Boundary Ties
- Extended `calculate_shared_points()` to accept `is_sprint: bool = False` and `consecutive_green_laps: Optional[int] = None`.
- Added regression tests for dead-heat finishes across P8 and P9:
  - $(1.0 + 0.0) / 2 = 0.5$ points each for tied 8th/9th finishers.
  - $(2.0 + 1.0) / 2 = 1.5$ points each for tied 7th/8th finishers.

### 3.4 Downstream Calculations Audit
- **Driver Maximum Capacity:** P1 awards 8 points. 2026 single-driver sprint capacity remains 8 points per sprint.
- **Constructor Maximum Capacity:** Two cars score: P1 (8) + P2 (7) = 15 points per sprint.
- **Standings & Elimination:** Audited `is_mathematically_eliminated()` and `calculate_clinch_threshold()`. Added dedicated test scenarios combining remaining GPs and sprints for 2026.
- **Historical Seed Data Check:** Audited `services/api/app/racing/seed_data.py` and runtime databases. No stored derived standings or cached projections were corrupted with the erroneous P8 = 0 calculation (seed data uses the verified 2024 baseline).

---

## 4. Verification Evidence & Test Execution

| Verification Target | Command Executed | Outcome | Details |
|---|---|---|---|
| Backend Pytest Suite | `pytest services/api/tests -v` | **PASSED (36/36)** | 24 championship arithmetic unit tests + 12 API integration tests passed in 2.46s |
| Web Production Build | `npm run build` in `apps/web` | **PASSED (Exit 0)** | Next.js 15.5.27 compiled successfully in 2.0s with zero errors |
| Mobile TypeScript Validation | `npx tsc --project apps/mobile/tsconfig.json --noEmit` | **PASSED (Exit 0)** | Zero TypeScript diagnostics across React Native / Expo codebase |
| Docker Daemon | `docker compose config` | **BLOCKED (Environmental)** | Host Docker Desktop daemon (`//./pipe/dockerDesktopLinuxEngine`) is offline |

---

## 5. Scope Governance & Environmental Blockers

- **Prior Release Tags:** `v1.1.0`, `v1.1.1`, `v1.1.2`, `v1.1.3`, `v1.1.4`, `v1.1.5`, and `v1.1.6` are preserved intact.
- **Full Specification Preserved:** No Release 2–8 modules have been omitted, simplified, or claimed complete prematurely.
- **Docker Block:** Full-stack container integration remains logged as **`BLOCKED (Environmental: Docker Desktop offline)`**.
