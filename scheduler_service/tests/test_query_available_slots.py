from scheduler_service.schedulers.genetic.populator.create_schedule_population import query_available_satellite_schedule_slots
from app_config import get_db_session
from app_config.database.mapping import ScheduleRequest, ScheduledImaging, Schedule, Satellite, ContactEvent, GroundStation
from datetime import datetime, timedelta

def test_query_available_satellite_schedule_slots():
    session = get_db_session()
    
    schedule = Schedule(name="test_schedule_for_query_available_satellite_schedule_slots")
    session.add(schedule)
    session.flush()

    satellite = session.query(Satellite).first()
    event_duration = timedelta(minutes=10)

    imaging1 = create_dummy_imaging_event(
        schedule_id=schedule.id,
        satellite_id=satellite.id,
        start_time=datetime(2022, 1, 1, 0, 0, 0),
        duration=event_duration
    )

    gap_start = imaging1.start_time + event_duration
    gap_duration = event_duration + 0.5*event_duration # give some buffer to schedule request

    imaging2 = create_dummy_imaging_event(
        schedule_id=schedule.id,
        satellite_id=satellite.id,
        start_time=gap_start + gap_duration,
        duration=event_duration
    )
    session.add_all([imaging1, imaging2])
    session.flush()

    # Make request window span the time between imaging1 and imaging2,
    # plus a little buffer that's not large enough to schedule the event,
    # to test that the query returns the correct time slot - the gaps
    # between imaging1 and imaging2
    request_window_start = imaging1.start_time - 0.5*event_duration # 5 minutes before imaging1 starts
    request_window_end = imaging2.start_time + imaging2.duration + 0.5*event_duration # 5 minutes after imaging2 ends
    request = ScheduleRequest(
        schedule_id=schedule.id,
        order_type="imaging",
        priority=1,
        window_start=request_window_start,
        window_end=request_window_end,
        duration=event_duration,
        delivery_deadline=request_window_end,
        status="processing"
    )
    session.add(request)
    session.flush()
    
    slots = query_available_satellite_schedule_slots(request.id, schedule.id).all()
    print(slots)
    print("pass")

def create_dummy_imaging_event(schedule_id, satellite_id, start_time, duration):
    session = get_db_session()
    groundstation = session.query(GroundStation).first()
    request = ScheduleRequest(
        schedule_id=schedule_id,
        asset_id=satellite_id,
        asset_type="satellite",
        order_type="imaging",
        priority=1,
        window_start=start_time,
        window_end=start_time+duration,
        duration=duration,
        delivery_deadline=start_time+duration,
        status="scheduled"
    )
    contact = ContactEvent(
        schedule_id=schedule_id,
        asset_id=satellite_id,
        groundstation_id=groundstation.id,
        start_time=request.window_start - timedelta(minutes=10),
        duration=timedelta(minutes=5)
    )
    session.add_all([request, contact])
    session.flush()

    imaging = ScheduledImaging(
        schedule_id=schedule_id,
        asset_id=satellite_id,
        request_id=request.id,
        start_time=start_time,
        duration=duration,
        window_start=start_time,
        window_end=start_time+duration,
        uplink_contact_id=contact.id,
        uplink_size=request.uplink_size,
        downlink_size=request.downlink_size,
        priority=request.priority
    )
    session.add(imaging)
    session.flush()
    return imaging

test_query_available_satellite_schedule_slots()