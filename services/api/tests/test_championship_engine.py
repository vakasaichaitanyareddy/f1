"""
APEX GP — Exhaustive Unit Test Suite for FIA Points, Regulations, and Tie-Breaker Engine
Verifies modern, historical, and 2025+ scoring, sprint rules, fastest-lap distance conditions
(Article 6.4 boundaries: below 50%, exactly 50%, between 50% and 75%), 2025 abolition,
shortened race graduated bands (Article 6.5), penalties, countback, and clinching boundaries.
"""

import pytest
from app.championship.engine import (
    calculate_grand_prix_points,
    calculate_sprint_points,
    calculate_max_remaining_points,
    evaluate_fia_countback,
    is_mathematically_eliminated,
    calculate_clinch_threshold,
    is_fastest_lap_eligible,
    get_regulation_provenance,
)

# 1. Standard Modern Era GP Points
def test_grand_prix_standard_modern_points():
    expected = {
        1: 25.0, 2: 18.0, 3: 15.0, 4: 12.0, 5: 10.0,
        6: 8.0, 7: 6.0, 8: 4.0, 9: 2.0, 10: 1.0, 11: 0.0, 20: 0.0
    }
    for pos, pts in expected.items():
        assert calculate_grand_prix_points(pos, season=2024) == pts

# 2. Historical Eras (2003-2009, 1991-2002)
def test_grand_prix_historical_eras():
    # 2003-2009 (10, 8, 6, 5, 4, 3, 2, 1)
    assert calculate_grand_prix_points(1, season=2008) == 10.0
    assert calculate_grand_prix_points(2, season=2008) == 8.0
    assert calculate_grand_prix_points(8, season=2008) == 1.0
    assert calculate_grand_prix_points(9, season=2008) == 0.0

    # 1991-2002 (10, 6, 4, 3, 2, 1)
    assert calculate_grand_prix_points(1, season=1998) == 10.0
    assert calculate_grand_prix_points(2, season=1998) == 6.0
    assert calculate_grand_prix_points(6, season=1998) == 1.0
    assert calculate_grand_prix_points(7, season=1998) == 0.0

# 3. Fastest Lap Bonus Rule (2019–2024 Top 10 Requirement & Distance Conditions)
def test_fastest_lap_top10_condition():
    # Full distance (100%): Top 10 eligible
    assert calculate_grand_prix_points(1, fastest_lap=True, season=2024, distance_completed_ratio=1.0) == 26.0
    assert calculate_grand_prix_points(10, fastest_lap=True, season=2024, distance_completed_ratio=1.0) == 2.0
    # Ineligible finishers (outside top 10)
    assert calculate_grand_prix_points(11, fastest_lap=True, season=2024, distance_completed_ratio=1.0) == 0.0
    assert calculate_grand_prix_points(18, fastest_lap=True, season=2024, distance_completed_ratio=1.0) == 0.0
    # Pre-2019 season did not award FL point
    assert calculate_grand_prix_points(1, fastest_lap=True, season=2018) == 25.0

# 4. Shortened Races and Fastest Lap Distance Boundaries (Below 50%, Exactly 50%, 50% to 75%)
def test_fastest_lap_distance_boundaries():
    # A) Strictly Below 50% distance (< 0.50): FL bonus is INELIGIBLE
    # Case A1: 20% distance (<25% scale: P1 is 6 pts) -> FL NOT awarded
    assert is_fastest_lap_eligible(1, season=2024, distance_completed_ratio=0.20) is False
    assert calculate_grand_prix_points(1, fastest_lap=True, season=2024, distance_completed_ratio=0.20) == 6.0

    # Case A2: 49.9% distance (25%-50% scale: P1 is 13 pts) -> FL NOT awarded
    assert is_fastest_lap_eligible(1, season=2024, distance_completed_ratio=0.499) is False
    assert calculate_grand_prix_points(1, fastest_lap=True, season=2024, distance_completed_ratio=0.499) == 13.0

    # B) Exactly 50% distance (0.50): Leader completed >= 50% distance -> FL bonus is ELIGIBLE!
    # In 50%-75% band (Article 6.5 Column 3), P1 base is 19 pts.
    # With FL bonus: 19 + 1 = 20 pts.
    assert is_fastest_lap_eligible(1, season=2024, distance_completed_ratio=0.50) is True
    assert calculate_grand_prix_points(1, fastest_lap=True, season=2024, distance_completed_ratio=0.50) == 20.0
    # P10 base is 1 pt. With FL: 1 + 1 = 2 pts.
    assert calculate_grand_prix_points(10, fastest_lap=True, season=2024, distance_completed_ratio=0.50) == 2.0
    # P11 base is 0 pts. With FL: 0 pts (outside top 10).
    assert calculate_grand_prix_points(11, fastest_lap=True, season=2024, distance_completed_ratio=0.50) == 0.0

    # C) Between 50% and 75% distance (e.g. 60%, 70%): FL bonus is ELIGIBLE!
    # Crucial rule fix: do not automatically suppress FL bonus for every race in 50%–<75% band!
    assert is_fastest_lap_eligible(1, season=2024, distance_completed_ratio=0.60) is True
    assert calculate_grand_prix_points(1, fastest_lap=True, season=2024, distance_completed_ratio=0.60) == 20.0
    assert calculate_grand_prix_points(2, fastest_lap=True, season=2024, distance_completed_ratio=0.60) == 15.0  # 14 + 1
    assert calculate_grand_prix_points(1, fastest_lap=False, season=2024, distance_completed_ratio=0.60) == 19.0 # Base only

