"""
APEX GP — Unit Test Suite for FIA Points, Scoring, and Tie-Breaker Countback Engine
Ensures mathematical accuracy and compliance with Official FIA Formula 1 Sporting Regulations.
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

def test_grand_prix_standard_points():
    assert calculate_grand_prix_points(1) == 25.0
    assert calculate_grand_prix_points(2) == 18.0
    assert calculate_grand_prix_points(3) == 15.0
    assert calculate_grand_prix_points(4) == 12.0
    assert calculate_grand_prix_points(5) == 10.0
    assert calculate_grand_prix_points(6) == 8.0
    assert calculate_grand_prix_points(7) == 6.0
    assert calculate_grand_prix_points(8) == 4.0
    assert calculate_grand_prix_points(9) == 2.0
    assert calculate_grand_prix_points(10) == 1.0
    # Outside top 10 scores 0
    assert calculate_grand_prix_points(11) == 0.0
    assert calculate_grand_prix_points(20) == 0.0

def test_grand_prix_fastest_lap_points():
    # Inside top 10 gets bonus
    assert calculate_grand_prix_points(1, fastest_lap=True) == 26.0
    assert calculate_grand_prix_points(10, fastest_lap=True) == 2.0
    # Outside top 10 gets NO bonus point according to FIA rules
    assert calculate_grand_prix_points(11, fastest_lap=True) == 0.0
    assert calculate_grand_prix_points(15, fastest_lap=True) == 0.0

def test_sprint_points():
    assert calculate_sprint_points(1) == 8.0
    assert calculate_sprint_points(2) == 7.0
    assert calculate_sprint_points(8) == 1.0
    assert calculate_sprint_points(9) == 0.0

def test_max_remaining_points():
    # 3 GPs (3 * 26 = 78) + 1 Sprint (8) = 86 points
    assert calculate_max_remaining_points(3, 1) == 86.0
    # 0 remaining
    assert calculate_max_remaining_points(0, 0) == 0.0

def test_fia_countback_resolution():
    # Driver A: 2 wins, 1 second place
    # Driver B: 1 win, 3 second places
    finishes_a = [1, 1, 2]
    finishes_b = [1, 2, 2, 2]
    # Driver A wins on more 1st places
    assert evaluate_fia_countback(finishes_a, finishes_b) == 1

    # Equal wins (1 each), Driver B has more 2nd places
    finishes_a = [1, 3, 4]
    finishes_b = [1, 2, 5]
    assert evaluate_fia_countback(finishes_a, finishes_b) == -1

    # Completely identical
    finishes_a = [1, 2, 3]
    finishes_b = [1, 2, 3]
    assert evaluate_fia_countback(finishes_a, finishes_b) == 0

def test_mathematical_elimination():
    # Leader has 350 pts. Driver has 290 pts. 2 GPs remaining (52 max pts).
    # 290 + 52 = 342 < 350 -> ELIMINATED
    assert is_mathematically_eliminated(290, 350, remaining_gps=2, remaining_sprints=0) is True

    # Leader has 350 pts. Driver has 300 pts. 2 GPs remaining (52 max pts).
    # 300 + 52 = 352 > 350 -> CAN STILL WIN
    assert is_mathematically_eliminated(300, 350, remaining_gps=2, remaining_sprints=0) is False

def test_clinch_threshold():
    # Leader has 400 pts, P2 has 340 pts. Lead = 60 pts.
    # 2 GPs left (52 max pts). 60 > 52 -> Title is CLINCHED.
    clinched, gap = calculate_clinch_threshold(400, 340, remaining_gps=2, remaining_sprints=0)
    assert clinched is True
    assert gap == 60.0

    # 3 GPs left (78 max pts). Lead = 60 < 78 -> NOT clinched.
    clinched, gap = calculate_clinch_threshold(400, 340, remaining_gps=3, remaining_sprints=0)
    assert clinched is False
