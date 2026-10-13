# APEX GP — Release Notes v1.1.3

> **Release Version:** `v1.1.3`  
> **Type:** Official 2026 Ruleset Verification & Scoring Gates Patch  
> **Date:** 2026-10-12  
> **Git Tag:** `v1.1.3` (following `v1.1.2`, `v1.1.1`, and `v1.1.0`)  

---

## 1. Scope & Overview

APEX GP v1.1.3 implements the definitive, governing regulations for the **2026 Formula 1 World Championship**, verified against official FIA Technical & Sporting Regulations:
- **Section A, Issue 03, Article A2.2**
- **Section B, Issue 09 (published October 1, 2026)**

This release completely decouples the 2025 and 2026 rulesets in both the calculation engine and regulatory documentation, eliminating older Article 6.4/6.5 citations for the 2026 season.

All historical rules (1991–2002, 2003–2009, 2010–2018, 2014 Abu Dhabi double points, 2019–2021 fastest-lap eligibility, 2022–2024 distance-dependent fastest-lap eligibility, and 2025 fastest-lap abolition) remain completely intact and independently tested.

---

## 2. Key 2026 Enhancements & Regulatory Rules Implementations

### 2.1. 2026 Grand Prix Scoring Gate (Section A, Article A2.2)
- Implemented `consecutive_green_laps: Optional[int] = None` in `calculate_grand_prix_points()`.
- For `season >= 2026`, **no championship points** are awarded unless the leader has completed at least **two complete, consecutive laps without a Safety Car (SC) or Virtual Safety Car (VSC)** procedure (`consecutive_green_laps >= 2`).
- If `consecutive_green_laps < 2`, points awarded are strictly `0.0` regardless of distance completed.

### 2.2. 2026 Sprint Scoring Gate (Section A, Article A2.2)
- Implemented `distance_completed_ratio: float = 1.0` and `consecutive_green_laps: Optional[int] = None` in `calculate_sprint_points()`.
- For `season >= 2026`, Sprint points (8, 7, 6, 5, 4, 3, 2, 1) require **both**:
  1. The leader completing at least **two complete, consecutive laps without SC/VSC** (`consecutive_green_laps >= 2`), AND
  2. Completion of at least **50% of the scheduled sprint distance** (`distance_completed_ratio >= 0.50`).
- If either condition fails, points awarded are strictly `0.0`.

### 2.3. 2026 Championship Countback Fallback to Qualifying (Section A, Article A2.2)
- Extended `evaluate_fia_countback()` with `qualifying_finishes_a`, `qualifying_finishes_b`, and `season`.
- Under the 2026 regulations, if competitors remain tied after evaluating Grand Prix race finishing positions (most 1st, then 2nd, 3rd, etc.) and auxiliary sprint finishes, countback **falls back to Qualifying results** (comparing most 1st places / pole positions in qualifying, then 2nd places, 3rd places, etc.).
- If still tied across all criteria, returns `0` representing FIA discretion.
- Propagated through `is_mathematically_eliminated()` and `calculate_clinch_threshold()`.

### 2.4. Independent 2025 vs 2026 Provenance Metadata
- Separated `REGULATION_PROVENANCE_REGISTRY["2026"]` and `REGULATION_PROVENANCE_REGISTRY["2025"]`.
- 2026 points to Section A Issue 03 Art A2.2 & Section B Issue 09.
- 2025 points to Issue 1 (WMSC ratified Oct 17, 2024), Articles 6.4/6.5.

---

## 3. Verification & Test Evidence

### 3.1. Pytest Test Suite
Executed: `$env:PYTHONPATH="e:\f1\services\api"; pytest services/api/tests`
- **Result:** **31 passed in 1.92s** (100% success rate, 0 failures, 0 errors).
  - 19 unit tests in `services/api/tests/test_championship_engine.py`:
    - Tests 1–15: Historical eras, 2014 double points, 2019–2021 FL, 2022–2024 FL distance boundaries, 2025 FL abolition, dead-heat split points, constructor max capacity, countback GP vs sprint separation.
    - Test 16: `test_2026_grand_prix_consecutive_green_laps_gate` (insufficient consecutive laps <2 yields 0.0 pts; exactly 2 consecutive green laps awards points across all distance bands).
    - Test 17: `test_2026_sprint_scoring_gates` (insufficient green laps yields 0.0; sprint distance <50% yields 0.0; exactly 50% distance and 2 green laps awards 8, 7... 1 pts).
    - Test 18: `test_2026_countback_qualifying_fallback` (GP and sprint tied resolves on qualifying pole count / 2nd places; completely tied resolves to 0; 2024 does not use qualifying fallback).
    - Test 19: `test_2026_regulation_provenance_independence` (verifies distinct metadata and field properties for 2026 vs 2025).
  - 12 integration tests in `services/api/tests/test_api_endpoints.py` (100% pass).

### 3.2. Web Production Build (Next.js 15)
Executed: `npm run build` in `apps/web`
- **Result:** Compiled successfully; all static routes generated; 0 TypeScript or linting errors.

### 3.3. Mobile TypeScript Validation (Expo / React Native)
Executed: `npx tsc --project apps/mobile/tsconfig.json --noEmit`
- **Result:** Exited with code 0 (clean compilation, 0 type errors).

### 3.4. Docker Daemon Status
Executed: `docker info`
- **Result:** Docker Desktop daemon on Windows host pipe (`//./pipe/dockerDesktopLinuxEngine`) remains offline.
- **Status:** Explicitly recorded as `BLOCKED (Environmental: Docker Desktop daemon not running)`. No false claims of container execution made.

---

## 4. Git Artifacts

- **Commit:** `fix(championship): v1.1.3 2026 ruleset separation, scoring gates, and qualifying countback fallback`
- **Tag:** `v1.1.3`
- **Preserved Tags:** `v1.1.0`, `v1.1.1`, `v1.1.2`
