from app_config import get_db_session, rabbit, logging
from app_config.database.mapping import ScheduleRequest, ImageOrder, MaintenanceOrder, TransmittedEvent, SatelliteOutage, GroundStationOutage, ContactEvent, ScheduledImaging, ScheduledMaintenance, GroundStation, Schedule, EclipseProcessingBlock, TransmissionOutage, CaptureOpportunity, ScheduledEvent
from sqlalchemy import or_, and_, func, exists, column
from .scheduler_tools import calculate_top_scheduling_plans, query_satellite_available_time_slots
from datetime import datetime, timedelta
from event_processing.capture_opportunities import ensure_capture_opportunities_populated
from event_processing.contact_events import ensure_contact_events_populated
from event_processing.eclipse_events import ensure_eclipse_events_populated
from rabbit_wrapper import TopicConsumer, TopicPublisher

logger = logging.getLogger(__name__)

def register_request_scheduler_listener():
    schedule_request_consumer = TopicConsumer(rabbit())
    schedule_request_consumer.bind("schedule.request.*.created")
    schedule_request_consumer.bind("schedule.request.*.displaced")
    schedule_request_consumer.register_callback(lambda request_id: process_request(request_id))

    schedule_decline_consumer = TopicConsumer(rabbit(), "schedule.request.*.decline")
    schedule_decline_consumer.register_callback(lambda request_id: decline_request(request_id))

def process_request(request_id: int):
    restart_interrupted_requests()
    session = get_db_session()
    request = session.query(ScheduleRequest).filter_by(id=request_id).one()
    if not (request.status == "received" or request.status == "displaced"):
        logger.error("BUG WARNING: Something went wrong. Cannot start processing request with id={request_id}. It may have already been scheduled or rejected, or is already currently being processed. Status: {request.status}")
        return
    request.status = "processing"
    session.commit()
    logger.info(f"Processing {request.order_type} request with id={request_id}...")
    if request.order_type == "outage":
        schedule_outage_request(request.id)
    else:
        schedule_transmitted_event(request.id)
    pass
        
def restart_interrupted_requests():
    session = get_db_session()
    # if there were orders we never finished processing, reset them
    interrupted_requests = session.query(ScheduleRequest).filter(
        or_(
            ScheduleRequest.status=="processing",
            ScheduleRequest.status=="received"
        )
    ).all()
    for request in interrupted_requests:
        request.status = "received"
        session.commit()
        TopicPublisher(rabbit(), f"schedule.request.{request.order_type}.created").publish_message(request.id)

def decline_request(request_id: int):
    session = get_db_session()
    request = session.query(ScheduleRequest).filter_by(id=request_id).one()

    displace_scheduled_request(request_id, "", emit=False)
    request.status = "declined"
    request.status_message = "The request was declined by an opertor."
    session.commit()

    # publish event notifying declined
    TopicPublisher(rabbit(), f"schedule.request.{request.order_type}.declined").publish_message(request.id)
    logger.info(f"Declined {request.order_type} request with id={request.id}.")

