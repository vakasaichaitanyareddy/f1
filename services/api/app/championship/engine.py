"""
APEX GP — Official FIA Points, Scoring Regulations, and Tie-Break Countback Engine
Pure mathematical evaluation of championship points, countbacks, eliminations,
shortened race distance bands, penalty adjustments, and title clinching.
"""

from typing import List, Dict, Tuple, Any, Optional

# Standard Modern Grand Prix Points (2010–present, P1 to P10)
MODERN_GP_POINTS: Dict[int, float] = {
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

# 2003-2009 Grand Prix Points (P1 to P8)
ERA_2003_2009_POINTS: Dict[int, float] = {
    1: 10.0,
    2: 8.0,
    3: 6.0,
    4: 5.0,
    5: 4.0,
    6: 3.0,
    7: 2.0,
    8: 1.0,
}

# 1991-2002 Grand Prix Points (P1 to P6)
ERA_1991_2002_POINTS: Dict[int, float] = {
    1: 10.0,
    2: 6.0,
    3: 4.0,
    4: 3.0,
    5: 2.0,
    6: 1.0,
}

# Modern Sprint Points (2022–present, P1 to P8)
SPRINT_POINTS_2022_PRESENT: Dict[int, float] = {
    1: 8.0,
    2: 7.0,
    3: 6.0,
    4: 5.0,
    5: 4.0,
    6: 3.0,
    7: 2.0,
    8: 1.0,
}

# 2021 Inaugural Sprint Qualifying Points (P1 to P3)
SPRINT_POINTS_2021: Dict[int, float] = {
    1: 3.0,
    2: 2.0,
    3: 1.0,
}

# Post-2021 Shortened Race Points Graduated Scale (FIA Sporting Regulations Article 6.5)
# Band 1: Less than 25% completed but leader completed at least 2 laps without safety car
SHORTENED_LESS_THAN_25: Dict[int, float] = {
    1: 6.0,
    2: 4.0,
    3: 3.0,
    4: 2.0,
    5: 1.0,
}

# Band 2: 25% to less than 50% distance completed
SHORTENED_25_TO_50: Dict[int, float] = {
    1: 13.0,
    2: 10.0,
    3: 8.0,
    4: 6.0,
    5: 5.0,
    6: 4.0,
    7: 3.0,
    8: 2.0,
    9: 1.0,
}

# Band 3: 50% to less than 75% distance completed
SHORTENED_50_TO_75: Dict[int, float] = {
    1: 19.0,
    2: 14.0,
    3: 12.0,
    4: 10.0,
    5: 8.0,
    6: 6.0,
    7: 4.0,
    8: 3.0,
    9: 2.0,
    10: 1.0,
}

FASTEST_LAP_POINT = 1.0

def calculate_grand_prix_points(
    position: int,
    fastest_lap: bool = False,
    season: int = 2024,
    distance_completed_ratio: float = 1.0,
    penalty_points_deduction: float = 0.0,
) -> float:
    """
    Computes points awarded for a Grand Prix finish according to season and FIA regulations.
    Supports:
    - Standard full distance (>= 75%)
    - Shortened races (Article 6.5 graduated points: <25%, 25-50%, 50-75%)
    - Half-points rule for historical seasons (pre-2022 <75% rule)
    - Fastest lap bonus point eligibility (1950-1959, 2019-2024 top 10; omitted for shortened races per 6.5)
    - Penalty deductions
    """
    if position < 1:
        return 0.0

    # Handle shortened race scenarios
    if distance_completed_ratio < 0.25:
        if distance_completed_ratio <= 0.0:
            return 0.0
        if season >= 2022:
            base = SHORTENED_LESS_THAN_25.get(position, 0.0)
            fl_eligible = False
        else:
            # Historical: No points awarded if under 2 laps / insufficient distance
            return 0.0
    elif distance_completed_ratio < 0.50:
        if season >= 2022:
            base = SHORTENED_25_TO_50.get(position, 0.0)
            fl_eligible = False
        else:
            # Half points rule in historical seasons
            full_base = MODERN_GP_POINTS.get(position, 0.0) if season >= 2010 else ERA_2003_2009_POINTS.get(position, 0.0)
            base = full_base * 0.5
            fl_eligible = True
    elif distance_completed_ratio < 0.75:
        if season >= 2022:
            base = SHORTENED_50_TO_75.get(position, 0.0)
            fl_eligible = False
        else:
            full_base = MODERN_GP_POINTS.get(position, 0.0) if season >= 2010 else ERA_2003_2009_POINTS.get(position, 0.0)
            base = full_base * 0.5
            fl_eligible = True
    else:
        # Full distance (>= 75%)
        if season >= 2010:
            base = MODERN_GP_POINTS.get(position, 0.0)
        elif season >= 2003:
            base = ERA_2003_2009_POINTS.get(position, 0.0)
        else:
            base = ERA_1991_2002_POINTS.get(position, 0.0)
        fl_eligible = True

    # Fastest lap bonus point applicability
    # Awarded in 2019-2024 if finished in top 10 and race distance eligible
    fl_awarded = 0.0
    if fastest_lap and fl_eligible:
        if 2019 <= season <= 2024 and 1 <= position <= 10:
            fl_awarded = FASTEST_LAP_POINT

    total = base + fl_awarded - penalty_points_deduction
    return max(0.0, total)

def calculate_sprint_points(position: int, season: int = 2024) -> float:
    """Computes points awarded for a Sprint session according to season regulations."""
    if season == 2021:
        return SPRINT_POINTS_2021.get(position, 0.0)
    elif season >= 2022:
        return SPRINT_POINTS_2022_PRESENT.get(position, 0.0)
    return 0.0

def calculate_max_remaining_points(
    remaining_gps: int,
    remaining_sprints: int = 0,
    season: int = 2024,
) -> float:
    """
    Maximum points a single driver could mathematically score in the remainder of the season.
    For 2019-2024: 25 (win) + 1 (FL) = 26 pts per GP + 8 pts per Sprint.
    """
    fl_potential = 1.0 if (2019 <= season <= 2024) else 0.0
    gp_max = MODERN_GP_POINTS[1] + fl_potential if season >= 2010 else ERA_2003_2009_POINTS[1]
    sprint_max = 8.0 if season >= 2022 else (3.0 if season == 2021 else 0.0)

    return (remaining_gps * gp_max) + (remaining_sprints * sprint_max)

def evaluate_fia_countback(
    finishes_a: List[int],
    finishes_b: List[int],
    max_position: int = 24
) -> int:
    """
    Evaluates FIA countback rule for tied championship points (Article 7.2 of Sporting Regulations):
    Compares number of 1st places, then 2nd places, then 3rd places, etc.
    Returns:
       1 if driver A finishes ahead
      -1 if driver B finishes ahead
       0 if completely tied on all countback criteria
    """
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
    remaining_sprints: int = 0,
    driver_finishes: Optional[List[int]] = None,
    leader_finishes: Optional[List[int]] = None,
    season: int = 2024,
) -> bool:
    """
    Determines if a driver is mathematically eliminated from the championship.
    A driver is strictly eliminated if their maximum achievable points < leader's current points.
    If maximum achievable points == leader's points, FIA countback decides if title is achievable.
    """
    max_possible = driver_points + calculate_max_remaining_points(remaining_gps, remaining_sprints, season=season)
    if max_possible < leader_points:
        return True

    if max_possible == leader_points:
        if driver_finishes is not None and leader_finishes is not None:
            # Best possible scenario: driver wins all remaining GPs and sprints
            hypothetical_driver_finishes = list(driver_finishes) + [1] * remaining_gps
            tie_result = evaluate_fia_countback(hypothetical_driver_finishes, leader_finishes)
            # If driver cannot beat or tie leader on countback, they are eliminated
            return tie_result < 0
        return False

    return False

