"""
APEX GP — Official FIA Points, Scoring Regulations, and Tie-Break Countback Engine
Pure mathematical evaluation of championship points, countbacks, eliminations,
shortened race distance bands, penalty adjustments, and title clinching.

FIA Regulation Provenance and Version Metadata:
- 2025+ Sporting Regulations: Article 6.4/6.5 (Issue 1, published Oct 2024; Fastest-lap bonus point abolished)
- 2022–2024 Sporting Regulations: Article 6.4 (Fastest-lap bonus point requiring >=50% distance completed & top 10 finish),
  Article 6.5 (Shortened race graduated point allocations: <25%, 25%–<50%, 50%–<75%)
- 2019–2021 Sporting Regulations: Article 6.4 (Fastest-lap bonus point requiring >=50% distance completed & top 10 finish),
  Half-points rule for races stopped between 2 laps and 75% distance
- 2003–2009 Sporting Regulations: 10-8-6-5-4-3-2-1 scale (no FL bonus point)
- 1991–2002 Sporting Regulations: 10-6-4-3-2-1 scale (no FL bonus point)
"""

from typing import List, Dict, Tuple, Any, Optional

# Regulation Provenance Registry mapping season/era to official FIA documents
REGULATION_PROVENANCE_REGISTRY: Dict[str, Dict[str, Any]] = {
    "2025_ONWARD": {
        "season_range": "2025+",
        "fia_document": "FIA Formula One World Championship Sporting Regulations",
        "document_version": "2025 Issue 1 (WMSC ratified Oct 17, 2024)",
        "source_reference": "Article 6.4 (Fastest lap bonus point rescinded), Article 6.5 (Points scales)",
        "fl_bonus_active": False,
        "fl_distance_threshold": None,
    },
    "2022_2024": {
        "season_range": "2022-2024",
        "fia_document": "FIA Formula One World Championship Sporting Regulations",
        "document_version": "2022-2024 Editions (Post-Spa 2021 graduated scale overhaul)",
        "source_reference": "Article 6.4 (FL bonus point: top 10 & leader completed >=50% distance), Article 6.5 (Columns 1-4 points)",
        "fl_bonus_active": True,
        "fl_distance_threshold": 0.50,
    },
    "2019_2021": {
        "season_range": "2019-2021",
        "fia_document": "FIA Formula One World Championship Sporting Regulations",
        "document_version": "2019-2021 Editions (FL re-introduced by WMSC in March 2019)",
        "source_reference": "Article 6.4 (FL bonus point: top 10 & leader completed >=50% distance), Half-points for <75%",
        "fl_bonus_active": True,
        "fl_distance_threshold": 0.50,
    },
    "2010_2018": {
        "season_range": "2010-2018",
        "fia_document": "FIA Formula One World Championship Sporting Regulations",
        "document_version": "2010 Edition (Modern 25-18-15-12-10-8-6-4-2-1 system introduced)",
        "source_reference": "Article 6.4 (No fastest lap bonus point)",
        "fl_bonus_active": False,
        "fl_distance_threshold": None,
    },
    "2003_2009": {
        "season_range": "2003-2009",
        "fia_document": "FIA Formula One World Championship Sporting Regulations",
        "document_version": "2003-2009 Editions",
        "source_reference": "Article 6.4 (10-8-6-5-4-3-2-1 point allocation, no FL point)",
        "fl_bonus_active": False,
        "fl_distance_threshold": None,
    },
    "1991_2002": {
        "season_range": "1991-2002",
        "fia_document": "FIA Formula One World Championship Sporting Regulations",
        "document_version": "1991-2002 Editions",
        "source_reference": "10-6-4-3-2-1 point allocation (no FL point)",
        "fl_bonus_active": False,
        "fl_distance_threshold": None,
    },
}

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
# Band 1: Less than 25% completed (Column 1)
SHORTENED_LESS_THAN_25: Dict[int, float] = {
    1: 6.0,
    2: 4.0,
    3: 3.0,
    4: 2.0,
    5: 1.0,
}

# Band 2: 25% to less than 50% completed (Column 2)
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

# Band 3: 50% to less than 75% completed (Column 3)
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