def optimized_request_planning(request_id) -> list:
    session = get_db_session()
    request = session.query(ScheduleRequest).filter_by(id=request_id).one()
    schedule = session.query(Schedule).filter_by(id=request.schedule_id).one()

    current_time = datetime.now() + schedule.time_offset
    min_context_cutoff = current_time + schedule.rejection_cutoff
    min_context_cutoff = min_context_cutoff.replace(tzinfo=request.delivery_deadline.tzinfo)
    max_context_cutoff = request.delivery_deadline


    # We need eclipse events within request window for sure
    ensure_eclipse_events_populated(request.window_start, request.delivery_deadline) # TODO IMPORTANT!!!: Think of the interaction of this with the state checkpoint and calculating state. if we are only ensuring from this context cutoff, how do we know that the state is correct when we are calculating the state from the last checkpoint? UPDATE: No problem. we know because if an event was ever scheduled there, the eclipses must have already been populated. eclipses don't matter when we don't have any events taking place, and whenever we schedule an event to take place, we ensure that the eclipses are populated (exactly what we are doing now). Outages don't affect state. they just displace events. if there were no events there to begin with, nothing is affected. Only edge case is when one eclipse processing block ends close to another one starts, and they have an eclipse that spans from one's end to another's start. that means that by our internal model, it seems that the eclipse briefly ended and started again - so it seems like the satellite regained all its power. This is the only problem case.

    context_growth_increment = max(timedelta(days=7), request.window_end-request.window_start)
    lower_context_cutoff = request.window_start
    upper_context_cutoff = request.window_end

    retry_count = 0
    failure_reason = None
    while lower_context_cutoff > min_context_cutoff or upper_context_cutoff < max_context_cutoff:
        retry_count += 1
        if retry_count > 5:
            reject_request(request.id, f"Spent too much time trying to find a valid schedule plan. Failure reason during last try: {failure_reason}")
            return []
        if lower_context_cutoff < min_context_cutoff:
            ensure_eclipse_events_populated(lower_context_cutoff - context_growth_increment, lower_context_cutoff, request.asset_id) # 10 minutes for overlap
            ensure_eclipse_events_populated(upper_context_cutoff, upper_context_cutoff + context_growth_increment, request.asset_id)
        lower_context_cutoff = max(lower_context_cutoff - context_growth_increment, min_context_cutoff)
        upper_context_cutoff = min(upper_context_cutoff + context_growth_increment, max_context_cutoff)

        ensure_contact_events_populated(lower_context_cutoff, upper_context_cutoff)

        # # for all contacts overlapping the incremented durations of the context cutoffs, calculate eclipses around those contact periods, with a buffer of `max_eclipse_duration` before each contact, to make sure it has enough power/energy to finish the contact.
        # # We add the buffer before the contact so that there never comes a case where the satellite is low on power and still in eclipse and happens to come in contact, and doesn't have enough power to do the contact, but we don't realize because we didn't know the ecipse was continuous, and not just starting once the contact starts
        # # Also, we calculate eclipses specifically only for that satellite which is in contact.
        # contact_time_range = func.tstzrange(ContactEvent.start_time, ContactEvent.start_time + ContactEvent.duration)
        # max_eclipse_duration = timedelta(hours=1)
        # eclipse_processing_time_range = contact_time_range.op('+')(
        #     func.tstzrange(
        #         ContactEvent.start_time - max_eclipse_duration,
        #         ContactEvent.start_time + ContactEvent.duration
        #     )
        # )

        # eclipse_processing_ranges = session.query(
        #     ContactEvent.id.label('contact_id'),
        #     ContactEvent.asset_id.label('satellite_id'),
        #     eclipse_processing_time_range.label('time_range')
        # ).filter(
        #     contact_time_range.op('&&')(func.tstzrange(lower_context_cutoff, upper_context_cutoff)),
        #     ~exists(EclipseProcessingBlock).where(
        #         ContactEvent.asset_id==EclipseProcessingBlock.satellite_id,
        #         EclipseProcessingBlock.time_range.op('@>')(column('time_range')) # remove the ones where we have already completely processed the time range for eclipses already
        #     )
        # ).all()

        # for range in eclipse_processing_ranges:
        #     ensure_eclipse_events_populated(range.time_range.lower, range.time_range.upper, range.satellite_id)


        scheduling_plans, failure_reason = calculate_top_scheduling_plans(
            request_id=request.id,
            context_cutoff_time=lower_context_cutoff, # we only need lower_context_cutoff because we assume upper cutoff is request.delivery_deadline. best case we have already processed contacts past upper_context_cutoff and we gett a better scheduling plann sooner. worst case, no contacts are found there and this function expands the upper context cutoff
            top_n=1,
            workload_distribution_factor=0.75
        )

        if len(scheduling_plans) > 0:
            return scheduling_plans


        context_growth_increment = min(context_growth_increment*2, timedelta(days=60)) # double the time offset, but cap it at 40 days
        current_time = datetime.now() + schedule.time_offset
        min_context_cutoff = current_time + schedule.rejection_cutoff
        min_context_cutoff = min_context_cutoff.replace(tzinfo=request.delivery_deadline.tzinfo)
        max_context_cutoff = request.delivery_deadline
    
    reject_request(request.id, f"{failure_reason}")
    return []


def schedule_transmitted_event(request_id: int):
    session = get_db_session()
    request = session.query(ScheduleRequest).filter_by(id=request_id).one()
    schedule = session.query(Schedule).filter_by(id=request.schedule_id).one()

    current_time = datetime.now() + schedule.time_offset
    context_cutoff = current_time + schedule.rejection_cutoff
    context_cutoff = context_cutoff.replace(tzinfo=request.delivery_deadline.tzinfo)

    if context_cutoff > request.window_end - request.duration:
        reject_request(request.id, "Not enough time to plan event. Can't uplink and perform event before its end time.")
        return
    

    if request.order_type == "imaging":
        ensure_capture_opportunities_populated(request.window_start, request.window_end, request.order_id)
        order = session.query(ImageOrder).filter_by(id=request.order_id).one()
        capture_opportunity_time_range = func.tstzrange(CaptureOpportunity.start_time, CaptureOpportunity.start_time+CaptureOpportunity.duration)
        capture_opportunities_exist = session.query(CaptureOpportunity).filter(
            CaptureOpportunity.image_type==order.image_type,
            CaptureOpportunity.latitude==order.latitude,
            CaptureOpportunity.longitude==order.longitude,
            capture_opportunity_time_range.op('&&')(func.tstzrange(request.window_start, request.window_end))
        ).count() > 0
        if not capture_opportunities_exist:
            reject_request(request.id, "No satellites can capture this area during the requested time window.")
            return
    available_time_slots = query_satellite_available_time_slots(request.id, request.priority_tier, request.priority).count()
    if available_time_slots == 0:
        reject_request(request.id, "No available time slots for this event.")
        return
    
    scheduling_plans = optimized_request_planning(request_id)

    if len(scheduling_plans) > 0:
        execute_schedule_plan(scheduling_plans[0])
    


