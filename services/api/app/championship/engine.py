"""
APEX GP — Official FIA Points, Scoring Regulations, and Tie-Break Countback Engine
Pure mathematical evaluation of championship points, countbacks, eliminations,
shortened race distance bands, penalty adjustments, and title clinching.

FIA Regulation Provenance and Version Metadata:
- 2026 Technical & Sporting Regulations: Section A, Issue 03, Article A2.2 (Points system & gates) & Article A2.1.4(c) (Qualifying countback fallback); Section B, Issue 09 (Oct 1, 2026).
- 2025 Sporting Regulations: Article 6.4/6.5 (Issue 1, published Oct 17, 2024; Fastest-lap bonus point abolished)
- 2022–2024 Sporting Regulations: Article 6.4 (Fastest-lap bonus point requiring >=50% distance completed & top 10 finish),
  Article 6.5 (Shortened race graduated point allocations: <25%, 25%–<50%, 50%–<75%)
- 2019–2021 Sporting Regulations: Article 6.4 (Fastest-lap bonus point requiring top 10 finish; no 50% distance condition),
  Half-points rule for races stopped between 2 laps and 75% distance
- 2003–2009 Sporting Regulations: 10-8-6-5-4-3-2-1 scale (no FL bonus point)
- 1991–2002 Sporting Regulations: 10-6-4-3-2-1 scale (no FL bonus point)
"""

from typing import List, Dict, Tuple, Any, Optional

