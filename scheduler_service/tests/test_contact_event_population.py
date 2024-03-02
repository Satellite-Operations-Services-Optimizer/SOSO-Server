import pytest
from datetime import datetime, timedelta, timezone
from scheduler_service.event_processing.contact_events import ensure_contact_events_populated
from scheduler_service.satellite_state.state_generator import SatelliteStateGenerator
from app_config import get_db_session
from app_config.database.mapping import Satellite, SatelliteEclipse, GroundStation, ContactEvent
from sqlalchemy import func
from collections import deque
import time

def test_accurate_contact_event_population(test_satellite: Satellite, test_groundstation: GroundStation):
    # start_time = datetime(2024, 2, 14, 2, 20, 45, 772453)# + timedelta(hours=5.3)
    start_time = datetime.utcnow()
    end_time = start_time + timedelta(days=1)

    # populate contact events across the time range and mark time range as processed
    log_start = time.time()
    ensure_contact_events_populated(start_time, end_time)
    elapsed_time = time.time() - log_start
    print(f"ensure_contact_events_populated took {elapsed_time} seconds.")


    # Iterate over time and calculate contact at each time step
    log_start = time.time()
    sat_state_generator = SatelliteStateGenerator(test_satellite)
    ts = sat_state_generator._get_timescale()
    skyfield_end_time = sat_state_generator._ensure_skyfield_time(end_time)
    current_time = sat_state_generator._ensure_skyfield_time(start_time)
    while current_time.tt < skyfield_end_time.tt:
        sat_state_generator.is_in_contact_with(test_groundstation, current_time)
        current_time = ts.utc(current_time.utc_datetime() + timedelta(minutes=1))

    elapsed_time = time.time() - log_start
    print(f"Iterating state took {elapsed_time} seconds.")
    return

    session = get_db_session()
    expected_contacts = session.query(ContactEvent.utc_time_range).filter(
        ContactEvent.asset_id == test_satellite.id,
        ContactEvent.groundstation_id == test_groundstation.id,
        ContactEvent.utc_time_range.op('&&')(func.tsrange(start_time, end_time))
    ).order_by(ContactEvent.start_time).all()

    expected_contacts_queue = deque([eclipse_row[0] for eclipse_row in expected_contacts])
    current_contact = expected_contacts_queue.popleft() if expected_contacts_queue else None
    prev_contact_end = None

    state_generator = SatelliteStateGenerator(test_satellite)

    log_start = time.time()
    for satellite_state in state_generator.track(start_time, end_time):
        pass
    elapsed_time = time.time() - log_start
    print(f"Iterating state took {elapsed_time} seconds.")

    for satellite_state in state_generator.track(start_time, end_time):
        move_to_next_contact = satellite_state.time > current_contact.upper.replace(tzinfo=timezone.utc) if current_contact else False
        if move_to_next_contact:
            prev_contact_end = current_contact.upper.replace(tzinfo=timezone.utc) if current_contact else None
            current_contact = expected_contacts_queue.popleft() if expected_contacts_queue else None

        
        if current_contact is None:
            contact_expected = False
        else:
            expected_contact_start = current_contact.lower.replace(tzinfo=timezone.utc)
            expected_contact_end = current_contact.upper.replace(tzinfo=timezone.utc)
            contact_expected = satellite_state.time >= expected_contact_start and satellite_state.time <= expected_contact_end
        

        if contact_expected:
            assert state_generator.is_in_contact_with(test_groundstation, satellite_state.time)
        else:
            # Don't throw an error if it is an undersampling problem.
            # Sampling rate for eclipse in the SatelliteStateGenerator.eclipse_events() method which is used by
            # the ensure_eclipse_events_populated() method uses a sampling rate of 1 minute.
            sampling_rate = timedelta(minutes=1)
            if prev_contact_end:
                is_undersampling_problem = abs(satellite_state.time - prev_contact_end) < sampling_rate
            elif not current_contact:
                # TODO verify logic
                is_undersampling_problem = current_contact and abs(satellite_state.time - current_contact.lower.replace(tzinfo=timezone.utc)) < sampling_rate
            else:
                is_undersampling_problem = False
            
            in_contact = state_generator.is_in_contact_with(test_groundstation, satellite_state.time)
            assert not in_contact or is_undersampling_problem


session = get_db_session()
for satellite, groundstation in session.query(Satellite, GroundStation).all():
    test_accurate_contact_event_population(satellite, groundstation)
    exit()

print("done")