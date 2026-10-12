# APEX GP — Official FIA Formula 1 Regulations and Scoring Rules Matrix (1991–2026)

> **Regulatory Status:** AUTHORITATIVE ARCHIVE & SPECIFICATION  
> **Applicable System:** APEX GP Championship Calculation Engine (`services/api/app/championship/engine.py`)  
> **Source Verification Date:** 2026-10-12  

---

## 1. Executive Summary

This document specifies the season-by-season scoring, tie-breaking countback, fastest-lap bonus eligibility, shortened race scales, and special championship exceptions across every Formula 1 World Championship season from **1991 through 2026**.

All rules are verified against official FIA Sporting Regulations, WMSC bulletins, and official regulatory archives. No historical rules are inferred from contemporary regulations.

---

## 2. Era-by-Era Regulatory Matrix (1991–2026)

| Season Range | Official FIA Document & Version | Official Document URL | Relevant Articles | Grand Prix Scoring Scale | Sprint Format & Points | Fastest-Lap Bonus Point | Shortened Race Rules | Countback & Tie-Breaker | Special Exceptions | Verified Test Reference |
|---|---|---|---|---|---|---|---|---|---|---|
| **2026** | *FIA Formula One World Championship Sporting Regulations — 2026 Technical & Sporting Regulations* (Section A, Issue 03 & Section B, Issue 09, 1 Oct 2026) | [fia.com/regulation/category/110](https://www.fia.com/regulation/category/110) | Section A, Art. A2.2 | 25, 18, 15, 12, 10, 8, 6, 4, 2, 1 (Top 10) | 8, 7, 6, 5, 4, 3, 2, 1 (Top 8, subject to scoring gates) | **None** (Fastest-lap bonus point abolished) | Graduated scale (<25%, 25%–<50%, 50%–<75%, $\ge$75%). **Scoring gate:** No GP points awarded unless leader completed $\ge$2 complete consecutive laps without SC/VSC procedure. | GP wins, 2nd, 3rd... If unresolved by GP/Sprint finishes, **falls back to Qualifying results** (most poles, 2nd, etc.). If still tied, FIA discretion. | **Sprint Scoring Gate:** Requires $\ge$2 consecutive green laps AND $\ge$50% scheduled sprint distance completed. Single-driver max GP is 25 pts; Constructor max is 43 pts. | `test_2026_grand_prix_consecutive_green_laps_gate`, `test_2026_sprint_scoring_gates`, `test_2026_countback_qualifying_fallback`, `test_2026_regulation_provenance_independence` |
| **2025** | *FIA Formula One World Championship Sporting Regulations* (2025 Issue 1, ratified WMSC 17 Oct 2024) | [fia.com/regulation/category/110](https://www.fia.com/regulation/category/110) | Art. 6.4, 6.5, 7.2 | 25, 18, 15, 12, 10, 8, 6, 4, 2, 1 (Top 10) | 8, 7, 6, 5, 4, 3, 2, 1 (Top 8) | **None** (Rescinded by WMSC amendment for 2025) | Graduated scale: <25% (Col 1: 6-4-3-2-1), 25%–<50% (Col 2: 13-10-8-6-5-4-3-2-1), 50%–<75% (Col 3: 19-14-12-10-8-6-4-3-2-1), $\ge$75% (Full) | Art. 7.2: GP 1st places, 2nd, 3rd, etc. Sprint results excluded from primary GP countback. If fully tied, FIA discretion. | Maximum single-driver GP score is 25 pts (no FL bonus). Constructor max is 43 pts. | `test_fastest_lap_removal_2025_onward`, `test_constructor_max_capacity` |
| **2022–2024** | *FIA Formula One World Championship Sporting Regulations* (2022–2024 Editions, post-Spa 2021 overhaul) | [fia.com/regulation/category/110](https://www.fia.com/regulation/category/110) | Art. 6.4, 6.5, 7.2 | 25, 18, 15, 12, 10, 8, 6, 4, 2, 1 (Top 10) | 8, 7, 6, 5, 4, 3, 2, 1 (Top 8, introduced 2022) | **1 Point**, strictly subject to: 1) Finisher in Top 10, AND 2) Leader completed $\ge$50% race distance. | Graduated 4-band scale (Columns 1 to 4 of Art. 6.5). Requires leader to complete $\ge$2 laps under green flag conditions without safety car. | Art. 7.2: GP 1st, 2nd, 3rd places. Sprint races are distinct sessions not aggregated into GP win countbacks. | FL point awarded in full distance AND 50%–<75% band (Col 3), but suppressed in <25% and 25%–<50% bands. | `test_fastest_lap_top10_condition`, `test_fastest_lap_distance_boundaries`, `test_countback_sprint_vs_grand_prix` |
| **2021** | *2021 Formula One Sporting Regulations* (Issue 13, 8 Dec 2021) | [fia.com/regulation/category/110](https://www.fia.com/regulation/category/110) | Art. 6.4, 6.5, 7.2 | 25, 18, 15, 12, 10, 8, 6, 4, 2, 1 (Top 10) | Inaugural Sprint Qualifying: 3, 2, 1 (Top 3 only) | **1 Point** to Top 10 finisher in races where points are awarded. (No modern 50% distance threshold in 2021 regulations). | Pre-2022 Rule: If leader completed >2 laps but <75% scheduled distance, **Half Points** awarded. | Art. 7.2: GP wins, seconds, thirds. Sprint Qualifying wins did not count as GP wins. | Sprint Qualifying pole/points treated as auxiliary session points. | `test_sprint_points_regulations`, `test_fastest_lap_era_distinction_2019_2021_vs_2022_2024` |
| **2019–2020** | *2019–2020 Formula One Sporting Regulations* (FL point re-introduced March 2019) | [fia.com/regulation/category/110](https://www.fia.com/regulation/category/110) | Art. 6.4, 6.5, 7.2 | 25, 18, 15, 12, 10, 8, 6, 4, 2, 1 (Top 10) | None | **1 Point** to Top 10 finisher in races where points are awarded. | Pre-2022 Rule: Half points if leader completed >2 laps and <75% distance. | Art. 7.2: Most 1st places, then 2nd, 3rd, etc. | FL point eligible even in shortened half-points races (e.g. 12.5 + 1.0 = 13.5 pts). | `test_fastest_lap_era_distinction_2019_2021_vs_2022_2024` |
| **2015–2018** | *2015–2018 Formula One Sporting Regulations* | [fia.com/regulation/category/110](https://www.fia.com/regulation/category/110) | Art. 6.4, 6.5, 7.2 | 25, 18, 15, 12, 10, 8, 6, 4, 2, 1 (Top 10) | None | **None** | Half points if leader completed >2 laps and <75% distance. | Art. 7.2: Most 1st places, then 2nd, 3rd, etc. | Double points rule abolished after 2014. | `test_grand_prix_standard_modern_points` |
| **2014** | *2014 Formula One Sporting Regulations* (WMSC approved Dec 2013) | [fia.com/regulation/category/110](https://www.fia.com/regulation/category/110) | Art. 6.4 ("Double Points"), Art. 6.5, 7.2 | Rounds 1–18: 25, 18, 15, 12, 10, 8, 6, 4, 2, 1.<br>**Round 19 (Abu Dhabi GP Final Event): 50, 36, 30, 24, 20, 16, 12, 8, 4, 2.** | None | **None** | Half points if leader completed >2 laps and <75% distance. | Art. 7.2: Most 1st places, then 2nd, 3rd, etc. | **Final event double points:** Driver max GP score = 50 pts. Constructor max score = 50 + 36 = 86 pts. | `test_2014_double_points_season_finale` |
| **2010–2013** | *2010–2013 Formula One Sporting Regulations* | [fia.com/regulation/category/110](https://www.fia.com/regulation/category/110) | Art. 6.4, 6.5, 7.2 | 25, 18, 15, 12, 10, 8, 6, 4, 2, 1 (Top 10 introduced) | None | **None** | Half points if leader completed >2 laps and <75% distance. | Art. 7.2: Most 1st places, then 2nd, 3rd, etc. | Modern 25-point system introduced in 2010 to reflect grid expansion. | `test_grand_prix_standard_modern_points` |
| **2003–2009** | *2003–2009 Formula One Sporting Regulations* | [fia.com/regulation/category/110](https://www.fia.com/regulation/category/110) | Art. 6.4, 6.5 | 10, 8, 6, 5, 4, 3, 2, 1 (Top 8) | None | **None** | Half points if leader completed >2 laps and <75% distance. (e.g. 2009 Malaysian GP). | Most 1st places, then 2nd, 3rd, etc. | 8-place scoring introduced in 2003 to reward consistency. | `test_grand_prix_historical_eras` |
| **1991–2002** | *1991–2002 Formula One Sporting Regulations* | [fia.com/regulation/category/110](https://www.fia.com/regulation/category/110) | FIA Sporting Code / Appendices | 10, 6, 4, 3, 2, 1 (Top 6) | None | **None** | Half points if leader completed >2 laps and <75% distance. (e.g. 1991 Australian GP). | Most 1st places, then 2nd, 3rd, etc. | All rounds count towards championship (prior drop-score system eliminated in 1991). | `test_grand_prix_historical_eras` |

---

## 3. Detailed Regulatory Provisions

### 3.1. Fastest-Lap Bonus Point Evolution
1. **1991–2018:** No fastest-lap bonus points awarded in any race.
2. **2019–2021 (WMSC March 2019 Amendment):** 1 bonus point awarded to the driver setting the fastest lap, provided they finished classified in the top 10 and the race was not suspended before points were awarded. Crucially, the 50% minimum distance requirement did **not** exist in the regulations during this window.
3. **2022–2024 (Post-Spa 2021 Restructuring):** Article 6.4 required both finishing in the top 10 AND the leader completing at least 50% of scheduled race distance. The bonus was eligible in full-distance races ($\ge 75\%$) and the 50%–<75% band (Column 3 of Article 6.5), but ineligible in the <25% and 25%–<50% bands.
4. **2025 Onward (WMSC October 2024 Decision):** Article 6.4 amended to eliminate the fastest-lap bonus point completely.

### 3.2. 2014 Double Points Finale (Article 6.4)
- Enacted solely for the 2014 season to prolong championship contention until the final round (Abu Dhabi Grand Prix, Round 19).
- Double points applied to both the Driver World Championship and the Constructor World Championship.
- Finishing scale: 50, 36, 30, 24, 20, 16, 12, 8, 4, 2.
- Maximum constructor haul in the finale was 86 points (50 + 36).
- The regulation was universally repealed ahead of the 2015 season.

### 3.3. Shortened Race Distance Bands
- **Pre-2022 Historical Rule:**
  - $< 2$ laps completed: No points awarded.
  - $\ge 2$ laps and $< 75\%$ distance: Half points awarded (50% of standard scale).
  - $\ge 75\%$ distance: Full points awarded.
- **2022 Onward Modern Rule (Article 6.5):**
  - $< 2$ laps under green flag without SC/VSC: No points awarded.
  - $\ge 2$ laps and $< 25\%$ distance: Column 1 (6, 4, 3, 2, 1).
  - $25\% \le \text{distance} < 50\%$: Column 2 (13, 10, 8, 6, 5, 4, 3, 2, 1).
  - $50\% \le \text{distance} < 75\%$: Column 3 (19, 14, 12, 10, 8, 6, 4, 3, 2, 1).
  - $\ge 75\%$ distance: Column 4 (Full 25, 18, 15, 12, 10, 8, 6, 4, 2, 1).

### 3.4. Dead-Heat and Shared Points
- When two or more competitors finish in a dead-heat or tie for finishing positions, the points for all tied positions are aggregated and divided equally among them (decimal points permitted).
- Verified in `calculate_shared_points()` and tested against tied P1 finishes (21.5 pts in modern era; 43.0 pts in 2014 finale).

### 3.5. Tie-Breaking Countback Hierarchy (Historical Seasons 1991–2025: Article 7.2)
1. Most 1st place finishes in Grand Prix races.
2. Most 2nd place finishes in Grand Prix races.
3. Most 3rd place finishes, descending sequentially down to 24th place.
4. **No Sprint or Qualifying Intermediate Stages:** Under Article 7.2, sprint race results (introduced in 2021) and qualifying results are not statutory countback tie-breakers. Sprint victories or points do not alter Grand Prix finishing position tallies.
5. **FIA Discretion on Dead Heat (Article 7.2(d)):** If comparison of all Grand Prix finishing positions fails to produce a winner, Article 7.2(d) explicitly mandates that *"the FIA will nominate the winner according to such criteria as it thinks fit."* In this scenario, the calculation engine returns an unresolved tie (`0`), leaving the outcome to official FIA determination.

### 3.6. Constructor Points Capacity
- In every Grand Prix or Sprint, constructors can score points for up to **two cars**.
- Maximum single-event capacity:
  - 2024 GP + Sprint: $(25 + 18 + 1) + (8 + 7) = 44 + 15 = 59$ points.
  - 2025 GP + Sprint: $(25 + 18) + (8 + 7) = 43 + 15 = 58$ points.
  - 2026 GP + Sprint: $(25 + 18) + (8 + 7) = 43 + 15 = 58$ points.
  - 2014 Finale GP: $(50 + 36) = 86$ points.

### 3.7. 2026 Sporting Regulations & Specific Gates (Section A, Article A2.2 & Article A2.1.4(c))
- **Governing Reference:** Official FIA 2026 Technical & Sporting Regulations, Section A, Issue 03, Article A2.2 (points & scoring gates), Article A2.1.4(c) (countback), and Section B, Issue 09 (published October 1, 2026).
- **Grand Prix Scoring Gate:** No championship points are awarded to any driver or constructor unless the leader has completed at least **two complete, consecutive laps without a Safety Car (SC) or Virtual Safety Car (VSC)** procedure (Article A2.2). Missing eligibility context raises a typed `InsufficientContextError`.
- **Sprint Scoring Gate:** Sprint points (8, 7, 6, 5, 4, 3, 2, 1) are awarded only if:
  1. The leader has completed at least **two complete, consecutive laps without SC or VSC**, AND
  2. At least **50% of the scheduled sprint distance** has been completed (Article A2.2).
- **Championship Countback Fallback to Qualifying (Article A2.1.4(c)):** If competitors remain tied after exhaustive comparison of Grand Prix finishing positions (1st, 2nd, 3rd, etc.), countback falls back directly to **Qualifying results** (comparing most 1st places / pole positions in qualifying, then 2nd places, 3rd places, etc.). If still tied across all criteria, the FIA will nominate the winner. Sprint sessions are not inserted as an intervening tie-break stage for the 2026 Championship countback under Article A2.1.4(c).
- **Session History Invalidation Protection:** Once a qualifying sequence of consecutive green-flag laps has occurred anywhere in session history, eligibility is satisfied and cannot be invalidated by later neutralizations or stoppages.
- **2014 Double Points Event Identity:** Derived strictly from verified season and round metadata (Round 19 of 19) rather than caller-supplied Boolean flags.


