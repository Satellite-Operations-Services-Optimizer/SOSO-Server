from datetime import datetime, timedelta
from app_config import get_db_session
from app_config.database.mapping import ContactEvent, Schedule, Satellite, GroundStation, GroundStationOutage, CaptureOpportunity, ImageOrder, ScheduleRequest, TransmissionOutage
from helpers import create_dummy_imaging_event
from scheduler_service.schedulers.scheduler_tools import get_candidate_contact_queries

def test_candidate_contact_queries():
    context_cutoff_time = datetime(2022, 5, 15, 0, 0, 0)


    session = get_db_session()
    schedule = Schedule(name="test query candidate uplink/downlink contacts for a request")
    session.add(schedule)
    session.flush()

    satellite_1 = session.query(Satellite).first()
    satellite_2 = session.query(Satellite).offset(1).first()
    groundstation_1 = session.query(GroundStation).first()
    groundstation_2 = session.query(GroundStation).offset(1).first()

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
    session.add(contact_outside_of_context_cutoff)

    contact_overlapping_context_cutoff = ContactEvent(
        schedule_id=schedule.id,
        asset_id=satellite_1.id,
        groundstation_id=groundstation_1.id,
        start_time=context_cutoff_time - large_enough_contact_duration,
        duration= 2*large_enough_contact_duration # it still is enough to uplink within the cutoff
    )
    session.add(contact_overlapping_context_cutoff)

    contact_too_small_within_context_cutoff = ContactEvent(
        schedule_id=schedule.id,
        asset_id=satellite_1.id,
        groundstation_id=groundstation_2.id,
        start_time=context_cutoff_time - large_enough_contact_duration,
        duration=large_enough_contact_duration + too_small_contact_duration
    )
    session.add(contact_too_small_within_context_cutoff)

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
    session.add(contact_already_transmitting)
    session.flush()

    transmission_outage = TransmissionOutage(
        schedule_id=schedule.id,
        asset_id=groundstation_1.id,
        contact_id=contact_already_transmitting.id,
        start_time=contact_already_transmitting.start_time + contact_already_transmitting.duration - contact_reconfig_time,
        duration=contact_already_transmitting.duration + contact_reconfig_time
    )
    session.add(transmission_outage)

    gap_start = transmission_outage.start_time + transmission_outage.duration
    gap_duration = default_gap_duration + contact_reconfig_time

    contact_invalid_because_transmitting_different_sat = ContactEvent(
        schedule_id=schedule.id,
        asset_id=satellite_1.id,
        groundstation_id=groundstation_1.id,
        start_time=gap_start + gap_duration,
        duration=large_enough_contact_duration
    )
    session.add(contact_invalid_because_transmitting_different_sat)

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
    session.add(transmission_outage_different_sat)
    session.flush()

    gap_start = transmission_outage_different_sat.start_time + transmission_outage_different_sat.duration
    gap_duration = default_gap_duration

    regular_outage = GroundStationOutage(
        schedule_id=schedule.id,
        asset_id=groundstation_1.id,
        outage_reason="some random reason",
        start_time=gap_start + gap_duration,
        duration=contact_reconfig_time + large_enough_contact_duration + contact_reconfig_time
    )
    session.add(regular_outage)

    contact_in_outage = ContactEvent(
        schedule_id=schedule.id,
        asset_id=satellite_1.id,
        groundstation_id=groundstation_1.id,
        start_time=regular_outage.start_time + contact_reconfig_time,
        duration=large_enough_contact_duration
    )
    session.add(contact_in_outage)

    gap_start = regular_outage.start_time + regular_outage.duration
    gap_duration = default_gap_duration + medium_image_duration

    contact_too_early_for_downlink = ContactEvent( # must make request start at a time that makes this contact too early for downlink
        schedule_id=schedule.id,
        asset_id=satellite_1.id,
        groundstation_id=groundstation_1.id,
        start_time=gap_start + gap_duration,
        duration=large_enough_contact_duration
    )
    session.add(contact_too_early_for_downlink)

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

    capture_opportunity = CaptureOpportunity(
        schedule_id=schedule.id,
        asset_id=satellite_1.id,
        image_type="medium",
        latitude=0.0,
        longitude=0.0,
        start_time=gap_start + gap_duration,
        duration=medium_image_duration
    )
    session.add(capture_opportunity)

    gap_start = capture_opportunity.start_time + capture_opportunity.duration
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
    session.add(contact_overlapping_event)

    contact_diff_groundstation_overlapping_contact = ContactEvent(
        schedule_id=schedule.id,
        asset_id=satellite_1.id,
        groundstation_id=groundstation_2.id,
        start_time=contact_overlapping_event.start_time + 0.5*contact_overlapping_event.duration,
        duration=large_enough_contact_duration
    )
    session.add(contact_diff_groundstation_overlapping_contact)

    gap_start = max(contact_diff_groundstation_overlapping_contact.start_time + contact_diff_groundstation_overlapping_contact.duration, imaging2.start_time + imaging2.duration)
    gap_duration = default_gap_duration

    contact_different_satellite = ContactEvent(
        schedule_id=schedule.id,
        asset_id=satellite_2.id,
        groundstation_id=groundstation_1.id,
        start_time=gap_start + gap_duration,
        duration=large_enough_contact_duration
    )
    session.add(contact_different_satellite)

    gap_start = contact_different_satellite.start_time + contact_different_satellite.duration
    gap_duration = default_gap_duration

    contact_too_small = ContactEvent(
        schedule_id=schedule.id,
        asset_id=satellite_1.id,
        groundstation_id=groundstation_1.id,
        start_time=contact_different_satellite.start_time + contact_different_satellite.duration,
        duration=too_small_contact_duration
    )
    session.add(contact_too_small)

    gap_start = contact_too_small.start_time + contact_too_small.duration
    gap_duration = default_gap_duration

    contact_too_late_for_uplink = ContactEvent( # must make request start at time that makes this contact too late for uplink
        schedule_id=schedule.id,
        asset_id=satellite_1.id,
        groundstation_id=groundstation_1.id,
        start_time=gap_start + gap_duration,
        duration=large_enough_contact_duration
    )
    session.add(contact_too_late_for_uplink)

    gap_start = contact_too_late_for_uplink.start_time + contact_too_late_for_uplink.duration
    gap_duration = 0.5*medium_image_duration + default_gap_duration # not enough time left after uplink for imaging to take place. NOTE: make sure to set request window to end at a time that makes this contact too late for uplink (0.5*imaging_duration after contact ends)

    contact_outside_request_window = ContactEvent(
        schedule_id=schedule.id,
        asset_id=satellite_1.id,
        groundstation_id=groundstation_1.id,
        start_time=gap_start + gap_duration,
        duration=large_enough_contact_duration
    )
    session.add(contact_outside_request_window)

    gap_start = contact_outside_request_window.start_time + contact_outside_request_window.duration
    gap_duration = default_gap_duration

    contact_overlapping_delivery_deadline = ContactEvent( # must make delivery deadline overlap with this contact
        schedule_id=schedule.id,
        asset_id=satellite_1.id,
        groundstation_id=groundstation_1.id,
        start_time=gap_start + gap_duration,
        duration=large_enough_contact_duration
    )
    session.add(contact_overlapping_delivery_deadline)

    gap_start = contact_overlapping_delivery_deadline.start_time + contact_overlapping_delivery_deadline.duration
    gap_duration = default_gap_duration

    contact_after_delivery_deadline = ContactEvent(
        schedule_id=schedule.id,
        asset_id=satellite_1.id,
        groundstation_id=groundstation_1.id,
        start_time=gap_start + gap_duration,
        duration=large_enough_contact_duration
    )
    session.add(contact_after_delivery_deadline)

    request_start_time = contact_too_early_for_downlink.start_time - 0.5*medium_image_duration # not enough time for imaging to take place before downlink (0.5*imaging_duration)
    request_end_time = contact_too_late_for_uplink.start_time + contact_too_late_for_uplink.duration + 0.5*medium_image_duration # not enough time left after uplink for imaging to take place (0.5*imaging_duration)
    delivery_deadline = contact_overlapping_delivery_deadline.start_time + 0.5*contact_overlapping_delivery_deadline.duration
    order = ImageOrder(
        schedule_id=schedule.id,
        latitude=0.0,
        longitude=0.0,
        image_type="medium",
        start_time=request_start_time,
        end_time=request_end_time,
        delivery_deadline=delivery_deadline
    )
    session.add(order)
    session.flush()
    order = session.query(ImageOrder).filter_by(id=order.id).one() # order.duration is a generated field, and it is not being generated upon flush

    request = ScheduleRequest(
        schedule_id=schedule.id,
        asset_id=satellite_1.id, # we want contact points specifically for this satellite
        order_type="imaging",
        order_id=order.id,
        priority=1,
        window_start=order.start_time,
        window_end=order.end_time,
        duration=order.duration,
        delivery_deadline=order.delivery_deadline,
        uplink_size=order.uplink_size,
        downlink_size=order.downlink_size,
        status="processing"
    )
    session.add(request)
    session.flush()

    candidate_uplinks_query, candidate_downlinks_query = get_candidate_contact_queries(request.id, context_cutoff_time)

    # test candidate uplinks
    candidate_uplinks = candidate_uplinks_query.order_by(ContactEvent.start_time).all()
    candidate_uplink_ids = {contact.id:contact for contact in candidate_uplinks}

    assert contact_outside_of_context_cutoff.id not in candidate_uplink_ids, "we must not be able to uplink at a time before our context cutoff"
    assert contact_overlapping_context_cutoff.id in candidate_uplink_ids, "we must be able to uplink at a time that overlaps with our context cutoff if enough time still remains within cutoff for uplink"
    assert contact_too_small_within_context_cutoff.id not in candidate_uplink_ids, "we must not be able to uplink at a time that is too small within our context cutoff"
    assert contact_already_transmitting.id in candidate_uplink_ids, "we must be able to uplink at a contact that is already uplinking to our desired satellite"
    assert contact_invalid_because_transmitting_different_sat.id not in candidate_uplink_ids, "we must not be able to uplink at a contact that is transmitting to a different satellite. groundstation cannot communicate with two satellites at once."
    assert contact_transmitting_to_different_satellite.id not in candidate_uplink_ids, "we should only receive valid contacts for our specified target satellite, not other satellies"
    assert contact_in_outage.id not in candidate_uplink_ids, "we must not be able to uplink at a contact when the groundstation is in an outage"
    assert contact_too_early_for_downlink.id in candidate_uplink_ids, "we should be able to uplink when the contact is within the request window minus event duration at the end of window. not possible to be too early for uplink unless we are outside context cutoff"
    assert contact_overlapping_event.id in candidate_uplink_ids, "we should be able to uplink at a contact that overlaps with an event"
    assert contact_diff_groundstation_overlapping_contact.id in candidate_uplink_ids, "we should be able to uplink at contact opportunities with different groundstations"
    assert contact_different_satellite.id not in candidate_uplink_ids, "we should only receive valid contacts for our specified target satellite, not other satellites"
    assert contact_too_small.id not in candidate_uplink_ids, "we must not be able to uplink at a contact that is too small for uplink"
    assert contact_too_late_for_uplink.id not in candidate_uplink_ids, "we must not be able to uplink at a contact that doesn't finish in time for us to start and finish imaging before the end of the request window"
    assert contact_outside_request_window.id not in candidate_uplink_ids, "we must not be able to uplink at a contact that is after the request window"
    assert contact_overlapping_delivery_deadline.id not in candidate_uplink_ids, "we must not be able to uplink at a contact that is after the request window"
    assert contact_after_delivery_deadline.id not in candidate_uplink_ids, "we must not be able to uplink at a contact that is after the request window"

    assert len(candidate_uplinks) == 5, "the contacts whose presence were checked for above should be the only possible uplink contacts"


    # test candidate downlinks
    candidate_downlinks = candidate_downlinks_query.order_by(ContactEvent.start_time).all()
    candidate_downlink_ids = {contact.id:contact for contact in candidate_downlinks}

    assert contact_outside_of_context_cutoff.id not in candidate_downlink_ids, "we must not be able to downlink at a time before our request window"
    assert contact_overlapping_context_cutoff.id not in candidate_downlink_ids, "we must not be able to downlink at a time before our request window"
    assert contact_too_small_within_context_cutoff.id not in candidate_downlink_ids, "we must not be able to downlink at a time before our request window"
    assert contact_already_transmitting.id not in candidate_downlink_ids, "we must not be able to downlink at a time before our request window"
    assert contact_invalid_because_transmitting_different_sat.id not in candidate_downlink_ids, "we must not be able to downlink at a time before our request window"
    assert contact_transmitting_to_different_satellite.id not in candidate_downlink_ids, "we should only receive valid contacts for our specified target satellite, not other satellites"
    assert contact_in_outage.id not in candidate_downlink_ids, "we must not be able to downlink at a time before our request window/ downlink at a groundstation in outage"
    assert contact_too_early_for_downlink.id not in candidate_downlink_ids, "we must not be able to downlink before we can possibly have had a chance to even perform the imaging event"
    assert contact_overlapping_event.id in candidate_downlink_ids, "we should be able to downlink at a contact that overlaps with an event"
    assert contact_diff_groundstation_overlapping_contact.id in candidate_downlink_ids, "we should be able to downlink at contact opportunities with different groundstations"
    assert contact_different_satellite.id not in candidate_downlink_ids, "we should only receive valid contacts for our specified target satellite, not other satellies"
    assert contact_too_small.id not in candidate_downlink_ids, "we must not be able to downlink at a contact that is too small for downlink"
    assert contact_too_late_for_uplink.id in candidate_downlink_ids, "we must be able to downlink at a contact that is still within the request window"
    assert contact_outside_request_window.id in candidate_downlink_ids, "we should be able to downlink at a contact that is after the request window, but before the delivery deadline"
    assert contact_overlapping_delivery_deadline.id not in candidate_downlink_ids, "we must not be able to downlink if there is not enough time to downlink before the delivery deadline"
    assert contact_after_delivery_deadline.id not in candidate_downlink_ids, "we must not be able to downlink at a contact that is after the delivery deadline"

    assert len(candidate_downlinks)==4, "the contacts whose presence were checked for above should be the only possible downlink contacts"

    session.rollback()

test_candidate_contact_queries()