def execute_schedule_plan(schedule_plan):
    session = get_db_session()
    request = session.query(ScheduleRequest).filter_by(id=schedule_plan.request_id).one()

    if request.order_type != "imaging" and request.order_type != "maintenance":
        raise ValueError(f"Unsupported order type: {request.order_type}. Can only execute scheduling plans for imaging and maintenance orders")

    # unschedule any overlapping events and mark them as rejected, with reason of "lower priority"
    transmitted_event_time_range = func.tstzrange(TransmittedEvent.start_time, TransmittedEvent.start_time + TransmittedEvent.duration)
    displaced_events = session.query(TransmittedEvent).filter_by(
        asset_id=request.asset_id,
        asset_type=request.asset_type,
        schedule_id=request.schedule_id
    ).filter(transmitted_event_time_range.op('&&')(schedule_plan.time_range)).all()

    for event in displaced_events:
        displace_scheduled_request(event.request_id, "Event was displaced in favor of a higher priority event.")

    session.commit()


    # schedule the event
    if request.order_type == "imaging":
        EventTable = ScheduledImaging
    else:
        EventTable = ScheduledMaintenance
    event = EventTable(
        schedule_id=request.schedule_id,
        request_id=request.id,
        asset_id=schedule_plan.asset_id,
        start_time=schedule_plan.time_range.lower,
        duration=request.duration,
        window_start=request.window_start,
        window_end=request.window_end,
        uplink_contact_id=schedule_plan.uplink_contact_id,
        downlink_contact_id=schedule_plan.downlink_contact_id,
        uplink_size=request.uplink_size,
        downlink_size=request.downlink_size,
        power_usage=request.power_usage,
        priority=request.priority
    )
    session.add(event)

    # set groundstations in outage for transmission contact
    if schedule_plan.uplink_contact_id is not None:
        uplink_transmission_outage = session.query(TransmissionOutage).filter_by(
            contact_id=event.uplink_contact_id
        ).one_or_none()
        if uplink_transmission_outage is None:
            uplink_contact = session.query(ContactEvent).filter_by(id=schedule_plan.uplink_contact_id).one()
            uplink_groundstation = session.query(GroundStation).filter_by(id=uplink_contact.groundstation_id).one()
            uplink_outage = TransmissionOutage(
                schedule_id=request.schedule_id,
                asset_id=uplink_groundstation.id,
                contact_id=uplink_contact.id,
                start_time=uplink_contact.start_time - uplink_groundstation.reconfig_duration,
                duration=uplink_contact.duration + 2*uplink_groundstation.reconfig_duration
            )
            session.add(uplink_outage)
    
    if schedule_plan.downlink_contact_id is not None:
        downlink_transmission_outage = session.query(TransmissionOutage).filter_by(
            contact_id=event.downlink_contact_id
        ).one_or_none()
        if downlink_transmission_outage is None:
            downlink_contact = session.query(ContactEvent).filter_by(id=schedule_plan.downlink_contact_id).one()
            downlink_groundstation = session.query(GroundStation).filter_by(id=downlink_contact.groundstation_id).one()
            downlink_outage = TransmissionOutage(
                schedule_id=request.schedule_id,
                asset_id=downlink_groundstation.id,
                contact_id=downlink_contact.id,
                start_time=downlink_contact.start_time - downlink_groundstation.reconfig_duration,
                duration=downlink_contact.duration + 2*downlink_groundstation.reconfig_duration
            )
            session.add(downlink_outage)

    notify_request_scheduled(request.id)

