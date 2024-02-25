from app_config import get_db_session
from app_config.database.mapping import SatelliteOutage, GroundStationOutage, TransmittedEvent, ScheduleRequest, ContactEvent

def schedule_outage(outage_request, unscheduled_items_state):
    """
    unschedule all scheduled events that overlap, as well as all events that are associated with overlapping contacts (if this is a groundstation outage)
    """
    session = get_db_session()

    if outage_request.asset_type != "satellite":
        raise ValueError("This function is only for scheduling satellite outages")

    OutageModel = SatelliteOutage if outage_request.asset_type == "satellite" else GroundStationOutage
    outage = OutageModel(
        schedule_id=outage_request.schedule_id,
        asset_id=outage_request.asset_id,
        request_id=outage_request.id,
        start_time=outage_request.window_start,
        duration=outage_request.window_end - outage_request.window_start
    )
    session.flush()

    # events scheduled to be performed during the outage
    overlapping_events = session.query(TransmittedEvent).filter_by(
        schedule_id=outage.schedule_id,
        asset_id=outage.asset_id,
        asset_type=outage.asset_type
    ).filter(TransmittedEvent.utc_time_range.overlaps(outage.utc_time_range)).all()

    if outage.asset_type == "satellite":
        contact_event_filter = ContactEvent.asset_id==outage.asset_id
    else:
        contact_event_filter = ContactEvent.groundstation_id==outage.asset_id
    overlapping_contacts_subquery = session.query(ContactEvent.id).filter(
        ContactEvent.schedule_id==outage.schedule_id,
        contact_event_filter
    ).filter(
        ContactEvent.utc_time_range.overlaps(outage.utc_time_range)
    ).subquery()

    untransmittable_events = session.query(TransmittedEvent).filter(
        or_(
            TransmittedEvent.uplink_contact_id.in_(overlapping_contacts_subquery),
            TransmittedEvent.downlink_contact_id.in_(overlapping_contacts_subquery)
        )
    ).all()

    for event in overlapping_events+untransmittable_events:
        session.delete(event)
        session.query(ScheduleRequest).filter_by(id=event.request_id).update({"status": unscheduled_items_state})

    session.commit()
