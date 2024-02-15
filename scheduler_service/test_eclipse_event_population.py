import pytest
from datetime import datetime, timedelta, timezone
from scheduler_service.fixed_event_processing.eclipse_events import ensure_eclipse_events_populated
from scheduler_service.satellite_state.state_generator import SatelliteStateGenerator
from app_config import get_db_session
from app_config.database.mapping import Satellite, SatelliteEclipse
from sqlalchemy import func
from collections import deque

def test_accurate_eclipse_event_population(test_satellite: Satellite):
    start_time = datetime(2024, 2, 14, 2, 20, 45, 772453) + timedelta(hours=5.3)
    # start_time = datetime.utcnow()
    end_time = start_time + timedelta(days=1)
    ensure_eclipse_events_populated(start_time, end_time)
    return

    session = get_db_session()
    satellite_eclipses_within_time_range = session.query(SatelliteEclipse.utc_time_range).filter(
        SatelliteEclipse.asset_id == test_satellite.id,
        SatelliteEclipse.utc_time_range.op('&&')(func.tsrange(start_time, end_time))
    ).order_by(SatelliteEclipse.start_time).all()

    expected_eclipses = deque([eclipse_row[0] for eclipse_row in satellite_eclipses_within_time_range])
    current_eclipse = expected_eclipses.popleft() if expected_eclipses else None
    previous_eclipse_end = None
    for satellite_state in SatelliteStateGenerator(test_satellite).track(start_time, end_time):
        move_to_next_eclipse = satellite_state.time > current_eclipse.upper.replace(tzinfo=timezone.utc) if current_eclipse else False
        if move_to_next_eclipse:
            previous_eclipse_end = current_eclipse.upper.replace(tzinfo=timezone.utc) if current_eclipse else None
            current_eclipse = expected_eclipses.popleft() if expected_eclipses else None

        
        if current_eclipse is None:
            eclipse_expected = False
        else:
            expected_eclipse_start = current_eclipse.lower.replace(tzinfo=timezone.utc)
            expected_eclipse_end = current_eclipse.upper.replace(tzinfo=timezone.utc)
            eclipse_expected = satellite_state.time >= expected_eclipse_start and satellite_state.time <= expected_eclipse_end
        

        if eclipse_expected:
            assert not satellite_state.is_sunlit
        else:
            # Don't throw an error if it is an undersampling problem.
            # Sampling rate for eclipse in the SatelliteStateGenerator.eclipse_events() method which is used by
            # the ensure_eclipse_events_populated() method uses a sampling rate of 1 minute.
            sampling_rate = timedelta(minutes=1)
            if previous_eclipse_end:
                is_undersampling_problem = abs(satellite_state.time - previous_eclipse_end) < sampling_rate
            elif not current_eclipse:
                # TODO verify logic
                is_undersampling_problem = current_eclipse and abs(satellite_state.time - current_eclipse.lower.replace(tzinfo=timezone.utc)) < sampling_rate
            else:
                is_undersampling_problem = False
            assert satellite_state.is_sunlit or is_undersampling_problem


session = get_db_session()
for satellite in session.query(Satellite).all():
    test_accurate_eclipse_event_population(satellite)
    exit()

print("done")