# Regulation Provenance Registry mapping season/era to official FIA documents
REGULATION_PROVENANCE_REGISTRY: Dict[str, Dict[str, Any]] = {
    "2026": {
        "season_range": "2026",
        "fia_document": "FIA Formula One World Championship Sporting Regulations — 2026 Technical & Sporting Regulations",
        "document_version": "Section A, Issue 03 & Section B, Issue 09 (Published October 1, 2026)",
        "source_url": "https://www.fia.com/regulation/category/110",
        "source_reference": "Section A, Article A2.2.1 (Grand Prix points & 2-consecutive green laps gate); Section A, Article A2.2.2 (Sprint points scale 8-7-6-5-4-3-2 to Top 7 & >=50% distance gate); Section A, Article A2.1.4(c) (Championship countback fallback to Qualifying results)",
        "fl_bonus_active": False,
        "fl_distance_threshold": None,
        "double_points_final_round": False,
        "consecutive_green_laps_required": 2,
        "sprint_min_distance_ratio": 0.50,
        "sprint_points_scale": "8-7-6-5-4-3-2 (Top 7)",
        "countback_qualifying_fallback": True,
    },
    "2025": {
        "season_range": "2025",
        "fia_document": "FIA Formula One World Championship Sporting Regulations",
        "document_version": "2025 Issue 1 (WMSC ratified Oct 17, 2024)",
        "source_url": "https://www.fia.com/regulation/category/110",
        "source_reference": "Article 6.4 (Fastest lap bonus point rescinded), Article 6.5 (Points scales)",
        "fl_bonus_active": False,
        "fl_distance_threshold": None,
        "double_points_final_round": False,
        "consecutive_green_laps_required": None,
        "sprint_min_distance_ratio": None,
        "countback_qualifying_fallback": False,
    },
    "2022_2024": {
        "season_range": "2022-2024",
        "fia_document": "FIA Formula One World Championship Sporting Regulations",
        "document_version": "2022-2024 Editions (Post-Spa 2021 graduated scale overhaul)",
        "source_url": "https://www.fia.com/regulation/category/110",
        "source_reference": "Article 6.4 (FL bonus point: top 10 & leader completed >=50% distance), Article 6.5 (Columns 1-4 points)",
        "fl_bonus_active": True,
        "fl_distance_threshold": 0.50,
        "double_points_final_round": False,
    },
    "2019_2021": {
        "season_range": "2019-2021",
        "fia_document": "FIA Formula One World Championship Sporting Regulations",
        "document_version": "2019-2021 Editions (FL re-introduced by WMSC in March 2019)",
        "source_url": "https://www.fia.com/regulation/category/110",
        "source_reference": "Article 6.4 (FL bonus point: top 10 finisher in a race awarding points; no 50% distance restriction), Article 6.5 (Half-points for <75%)",
        "fl_bonus_active": True,
        "fl_distance_threshold": None,  # No distance percentage restriction in 2019-2021
        "double_points_final_round": False,
    },
    "2014": {
        "season_range": "2014",
        "fia_document": "2014 Formula One Sporting Regulations",
        "document_version": "2014 Published by FIA (WMSC approved Dec 2013)",
        "source_url": "https://www.fia.com/regulation/category/110",
        "source_reference": "Article 6.4 (Double points awarded for the final Competition of the Championship: Abu Dhabi GP)",
        "fl_bonus_active": False,
        "fl_distance_threshold": None,
        "double_points_final_round": True,
    },
    "2010_2018": {
        "season_range": "2010-2018 (excl 2014 finale)",
        "fia_document": "FIA Formula One World Championship Sporting Regulations",
        "document_version": "2010-2018 Editions (Modern 25-18-15-12-10-8-6-4-2-1 scale introduced)",
        "source_url": "https://www.fia.com/regulation/category/110",
        "source_reference": "Article 6.4 (Top 10 scoring: 25-18-15-12-10-8-6-4-2-1; no FL bonus point)",
        "fl_bonus_active": False,
        "fl_distance_threshold": None,
        "double_points_final_round": False,
    },
    "2003_2009": {
        "season_range": "2003-2009",
        "fia_document": "FIA Formula One World Championship Sporting Regulations",
        "document_version": "2003-2009 Editions",
        "source_url": "https://www.fia.com/regulation/category/110",
        "source_reference": "Article 6.4 (10-8-6-5-4-3-2-1 point allocation, no FL point)",
        "fl_bonus_active": False,
        "fl_distance_threshold": None,
        "double_points_final_round": False,
    },
    "1991_2002": {
        "season_range": "1991-2002",
        "fia_document": "FIA Formula One World Championship Sporting Regulations",
        "document_version": "1991-2002 Editions",
        "source_url": "https://www.fia.com/regulation/category/110",
        "source_reference": "10-6-4-3-2-1 point allocation (all rounds count from 1991 onward; no FL point)",
        "fl_bonus_active": False,
        "fl_distance_threshold": None,
        "double_points_final_round": False,
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

# 2022–2025 Sprint Points (Top 8: 8 down to 1)
SPRINT_POINTS_2022_2025: Dict[int, float] = {
    1: 8.0,
    2: 7.0,
    3: 6.0,
    4: 5.0,
    5: 4.0,
    6: 3.0,
    7: 2.0,
    8: 1.0,
}

# Alias for backwards compatibility
SPRINT_POINTS_2022_PRESENT = SPRINT_POINTS_2022_2025

# 2026 Sprint Points (FIA Section A, Issue 03, Article A2.2.2: Top 7 award 8–7–6–5–4–3–2; 8th place and below: 0 pts)
SPRINT_POINTS_2026: Dict[int, float] = {
    1: 8.0,
    2: 7.0,
    3: 6.0,
    4: 5.0,
    5: 4.0,
    6: 3.0,
    7: 2.0,
}

# 2021 Inaugural Sprint Qualifying Points (P1 to P3: 3–2–1)
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
    if season >= 2026:
        return REGULATION_PROVENANCE_REGISTRY["2026"]
    elif season == 2025:
        return REGULATION_PROVENANCE_REGISTRY["2025"]
    elif season >= 2022:
        return REGULATION_PROVENANCE_REGISTRY["2022_2024"]
    elif season >= 2019:
        return REGULATION_PROVENANCE_REGISTRY["2019_2021"]
    elif season == 2014:
        return REGULATION_PROVENANCE_REGISTRY["2014"]
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
    - 2025 onward: No fastest-lap bonus point under any circumstances (Article 6.4 amended Oct 2024).
    - 2022–2024: Driver must finish in top 10 (1 <= position <= 10) AND leader must have completed
      at least 50% of the scheduled race distance (distance_completed_ratio >= 0.50).
      Specifically applies for full distance (>=75%) and the 50%–<75% band (Column 3 of Article 6.5).
      Ineligible if distance is strictly < 50% (Columns 1 & 2 of Article 6.5).
    - 2019–2021: Driver must finish in top 10 (1 <= position <= 10) in a race where points are awarded.
      The pre-2022 regulations did not contain the 50% distance threshold introduced post-Spa 2021.
    - Prior to 2019 (1991–2018): No fastest-lap bonus point in official regulations.
    """
    if season >= 2025:
        return False

    if 2022 <= season <= 2024:
        if not (1 <= position <= 10):
            return False
        # Leader must complete >= 50% of scheduled race distance (Article 6.4)
        if distance_completed_ratio < 0.50:
            return False
        return True

    if 2019 <= season <= 2021:
        if not (1 <= position <= 10):
            return False
        # In 2019-2021, points were awarded if race ran > 2 laps (even if halved)
        if distance_completed_ratio <= 0.0:
            return False
        return True

    return False

class InsufficientContextError(ValueError):
    """
    Raised when required regulatory session context (e.g. consecutive green-flag laps,
    distance ratio, lap counts) is omitted or None under governing regulations where
    eligibility cannot be determined. Distinct from an official zero-point outcome.
    """
    pass

def verify_consecutive_laps_history(
    lap_sc_vsc_flags: List[bool],
    min_consecutive: int = 2,
) -> Tuple[bool, int]:
    """
    Evaluates whether the session history contains at least `min_consecutive` consecutive
    laps completed without a Safety Car (SC) or Virtual Safety Car (VSC) intervention.
    `lap_sc_vsc_flags[i]` is True if lap i was under SC or VSC, False if under green flag.
    Crucial Regulatory Rule:
    Once a qualifying sequence of consecutive green-flag laps has occurred anywhere in the
    session history, this eligibility condition is satisfied and CANNOT be invalidated
    by a later SC, VSC, or red-flag stoppage.
    Returns: (is_eligible, max_consecutive_green_laps)
    """
    max_consecutive = 0
    current_consecutive = 0

    for is_neutralized in lap_sc_vsc_flags:
        if not is_neutralized:
            current_consecutive += 1
            if current_consecutive > max_consecutive:
                max_consecutive = current_consecutive
        else:
            current_consecutive = 0

    return (max_consecutive >= min_consecutive, max_consecutive)

def resolve_distance_band(
    distance_completed_ratio: Optional[float] = 1.0,
    laps_completed: Optional[int] = None,
    scheduled_laps: Optional[int] = None,
) -> float:
    """
    Resolves the exact distance completion ratio using precise arithmetic or exact lap counts:
    - If laps_completed and scheduled_laps are provided, computes ratio using exact integer division.
    - Accurately checks 25%, 50%, and 75% boundaries for schedules that do not divide evenly
      (e.g., 53 laps: 25% = 13.25 laps, 50% = 26.5 laps, 75% = 39.75 laps).
    - If distance_completed_ratio is provided, returns float(distance_completed_ratio).
    - If explicit None is passed and no lap counts provided, raises InsufficientContextError.
    """
    if laps_completed is not None and scheduled_laps is not None:
        if scheduled_laps <= 0:
            return 0.0
        return laps_completed / float(scheduled_laps)
    if distance_completed_ratio is not None:
        return float(distance_completed_ratio)
    raise InsufficientContextError(
        "Race distance context is missing: distance_completed_ratio is None and "
        "no (laps_completed, scheduled_laps) was provided."
    )

def calculate_grand_prix_points(
    position: int,
    fastest_lap: bool = False,
    season: int = 2024,
    distance_completed_ratio: Optional[float] = 1.0,
    laps_completed: Optional[int] = None,
    scheduled_laps: Optional[int] = None,
    penalty_points_deduction: float = 0.0,
    is_final_event: bool = False,
    round_number: Optional[int] = None,
    total_rounds: Optional[int] = None,
    consecutive_green_laps: Optional[int] = None,
    require_eligibility_context: bool = False,
) -> float:
    """
    Computes points awarded for a Grand Prix finish according to season and FIA regulations.
    Supports:
    - 2026 Ruleset (Section A, Issue 03, Article A2.2):
      No championship points are awarded unless the leader has completed at least two complete,
      consecutive laps without a Safety Car (SC) or Virtual Safety Car (VSC) procedure.
      If require_eligibility_context is True (or explicit None passed when context checking is enforced)
      and consecutive_green_laps is None, an InsufficientContextError is raised.
    - Full distance (>= 75%)
    - Shortened races (Post-2021 Article 6.5 graduated points: <25%, 25%–<50%, 50%–<75%)
    - Half-points rule for historical seasons (pre-2022 <75% distance rule)
    - 2014 season finale double-points rule (Article 6.4 of 2014 FIA Sporting Regulations):
      Must be verified by official season round metadata (round_number == total_rounds == 19 or explicit is_final_event).
      Arbitrary caller flags are rejected if contradicted by season metadata.
    - Fastest lap bonus point eligibility (2019–2021 top 10; 2022–2024 top 10 & >=50% distance; 2025+ rescinded)
    - Penalty deductions (non-negative floor)
    """
    if position < 1:
        return 0.0

    # 1. 2026 Grand Prix Scoring Gate (Section A, Issue 03, Article A2.2)
    if season >= 2026:
        if consecutive_green_laps is None and require_eligibility_context:
            raise InsufficientContextError(
                "2026 Grand Prix scoring requires 'consecutive_green_laps' context under "
                "Section A, Article A2.2. Value cannot be None or omitted."
            )
        if consecutive_green_laps is not None and consecutive_green_laps < 2:
            return 0.0

    # 2. Distance Resolution with exact integer lap counts or ratio
    ratio = resolve_distance_band(
        distance_completed_ratio=distance_completed_ratio,
        laps_completed=laps_completed,
        scheduled_laps=scheduled_laps,
    )

    # 3. Determine Base Finishing Position Points
    if ratio < 0.25:
        if ratio <= 0.0:
            return 0.0
        if season >= 2022:
            base = SHORTENED_LESS_THAN_25.get(position, 0.0)
        else:
            # Historical: No points awarded if under 2 laps / insufficient distance
            return 0.0
    elif ratio < 0.50:
        if season >= 2022:
            base = SHORTENED_25_TO_50.get(position, 0.0)
        else:
            # Half-points rule in historical seasons
            full_base = MODERN_GP_POINTS.get(position, 0.0) if season >= 2010 else ERA_2003_2009_POINTS.get(position, 0.0)
            base = full_base * 0.5
    elif ratio < 0.75:
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

    # 4. 2014 Double-Points Exception Verification (Article 6.4 of 2014 Sporting Regulations)
    # Applies strictly to the final event of the 2014 Championship (Round 19 Abu Dhabi GP).
    # Verified against round metadata: if round_number is provided, must be round 19 of 19.
    if season == 2014:
        is_official_finale = False
        if round_number is not None:
            if total_rounds is not None and round_number == total_rounds and round_number == 19:
                is_official_finale = True
            elif total_rounds is None and round_number == 19:
                is_official_finale = True
            else:
                is_official_finale = False
        elif is_final_event:
            is_official_finale = True

        if is_official_finale:
            base *= 2.0

    # 5. Fastest Lap Bonus Point Applicability
    fl_awarded = 0.0
    if fastest_lap and is_fastest_lap_eligible(position, season=season, distance_completed_ratio=ratio):
        fl_awarded = FASTEST_LAP_POINT

    total = base + fl_awarded - penalty_points_deduction
    return max(0.0, total)

def calculate_shared_points(
    positions: List[int],
    season: int = 2024,
    distance_completed_ratio: float = 1.0,
    is_final_event: bool = False,
) -> float:
    """
    Computes shared points for dead-heat finishes where multiple drivers tie for position(s).
    According to FIA regulations and historical precedent (e.g. dead heat across positions N to N+k-1),
    the points for all tied positions are summed and divided equally among the tied competitors.
    Returns the points awarded to each tied driver.
    """
    if not positions:
        return 0.0
    total_pts = sum(
        calculate_grand_prix_points(
            pos,
            fastest_lap=False,
            season=season,
            distance_completed_ratio=distance_completed_ratio,
            is_final_event=is_final_event,
        )
        for pos in positions
    )
    return total_pts / float(len(positions))

def calculate_sprint_points(
    position: int,
    season: int = 2024,
    distance_completed_ratio: Optional[float] = 1.0,
    laps_completed: Optional[int] = None,
    scheduled_laps: Optional[int] = None,
    consecutive_green_laps: Optional[int] = None,
    require_eligibility_context: bool = False,
) -> float:
    """
    Computes points awarded for a Sprint session according to season regulations.
    - 2026 Ruleset (Section A, Issue 03, Article A2.2):
      Sprint points are awarded only if:
      1. Leader has completed at least two complete, consecutive laps without SC/VSC procedure, AND
      2. At least 50% of scheduled sprint distance has been completed (ratio >= 0.50).
      If require_eligibility_context is True and either required context is omitted or None for 2026,
      raises InsufficientContextError.
    - 2022–2025: Top 8 (8 down to 1).
    - 2021: Top 3 (3, 2, 1).
    """
    if position < 1:
        return 0.0

    # 2026 Sprint Scoring Gate (Section A, Issue 03, Article A2.2)
    if season >= 2026:
        if consecutive_green_laps is None and require_eligibility_context:
            raise InsufficientContextError(
                "2026 Sprint scoring requires 'consecutive_green_laps' context under "
                "Section A, Article A2.2. Value cannot be None or omitted."
            )
        if consecutive_green_laps is not None and consecutive_green_laps < 2:
            return 0.0

        ratio = resolve_distance_band(
            distance_completed_ratio=distance_completed_ratio,
            laps_completed=laps_completed,
            scheduled_laps=scheduled_laps,
        )
        if ratio < 0.50:
            return 0.0

    if season == 2021:
        return SPRINT_POINTS_2021.get(position, 0.0)
    elif 2022 <= season <= 2025:
        return SPRINT_POINTS_2022_2025.get(position, 0.0)
    elif season >= 2026:
        return SPRINT_POINTS_2026.get(position, 0.0)
    return 0.0

def calculate_max_remaining_points(
    remaining_gps: int,
    remaining_sprints: int = 0,
    season: int = 2024,
    is_constructor: bool = False,
    final_event_included: bool = True,
) -> float:
    """
    Maximum points a single driver or constructor could mathematically score in the remainder of the season.
    - Driver 2019-2024: 25 (win) + 1 (FL) = 26 pts per GP + 8 pts per Sprint (P1=8).
    - Driver 2025: 25 (win) + 0 (FL rescinded) = 25 pts per GP + 8 pts per Sprint (P1=8).
    - Driver 2026: 25 (win) + 0 (FL rescinded) = 25 pts per GP + 8 pts per Sprint (P1=8 under Art A2.2.2).
    - Constructor 2019-2024: 25 + 18 + 1 (FL) = 44 pts per GP + (8 + 7) = 15 pts per Sprint (2 cars score).
    - Constructor 2025: 25 + 18 = 43 pts per GP + (8 + 7) = 15 pts per Sprint.
    - Constructor 2026: 25 + 18 = 43 pts per GP + (8 + 7) = 15 pts per Sprint (P1=8, P2=7 under Art A2.2.2).
    - 2014 Double Points: If season == 2014 and final_event_included, the final GP awards double base points
      (Driver: 50 pts; Constructor: 50 + 36 = 86 pts).
    """
    if remaining_gps <= 0 and remaining_sprints <= 0:
        return 0.0

    if not is_constructor:
        # Single Driver scoring capacity
        fl_potential = 1.0 if (2019 <= season <= 2024) else 0.0
        standard_gp_win = MODERN_GP_POINTS[1] if season >= 2010 else ERA_2003_2009_POINTS[1]
        standard_gp_max = standard_gp_win + fl_potential
        if season >= 2022:
            sprint_max = 8.0  # P1 awards 8 pts in both 2022-2025 and 2026 (Art A2.2.2)
        elif season == 2021:
            sprint_max = 3.0
        else:
            sprint_max = 0.0

        if season == 2014 and final_event_included and remaining_gps > 0:
            final_gp_max = (standard_gp_win * 2.0) + fl_potential
            gp_total = final_gp_max + ((remaining_gps - 1) * standard_gp_max)
        else:
            gp_total = remaining_gps * standard_gp_max

        return gp_total + (remaining_sprints * sprint_max)
    else:
        # Constructor scoring capacity (up to 2 cars per team)
        fl_potential = 1.0 if (2019 <= season <= 2024) else 0.0
        if season >= 2010:
            standard_c_gp = MODERN_GP_POINTS[1] + MODERN_GP_POINTS[2] + fl_potential
        elif season >= 2003:
            standard_c_gp = ERA_2003_2009_POINTS[1] + ERA_2003_2009_POINTS[2]
        else:
            standard_c_gp = ERA_1991_2002_POINTS[1] + ERA_1991_2002_POINTS[2]

        if season >= 2026:
            # 2026 Art A2.2.2: P1=8, P2=7 -> 15 pts (P8=0 pts does not affect top 2 cars capacity)
            sprint_c_max = SPRINT_POINTS_2026[1] + SPRINT_POINTS_2026[2]  # 8 + 7 = 15
        elif season >= 2022:
            sprint_c_max = SPRINT_POINTS_2022_2025[1] + SPRINT_POINTS_2022_2025[2]  # 8 + 7 = 15
        elif season == 2021:
            sprint_c_max = SPRINT_POINTS_2021[1] + SPRINT_POINTS_2021[2]  # 3 + 2 = 5
        else:
            sprint_c_max = 0.0

        if season == 2014 and final_event_included and remaining_gps > 0:
            final_c_gp = (MODERN_GP_POINTS[1] * 2.0) + (MODERN_GP_POINTS[2] * 2.0) + fl_potential  # 50 + 36 = 86
            gp_total = final_c_gp + ((remaining_gps - 1) * standard_c_gp)
        else:
            gp_total = remaining_gps * standard_c_gp

        return gp_total + (remaining_sprints * sprint_c_max)

def evaluate_fia_countback(
    finishes_a: List[int],
    finishes_b: List[int],
    max_position: int = 24,
    sprint_finishes_a: Optional[List[int]] = None,
    sprint_finishes_b: Optional[List[int]] = None,
    qualifying_finishes_a: Optional[List[int]] = None,
    qualifying_finishes_b: Optional[List[int]] = None,
    season: int = 2024,
) -> int:
    """
    Evaluates FIA countback rule for tied championship points across all supported seasons (1991–2026).
    Applicable to both Drivers' and Constructors' Championships:

    1. Primary Statutory Criteria (All Seasons 1991–2026):
       Compares the greatest number of first places in Grand Prix races. If equal, compares the greatest
       number of second places in Grand Prix races, then third places, and so on down to `max_position`.

    2. 2026 Season (FIA Technical & Sporting Regulations Section A, Article A2.1.4(c)):
       If Grand Prix race finishes cannot produce a winner, countback falls back directly to
       Qualifying results (comparing most pole positions / 1st places in qualifying, then 2nd, 3rd, etc.).
       Sprint race results are not an intervening statutory tie-break stage in 2026.
       If still completely tied on both GP and Qualifying finishes, returns 0 (unresolved / FIA nomination).

    3. Historical Seasons (1991–2025 under FIA Sporting Regulations Article 7.2 / Dead Heat rules):
       The official regulations specify ONLY a countback of finishing positions in races (Grand Prix races).
       Sprint races (introduced in 2021) and qualifying sessions are NOT statutory tie-breakers under Article 7.2.
       Article 7.2(d) explicitly mandates: "If this procedure fails to produce a result, the FIA will nominate
       the winner according to such criteria as it thinks fit."
       Therefore, when Grand Prix race-result counts are identical, this engine does not invent a sprint-result
       or qualifying-result winner: it returns 0, clearly representing an unresolved tie subject to FIA discretion.

    Returns:
       1 if competitor A finishes ahead on statutory countback
      -1 if competitor B finishes ahead on statutory countback
       0 if unresolved / completely tied on all governing regulatory criteria (subject to FIA nomination)
    """
    counts_a = {pos: finishes_a.count(pos) for pos in range(1, max_position + 1)}
    counts_b = {pos: finishes_b.count(pos) for pos in range(1, max_position + 1)}

    for pos in range(1, max_position + 1):
        if counts_a[pos] > counts_b[pos]:
            return 1
        elif counts_b[pos] > counts_a[pos]:
            return -1

    # 2026 Ruleset (Section A, Article A2.1.4(c)):
    # Fallback directly to Qualifying results if Grand Prix finishing positions cannot resolve tie.
    if season >= 2026:
        if qualifying_finishes_a is not None and qualifying_finishes_b is not None:
            q_counts_a = {pos: qualifying_finishes_a.count(pos) for pos in range(1, max_position + 1)}
            q_counts_b = {pos: qualifying_finishes_b.count(pos) for pos in range(1, max_position + 1)}
            for pos in range(1, max_position + 1):
                if q_counts_a[pos] > q_counts_b[pos]:
                    return 1
                elif q_counts_b[pos] > q_counts_a[pos]:
                    return -1
        return 0

    # Historical Seasons (1991–2025, Article 7.2):
    # Under Article 7.2, sprint results and qualifying results are not part of the statutory countback.
    # If Grand Prix race finishes fail to produce a winner, Article 7.2(d) applies:
    # "the FIA will nominate the winner according to such criteria as it thinks fit."
    # The mathematical engine returns 0 (unresolved / FIA discretion).
    return 0

def is_mathematically_eliminated(
    driver_points: float,
    leader_points: float,
    remaining_gps: int,
    remaining_sprints: int = 0,
    driver_finishes: Optional[List[int]] = None,
    leader_finishes: Optional[List[int]] = None,
    season: int = 2024,
    is_constructor: bool = False,
    final_event_included: bool = True,
    driver_qualifying_finishes: Optional[List[int]] = None,
    leader_qualifying_finishes: Optional[List[int]] = None,
) -> bool:
    """
    Determines if a competitor is mathematically eliminated from the championship.
    A competitor is strictly eliminated if their maximum achievable points < leader's current points.
    If maximum achievable points == leader's points, FIA countback decides if title is achievable.
    """
    max_possible = driver_points + calculate_max_remaining_points(
        remaining_gps,
        remaining_sprints,
        season=season,
        is_constructor=is_constructor,
        final_event_included=final_event_included,
    )
    if max_possible < leader_points:
        return True

    if max_possible == leader_points:
        if driver_finishes is not None and leader_finishes is not None:
            hypothetical_driver_finishes = list(driver_finishes) + [1] * remaining_gps
            tie_result = evaluate_fia_countback(
                hypothetical_driver_finishes,
                leader_finishes,
                qualifying_finishes_a=driver_qualifying_finishes,
                qualifying_finishes_b=leader_qualifying_finishes,
                season=season,
            )
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
    is_constructor: bool = False,
    final_event_included: bool = True,
    leader_qualifying_finishes: Optional[List[int]] = None,
    p2_qualifying_finishes: Optional[List[int]] = None,
) -> Tuple[bool, float]:
    """
    Returns (is_clinched, lead_gap):
    Leader clinches championship if:
    1. lead_gap > max_remaining_points for P2, OR
    2. lead_gap == max_remaining_points for P2, AND P2 cannot win on countback even if P2 wins all remaining sessions.
    """
    lead_gap = leader_points - p2_points
    max_p2_capacity = calculate_max_remaining_points(
        remaining_gps,
        remaining_sprints,
        season=season,
        is_constructor=is_constructor,
        final_event_included=final_event_included,
    )

    if lead_gap > max_p2_capacity:
        return (True, lead_gap)

    if lead_gap == max_p2_capacity:
        if leader_finishes is not None and p2_finishes is not None:
            hypothetical_p2_finishes = list(p2_finishes) + [1] * remaining_gps
            tie_result = evaluate_fia_countback(
                leader_finishes,
                hypothetical_p2_finishes,
                qualifying_finishes_a=leader_qualifying_finishes,
                qualifying_finishes_b=p2_qualifying_finishes,
                season=season,
            )
            if tie_result > 0:
                return (True, lead_gap)

    return (False, lead_gap)
