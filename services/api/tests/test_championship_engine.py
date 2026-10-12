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

# 8. Sprint Points Regulations (2021 vs 2022-Present)
def test_sprint_points_regulations():
    # 2021 Sprint Qualifying: Top 3 only (3, 2, 1)
    assert calculate_sprint_points(1, season=2021) == 3.0
    assert calculate_sprint_points(2, season=2021) == 2.0
    assert calculate_sprint_points(3, season=2021) == 1.0
    assert calculate_sprint_points(4, season=2021) == 0.0

    # 2022-Present: Top 8 (8 to 1)
    assert calculate_sprint_points(1, season=2024) == 8.0
    assert calculate_sprint_points(8, season=2024) == 1.0
    assert calculate_sprint_points(9, season=2024) == 0.0

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

# 14. Constructor Maximum Capacity (2 cars per team)
def test_constructor_max_capacity():
    # 2024: 1 GP = P1 (25) + P2 (18) + FL (1) = 44 pts
    # 1 Sprint = P1 (8) + P2 (7) = 15 pts
    assert calculate_max_remaining_points(1, 1, season=2024, is_constructor=True) == 59.0

    # 2025: 1 GP = P1 (25) + P2 (18) = 43 pts (no FL)
    # 1 Sprint = 15 pts
    assert calculate_max_remaining_points(1, 1, season=2025, is_constructor=True) == 58.0

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
    assert evaluate_fia_countback(gp_a, gp_b, sprint_finishes_a=sprints_a, sprint_finishes_b=sprints_b) == -1

    # If GP finishes are identical, sprint finishes break the tie
    gp_tied_a = [1, 1, 2]
    gp_tied_b = [1, 1, 2]
    assert evaluate_fia_countback(gp_tied_a, gp_tied_b, sprint_finishes_a=sprints_a, sprint_finishes_b=sprints_b) == 1