# 5. 2025 Onward Fastest-Lap Bonus Abolition
def test_fastest_lap_removal_2025_onward():
    # 2025 season: No FL bonus under full distance
    assert is_fastest_lap_eligible(1, season=2025, distance_completed_ratio=1.0) is False
    assert calculate_grand_prix_points(1, fastest_lap=True, season=2025, distance_completed_ratio=1.0) == 25.0
    assert calculate_grand_prix_points(10, fastest_lap=True, season=2025, distance_completed_ratio=1.0) == 1.0

    # 2026 season: No FL bonus under any distance
    assert is_fastest_lap_eligible(1, season=2026, distance_completed_ratio=0.60) is False
    assert calculate_grand_prix_points(1, fastest_lap=True, season=2026, distance_completed_ratio=0.60) == 19.0

    # Max remaining points in 2025: 25 pts per GP (not 26) + 8 per sprint
    # 3 GPs (3 * 25 = 75) + 1 Sprint (8) = 83 points
    assert calculate_max_remaining_points(3, 1, season=2025) == 83.0
    assert calculate_max_remaining_points(3, 1, season=2024) == 86.0

# 6. Official FIA Regulatory Metadata Provenance
def test_regulation_provenance_metadata():
    prov_2025 = get_regulation_provenance(2025)
    assert prov_2025["fl_bonus_active"] is False
    assert "Article 6.4 (Fastest lap bonus point rescinded)" in prov_2025["source_reference"]

    prov_2024 = get_regulation_provenance(2024)
    assert prov_2024["fl_bonus_active"] is True
    assert prov_2024["fl_distance_threshold"] == 0.50

    prov_2008 = get_regulation_provenance(2008)
    assert prov_2008["fl_bonus_active"] is False

# 7. Penalties and Point Deductions
def test_penalty_point_deductions():
    # Driver finishes P1 (25 pts) but team receives 5 pts deduction penalty
    assert calculate_grand_prix_points(1, penalty_points_deduction=5.0, season=2024) == 20.0
    # Penalty cannot result in negative points
    assert calculate_grand_prix_points(10, penalty_points_deduction=5.0, season=2024) == 0.0

# 8. Sprint Points Regulations (2021 vs 2022–2025 vs 2026 Article A2.2.2)
def test_sprint_points_regulations():
    # 2021 Sprint Qualifying: Top 3 only (3, 2, 1)
    assert calculate_sprint_points(1, season=2021) == 3.0
    assert calculate_sprint_points(2, season=2021) == 2.0
    assert calculate_sprint_points(3, season=2021) == 1.0
    assert calculate_sprint_points(4, season=2021) == 0.0

    # 2022–2025: Top 8 scale (8, 7, 6, 5, 4, 3, 2, 1) across all eight positions
    expected_2022_2025 = {1: 8.0, 2: 7.0, 3: 6.0, 4: 5.0, 5: 4.0, 6: 3.0, 7: 2.0, 8: 1.0}
    for season_check in [2022, 2023, 2024, 2025]:
        for pos, expected_pts in expected_2022_2025.items():
            assert calculate_sprint_points(pos, season=season_check) == expected_pts
        assert calculate_sprint_points(9, season=season_check) == 0.0
        assert calculate_sprint_points(10, season=season_check) == 0.0

    # 2026: Section A, Issue 03, Article A2.2.2 scale (8, 7, 6, 5, 4, 3, 2, 1) across all eight positions;
    # Eighth place awards 1 point, and ninth place onward awards zero points (P8=1.0, P9=0.0)!
    expected_2026 = {1: 8.0, 2: 7.0, 3: 6.0, 4: 5.0, 5: 4.0, 6: 3.0, 7: 2.0, 8: 1.0}
    for pos, expected_pts in expected_2026.items():
        assert calculate_sprint_points(pos, season=2026, distance_completed_ratio=1.0, consecutive_green_laps=2) == expected_pts
    assert calculate_sprint_points(9, season=2026, distance_completed_ratio=1.0, consecutive_green_laps=2) == 0.0
    assert calculate_sprint_points(10, season=2026, distance_completed_ratio=1.0, consecutive_green_laps=2) == 0.0

# 9. Countback Tie-Break Resolution
def test_fia_countback_resolution():
    # Driver A: 3 wins, 0 seconds
    # Driver B: 2 wins, 5 seconds
    # A wins on countback of P1s
    assert evaluate_fia_countback([1, 1, 1], [1, 1, 2, 2, 2, 2, 2]) == 1

    # Equal wins (2 each), Driver B has more P2s
    assert evaluate_fia_countback([1, 1, 3], [1, 1, 2]) == -1

    # Equal on all positions
    assert evaluate_fia_countback([1, 2, 3], [1, 2, 3]) == 0

# 10. Mathematical Elimination and Clinch Boundaries
def test_mathematical_elimination_and_clinch():
    # Leader has 400 pts. Driver has 310 pts. 3 GPs left in 2024 (78 max pts). 310 + 78 = 388 < 400.
    assert is_mathematically_eliminated(310, 400, remaining_gps=3, remaining_sprints=0, season=2024) is True

    # Active contender in 2024 (330 + 78 = 408 > 400)
    assert is_mathematically_eliminated(330, 400, remaining_gps=3, remaining_sprints=0, season=2024) is False

    # In 2025, 3 GPs left = 3 * 25 = 75 pts.
    # Driver with 326 pts: 326 + 75 = 401 > 400 (Contender)
    assert is_mathematically_eliminated(326, 400, remaining_gps=3, remaining_sprints=0, season=2025) is False
    # Driver with 324 pts: 324 + 75 = 399 < 400 (Eliminated in 2025!)
    assert is_mathematically_eliminated(324, 400, remaining_gps=3, remaining_sprints=0, season=2025) is True

    # Clinch gap
    clinched, gap = calculate_clinch_threshold(400, 320, remaining_gps=3, remaining_sprints=0, season=2024)
    assert clinched is True
    assert gap == 80.0

    # 2026 Season with sprints: 2 GPs + 2 Sprints left
    # Max possible remaining for driver = (2 * 25) + (2 * 8) = 50 + 16 = 66 points
    # Driver with 335 pts vs Leader with 400 pts: 335 + 66 = 401 > 400 (Not eliminated)
    assert is_mathematically_eliminated(335, 400, remaining_gps=2, remaining_sprints=2, season=2026) is False
    # Driver with 333 pts vs Leader with 400 pts: 333 + 66 = 399 < 400 (Eliminated)
    assert is_mathematically_eliminated(333, 400, remaining_gps=2, remaining_sprints=2, season=2026) is True
    # Clinch threshold with 2026 sprint capacity:
    # Lead gap of 67 > 66 max capacity -> Clinched!
    clinched_2026, gap_2026 = calculate_clinch_threshold(400, 333, remaining_gps=2, remaining_sprints=2, season=2026)
    assert clinched_2026 is True
    assert gap_2026 == 67.0
    # Lead gap of 65 < 66 max capacity -> Not clinched!
    clinched_2026_no, gap_2026_no = calculate_clinch_threshold(400, 335, remaining_gps=2, remaining_sprints=2, season=2026)
    assert clinched_2026_no is False
    assert gap_2026_no == 65.0