def calculate_clinch_threshold(
    leader_points: float,
    p2_points: float,
    remaining_gps: int,
    remaining_sprints: int = 0,
    leader_finishes: Optional[List[int]] = None,
    p2_finishes: Optional[List[int]] = None,
    season: int = 2024,
) -> Tuple[bool, float]:
    """
    Returns (is_clinched, lead_gap):
    Leader clinches championship if:
    1. lead_gap > max_remaining_points for P2, OR
    2. lead_gap == max_remaining_points for P2, AND P2 cannot win on countback even if P2 wins all remaining sessions.
    """
    lead_gap = leader_points - p2_points
    max_p2_capacity = calculate_max_remaining_points(remaining_gps, remaining_sprints, season=season)

    if lead_gap > max_p2_capacity:
        return (True, lead_gap)

    if lead_gap == max_p2_capacity:
        if leader_finishes is not None and p2_finishes is not None:
            # If P2 wins all remaining races, can P2 surpass leader on countback?
            hypothetical_p2_finishes = list(p2_finishes) + [1] * remaining_gps
            # Countback between leader and hypothetical P2
            tie_result = evaluate_fia_countback(leader_finishes, hypothetical_p2_finishes)
            if tie_result > 0:
                # Leader still wins on countback!
                return (True, lead_gap)

    return (False, lead_gap)
