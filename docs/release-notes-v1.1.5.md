# APEX GP — Release Notes v1.1.5

> **Release Version:** `v1.1.5`  
> **Type:** Targeted Correctness Patch & Historical Countback Audit  
> **Date:** 2026-10-12  
> **Status:** PASSED & STABILIZED  
> **Preceding Tags:** `v1.1.0`, `v1.1.1`, `v1.1.2`, `v1.1.3`, `v1.1.4` (All preserved intact)

---

## 1. Executive Summary

Release `v1.1.5` implements the **Historical Countback Audit** for the APEX GP championship engine. Following rigorous inspection against official FIA Sporting Regulations (Article 7.2) across historical seasons (1991–2025) and Section A, Article A2.1.4(c) for the 2026 season:

1. **Statutory Race-Result Countback Strictly Enforced (Article 7.2):** For all historical seasons (1991–2025), countback is strictly determined by Grand Prix race finishing positions (most 1st places, then 2nd places, etc.). Sprint race results (introduced in 2021) and qualifying results are not statutory countback tie-breakers under Article 7.2.
2. **Explicit Unresolved / FIA Discretion Outcome (Article 7.2(d)):** When competitors finish tied on points and have identical Grand Prix finishing records, the engine no longer breaks the tie with an unofficial sprint or qualifying hierarchy. Instead, it returns `0` (unresolved tie), strictly reflecting Article 7.2(d): *"If this procedure fails to produce a result, the FIA will nominate the winner according to such criteria as it thinks fit."*
3. **Preservation of 2026 Direct Qualifying Fallback (Article A2.1.4(c)):** The 2026 ruleset continues to fall back directly to Qualifying finishing positions (most pole positions, then 2nd, 3rd, etc.) if GP finishes are tied, without inserting sprint results as an intermediate stage.
4. **Targeted Regression Suite Added:** Added test 24 (`test_season_specific_countback_behavior`) covering 2021, 2022, 2025, and 2026 seasons with identical GP counts, sprint differences, and qualifying differences.

All 36 automated tests (24 championship arithmetic unit tests and 12 REST API integration tests) pass with 100% compliance. Web production build (`npm run build`) and mobile typechecks (`tsc --noEmit`) compile with zero errors.

---

## 2. Detailed Audit & Regulatory Findings

| Season | Governing FIA Regulation | Statutory Tie-Break Criteria | Outcome When GP Finishes Are Identical |
|---|---|---|---|
| **2021** | 2021 F1 Sporting Regulations, Art. 7.2 | GP 1st places, then 2nd, 3rd, etc. Sprint Qualifying results excluded. | Unresolved (`0`) $\to$ FIA nomination (Art. 7.2(d)). Sprint wins do not break tie. |
| **2022** | 2022 F1 Sporting Regulations, Art. 7.2 | GP 1st places, then 2nd, 3rd, etc. Sprint race results excluded. | Unresolved (`0`) $\to$ FIA nomination (Art. 7.2(d)). Sprint wins do not break tie. |
| **2025** | 2025 F1 Sporting Regulations, Art. 7.2 | GP 1st places, then 2nd, 3rd, etc. Sprint race results excluded. | Unresolved (`0`) $\to$ FIA nomination (Art. 7.2(d)). Sprint wins do not break tie. |
| **2026** | 2026 Technical & Sporting Regulations, Section A, Art. A2.1.4(c) | GP 1st places, then 2nd, 3rd, etc. Direct fallback to Qualifying results (most poles, 2nd, etc.). | Broken by Qualifying results; if qualifying also tied $\to$ Unresolved (`0`, FIA discretion). |

---

## 3. Verification Test Evidence

| Verification Suite | Command Executed | Outcome | Details |
|---|---|---|---|
| Backend Pytest Suite | `pytest services/api/tests -v` | **PASSED (36/36)** | 24 championship unit tests + 12 API integration tests passed in 2.39s (baseline preserved + 1 test added) |
| Web Production Build | `npm run build` in `apps/web` | **PASSED (Exit 0)** | Next.js 15.5.27 production build compiled in 2.1s; static pages generated |
| Mobile Typecheck | `npx tsc --project apps/mobile/tsconfig.json --noEmit` | **PASSED (Exit 0)** | Zero TypeScript errors across React Native / Expo codebase |
| Docker Daemon | `docker compose config` | **BLOCKED (Environmental)** | Docker Desktop offline on Windows host (`//./pipe/dockerDesktopLinuxEngine`) |

---

## 4. Integrity Checkpoint

- All prior release tags (`v1.1.0`, `v1.1.1`, `v1.1.2`, `v1.1.3`, `v1.1.4`) are preserved intact in Git history.
- No Release 2–8 functionality was initiated or removed during this targeted audit.