# 11. 2014 Double Points Season Finale (Article 6.4 of 2014 FIA Sporting Regulations)
def test_2014_double_points_season_finale():
    # Ordinary 2014 GP (Rounds 1-18) awards standard 25-18-15-12-10-8-6-4-2-1
    assert calculate_grand_prix_points(1, season=2014, is_final_event=False) == 25.0
    assert calculate_grand_prix_points(2, season=2014, is_final_event=False) == 18.0
    assert calculate_grand_prix_points(10, season=2014, is_final_event=False) == 1.0

    # 2014 Final Event (Abu Dhabi GP) awards double points: P1=50, P2=36, P3=30, P4=24, P5=20, P6=16, P7=12, P8=8, P9=4, P10=2
    assert calculate_grand_prix_points(1, season=2014, is_final_event=True) == 50.0
    assert calculate_grand_prix_points(2, season=2014, is_final_event=True) == 36.0
    assert calculate_grand_prix_points(3, season=2014, is_final_event=True) == 30.0
    assert calculate_grand_prix_points(4, season=2014, is_final_event=True) == 24.0
    assert calculate_grand_prix_points(5, season=2014, is_final_event=True) == 20.0
    assert calculate_grand_prix_points(6, season=2014, is_final_event=True) == 16.0
    assert calculate_grand_prix_points(7, season=2014, is_final_event=True) == 12.0
    assert calculate_grand_prix_points(8, season=2014, is_final_event=True) == 8.0
    assert calculate_grand_prix_points(9, season=2014, is_final_event=True) == 4.0
    assert calculate_grand_prix_points(10, season=2014, is_final_event=True) == 2.0
    assert calculate_grand_prix_points(11, season=2014, is_final_event=True) == 0.0

    # Ensure other seasons do not erroneously trigger double points
    assert calculate_grand_prix_points(1, season=2024, is_final_event=True) == 25.0
    assert calculate_grand_prix_points(1, season=2013, is_final_event=True) == 25.0

    # Max remaining points with 2014 finale included:
    # If 1 GP remaining in 2014 and it's the finale: 50 pts (driver) or 50 + 36 = 86 pts (constructor)
    assert calculate_max_remaining_points(1, 0, season=2014, is_constructor=False, final_event_included=True) == 50.0
    assert calculate_max_remaining_points(1, 0, season=2014, is_constructor=True, final_event_included=True) == 86.0

    # If 2 GPs remaining in 2014 (1 regular + 1 double finale): 25 + 50 = 75 pts (driver)
    # Constructor: (25 + 18) + (50 + 36) = 43 + 86 = 129 pts
    assert calculate_max_remaining_points(2, 0, season=2014, is_constructor=False, final_event_included=True) == 75.0
    assert calculate_max_remaining_points(2, 0, season=2014, is_constructor=True, final_event_included=True) == 129.0

# 12. 2019–2021 vs 2022–2024 Fastest Lap Distance Distinction
def test_fastest_lap_era_distinction_2019_2021_vs_2022_2024():
    # In 2019-2021, the regulations awarded FL point to top 10 finisher if points were awarded,
    # without the post-Spa 2021 50% distance condition.
    # E.g. at 40% race distance:
    # 2020: FL point is eligible (as top 10 finished in a shortened race awarding half-points)
    assert is_fastest_lap_eligible(1, season=2020, distance_completed_ratio=0.40) is True
    # Half points for P1 in 2020 = 12.5 + 1.0 (FL) = 13.5 pts
    assert calculate_grand_prix_points(1, fastest_lap=True, season=2020, distance_completed_ratio=0.40) == 13.5

    # 2023: Under modern Article 6.4, leader must complete >= 50% distance for FL point to be awarded.
    # At 40% distance (<50% band), Column 2 applies (P1 base = 13 pts), but FL is INELIGIBLE
    assert is_fastest_lap_eligible(1, season=2023, distance_completed_ratio=0.40) is False
    assert calculate_grand_prix_points(1, fastest_lap=True, season=2023, distance_completed_ratio=0.40) == 13.0

# 13. Dead-Heat Tied Finishes and Split Points
def test_dead_heat_shared_points():
    from app.championship.engine import calculate_shared_points

    # Modern era: 2 drivers dead-heat for P1 (tied across P1 and P2)
    # Points for P1 (25) + P2 (18) = 43 pts / 2 = 21.5 pts each
    assert calculate_shared_points([1, 2], season=2024) == 21.5

    # 3 drivers tie across P3, P4, P5
    # P3 (15) + P4 (12) + P5 (10) = 37 pts / 3 = 12.3333... pts each
    shared_3way = calculate_shared_points([3, 4, 5], season=2024)
    assert abs(shared_3way - (37.0 / 3.0)) < 1e-6

    # 2014 Finale dead-heat for P1 (tied across P1 and P2)
    # P1 (50) + P2 (36) = 86 pts / 2 = 43.0 pts each
    assert calculate_shared_points([1, 2], season=2014, is_final_event=True) == 43.0

    # Sprint dead-heat across P8 and P9 (boundary test where P8 awards 1 pt and P9 awards 0 pts):
    # Total points = P8 (1.0) + P9 (0.0) = 1.0 / 2 = 0.5 points each
    # In 2024:
    assert calculate_shared_points([8, 9], season=2024, is_sprint=True) == 0.5
    # In 2026:
    assert calculate_shared_points([8, 9], season=2026, is_sprint=True, consecutive_green_laps=2) == 0.5
    # Dead-heat across P1 and P2 in 2026 Sprint: P1 (8) + P2 (7) = 15 / 2 = 7.5 pts each
    assert calculate_shared_points([1, 2], season=2026, is_sprint=True, consecutive_green_laps=2) == 7.5
    # Dead-heat across P7 and P8 in 2026 Sprint: P7 (2) + P8 (1) = 3 / 2 = 1.5 pts each
    assert calculate_shared_points([7, 8], season=2026, is_sprint=True, consecutive_green_laps=2) == 1.5