def schedule_outage_request(request_id):
    """
    unschedule all scheduled events that overlap, as well as all events that are associated with overlapping contacts (if this is a groundstation outage)
    """
    session = get_db_session()

    request = session.query(ScheduleRequest).filter_by(id=request_id).one()
    if request.order_type != "outage":
        raise Exception("This function only scheduling outages.")

    # events scheduled to be performed during the outage
    request_ids_for_overlapping_events = session.query(TransmittedEvent.request_id).filter_by(
        schedule_id=request.schedule_id,
        asset_id=request.asset_id,
        asset_type=request.asset_type
    ).filter(TransmittedEvent.utc_time_range.overlaps(request.utc_window_time_range))

    if request.asset_type == "satellite":
        contact_event_filter = ContactEvent.asset_id==request.asset_id
    else:
        contact_event_filter = ContactEvent.groundstation_id==request.asset_id
    overlapping_contacts_subquery = session.query(ContactEvent.id).filter(
        ContactEvent.schedule_id==request.schedule_id,
        contact_event_filter
    ).filter(
        ContactEvent.utc_time_range.overlaps(request.utc_window_time_range)
    ).subquery()

    request_ids_for_untransmittable_events = session.query(TransmittedEvent.request_id).filter(
        or_(
            TransmittedEvent.uplink_contact_id.in_(overlapping_contacts_subquery),
            TransmittedEvent.downlink_contact_id.in_(overlapping_contacts_subquery)
        )
    )

    # union the two and get the unique ids
    displaced_requests = request_ids_for_overlapping_events.union(request_ids_for_untransmittable_events).distinct().all()
    for displaced_request in displaced_requests:
        displace_scheduled_request(displaced_request.request_id, message=f"Scheduled request was displaced due to an outage at {request.asset_type} id={request.asset_id}.")
    
    session.commit()

    OutageModel = SatelliteOutage if request.asset_type == "satellite" else GroundStationOutage
    outage = OutageModel(
        schedule_id=request.schedule_id,
        asset_id=request.asset_id,
        request_id=request.id,
        start_time=request.window_start,
        duration=request.window_end - request.window_start
    )
    session.add(outage)
    session.commit()

    notify_request_scheduled(request.id)

def displace_scheduled_request(request_id, message, emit=True):
    session = get_db_session()

    request =session.query(ScheduleRequest).filter_by(id=request_id).one()
    event = session.query(TransmittedEvent).filter_by(request_id=request.id).one_or_none()
    if event is None:
        return

    if event.uplink_contact_id is not None:
        session.query(TransmissionOutage).filter_by(
            contact_id=event.uplink_contact_id
        ).filter(
            exists(ContactEvent).where(
                ContactEvent.id==TransmissionOutage.contact_id,
                ContactEvent.total_uplink_size-event.uplink_size <= 0
            )
        ).delete()
    if event.downlink_contact_id is not None:
        session.query(TransmissionOutage).filter_by(
            contact_id=event.downlink_contact_id
        ).filter(
            exists(ContactEvent).where(
                ContactEvent.id==TransmissionOutage.contact_id,
                ContactEvent.total_downlink_size-event.downlink_size <= 0
            )
        ).delete()

    # have to delete this way and not with session.delete(event) because it deletes from all
    # children tables (both imaging and maintenance events) with the event.id if you do session.delete(event) (and id is not unique
    # across inherited tables, so it deletes potentially multiple rows, as long as it has the same id as event.id. it doesn't just)
    # delete the corresponding row of the `event` orm object we pass to it.)
    session.query(ScheduledEvent).filter_by(request_id=request.id).delete() 

    request.status = "displaced"
    request.status_message = message
    session.commit()

    if emit:
        TopicPublisher(rabbit(), f"schedule.request.{request.order_type}.displaced").publish_message(request.id)
        logger.info(f"Displaced {request.order_type} request with id={request.id}. {message}")

def reject_request(request_id, message):
    session = get_db_session()
    request = session.query(ScheduleRequest).filter_by(id=request_id).one()
    request.status = "rejected"

    if request.status_message is not None and request.status_message != "" and message != "":
        request.status_message = f"{request.status_message} {message}"
    else:
        request.status_message = message
    session.commit()
    TopicPublisher(rabbit(), f"schedule.request.{request.order_type}.rejected").publish_message(request.id)
    logger.info(f"Rejected {request.order_type} request with id={request.id}. {message}")

def notify_request_scheduled(request_id):
    session = get_db_session()
    request = session.query(ScheduleRequest).filter_by(id=request_id).one()
    event = session.query(ScheduledEvent).filter_by(request_id=request.id).one()

    request.status = "scheduled"
    if request.status_message is not None and request.status_message != "":
        request.status_message = f"{request.status_message} Succesfully scheduled request."
    else:
        request.status_message = "Successfully scheduled request."
    session.commit()
    TopicPublisher(rabbit(), f"schedule.request.{request.order_type}.scheduled").publish_message(request.id)
    logger.info(f"Scheduled {request.order_type} request with id={request.id}. event_id={event.id}.")