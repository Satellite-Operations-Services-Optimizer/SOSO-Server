from scheduler_service.schedulers.scheduler_tools import query_satellite_available_time_slots
from app_config import get_db_session
from app_config.database.mapping import ScheduleRequest, Schedule, Satellite, CaptureOpportunity, ImageOrder, SatelliteOutage
from datetime import datetime, timedelta
from helpers import create_dummy_imaging_event
from sqlalchemy import column

def test_query_available_satellite_schedule_slots():
    session = get_db_session()
    
    schedule = Schedule(name="test_schedule_for_query_available_satellite_schedule_slots")
    session.add(schedule)
    session.flush()

    satellite_1 = session.query(Satellite).first()
    satellite_2 = session.query(Satellite).offset(1).first()

    imaging1_start_time = datetime(2022, 5, 15, 0, 0, 0)
    imaging1 = create_dummy_imaging_event(
        schedule_id=schedule.id,
        satellite_id=satellite_1.id,
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
    undersized_opportunity_duration = imaging_duration - 0.5*imaging_duration
    undersized_opportunity = CaptureOpportunity(
        schedule_id=schedule.id,
        asset_id=satellite_1.id,
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
    invalid_gap_duration = 0.5*(imaging_duration - undersized_opportunity_duration)

    # satellite outage
    sat_outage_start = invalid_gap_start + invalid_gap_duration
    outage_duration = imaging_duration
    sat_outage = SatelliteOutage(
        schedule_id=schedule.id,
        asset_id=satellite_1.id,
        start_time=sat_outage_start,
        duration=outage_duration
    )
    session.add(sat_outage)
    session.flush()

    # make a capture opportunity that is long enough to schedule imaging to test if this is included in the available slots.
    # This will be the only capture opportunity that is long enough to schedule imaging, so the query should return this time slot alone (minus the time in which this opportunity overlaps with another scheduled event and the time it overlaps with the outage)
    outage_overlap_duration = timedelta(seconds=10)
    event_overlap_buffer = timedelta(seconds=10)
    sat_1_valid_opportunity_start = sat_outage.start_time + sat_outage.duration - outage_overlap_duration
    sat_1_valid_opportunity = CaptureOpportunity(
        schedule_id=schedule.id,
        asset_id=satellite_1.id,
        image_type=image_type,
        latitude=latitude,
        longitude=longitude,
        start_time=sat_1_valid_opportunity_start,
        duration=outage_overlap_duration + imaging_duration + event_overlap_buffer
    )
    session.add(sat_1_valid_opportunity)
    session.flush()

    overlapping_event_start = sat_1_valid_opportunity.start_time + sat_1_valid_opportunity.duration - event_overlap_buffer
    overlapping_event = create_dummy_imaging_event(
        schedule_id=schedule.id,
        satellite_id=satellite_1.id,
        start_time=overlapping_event_start,
        contact_start=imaging1.start_time - timedelta(days=1) # make sure this contact event is not in the way of any other events we are interested in
    )

    sat_2_valid_opportunity_start = overlapping_event.start_time + overlapping_event.duration
    sat_2_valid_opportunity = CaptureOpportunity(
        schedule_id=schedule.id,
        asset_id=satellite_1.id + 1,
        image_type=image_type,
        latitude=latitude,
        longitude=longitude,
        start_time=sat_2_valid_opportunity_start,
        duration=imaging_duration + timedelta(seconds=10) # make sure more than long enough
    )
    session.add(sat_2_valid_opportunity)
    session.flush()

    # Make order window span the time between the first and the last event (imaging1 and the sat_2_valid_opportunity)
    # plus a little buffer that's not large enough to schedule the event,
    # to test that the query returns the correct time slot - the gaps
    # between imaging1 and sat_2_valid_opportunity, and the gap
    order_window_start = imaging1.start_time - 0.5*imaging_duration # 5 minutes before imaging1 starts, to create an invalid gap
    order_window_end = sat_2_valid_opportunity.start_time + sat_2_valid_opportunity.duration

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
    
    slots = query_satellite_available_time_slots(request.id).order_by(column('time_range')).all()
    assert len(slots) == 2

    # Make timezone info the same for comparison
    sat_1_valid_time_range_start = sat_1_valid_opportunity.start_time.replace(tzinfo=slots[0].time_range.lower.tzinfo) + outage_overlap_duration
    sat_1_valid_time_range_end = overlapping_event.start_time.replace(tzinfo=slots[0].time_range.upper.tzinfo)
    assert slots[0].time_range.lower == sat_1_valid_time_range_start
    assert slots[0].time_range.upper == sat_1_valid_time_range_end

    assert slots[0].schedule_id == schedule.id
    assert slots[0].asset_id == satellite_1.id

    sat_2_valid_time_range_start = sat_2_valid_opportunity.start_time.replace(tzinfo=slots[1].time_range.lower.tzinfo)
    sat_2_valid_time_range_end = sat_2_valid_time_range_start + sat_2_valid_opportunity.duration
    assert slots[1].time_range.lower == sat_2_valid_time_range_start
    assert slots[1].time_range.upper == sat_2_valid_time_range_end

    assert slots[1].schedule_id == schedule.id
    assert slots[1].asset_id == satellite_2.id

    session.rollback()


test_query_available_satellite_schedule_slots()