# 14. Constructor Maximum Capacity (2 cars per team)
def test_constructor_max_capacity():
    # 2024: 1 GP = P1 (25) + P2 (18) + FL (1) = 44 pts
    # 1 Sprint = P1 (8) + P2 (7) = 15 pts
    assert calculate_max_remaining_points(1, 1, season=2024, is_constructor=True) == 59.0

    # 2025: 1 GP = P1 (25) + P2 (18) = 43 pts (no FL)
    # 1 Sprint = 15 pts
    assert calculate_max_remaining_points(1, 1, season=2025, is_constructor=True) == 58.0

    # 2026: 1 GP = P1 (25) + P2 (18) = 43 pts (no FL)
    # 1 Sprint = P1 (8) + P2 (7) = 15 pts (Article A2.2.2)
    assert calculate_max_remaining_points(1, 1, season=2026, is_constructor=True) == 58.0

# 15. Countback Distinction Between Grand Prix and Sprint Race Wins
def test_countback_sprint_vs_grand_prix():
    # Competitor A: 2 Grand Prix wins, 0 GP P2s, 5 Sprint wins
    # Competitor B: 3 Grand Prix wins, 0 GP P2s, 0 Sprint wins
    # Under FIA Article 7.2, Competitor B wins the countback because Grand Prix wins take precedence!
    gp_a = [1, 1, 3]
    gp_b = [1, 1, 1]
    sprints_a = [1, 1, 1, 1, 1]
    sprints_b = [2, 2, 2, 2, 2]

    # B wins based on GP finishing positions despite A having 5 sprint wins
    assert evaluate_fia_countback(gp_a, gp_b, sprint_finishes_a=sprints_a, sprint_finishes_b=sprints_b, season=2024) == -1

    # Under Article 7.2 for pre-2026 seasons (e.g. 2024), if Grand Prix race finishes are identical,
    # Sprint results are NOT a statutory tie-breaker under the regulations.
    # The tie is unresolved and subject to FIA discretion under Article 7.2(d), returning 0.
    gp_tied_a = [1, 1, 2]
    gp_tied_b = [1, 1, 2]
    assert evaluate_fia_countback(gp_tied_a, gp_tied_b, sprint_finishes_a=sprints_a, sprint_finishes_b=sprints_b, season=2024) == 0

# 16. 2026 Grand Prix Scoring Gate (Section A, Issue 03, Article A2.2)
def test_2026_grand_prix_consecutive_green_laps_gate():
    # Case A: Insufficient consecutive green-flag laps (< 2 complete laps without SC/VSC)
    # E.g. Race completed 30 laps, but safety car intervened constantly, maximum consecutive green laps was 1
    # Under Section A, Article A2.2, NO championship points are awarded.
    assert calculate_grand_prix_points(1, season=2026, distance_completed_ratio=0.80, consecutive_green_laps=1) == 0.0
    assert calculate_grand_prix_points(2, season=2026, distance_completed_ratio=0.80, consecutive_green_laps=0) == 0.0
    assert calculate_grand_prix_points(10, season=2026, distance_completed_ratio=0.80, consecutive_green_laps=1) == 0.0

    # Case B: Exactly 2 consecutive green-flag laps completed without SC/VSC
    # Gate is satisfied! Points awarded according to distance band.
    # Full distance: P1 = 25.0
    assert calculate_grand_prix_points(1, season=2026, distance_completed_ratio=1.0, consecutive_green_laps=2) == 25.0
    # 50%-75% band: P1 = 19.0
    assert calculate_grand_prix_points(1, season=2026, distance_completed_ratio=0.60, consecutive_green_laps=2) == 19.0
    # 25%-50% band: P1 = 13.0
    assert calculate_grand_prix_points(1, season=2026, distance_completed_ratio=0.40, consecutive_green_laps=2) == 13.0
    # <25% band: P1 = 6.0
    assert calculate_grand_prix_points(1, season=2026, distance_completed_ratio=0.20, consecutive_green_laps=2) == 6.0

    # More than 2 consecutive green laps (e.g. 10 laps)
    assert calculate_grand_prix_points(1, season=2026, distance_completed_ratio=1.0, consecutive_green_laps=10) == 25.0

    # Earlier seasons (e.g. 2024, 2025) do not enforce this specific 2026 gate if not provided or legacy
    assert calculate_grand_prix_points(1, season=2024, distance_completed_ratio=1.0, consecutive_green_laps=1) == 25.0

