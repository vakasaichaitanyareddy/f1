"""
APEX GP — Exhaustive Unit Test Suite for FIA Points, Regulations, and Tie-Breaker Engine
Verifies modern and historical scoring, sprint rules, fastest-lap conditions,
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

# 3. Fastest Lap Bonus Rule (2019–2024 top 10 requirement)
def test_fastest_lap_bonus_applicability():
    # Inside top 10 gets bonus
    assert calculate_grand_prix_points(1, fastest_lap=True, season=2024) == 26.0
    assert calculate_grand_prix_points(10, fastest_lap=True, season=2024) == 2.0
    # Outside top 10 gets NO bonus point
    assert calculate_grand_prix_points(11, fastest_lap=True, season=2024) == 0.0
    assert calculate_grand_prix_points(18, fastest_lap=True, season=2024) == 0.0
    # Pre-2019 season did not have fastest lap point
    assert calculate_grand_prix_points(1, fastest_lap=True, season=2018) == 25.0

# 4. Shortened Race Distance Bands (FIA Article 6.5 post-2021)
def test_shortened_race_distance_bands():
    # Less than 25% completed (e.g. 20% distance): 6, 4, 3, 2, 1 (No FL point)
    assert calculate_grand_prix_points(1, distance_completed_ratio=0.20, season=2024) == 6.0
    assert calculate_grand_prix_points(2, distance_completed_ratio=0.20, season=2024) == 4.0
    assert calculate_grand_prix_points(5, distance_completed_ratio=0.20, season=2024) == 1.0
    assert calculate_grand_prix_points(6, distance_completed_ratio=0.20, season=2024) == 0.0

    # 25% to 50% completed (e.g. 40% distance): 13, 10, 8, 6, 5, 4, 3, 2, 1
    assert calculate_grand_prix_points(1, distance_completed_ratio=0.40, season=2024) == 13.0
    assert calculate_grand_prix_points(2, distance_completed_ratio=0.40, season=2024) == 10.0
    assert calculate_grand_prix_points(9, distance_completed_ratio=0.40, season=2024) == 1.0
    assert calculate_grand_prix_points(10, distance_completed_ratio=0.40, season=2024) == 0.0

    # 50% to 75% completed (e.g. 60% distance): 19, 14, 12, 10, 8, 6, 4, 3, 2, 1
    assert calculate_grand_prix_points(1, distance_completed_ratio=0.60, season=2024) == 19.0
    assert calculate_grand_prix_points(2, distance_completed_ratio=0.60, season=2024) == 14.0
    assert calculate_grand_prix_points(10, distance_completed_ratio=0.60, season=2024) == 1.0

    # Pre-2022 Half-Points Rule (e.g. Spa 2021 / Malaysia 2009)
    assert calculate_grand_prix_points(1, distance_completed_ratio=0.60, season=2021) == 12.5
    assert calculate_grand_prix_points(2, distance_completed_ratio=0.60, season=2021) == 9.0

# 5. Penalties and Point Deductions
def test_penalty_point_deductions():
    # Driver finishes P1 (25 pts) but team receives 5 pts deduction penalty
    assert calculate_grand_prix_points(1, penalty_points_deduction=5.0, season=2024) == 20.0
    # Penalty cannot result in negative points
    assert calculate_grand_prix_points(10, penalty_points_deduction=5.0, season=2024) == 0.0

# 6. Sprint Points Regulations (2021 vs 2022-Present)
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

# 7. Maximum Remaining Capacity
def test_max_remaining_points_capacity():
    # 3 GPs (3 * 26 = 78) + 1 Sprint (8) = 86 points in 2024
    assert calculate_max_remaining_points(3, 1, season=2024) == 86.0
    # Historical 2008: 3 GPs * 10 = 30 pts (no sprints, no FL)
    assert calculate_max_remaining_points(3, 0, season=2008) == 30.0

# 8. Countback Tie-Break Resolution
def test_fia_countback_resolution():
    # Driver A: 3 wins, 0 seconds
    # Driver B: 2 wins, 5 seconds
    # A wins on countback of P1s
    assert evaluate_fia_countback([1, 1, 1], [1, 1, 2, 2, 2, 2, 2]) == 1

    # Equal wins (2 each), Driver B has more P2s
    assert evaluate_fia_countback([1, 1, 3], [1, 1, 2]) == -1

    # Equal on all positions
    assert evaluate_fia_countback([1, 2, 3], [1, 2, 3]) == 0

# 9. Mathematical Elimination Edge Cases
def test_mathematical_elimination_scenarios():
    # Strict elimination (max achievable < leader)
    # Leader has 400 pts. Driver has 310 pts. 3 GPs left (78 max pts). 310 + 78 = 388 < 400.
    assert is_mathematically_eliminated(310, 400, remaining_gps=3, remaining_sprints=0) is True

    # Active contender (max achievable > leader)
    assert is_mathematically_eliminated(330, 400, remaining_gps=3, remaining_sprints=0) is False

    # Tie boundary with countback
    # Driver has 322 + 78 = 400 == Leader (400).
    # If Leader has 12 wins, Driver only has 2 wins: Driver CANNOT beat Leader on countback (even winning remaining 3)
    driver_finishes = [1, 1, 2, 3] # With 3 more wins = 5 wins total
    leader_finishes = [1] * 10      # 10 wins
    assert is_mathematically_eliminated(
        322, 400, remaining_gps=3, remaining_sprints=0,
        driver_finishes=driver_finishes, leader_finishes=leader_finishes
    ) is True

# 10. Title Clinching Logic
def test_title_clinching_boundaries():
    # Lead gap > max capacity -> Clinched
    # Leader: 400, P2: 320. Gap: 80. Remaining: 3 GPs (78 pts). 80 > 78 -> CLINCHED
    clinched, gap = calculate_clinch_threshold(400, 320, remaining_gps=3, remaining_sprints=0)
    assert clinched is True
    assert gap == 80.0

    # Lead gap == max capacity, but Leader leads unassailably on countback
    # Leader: 400, P2: 322. Gap: 78. Remaining: 3 GPs (78 pts).
    # Leader has 10 wins, P2 has 2 wins. Even if P2 wins 3 remaining (total 5), Leader has 10 -> CLINCHED!
    clinched, gap = calculate_clinch_threshold(
        400, 322, remaining_gps=3, remaining_sprints=0,
        leader_finishes=[1]*10, p2_finishes=[1]*2
    )
    assert clinched is True
    assert gap == 78.0

    # Lead gap < max capacity -> NOT clinched
    clinched, gap = calculate_clinch_threshold(400, 330, remaining_gps=3, remaining_sprints=0)
    assert clinched is False
