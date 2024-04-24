from datetime import datetime, timedelta
from app_config import get_db_session
from app_config.database.mapping import ContactEvent, Schedule, Satellite, GroundStation, GroundStationOutage, CaptureOpportunity, ImageOrder, ScheduleRequest, TransmissionOutage
from helpers import create_dummy_imaging_event
from scheduler_service.schedulers.scheduler_tools import query_candidate_scheduling_plans
from sqlalchemy import column
from itertools import product

def test_candidate_contact_queries():
    context_cutoff_time = datetime(2022, 5, 15, 0, 0, 0)


    session = get_db_session()
    schedule = Schedule(name="test query candidate scheduling plans for a request")
    session.add(schedule)
    session.flush()

    satellite_1 = session.query(Satellite).first()
    satellite_2 = session.query(Satellite).offset(1).first()
    groundstation_1 = session.query(GroundStation).first()
    groundstation_2 = session.query(GroundStation).offset(1).first()

    target_latitude = 0.0
    target_longitude = 0.0

    medium_image_downlink_size = 256
    command_size = 0.001 # 1kb
    medium_image_duration = timedelta(seconds=45)

    request_downlink_duration = timedelta(seconds=medium_image_downlink_size / groundstation_1.downlink_rate_mbps)
    request_uplink_duration = timedelta(seconds=command_size / groundstation_1.uplink_rate_mbps)
    too_small_contact_duration = 0.5*min(request_downlink_duration, request_uplink_duration)
    large_enough_contact_duration = request_downlink_duration
    default_gap_duration = timedelta(minutes=1)

    contact_outside_of_context_cutoff = ContactEvent(
        schedule_id=schedule.id,
        asset_id=satellite_1.id,
        groundstation_id=groundstation_1.id,
        start_time=context_cutoff_time - 4*large_enough_contact_duration,
        duration=large_enough_contact_duration,
    )

    contact_overlapping_context_cutoff = ContactEvent(
        schedule_id=schedule.id,
        asset_id=satellite_1.id,
        groundstation_id=groundstation_1.id,
        start_time=context_cutoff_time - large_enough_contact_duration,
        duration= 2*large_enough_contact_duration # it still is enough to uplink within the cutoff
    )

    contact_too_small_within_context_cutoff = ContactEvent(
        schedule_id=schedule.id,
        asset_id=satellite_1.id,
        groundstation_id=groundstation_2.id,
        start_time=context_cutoff_time - large_enough_contact_duration,
        duration=large_enough_contact_duration + too_small_contact_duration
    )

    contact_reconfig_time = timedelta(minutes=6)

    gap_start = contact_overlapping_context_cutoff.start_time + contact_overlapping_context_cutoff.duration
    gap_duration = default_gap_duration + contact_reconfig_time

    contact_already_transmitting = ContactEvent(
        schedule_id=schedule.id,
        asset_id=satellite_1.id,
        groundstation_id=groundstation_1.id,
        start_time=gap_start + gap_duration,
        duration=request_downlink_duration + large_enough_contact_duration, # enough time to have finished transmitting what was already scheduled to be transmitted, and then start transmitting the new request
        total_downlink_size=medium_image_downlink_size # this is what was scheduled to be transmitted. it takes `request_downlink_duration` seconds to transmit this much data
    )

    transmission_outage = TransmissionOutage(
        schedule_id=schedule.id,
        asset_id=groundstation_1.id,
        contact_id=contact_already_transmitting.id,
        start_time=contact_already_transmitting.start_time + contact_already_transmitting.duration - contact_reconfig_time,
        duration=contact_already_transmitting.duration + contact_reconfig_time
    )

    gap_start = transmission_outage.start_time + transmission_outage.duration
    gap_duration = default_gap_duration + contact_reconfig_time

    contact_invalid_because_transmitting_different_sat = ContactEvent(
        schedule_id=schedule.id,
        asset_id=satellite_1.id,
        groundstation_id=groundstation_1.id,
        start_time=gap_start + gap_duration,
        duration=large_enough_contact_duration
    )

    contact_transmitting_to_different_satellite = ContactEvent(
        schedule_id=schedule.id,
        asset_id=satellite_2.id,
        groundstation_id=groundstation_1.id,
        start_time=gap_start + gap_duration,
        duration=large_enough_contact_duration,
        total_downlink_size=medium_image_downlink_size
    )
    session.add(contact_transmitting_to_different_satellite)
    session.flush()

    transmission_outage_different_sat = TransmissionOutage(
        schedule_id=schedule.id,
        asset_id=groundstation_1.id,
        contact_id=contact_transmitting_to_different_satellite.id,
        start_time=contact_transmitting_to_different_satellite.start_time + contact_transmitting_to_different_satellite.duration - contact_reconfig_time,
        duration=contact_transmitting_to_different_satellite.duration + contact_reconfig_time
    )

    gap_start = transmission_outage_different_sat.start_time + transmission_outage_different_sat.duration
    gap_duration = default_gap_duration

    regular_outage = GroundStationOutage(
        schedule_id=schedule.id,
        asset_id=groundstation_1.id,
        outage_reason="some random reason",
        start_time=gap_start + gap_duration,
        duration=contact_reconfig_time + large_enough_contact_duration + contact_reconfig_time
    )

    contact_in_outage = ContactEvent(
        schedule_id=schedule.id,
        asset_id=satellite_1.id,
        groundstation_id=groundstation_1.id,
        start_time=regular_outage.start_time + contact_reconfig_time,
        duration=large_enough_contact_duration
    )

    gap_start = regular_outage.start_time + regular_outage.duration
    gap_duration = default_gap_duration + medium_image_duration

    contact_too_early_for_downlink = ContactEvent( # must make request start at a time that makes this contact too early for downlink
        schedule_id=schedule.id,
        asset_id=satellite_1.id,
        groundstation_id=groundstation_1.id,
        start_time=gap_start + gap_duration,
        duration=large_enough_contact_duration
    )

    gap_start = contact_too_early_for_downlink.start_time + contact_too_early_for_downlink.duration
    gap_duration = default_gap_duration

    imaging1 = create_dummy_imaging_event(
        schedule_id=schedule.id,
        satellite_id=satellite_1.id,
        start_time=gap_start + gap_duration,
        contact_start=gap_start + gap_duration - timedelta(days=1) # make sure this contact event is not in the way of any other events we are interested in
    )

    gap_start = imaging1.start_time + imaging1.duration
    gap_duration = 0.5*large_enough_contact_duration

    # must make capture opportunity start at time that makes the remaining time for this contact smaller than the imaging time.
    # the imaging should still take place but after the contact ends. this is because contact is assumed to be instantaneous, so we don't have to be constrained by the capture opportunity duration.
    contact_overlapping_fit_capture_opportunity = ContactEvent( 
        schedule_id=schedule.id,
        asset_id=satellite_1.id,
        groundstation_id=groundstation_1.id,
        start_time=gap_start + gap_duration,
        duration=large_enough_contact_duration
    )

    prev_contact_end = contact_overlapping_fit_capture_opportunity.start_time + contact_overlapping_fit_capture_opportunity.duration
    capture_opportunity = CaptureOpportunity(
        schedule_id=schedule.id,
        asset_id=satellite_1.id,
        image_type="medium",
        latitude=target_latitude,
        longitude=target_longitude,
        start_time=prev_contact_end - 0.2*large_enough_contact_duration,
        duration=medium_image_duration
    )

    contact_too_early_for_donwlink_for_specific_event_time = ContactEvent(
        schedule_id=schedule.id,
        asset_id=satellite_1.id,
        groundstation_id=groundstation_1.id,
        start_time=capture_opportunity.start_time + capture_opportunity.duration - 0.2*large_enough_contact_duration,
        duration=large_enough_contact_duration
    )

    gap_start = contact_too_early_for_donwlink_for_specific_event_time.start_time + contact_too_early_for_donwlink_for_specific_event_time.duration
    gap_duration = 0.5*large_enough_contact_duration

    imaging2 = create_dummy_imaging_event(
        schedule_id=schedule.id,
        satellite_id=satellite_1.id,
        start_time=gap_start + gap_duration,
        contact_start=gap_start + gap_duration - timedelta(days=1) # make sure this contact event is not in the way of any other events we are interested in
    ) 

    contact_overlapping_event = ContactEvent(
        schedule_id=schedule.id,
        asset_id=satellite_1.id,
        groundstation_id=groundstation_1.id,
        start_time=imaging2.start_time + 0.2*imaging2.duration,
        duration=large_enough_contact_duration
    )

    contact_diff_groundstation_overlapping_contact = ContactEvent(
        schedule_id=schedule.id,
        asset_id=satellite_1.id,
        groundstation_id=groundstation_2.id,
        start_time=contact_overlapping_event.start_time + 0.5*contact_overlapping_event.duration,
        duration=large_enough_contact_duration
    )

    gap_start = max(contact_diff_groundstation_overlapping_contact.start_time + contact_diff_groundstation_overlapping_contact.duration, imaging2.start_time + imaging2.duration)
    gap_duration = default_gap_duration

    contact_different_satellite = ContactEvent(
        schedule_id=schedule.id,
        asset_id=satellite_2.id,
        groundstation_id=groundstation_1.id,
        start_time=gap_start + gap_duration,
        duration=large_enough_contact_duration
    )

    gap_start = contact_different_satellite.start_time + contact_different_satellite.duration
    gap_duration = default_gap_duration

    contact_too_small = ContactEvent(
        schedule_id=schedule.id,
        asset_id=satellite_1.id,
        groundstation_id=groundstation_1.id,
        start_time=contact_different_satellite.start_time + contact_different_satellite.duration,
        duration=too_small_contact_duration
    )

    gap_start = contact_too_small.start_time + contact_too_small.duration
    gap_duration = default_gap_duration

    contact_too_late_for_uplink = ContactEvent( # must make request start at time that makes this contact too late for uplink
        schedule_id=schedule.id,
        asset_id=satellite_1.id,
        groundstation_id=groundstation_1.id,
        start_time=gap_start + gap_duration,
        duration=large_enough_contact_duration
    )

    gap_start = contact_too_late_for_uplink.start_time + contact_too_late_for_uplink.duration
    gap_duration = 0.5*medium_image_duration + default_gap_duration # not enough time left after uplink for imaging to take place. NOTE: make sure to set request window to end at a time that makes this contact too late for uplink (0.5*imaging_duration after contact ends)

    contact_outside_request_window = ContactEvent(
        schedule_id=schedule.id,
        asset_id=satellite_1.id,
        groundstation_id=groundstation_1.id,
        start_time=gap_start + gap_duration,
        duration=large_enough_contact_duration
    )

    gap_start = contact_outside_request_window.start_time + contact_outside_request_window.duration
    gap_duration = default_gap_duration

    contact_overlapping_delivery_deadline = ContactEvent( # must make delivery deadline overlap with this contact
        schedule_id=schedule.id,
        asset_id=satellite_1.id,
        groundstation_id=groundstation_1.id,
        start_time=gap_start + gap_duration,
        duration=large_enough_contact_duration
    )

    gap_start = contact_overlapping_delivery_deadline.start_time + contact_overlapping_delivery_deadline.duration
    gap_duration = default_gap_duration

    contact_after_delivery_deadline = ContactEvent(
        schedule_id=schedule.id,
        asset_id=satellite_1.id,
        groundstation_id=groundstation_1.id,
        start_time=gap_start + gap_duration,
        duration=large_enough_contact_duration
    )

    session.add_all([
        contact_outside_of_context_cutoff,
        contact_overlapping_context_cutoff,
        contact_too_small_within_context_cutoff,
        contact_already_transmitting,
        transmission_outage,
        contact_invalid_because_transmitting_different_sat,
        # contact_transmitting_to_different_satellite,
        transmission_outage_different_sat,
        regular_outage,
        contact_in_outage,
        contact_too_early_for_downlink,
        imaging1,
        contact_overlapping_fit_capture_opportunity ,
        capture_opportunity,
        contact_too_early_for_donwlink_for_specific_event_time,
        imaging2,
        contact_overlapping_event,
        contact_diff_groundstation_overlapping_contact,
        contact_different_satellite,
        contact_too_small,
        contact_too_late_for_uplink,
        contact_outside_request_window,
        contact_overlapping_delivery_deadline,
        contact_after_delivery_deadline
    ])

    request_start_time = contact_too_early_for_downlink.start_time - 0.5*medium_image_duration # not enough time for imaging to take place before downlink (0.5*imaging_duration)
    request_end_time = contact_too_late_for_uplink.start_time + contact_too_late_for_uplink.duration + 0.5*medium_image_duration # not enough time left after uplink for imaging to take place (0.5*imaging_duration)
    delivery_deadline = contact_overlapping_delivery_deadline.start_time + 0.5*contact_overlapping_delivery_deadline.duration
    order = ImageOrder(
        schedule_id=schedule.id,
        latitude=target_latitude,
        longitude=target_longitude,
        image_type="medium",
        window_start=request_start_time,
        window_end=request_end_time,
        delivery_deadline=delivery_deadline
    )
    session.add(order)
    session.flush()
    order = session.query(ImageOrder).filter_by(id=order.id).one() # order.duration is a generated field, and it is not being generated upon flush

    request = ScheduleRequest(
        schedule_id=schedule.id,
        order_type="imaging",
        order_id=order.id,
        priority=1,
        window_start=order.window_start,
        window_end=order.window_end,
        duration=order.duration,
        delivery_deadline=order.delivery_deadline,
        uplink_size=order.uplink_size,
        downlink_size=order.downlink_size,
        status="processing"
    )
    session.add(request)
    session.flush()

    candidate_plans = query_candidate_scheduling_plans(request.id, context_cutoff_time).all()

    # expect all candidates to use the same (only available) capture opportunity
    for plan in candidate_plans:
        plan_tz = plan.time_range.lower.tzinfo
        uplink_contact = session.query(ContactEvent).filter_by(id=plan.uplink_contact_id).one()

        uplink_end_time = (uplink_contact.start_time + uplink_contact.duration).replace(tzinfo=plan_tz)
        capture_start_time = capture_opportunity.start_time.replace(tzinfo=plan_tz)
        imaging_start_time = max(capture_start_time, uplink_end_time)
        imaging_end_time = imaging_start_time + medium_image_duration
        assert plan.time_range.lower == imaging_start_time and plan.time_range.upper > imaging_end_time, "the correct capture opportunities must be identified and used for all candidate plans"

    permissible_uplink_ids = [
        contact_overlapping_context_cutoff.id,
        contact_already_transmitting.id,
        contact_too_early_for_downlink.id,
        contact_overlapping_fit_capture_opportunity.id
    ]
    permissible_downlink_ids = [
        contact_overlapping_event.id,
        contact_diff_groundstation_overlapping_contact.id,
        contact_too_late_for_uplink.id,
        contact_outside_request_window.id
    ]

    permissible_ids = product(permissible_uplink_ids, permissible_downlink_ids)
    expected_candidate_plans = sorted([ids for ids in permissible_ids])
    candidate_plans = sorted([(plan.uplink_contact_id, plan.downlink_contact_id) for plan in candidate_plans])

    for i, plan in enumerate(candidate_plans):
        assert plan == expected_candidate_plans[i], "the correct candidate plans must be identified"

    assert len(expected_candidate_plans) == len(candidate_plans)

    session.rollback()

test_candidate_contact_queries()