# 17. 2026 Sprint Scoring Gate (Section A, Issue 03, Article A2.2)
def test_2026_sprint_scoring_gates():
    # Sprint Condition 1: Must complete at least 2 consecutive green-flag laps without SC/VSC
    # Case A: 1 consecutive lap -> NO sprint points
    assert calculate_sprint_points(1, season=2026, distance_completed_ratio=0.75, consecutive_green_laps=1) == 0.0

    # Sprint Condition 2: Must complete at least 50% of scheduled sprint distance
    # Case B: Immediately below 50% distance (e.g. 49.9% or 45%) even with >=2 green laps -> NO points
    assert calculate_sprint_points(1, season=2026, distance_completed_ratio=0.499, consecutive_green_laps=5) == 0.0
    assert calculate_sprint_points(8, season=2026, distance_completed_ratio=0.45, consecutive_green_laps=3) == 0.0

    # Case C: Exactly 50% distance (0.50) with exactly 2 consecutive green laps -> POINTS AWARDED!
    # Under Section A, Issue 03, Article A2.2.2:
    # P1=8, P2=7, P3=6, P4=5, P5=4, P6=3, P7=2, P8=1.
    # Ninth place and below award zero points (P9=0.0, P10=0.0)!
    assert calculate_sprint_points(1, season=2026, distance_completed_ratio=0.50, consecutive_green_laps=2) == 8.0
    assert calculate_sprint_points(2, season=2026, distance_completed_ratio=0.50, consecutive_green_laps=2) == 7.0
    assert calculate_sprint_points(7, season=2026, distance_completed_ratio=0.50, consecutive_green_laps=2) == 2.0
    assert calculate_sprint_points(8, season=2026, distance_completed_ratio=0.50, consecutive_green_laps=2) == 1.0
    assert calculate_sprint_points(9, season=2026, distance_completed_ratio=0.50, consecutive_green_laps=2) == 0.0

    # Case D: Full sprint distance (100%) with 10 green laps
    assert calculate_sprint_points(1, season=2026, distance_completed_ratio=1.0, consecutive_green_laps=10) == 8.0
    assert calculate_sprint_points(7, season=2026, distance_completed_ratio=1.0, consecutive_green_laps=10) == 2.0
    assert calculate_sprint_points(8, season=2026, distance_completed_ratio=1.0, consecutive_green_laps=10) == 1.0
    assert calculate_sprint_points(9, season=2026, distance_completed_ratio=1.0, consecutive_green_laps=10) == 0.0

# 18. 2026 Championship Countback Fallback to Qualifying Results (Section A, Article A2.1.4(c))
def test_2026_countback_qualifying_fallback():
    # Both competitors have identical GP race results: [1, 2, 3] each.
    # Note: Competitor A has 1 sprint win, Competitor B has 5 sprint wins.
    # Under Section A, Article A2.1.4(c), 2026 countback proceeds directly from GP race finishes
    # to Qualifying finishes (comparing pole positions), without an intervening sprint tie-break stage!
    gp_finishes = [1, 2, 3]
    sprints_a = [1]
    sprints_b = [1, 1, 1, 1, 1]

    # Driver A: Qualifying [1, 1, 3] (two poles)
    # Driver B: Qualifying [1, 2, 2] (one pole)
    # Under 2026 Ruleset (Section A, Article A2.1.4(c)), Driver A wins on qualifying countback!
    assert evaluate_fia_countback(
        gp_finishes,
        gp_finishes,
        sprint_finishes_a=sprints_a,
        sprint_finishes_b=sprints_b,
        qualifying_finishes_a=[1, 1, 3],
        qualifying_finishes_b=[1, 2, 2],
        season=2026,
    ) == 1

    # Conversely, Driver B has more qualifying 2nd places when poles are tied
    assert evaluate_fia_countback(
        gp_finishes,
        gp_finishes,
        sprint_finishes_a=sprints_a,
        sprint_finishes_b=sprints_b,
        qualifying_finishes_a=[1, 3, 3],
        qualifying_finishes_b=[1, 2, 3],
        season=2026,
    ) == -1

    # Completely tied on GP AND Qualifying results -> 0 (FIA discretion)
    assert evaluate_fia_countback(
        gp_finishes,
        gp_finishes,
        sprint_finishes_a=sprints_a,
        sprint_finishes_b=sprints_b,
        qualifying_finishes_a=[1, 2, 3],
        qualifying_finishes_b=[1, 2, 3],
        season=2026,
    ) == 0

    # In pre-2026 seasons (e.g. 2024), neither sprint nor qualifying is an official statutory countback step under Article 7.2.
    # When Grand Prix finishes are identical, the outcome is unresolved (returns 0, subject to FIA discretion).
    assert evaluate_fia_countback(
        gp_finishes,
        gp_finishes,
        sprint_finishes_a=sprints_a,
        sprint_finishes_b=sprints_b,
        qualifying_finishes_a=[1, 1, 3],
        qualifying_finishes_b=[1, 2, 2],
        season=2024,
    ) == 0

# 19. 2026 Provenance Metadata Independence
def test_2026_regulation_provenance_independence():
    prov_2026 = get_regulation_provenance(2026)
    prov_2025 = get_regulation_provenance(2025)

    assert prov_2026["season_range"] == "2026"
    assert "Section A, Issue 03" in prov_2026["document_version"]
    assert "Article A2.2" in prov_2026["source_reference"]
    assert "Article A2.1.4(c)" in prov_2026["source_reference"]
    assert prov_2026["consecutive_green_laps_required"] == 2
    assert prov_2026["sprint_min_distance_ratio"] == 0.50
    assert prov_2026["countback_qualifying_fallback"] is True

    # 2025 retains distinct metadata
    assert prov_2025["season_range"] == "2025"
    assert "2025 Issue 1" in prov_2025["document_version"]
    assert "Article 6.4" in prov_2025["source_reference"]
    assert prov_2025["countback_qualifying_fallback"] is False

# 20. Missing-Context Handling and Typed Errors (2026 Gates & Distance)
def test_missing_context_handling_and_typed_errors():
    from app.championship.engine import InsufficientContextError, resolve_distance_band

    # When require_eligibility_context=True and consecutive_green_laps is omitted or None
    with pytest.raises(InsufficientContextError, match="requires 'consecutive_green_laps' context"):
        calculate_grand_prix_points(1, season=2026, require_eligibility_context=True)

    with pytest.raises(InsufficientContextError, match="requires 'consecutive_green_laps' context"):
        calculate_sprint_points(1, season=2026, require_eligibility_context=True)

    # When distance context is explicitly None and lap counts are not provided
    with pytest.raises(InsufficientContextError, match="Race distance context is missing"):
        resolve_distance_band(distance_completed_ratio=None, laps_completed=None, scheduled_laps=None)

    with pytest.raises(InsufficientContextError, match="Race distance context is missing"):
        calculate_grand_prix_points(1, season=2026, distance_completed_ratio=None, consecutive_green_laps=2)

    with pytest.raises(InsufficientContextError, match="Race distance context is missing"):
        calculate_sprint_points(1, season=2026, distance_completed_ratio=None, consecutive_green_laps=2)

