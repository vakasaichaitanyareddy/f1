from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.racing.models import (
    ConstructorModel, DriverModel, MeetingModel, SessionModel,
    SessionResultModel, SessionTypeEnum, SessionStatusEnum
)

async def seed_verified_2024_data(db: AsyncSession):
    """
    Seeds verified real-world Formula 1 2024 data (constructors, drivers, calendar, results).
    Uses authentic historical data without fabricated values.
    """
    # Check if already seeded
    check = await db.execute(select(ConstructorModel))
    if check.scalars().first():
        return

    # 1. Constructors
    constructors_data = [
        ConstructorModel(id="red_bull", name="Red Bull Racing", nationality="Austrian", color_hex="#3671C6", total_championships=6),
        ConstructorModel(id="ferrari", name="Ferrari", nationality="Italian", color_hex="#E80020", total_championships=16),
        ConstructorModel(id="mclaren", name="McLaren", nationality="British", color_hex="#FF8000", total_championships=8),
        ConstructorModel(id="mercedes", name="Mercedes-AMG", nationality="German", color_hex="#27F4D2", total_championships=8),
        ConstructorModel(id="aston_martin", name="Aston Martin", nationality="British", color_hex="#229971", total_championships=0),
        ConstructorModel(id="alpine", name="Alpine", nationality="French", color_hex="#0093CC", total_championships=2),
        ConstructorModel(id="williams", name="Williams", nationality="British", color_hex="#64C4FF", total_championships=9),
        ConstructorModel(id="rb", name="RB Honda RBPT", nationality="Italian", color_hex="#6692FF", total_championships=0),
        ConstructorModel(id="sauber", name="Kick Sauber", nationality="Swiss", color_hex="#52E252", total_championships=0),
        ConstructorModel(id="haas", name="Haas F1 Team", nationality="American", color_hex="#B6BABD", total_championships=0),
    ]
    for c in constructors_data:
        db.add(c)
    await db.flush()

    # 2. Key Drivers
    drivers_data = [
        DriverModel(id="max_verstappen", code="VER", permanent_number=1, first_name="Max", last_name="Verstappen", nationality="Dutch", constructor_id="red_bull", career_wins=61, career_podiums=109, career_poles=40, career_championships=3),
        DriverModel(id="sergio_perez", code="PER", permanent_number=11, first_name="Sergio", last_name="Perez", nationality="Mexican", constructor_id="red_bull", career_wins=6, career_podiums=39, career_poles=3, career_championships=0),
        DriverModel(id="charles_leclerc", code="LEC", permanent_number=16, first_name="Charles", last_name="Leclerc", nationality="Monegasque", constructor_id="ferrari", career_wins=8, career_podiums=39, career_poles=26, career_championships=0),
        DriverModel(id="carlos_sainz", code="SAI", permanent_number=55, first_name="Carlos", last_name="Sainz", nationality="Spanish", constructor_id="ferrari", career_wins=4, career_podiums=24, career_poles=6, career_championships=0),
        DriverModel(id="lando_norris", code="NOR", permanent_number=4, first_name="Lando", last_name="Norris", nationality="British", constructor_id="mclaren", career_wins=3, career_podiums=24, career_poles=7, career_championships=0),
        DriverModel(id="oscar_piastri", code="PIA", permanent_number=81, first_name="Oscar", last_name="Piastri", nationality="Australian", constructor_id="mclaren", career_wins=2, career_podiums=9, career_poles=0, career_championships=0),
        DriverModel(id="lewis_hamilton", code="HAM", permanent_number=44, first_name="Lewis", last_name="Hamilton", nationality="British", constructor_id="mercedes", career_wins=105, career_podiums=201, career_poles=104, career_championships=7),
        DriverModel(id="george_russell", code="RUS", permanent_number=63, first_name="George", last_name="Russell", nationality="British", constructor_id="mercedes", career_wins=2, career_podiums=14, career_poles=3, career_championships=0),
    ]
    for d in drivers_data:
        db.add(d)
    await db.flush()

    # 3. Calendar Meetings (Verified 2024 rounds)
    m1 = MeetingModel(
        id="2024_01_bahrain",
        season=2024,
        round_number=1,
        official_name="Formula 1 Gulf Air Bahrain Grand Prix 2024",
        location="Sakhir",
        country="Bahrain",
        circuit_id="bahrain",
        circuit_name="Bahrain International Circuit",
        circuit_length_km=5.412,
        laps_total=57,
        is_sprint_weekend=False
    )
    db.add(m1)
    await db.flush()

    # 4. Sessions for Meeting 1
    s_race = SessionModel(
        id="2024_01_race",
        meeting_id="2024_01_bahrain",
        name="Grand Prix Race",
        type=SessionTypeEnum.RACE,
        start_time_utc=datetime(2024, 3, 2, 15, 0, 0, tzinfo=timezone.utc),
        status=SessionStatusEnum.COMPLETED
    )
    db.add(s_race)
    await db.flush()

    # 5. Verified Bahrain 2024 Race Classification
    results = [
        SessionResultModel(id="res_01", session_id="2024_01_race", driver_id="max_verstappen", position=1, grid=1, laps=57, status="Finished", time_or_retired="1:31:44.742", points_awarded=26.0, fastest_lap=True, fastest_lap_time="1:32.608"),
        SessionResultModel(id="res_02", session_id="2024_01_race", driver_id="sergio_perez", position=2, grid=5, laps=57, status="Finished", time_or_retired="+22.457s", points_awarded=18.0, fastest_lap=False),
        SessionResultModel(id="res_03", session_id="2024_01_race", driver_id="carlos_sainz", position=3, grid=4, laps=57, status="Finished", time_or_retired="+25.110s", points_awarded=15.0, fastest_lap=False),
        SessionResultModel(id="res_04", session_id="2024_01_race", driver_id="charles_leclerc", position=4, grid=2, laps=57, status="Finished", time_or_retired="+39.669s", points_awarded=12.0, fastest_lap=False),
        SessionResultModel(id="res_05", session_id="2024_01_race", driver_id="george_russell", position=5, grid=3, laps=57, status="Finished", time_or_retired="+46.788s", points_awarded=10.0, fastest_lap=False),
        SessionResultModel(id="res_06", session_id="2024_01_race", driver_id="lando_norris", position=6, grid=7, laps=57, status="Finished", time_or_retired="+48.458s", points_awarded=8.0, fastest_lap=False),
        SessionResultModel(id="res_07", session_id="2024_01_race", driver_id="lewis_hamilton", position=7, grid=9, laps=57, status="Finished", time_or_retired="+50.324s", points_awarded=6.0, fastest_lap=False),
        SessionResultModel(id="res_08", session_id="2024_01_race", driver_id="oscar_piastri", position=8, grid=8, laps=57, status="Finished", time_or_retired="+56.082s", points_awarded=4.0, fastest_lap=False),
    ]
    for r in results:
        db.add(r)

    await db.commit()
