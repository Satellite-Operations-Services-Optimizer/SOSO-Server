from scheduler_service.schedulers.genetic.populator.create_schedule_population import query_satellite_available_time_slots
from app_config import get_db_session
from app_config.database.mapping import ScheduleRequest, Schedule, Satellite, CaptureOpportunity, ImageOrder
from datetime import datetime, timedelta
from helpers import create_dummy_imaging_event

def test_query_available_satellite_schedule_slots():
    session = get_db_session()
    
    schedule = Schedule(name="test_schedule_for_query_available_satellite_schedule_slots")
    session.add(schedule)
    session.flush()

    satellite = session.query(Satellite).first()

    imaging1_start_time = datetime(2022, 1, 1, 0, 0, 0)
    imaging1 = create_dummy_imaging_event(
        schedule_id=schedule.id,
        satellite_id=satellite.id,
        start_time=imaging1_start_time,
        contact_start=imaging1_start_time - timedelta(days=1) # make sure this contact event is not in the way of any other events we are interested in
    )

    imaging_duration = imaging1.duration

    # make a gap large enough to schedule our item, but don't schedule any capture opportunity within that gap, to test if the query actually ensures that the image can be taken when finding available slots
    valid_gap_start = imaging1.start_time + imaging1.duration
    valid_gap_duration = imaging_duration


    image_type = "medium"
    latitude = 40.7128
    longitude = -74.0060

    # make a capture opportunity that is not long enough to schedule imaging to test if this is filtered out
    undersized_opportunity_start = valid_gap_start + valid_gap_duration
    undersized_opportunity_duration = imaging_duration - timedelta(seconds=3) 
    undersized_opportunity = CaptureOpportunity(
        schedule_id=schedule.id,
        asset_id=satellite.id,
        image_type=image_type,
        latitude=latitude,
        longitude=longitude,
        start_time=undersized_opportunity_start,
        duration=undersized_opportunity_duration
    )
    session.add(undersized_opportunity)
    session.flush()

    # make a gap that is not large enough to schedule our item to make sure that these times are filtered out when finding available slots to schedule imaging
    invalid_gap_start = undersized_opportunity_start + undersized_opportunity_duration
    invalid_gap_duration = imaging_duration - timedelta(seconds=3)

    # make a capture opportunity that is long enough to schedule imaging to test if this is included in the available slots.
    # This will be the only capture opportunity that is long enough to schedule imaging, so the query should return this time slot alone (minus the time in which this opportunity overlaps with another scheduled event)
    valid_opportunity_start = invalid_gap_start + invalid_gap_duration
    event_overlap_buffer = timedelta(seconds=10)
    valid_opportunity = CaptureOpportunity(
        schedule_id=schedule.id,
        asset_id=satellite.id,
        image_type=image_type,
        latitude=latitude,
        longitude=longitude,
        start_time=valid_opportunity_start,
        duration=imaging_duration + event_overlap_buffer
    )
    session.add(valid_opportunity)
    session.flush()

    overlapping_event_start = valid_opportunity.start_time + valid_opportunity.duration - event_overlap_buffer
    overlapping_event = create_dummy_imaging_event(
        schedule_id=schedule.id,
        satellite_id=satellite.id,
        start_time=overlapping_event_start,
        contact_start=imaging1.start_time - timedelta(days=1) # make sure this contact event is not in the way of any other events we are interested in
    )


    # Make order window span the time between the first and the last event (imaging1 and the overlapping_event)
    # plus a little buffer that's not large enough to schedule the event,
    # to test that the query returns the correct time slot - the gaps
    # between imaging1 and overlapping_event
    order_window_start = imaging1.start_time - 0.5*imaging_duration # 5 minutes before imaging1 starts, to create an invalid gap
    order_window_end = overlapping_event.start_time + overlapping_event.duration + 0.5*imaging_duration # 5 minutes after overlapping_event ends

    # Create order to schedule
    order = ImageOrder(
        schedule_id=schedule.id,
        latitude=latitude,
        longitude=longitude,
        image_type="medium",
        start_time=order_window_start,
        end_time=order_window_end,
        delivery_deadline=order_window_end + timedelta(minutes=10)
    )
    session.add(order)
    session.flush()
    order = session.query(ImageOrder).filter_by(id=order.id).one() # order.duration is a generated field, and it is not being generated upon flush


    request = ScheduleRequest(
        schedule_id=schedule.id,
        order_type="imaging",
        order_id=order.id,
        priority=1,
        window_start=order.start_time,
        window_end=order.end_time,
        duration=order.duration,
        delivery_deadline=order.delivery_deadline,
        uplink_size=0, # for now, let's not worry about making sure that there are contacts
        downlink_size=0,
        status="processing"
    )
    session.add(request)
    session.flush()
    
    slots = query_satellite_available_time_slots(request.id, schedule.id).all()
    assert len(slots) == 1

    # Make timezone info the same for comparison
    valid_opportunity_start_time = valid_opportunity.start_time.replace(tzinfo=slots[0].time_range.lower.tzinfo)
    overlapping_event_start_time = overlapping_event.start_time.replace(tzinfo=slots[0].time_range.upper.tzinfo)
    assert slots[0].time_range.lower == valid_opportunity_start_time
    assert slots[0].time_range.upper == overlapping_event_start_time

    assert slots[0].schedule_id == schedule.id
    assert slots[0].asset_id == satellite.id

    session.rollback()


test_query_available_satellite_schedule_slots()