# 21. Consecutive-Lap Eligibility Session History Preservation
def test_consecutive_lap_history_not_invalidated_by_later_neutralization():
    from app.championship.engine import verify_consecutive_laps_history

    # Scenario 1: Green flag on laps 1-3 (3 consecutive green laps), then SC on lap 4, then race stopped
    # Laps: [False (green), False (green), False (green), True (SC), True (SC)]
    flags_early_green = [False, False, False, True, True]
    is_eligible, max_green = verify_consecutive_laps_history(flags_early_green, min_consecutive=2)
    assert is_eligible is True
    assert max_green == 3

    # Scenario 2: Safety car on laps 1-5, green flag on laps 6-7 (2 consecutive green laps),
    # then VSC on lap 8, then red flag.
    # Later neutralization CANNOT invalidate the qualifying sequence!
    flags_mid_green = [True, True, True, True, True, False, False, True]
    is_eligible, max_green = verify_consecutive_laps_history(flags_mid_green, min_consecutive=2)
    assert is_eligible is True
    assert max_green == 2

    # Scenario 3: Intermittent safety cars where consecutive green laps never reached 2
    # E.g.: [Green, SC, Green, SC, Green, SC] -> max consecutive green is 1
    flags_never_2 = [False, True, False, True, False, True]
    is_eligible, max_green = verify_consecutive_laps_history(flags_never_2, min_consecutive=2)
    assert is_eligible is False
    assert max_green == 1

# 22. Exact Integer Lap Counts and Distance Boundaries (Uneven Divisions)
def test_distance_thresholds_exact_integer_lap_counts():
    # 53-lap race (e.g. Monza / Suzuka schedule):
    # 25% = 13.25 laps -> 13 laps is <25%, 14 laps is >=25%
    # 50% = 26.50 laps -> 26 laps is <50%, 27 laps is >=50%
    # 75% = 39.75 laps -> 39 laps is <75%, 40 laps is >=75%

    # A) 13 laps / 53 laps = 0.24528 (< 25% band, Column 1)
    pts_13 = calculate_grand_prix_points(1, season=2024, laps_completed=13, scheduled_laps=53)
    assert pts_13 == 6.0

    # B) 14 laps / 53 laps = 0.26415 (25% to <50% band, Column 2)
    pts_14 = calculate_grand_prix_points(1, season=2024, laps_completed=14, scheduled_laps=53)
    assert pts_14 == 13.0

    # C) 26 laps / 53 laps = 0.49056 (< 50% band, Column 2)
    pts_26 = calculate_grand_prix_points(1, season=2024, laps_completed=26, scheduled_laps=53)
    assert pts_26 == 13.0

    # D) 27 laps / 53 laps = 0.50943 (50% to <75% band, Column 3)
    pts_27 = calculate_grand_prix_points(1, season=2024, laps_completed=27, scheduled_laps=53)
    assert pts_27 == 19.0

    # E) 39 laps / 53 laps = 0.73584 (< 75% band, Column 3)
    pts_39 = calculate_grand_prix_points(1, season=2024, laps_completed=39, scheduled_laps=53)
    assert pts_39 == 19.0

    # F) 40 laps / 53 laps = 0.75471 (>= 75% Full distance, Column 4)
    pts_40 = calculate_grand_prix_points(1, season=2024, laps_completed=40, scheduled_laps=53)
    assert pts_40 == 25.0

    # 44-lap race (e.g. Spa):
    # 50% = exactly 22 laps -> at 22 laps, ratio == 0.50 exactly
    pts_22_spa = calculate_grand_prix_points(1, season=2024, laps_completed=22, scheduled_laps=44)
    assert pts_22_spa == 19.0

# 23. 2014 Season Finale Metadata Verification
def test_2014_finale_derived_from_official_round_metadata():
    # Ordinary rounds in 2014 (Round 1 to 18 of 19): standard 25 points, double points MUST NOT activate
    assert calculate_grand_prix_points(1, season=2014, round_number=1, total_rounds=19) == 25.0
    assert calculate_grand_prix_points(1, season=2014, round_number=10, total_rounds=19) == 25.0
    assert calculate_grand_prix_points(1, season=2014, round_number=18, total_rounds=19) == 25.0

    # Even if an erroneous is_final_event=True is passed for Round 10, round metadata takes precedence!
    assert calculate_grand_prix_points(1, season=2014, round_number=10, total_rounds=19, is_final_event=True) == 25.0

    # Round 19 of 19: Official finale -> DOUBLE POINTS ACTIVATE (P1 = 50.0, P2 = 36.0)
    assert calculate_grand_prix_points(1, season=2014, round_number=19, total_rounds=19) == 50.0
    assert calculate_grand_prix_points(2, season=2014, round_number=19, total_rounds=19) == 36.0

    # Round 19 of other seasons (e.g. 2024 round 19): NEVER awards double points
    assert calculate_grand_prix_points(1, season=2024, round_number=19, total_rounds=24) == 25.0