def get_regulation_provenance(season: int) -> Dict[str, Any]:
    """Returns official FIA regulatory source metadata and document citations for a given season."""
    if season >= 2025:
        return REGULATION_PROVENANCE_REGISTRY["2025_ONWARD"]
    elif season >= 2022:
        return REGULATION_PROVENANCE_REGISTRY["2022_2024"]
    elif season >= 2019:
        return REGULATION_PROVENANCE_REGISTRY["2019_2021"]
    elif season >= 2010:
        return REGULATION_PROVENANCE_REGISTRY["2010_2018"]
    elif season >= 2003:
        return REGULATION_PROVENANCE_REGISTRY["2003_2009"]
    else:
        return REGULATION_PROVENANCE_REGISTRY["1991_2002"]

def is_fastest_lap_eligible(
    position: int,
    season: int = 2024,
    distance_completed_ratio: float = 1.0,
) -> bool:
    """
    Evaluates whether the fastest-lap bonus point is eligible according to official FIA regulations:
    - 2019–2024: Driver must finish in the top 10 (1 <= position <= 10) AND leader must have completed
      at least 50% of the scheduled race distance (distance_completed_ratio >= 0.50).
      Specifically, it applies both for full-distance races (>=75%) AND shortened races in the
      50% to <75% distance band (Column 3 of Article 6.5).
      It is ineligible if distance is strictly < 50% (Columns 1 & 2 of Article 6.5, or <50% in 2019-2021).
    - 2025 onward: No fastest-lap bonus point under any circumstances (Article 6.4 amended).
    - Prior to 2019: No fastest-lap bonus point (except historical 1950–1959 which used different scales).
    """
    if season >= 2025:
        return False

    if 2019 <= season <= 2024:
        # Must finish in top 10
        if not (1 <= position <= 10):
            return False
        # Leader must complete >= 50% of scheduled race distance (Article 6.4)
        if distance_completed_ratio < 0.50:
            return False
        return True

    return False

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
    - Full distance (>= 75%)
    - Shortened races (Article 6.5 graduated points: <25%, 25%–<50%, 50%–<75%)
    - Half-points rule for historical seasons (pre-2022 <75% rule)
    - Fastest lap bonus point eligibility (2019–2024: top 10 & >=50% distance; 2025+: rescinded)
    - Penalty deductions (non-negative floor)
    """
    if position < 1:
        return 0.0

    # 1. Determine Base Finishing Position Points
    if distance_completed_ratio < 0.25:
        if distance_completed_ratio <= 0.0:
            return 0.0
        if season >= 2022:
            base = SHORTENED_LESS_THAN_25.get(position, 0.0)
        else:
            # Historical: No points awarded if under 2 laps / insufficient distance
            return 0.0
    elif distance_completed_ratio < 0.50:
        if season >= 2022:
            base = SHORTENED_25_TO_50.get(position, 0.0)
        else:
            # Half-points rule in historical seasons
            full_base = MODERN_GP_POINTS.get(position, 0.0) if season >= 2010 else ERA_2003_2009_POINTS.get(position, 0.0)
            base = full_base * 0.5
    elif distance_completed_ratio < 0.75:
        if season >= 2022:
            # Band 3: 50% to less than 75% completed (Article 6.5 Column 3)
            base = SHORTENED_50_TO_75.get(position, 0.0)
        else:
            # Pre-2022: Half points awarded if between 2 laps and 75%
            full_base = MODERN_GP_POINTS.get(position, 0.0) if season >= 2010 else ERA_2003_2009_POINTS.get(position, 0.0)
            base = full_base * 0.5
    else:
        # Full distance (>= 75%)
        if season >= 2010:
            base = MODERN_GP_POINTS.get(position, 0.0)
        elif season >= 2003:
            base = ERA_2003_2009_POINTS.get(position, 0.0)
        else:
            base = ERA_1991_2002_POINTS.get(position, 0.0)

    # 2. Fastest Lap Bonus Point Applicability
    fl_awarded = 0.0
    if fastest_lap and is_fastest_lap_eligible(position, season=season, distance_completed_ratio=distance_completed_ratio):
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
    - 2019-2024: 25 (win) + 1 (FL) = 26 pts per GP + 8 pts per Sprint.
    - 2025 onward: 25 (win) + 0 (FL rescinded) = 25 pts per GP + 8 pts per Sprint.
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
            hypothetical_driver_finishes = list(driver_finishes) + [1] * remaining_gps
            tie_result = evaluate_fia_countback(hypothetical_driver_finishes, leader_finishes)
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
            hypothetical_p2_finishes = list(p2_finishes) + [1] * remaining_gps
            tie_result = evaluate_fia_countback(leader_finishes, hypothetical_p2_finishes)
            if tie_result > 0:
                return (True, lead_gap)

    return (False, lead_gap)
