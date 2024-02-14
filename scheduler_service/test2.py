import pytest
from datetime import datetime, timedelta, timezone
from scheduler_service.fixed_event_processing.utils import retrieve_and_lock_unprocessed_blocks_for_processing
from scheduler_service.fixed_event_processing.eclipse_events import ensure_eclipse_events_populated
from scheduler_service.satellite_state.state_generator import SatelliteStateGenerator
from app_config import get_db_session
from app_config.database.mapping import Satellite, SatelliteEclipse
from sqlalchemy import func
from collections import deque

def test_accurate_eclipse_event_population():
    start_time = datetime.utcnow()
    end_time = start_time + timedelta(days=1)
    ensure_eclipse_events_populated(start_time, end_time)

    session = get_db_session()
    test_satellite = session.query(Satellite).first()
    satellite_eclipses_within_time_range = session.query(SatelliteEclipse.utc_time_range).filter(
        SatelliteEclipse.asset_id == test_satellite.id,
        SatelliteEclipse.utc_time_range.op('&&')(func.tsrange(start_time, end_time))
    ).order_by(SatelliteEclipse.start_time).all()

    expected_eclipses = deque([eclipse_row[0] for eclipse_row in satellite_eclipses_within_time_range])
    current_eclipse = expected_eclipses.popleft() if expected_eclipses else None
    previous_eclipse_end = None
    for satellite_state in SatelliteStateGenerator(test_satellite).track(start_time, end_time):
        if current_eclipse is None:
            eclipse_expected = False
        else:
            expected_eclipse_start = current_eclipse.lower.replace(tzinfo=timezone.utc)
            expected_eclipse_end = current_eclipse.upper.replace(tzinfo=timezone.utc)

            if satellite_state.time > expected_eclipse_end:
                previous_eclipse_end = expected_eclipse_end
                current_eclipse = expected_eclipses.popleft() if expected_eclipses else None
            eclipse_expected = satellite_state.time >= expected_eclipse_start and satellite_state.time <= expected_eclipse_end

        if eclipse_expected:
            assert not satellite_state.is_sunlit
        else:
            resolution_problem = abs(satellite_state.time - previous_eclipse_end) < timedelta(minutes=1)
            assert satellite_state.is_sunlit or resolution_problem

        
    

    print("done")

test_accurate_eclipse_event_population()