# 24. Season-Specific Countback Regression Suite (2021, 2022, 2025, 2026)
def test_season_specific_countback_behavior():
    # Common scenarios for identical GP results
    gp_tied = [1, 1, 2, 3]  # Both have 2 wins, 1 second, 1 third
    sprints_a = [1, 1]      # Driver A has 2 sprint wins
    sprints_b = [2, 3]      # Driver B has 0 sprint wins
    quali_a = [1, 1, 1]     # Driver A has 3 poles
    quali_b = [2, 2, 2]     # Driver B has 0 poles

    # A) 2021 Season (Inaugural Sprint Qualifying era, Article 7.2)
    # Under 2021 Art 7.2, sprint and qualifying results are not statutory countback criteria.
    # Tied GP finishes -> unresolved / FIA nomination -> returns 0.
    assert evaluate_fia_countback(
        gp_tied, gp_tied,
        sprint_finishes_a=sprints_a, sprint_finishes_b=sprints_b,
        qualifying_finishes_a=quali_a, qualifying_finishes_b=quali_b,
        season=2021,
    ) == 0

    # B) 2022 Season (Sprint format expansion to top 8, Article 7.2)
    # Under 2022 Art 7.2, tie-breaker is exclusively GP finishes.
    # Sprint and qualifying differences do not alter the statutory result -> returns 0.
    assert evaluate_fia_countback(
        gp_tied, gp_tied,
        sprint_finishes_a=sprints_a, sprint_finishes_b=sprints_b,
        qualifying_finishes_a=quali_a, qualifying_finishes_b=quali_b,
        season=2022,
    ) == 0

    # C) 2025 Season (Fastest lap bonus rescinded, Article 7.2)
    # Under 2025 Art 7.2, identical GP finishes fail to produce a winner -> returns 0 (Art 7.2(d)).
    assert evaluate_fia_countback(
        gp_tied, gp_tied,
        sprint_finishes_a=sprints_a, sprint_finishes_b=sprints_b,
        qualifying_finishes_a=quali_a, qualifying_finishes_b=quali_b,
        season=2025,
    ) == 0

    # D) 2026 Season (Section A, Article A2.1.4(c))
    # Direct statutory fallback to Qualifying results: Driver A (3 poles) wins over Driver B (0 poles)!
    assert evaluate_fia_countback(
        gp_tied, gp_tied,
        sprint_finishes_a=sprints_a, sprint_finishes_b=sprints_b,
        qualifying_finishes_a=quali_a, qualifying_finishes_b=quali_b,
        season=2026,
    ) == 1

    # In 2026, if Driver B has more poles, Driver B wins (-1):
    assert evaluate_fia_countback(
        gp_tied, gp_tied,
        sprint_finishes_a=sprints_a, sprint_finishes_b=sprints_b,
        qualifying_finishes_a=quali_b, qualifying_finishes_b=quali_a,
        season=2026,
    ) == -1

    # In 2026, sprint finishes do not override qualifying fallback:
    # Driver A has better sprints, but Driver B has better qualifying -> Driver B wins (-1)
    assert evaluate_fia_countback(
        gp_tied, gp_tied,
        sprint_finishes_a=sprints_a, sprint_finishes_b=sprints_b,
        qualifying_finishes_a=[2, 2], qualifying_finishes_b=[1, 2],
        season=2026,
    ) == -1

    # If 2026 qualifying results are also identical, returns 0 (unresolved / FIA discretion):
    assert evaluate_fia_countback(
        gp_tied, gp_tied,
        sprint_finishes_a=sprints_a, sprint_finishes_b=sprints_b,
        qualifying_finishes_a=[1, 2], qualifying_finishes_b=[1, 2],
        season=2026,
    ) == 0

def test_scenario_calculator_mathematical_bounds():
    from app.championship.engine import calculate_driver_scenario_to_win

    # 1. Target driver trailing by 20 points with 2 GPs remaining (no sprints, 2024: 26 max pts/GP = 52 max)
    res = calculate_driver_scenario_to_win(
        target_driver_code="NOR",
        target_points=100.0,
        rival_driver_code="VER",
        rival_points=120.0,
        remaining_gps=2,
        remaining_sprints=0,
        season=2024
    )
    assert res["target_driver"] == "NOR"
    assert res["rival_driver"] == "VER"
    assert res["point_gap"] == 20.0
    assert res["is_eliminated"] is False
    assert res["clinched_now"] is False
    assert res["min_points_needed_if_rival_zero"] == 21.0
    # Rival cap: NOR max points = 100 + 52 = 152. Max VER can score = 152 - 120 = 32.0 pts
    assert res["max_rival_points_allowed"] == 32.0
    assert len(res["scenarios"]) == 2

    # 2. Target driver mathematically eliminated (trailing by 60 with 2 GPs remaining -> 52 max pts)
    res_elim = calculate_driver_scenario_to_win(
        target_driver_code="HAM",
        target_points=50.0,
        rival_driver_code="VER",
        rival_points=120.0,
        remaining_gps=2,
        remaining_sprints=0,
        season=2024
    )
    assert res_elim["is_eliminated"] is True
    assert res_elim["min_points_needed_if_rival_zero"] is None
    assert res_elim["max_rival_points_allowed"] == 0.0

    # 3. Target driver already clinched (leading by 70 with 2 GPs remaining -> max rival capacity = 52)
    res_clinch = calculate_driver_scenario_to_win(
        target_driver_code="VER",
        target_points=200.0,
        rival_driver_code="NOR",
        rival_points=130.0,
        remaining_gps=2,
        remaining_sprints=0,
        season=2024
    )
    assert res_clinch["clinched_now"] is True
    assert res_clinch["point_gap"] == -70.0
    assert res_clinch["min_points_needed_if_rival_zero"] == 0.0
    assert res_clinch["min_points_to_clinch"] == 0.0

    # 4. Target driver ahead of rival but not yet clinched (2024: leading by 8 pts with 23 GPs & 6 sprints remaining)
    # Target (VER: 26) vs Rival (PER: 18), capacity = 23*26 + 6*8 = 646. Lead = 8.
    res_ahead = calculate_driver_scenario_to_win(
        target_driver_code="VER",
        target_points=26.0,
        rival_driver_code="PER",
        rival_points=18.0,
        remaining_gps=23,
        remaining_sprints=6,
        season=2024
    )
    assert res_ahead["is_eliminated"] is False
    assert res_ahead["clinched_now"] is False
    assert res_ahead["point_gap"] == -8.0
    # Rival scores 0 -> Target already ahead by 8, needs 0 additional points to beat rival
    assert res_ahead["min_points_needed_if_rival_zero"] == 0.0
    # To guarantee clinching against rival's maximum 646 capacity: 646 - 8 + 1 = 639.0 points
    assert res_ahead["min_points_to_clinch"] == 639.0
    assert res_ahead["max_rival_points_allowed"] == 646.0

    # 5. Exactly tied with rival (gap = 0)
    res_tied_no_tb = calculate_driver_scenario_to_win(
        target_driver_code="LEC",
        target_points=100.0,
        rival_driver_code="NOR",
        rival_points=100.0,
        remaining_gps=1,
        remaining_sprints=0,
        season=2024
    )
    assert res_tied_no_tb["point_gap"] == 0.0
    assert res_tied_no_tb["min_points_needed_if_rival_zero"] == 1.0
    assert res_tied_no_tb["min_points_to_clinch"] == 27.0  # 26 max capacity + 1.0

    # 6. Exactly tied with rival with countback tie advantage
    res_tied_tb = calculate_driver_scenario_to_win(
        target_driver_code="LEC",
        target_points=100.0,
        rival_driver_code="NOR",
        rival_points=100.0,
        remaining_gps=1,
        remaining_sprints=0,
        target_finishes=[1, 1],
        rival_finishes=[2, 2],
        season=2024
    )
    assert res_tied_tb["countback_tie_advantage"] is True
    assert res_tied_tb["min_points_needed_if_rival_zero"] == 0.0

    # 7. Zero remaining events (season over)
    res_zero_remaining_ahead = calculate_driver_scenario_to_win(
        target_driver_code="VER",
        target_points=400.0,
        rival_driver_code="NOR",
        rival_points=380.0,
        remaining_gps=0,
        remaining_sprints=0,
        season=2024
    )
    assert res_zero_remaining_ahead["clinched_now"] is True
    assert res_zero_remaining_ahead["min_points_needed_if_rival_zero"] == 0.0
    assert res_zero_remaining_ahead["min_points_to_clinch"] == 0.0
    assert res_zero_remaining_ahead["max_rival_points_allowed"] == 0.0

