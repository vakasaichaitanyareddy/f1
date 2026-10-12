"""
APEX GP — Official FIA Points and Tie-Break Countback Engine
Pure mathematical evaluation of championship points, gaps, countbacks, and eliminations.
"""

from typing import List, Dict, Tuple, Any

# Official FIA F1 Grand Prix points distribution (P1 to P10)
GRAND_PRIX_POINTS = {
    1: 25.0,
    2: 18.0,
    3: 15.0,
    4: 12.0,
    5: 10.0,
    6: 8.0,
    7: 6.0,
    8: 4.0,
    9: 2.0,
    10: 1.0,
}

# Sprint session points distribution (P1 to P8)
SPRINT_POINTS = {
    1: 8.0,
    2: 7.0,
    3: 6.0,
    4: 5.0,
    5: 4.0,
    6: 3.0,
    7: 2.0,
    8: 1.0,
}

FASTEST_LAP_POINT = 1.0

def calculate_grand_prix_points(position: int, fastest_lap: bool = False) -> float:
    """Computes points awarded for a Grand Prix finish according to FIA regulations."""
    base = GRAND_PRIX_POINTS.get(position, 0.0)
    # Fastest lap point awarded only if driver finishes in top 10
    if fastest_lap and position <= 10 and position >= 1:
        base += FASTEST_LAP_POINT
    return base

def calculate_sprint_points(position: int) -> float:
    """Computes points awarded for a Sprint race according to FIA regulations."""
    return SPRINT_POINTS.get(position, 0.0)

def calculate_max_remaining_points(remaining_gps: int, remaining_sprints: int) -> float:
    """
    Maximum points a single driver could mathematically score in the remainder of the season:
    26 points per Grand Prix (25 win + 1 fastest lap) + 8 points per Sprint win.
    """
    return (remaining_gps * 26.0) + (remaining_sprints * 8.0)

def evaluate_fia_countback(
    finishes_a: List[int],
    finishes_b: List[int],
    max_position: int = 24
) -> int:
    """
    Evaluates FIA countback rule for tied points:
    Compares number of 1st places, then 2nd places, then 3rd places, etc.
    Returns:
       1 if driver A finishes ahead
      -1 if driver B finishes ahead
       0 if completely tied on all countback criteria
    """
    # Count frequency of each finishing position
    counts_a = {pos: finishes_a.count(pos) for pos in range(1, max_position + 1)}
    counts_b = {pos: finishes_b.count(pos) for pos in range(1, max_position + 1)}

    for pos in range(1, max_position + 1):
        if counts_a[pos] > counts_b[pos]:
            return 1
        elif counts_b[pos] > counts_a[pos]:
            return -1

    return 0

def is_mathematically_eliminated(
    driver_points: float,
    leader_points: float,
    remaining_gps: int,
    remaining_sprints: int,
    driver_finishes: List[int] = None,
    leader_finishes: List[int] = None,
) -> bool:
    """
    Determines if a driver is mathematically eliminated from the championship.
    A driver is strictly eliminated if their maximum achievable points < leader's current points.
    If maximum achievable points == leader's points, countback determines if they could win.
    """
    max_possible = driver_points + calculate_max_remaining_points(remaining_gps, remaining_sprints)
    if max_possible < leader_points:
        return True
    
    if max_possible == leader_points:
        if driver_finishes is not None and leader_finishes is not None:
            # Hypothetical best scenario: driver wins all remaining races
            hypothetical_driver_finishes = list(driver_finishes) + [1] * remaining_gps
            # Countback check
            tie_result = evaluate_fia_countback(hypothetical_driver_finishes, leader_finishes)
            return tie_result < 0
        return False
        
    return False

def calculate_clinch_threshold(
    leader_points: float,
    p2_points: float,
    remaining_gps: int,
    remaining_sprints: int = 0,
) -> Tuple[bool, float]:
    """
    Returns (is_clinched, lead_gap):
    Leader clinches championship if lead_gap > max_remaining_points for P2.
    """
    lead_gap = leader_points - p2_points
    max_p2_capacity = calculate_max_remaining_points(remaining_gps, remaining_sprints)
    is_clinched = lead_gap > max_p2_capacity
    return (is_clinched, lead_gap)
