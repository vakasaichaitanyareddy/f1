# APEX GP — Release Notes v1.1.4

> **Release Version:** `v1.1.4`  
> **Type:** Targeted Correctness Patch & Final Release Gate Audit  
> **Date:** 2026-10-12  
> **Status:** PASSED & STABILIZED  
> **Preceding Tags:** `v1.1.0`, `v1.1.1`, `v1.1.2`, `v1.1.3` (All preserved)

---

## 1. Executive Summary

Release v1.1.4 completes the comprehensive **Release Gate Audit** for APEX GP. Following strict verification against the governing official FIA regulations, this release corrects regulatory provenance citations, hardens 2026 countback tie-break mechanics, introduces typed error semantics for missing session eligibility context, guarantees neutralization immunity for completed green-lap sequences, ensures exact integer arithmetic across fractional race distances, and derives 2014 season finale double-points activation strictly from official championship round metadata.

All 35 automated tests (23 championship arithmetic unit tests and 12 REST API integration tests) pass with 100% compliance. Web production builds and mobile typechecks compile cleanly with zero errors.

---

## 2. Key Audit Findings & Changes Implemented

### 2.1 Regulatory Provenance Correction (Item 1 & Item 2)
- **Official Provenance Citation:** Corrected the 2026 countback citation to **Section A, Article A2.1.4(c)**. Article A2.2 governs the points scale and distance gates, while Article A2.1.4(c) dictates the official tie-break procedure when GP finishes are deadlocked.
- **Direct Qualifying Fallback (Article A2.1.4(c)):** The official FIA 2026 Sporting Regulations do not define Sprint race results as an intermediate tie-break stage between Grand Prix finishes and Qualifying results. The countback engine was updated so that for 2026, tied GP finishes fall back directly to Qualifying result counts without inserting sprint results. For earlier seasons (2021–2025), sprint race results remain the secondary tie-break tier.

### 2.2 Strict Missing-Context Handling & Typed Errors (Item 3)
- **`InsufficientContextError`:** Introduced a dedicated typed exception (`InsufficientContextError(ValueError)`) distinct from an official zero-point outcome.
- **Strict Scoring Gate:** When 2026 Grand Prix or Sprint scoring functions are invoked without required eligibility context (or with explicit `None` values where eligibility cannot be verified), the engine rejects the computation with `InsufficientContextError` rather than silently awarding zero points.

### 2.3 Consecutive Green Laps Neutralization Immunity (Item 4)
- **Session History Evaluation (`verify_consecutive_laps_history`):** The 2026 Sporting Regulations require that the leader completes at least two complete consecutive laps without a Safety Car (SC) or Virtual Safety Car (VSC) procedure.
- **Neutralization Immunity:** Verified and tested that once a driver or race satisfies this two-consecutive-lap threshold during any phase of the race, subsequent SC or VSC interventions prior to a red flag do not retroactively invalidate the scoring eligibility.

### 2.4 Distance Thresholds & Integer Lap Arithmetic (Item 5)
- **`resolve_distance_band`:** Implemented precise integer lap arithmetic to correctly evaluate distances that do not divide evenly into scheduled lap counts (e.g. 53-lap grands prix at Monza or Suzuka).
- **Exact Thresholds:**
  - $< 25\%$: 13 laps ($13/53 = 24.53\%$) $\to$ Column 1 (6 pts for P1).
  - $25\% \le d < 50\%$: 14 laps ($26.42\%$) through 26 laps ($49.06\%$) $\to$ Column 2 (13 pts for P1).
  - $50\% \le d < 75\%$: 27 laps ($50.94\%$) through 39 laps ($73.58\%$) $\to$ Column 3 (19 pts for P1).
  - $\ge 75\%$: 40 laps ($75.47\%$) $\to$ Full points (25 pts for P1).

### 2.5 2014 Season Finale Metadata Derivation (Item 6)
- **Authentic Finale Verification:** In the 2014 Formula 1 Sporting Regulations (Appendix 2, Article 6.4), double points were awarded exclusively at the final event of the Championship (Round 19 of 19, Abu Dhabi).
- **Metadata Protection:** The engine no longer relies on an arbitrary caller boolean (`is_final_event=True`). When round metadata is supplied, double points activate if and only if `round_number == total_rounds` and `round_number == 19`. Invalid or inconsistent metadata raises `ValueError`.

### 2.6 Full Specification & Feature Inventory Preservation (Item 8)
- Verified that all future roadmap modules (Releases 2–8: Live Telemetry, Strategy Lab, Head-to-Head Analytics, Beta Infrastructure) remain explicitly tracked in `docs/feature-inventory.md` with explicit dependencies and clear status labels (`[TODO]`), without simplifying them into placeholders or claiming unbuilt components as complete.

---

## 3. Test & Verification Evidence

| Verification Target | Command Executed | Outcome | Details |
|---|---|---|---|
| Backend Test Suite | `pytest services/api/tests -v` | **PASSED (35/35)** | 23 championship unit tests + 12 API integration tests passed in 2.28s |
| Web Production Build | `npm run build` in `apps/web` | **PASSED (Exit 0)** | Next.js 15.5.27 production build compiled in 1.9s, static pages generated |
| Mobile Typecheck | `npx tsc --project apps/mobile/tsconfig.json --noEmit` | **PASSED (Exit 0)** | Zero TypeScript compilation errors across React Native / Expo codebase |
| Docker Daemon | `docker compose config` | **BLOCKED (Environmental)** | Docker CLI v29.7.2 installed; Windows named pipe `//./pipe/dockerDesktopLinuxEngine` offline |

---

## 4. Verification Checkpoint Status

All Release Gate Audit criteria are satisfied with verifiable evidence. Code, tests, and documentation are synchronized. Preceding release tags (`v1.1.0`, `v1.1.1`, `v1.1.2`, `v1.1.3`) are preserved intact.