def test_championship_monte_carlo_simulator():
    from app.championship.simulator import ChampionshipMonteCarloSimulator

    standings = [
        {"driver_code": "VER", "points": 100.0, "wins": 3},
        {"driver_code": "PER", "points": 80.0, "wins": 1},
        {"driver_code": "LEC", "points": 70.0, "wins": 0},
        {"driver_code": "NOR", "points": 60.0, "wins": 0},
    ]

    sim = ChampionshipMonteCarloSimulator(
        standings=standings,
        remaining_gps=5,
        remaining_sprints=2,
        season=2024,
        random_seed=123
    )

    res = sim.run_simulation(iterations=1000)
    assert res["iterations"] == 1000
    assert len(res["probabilities"]) == 4

    # Leader VER should have the highest title probability
    ver_entry = next(p for p in res["probabilities"] if p["driver_code"] == "VER")
    nor_entry = next(p for p in res["probabilities"] if p["driver_code"] == "NOR")
    assert ver_entry["championship_probability_pct"] > nor_entry["championship_probability_pct"]
    assert ver_entry["expected_final_points"] > ver_entry["current_points"]

    # Sum of probabilities across all drivers should equal approximately 100%
    total_pct = sum(p["championship_probability_pct"] for p in res["probabilities"])
    assert 99.0 <= total_pct <= 101.0
    assert "model_assumptions" in res
    assert res["model_assumptions"]["baseline_dnf_rate_pct"] == 7.5


def test_championship_simulator_historical_scoring_eras():
    """
    Verifies that the Monte Carlo simulator applies the exact historical scoring
    rules corresponding to the simulated season (2003-2009 P1=10, 1991-2002 P1=10/P2=6,
    2021 sprint 3-2-1, 2026 sprint 8-1).
    """
    from app.championship.simulator import ChampionshipMonteCarloSimulator

    # 1. 2005 Season (10-8-6-5-4-3-2-1, no sprints)
    sim_2005 = ChampionshipMonteCarloSimulator(
        standings=[{"driver_code": "ALO", "points": 50.0}, {"driver_code": "RAI", "points": 40.0}],
        season=2005
    )
    assert sim_2005._get_points_for_position(1, is_sprint=False) == 10.0
    assert sim_2005._get_points_for_position(2, is_sprint=False) == 8.0
    assert sim_2005._get_points_for_position(9, is_sprint=False) == 0.0

    # 2. 1998 Season (10-6-4-3-2-1, no sprints)
    sim_1998 = ChampionshipMonteCarloSimulator(
        standings=[{"driver_code": "HAK", "points": 30.0}, {"driver_code": "MSC", "points": 24.0}],
        season=1998
    )
    assert sim_1998._get_points_for_position(1, is_sprint=False) == 10.0
    assert sim_1998._get_points_for_position(2, is_sprint=False) == 6.0
    assert sim_1998._get_points_for_position(7, is_sprint=False) == 0.0

    # 3. 2021 Sprint Scale (3-2-1)
    sim_2021 = ChampionshipMonteCarloSimulator(
        standings=[{"driver_code": "VER", "points": 200.0}, {"driver_code": "HAM", "points": 195.0}],
        season=2021
    )
    assert sim_2021._get_points_for_position(1, is_sprint=True) == 3.0
    assert sim_2021._get_points_for_position(2, is_sprint=True) == 2.0
    assert sim_2021._get_points_for_position(3, is_sprint=True) == 1.0
    assert sim_2021._get_points_for_position(4, is_sprint=True) == 0.0

    # 4. Modern 2024 Season (25-18-15... and sprint 8-7-6...)
    sim_2024 = ChampionshipMonteCarloSimulator(
        standings=[{"driver_code": "VER", "points": 100.0}],
        season=2024
    )
    assert sim_2024._get_points_for_position(1, is_sprint=False) == 25.0
    assert sim_2024._get_points_for_position(1, is_sprint=True) == 8.0






