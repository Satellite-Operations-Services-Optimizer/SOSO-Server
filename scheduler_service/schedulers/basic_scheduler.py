from app_config import get_db_session, rabbit
from app_config.database.mapping import ScheduleRequest, ImageOrder, MaintenanceOrder, TransmittedEvent, SatelliteOutage, GroundStationOutage, ContactEvent, ScheduledImaging, ScheduledMaintenance, GroundStation
from sqlalchemy import or_, and_
from scheduler_tools import calculate_top_scheduling_plans
from datetime import datetime, timedelta
from event_processing.capture_opportunities import ensure_capture_opportunities_populated
from event_processing.contact_events import ensure_contact_events_populated
from event_processing.eclipse_events import ensure_eclipse_events_populated
from rabbit_wrapper import TopicConsumer, TopicPublisher

def register_request_scheduler_listener():
    consumer = TopicConsumer(rabbit())
    consumer.bind("request.*.created")
    consumer.bind("request.*.displaced")
    consumer.register_callback(lambda request_id: schedule_request(request_id))

    declined_consumer = TopicConsumer(rabbit())
    declined_consumer.bind("request.*.declined")
    declined_consumer.register_callback(lambda request_id: decline_request(request_id))

def schedule_request(request_id: int):
    session = get_db_session()
    request = session.query(ScheduleRequest).filter_by(id=request_id).one()
    if request.order_type == "gs_outage" or request.order_type == "sat_outage":
        schedule_outage_request(request.id)
    else:
        schedule_planned_request(request.id)

def schedule_planned_request(request_id: int):
    session = get_db_session()
    request = session.query(ScheduleRequest).filter_by(id=request_id).one()
    schedule = session.query(ScheduleRequest).filter_by(id=request.schedule_id).one()

    enough_time_for_scheduling_and_sending_to_groundstation = timedelta(minutes=10)
    current_time = datetime.now() - schedule.reference_time_offset

    context_cutoff = current_time + enough_time_for_scheduling_and_sending_to_groundstation

    ensure_eclipse_events_populated(context_cutoff, request.delivery_deadline) # TODO IMPORTANT!!!: Think of the interaction of this with the state checkpoint and calculating state. if we are only ensuring from this context cutoff, how do we know that the state is correct when we are calculating the state from the last checkpoint?
    ensure_contact_events_populated(context_cutoff, request.delivery_deadline)
    ensure_capture_opportunities_populated(context_cutoff, request.delivery_deadline, request.order_id)
    scheduling_plan = calculate_top_scheduling_plans(
        request_id=request.id,
        context_cutoff_time=context_cutoff,
        top_n=1,
        workload_distribution_factor=0.75
    )

    if len(scheduling_plan) > 0:
        execute_schedule_plan(scheduling_plan[0])
        return
    
    prev_status = request.status
    request.status = "rejected"
    if request.status == "displaced":
        request.status_message = f"{prev_status} Could not find a new spot to schedule the event."
    else:
        request.status_message = f"Could not find a spot to schedule this event."
    
    session.commit()
    # publish event notifying rejected


def execute_schedule_plan(schedule_plan):
    session = get_db_session()
    request = session.query(ScheduleRequest).filter_by(id=schedule_plan.request_id).one()

    if request.order_type != "imaging" and request.order_type != "maintenance":
        raise ValueError(f"Unsupported order type: {request.order_type}. Can only execute scheduling plans for imaging and maintenance orders")

    # unschedule any overlapping events and mark them as rejected, with reason of "lower priority"
    displaced_events = session.query(TransmittedEvent).filter_by(
        asset_id=request.asset_id,
        asset_type=request.asset,
        schedule_id=request.schedule
    ).filter(TransmittedEvent.utc_time_range.overlaps(schedule_plan.utc_time_range)).all()

    for event in displaced_events:
        displace_event(event, "Event was displaced in favor of a higher priority event.")

    session.commit()


    # schedule the event
    if request.order_type == "imaging":
        event = ScheduledImaging(
            schedule_id=request.schedule_id,
            request_id=request.id,
            duration=request.duration,
            asset_id=schedule_plan.asset_id,
            uplink_contact_id=schedule_plan.uplink_contact_id,
            downlink_contact_id=schedule_plan.downlink_contact_id,
            start_time=schedule_plan.time_range.lower,
        )
        session.add(event)
    elif request.order_type == "maintenance":
        event = ScheduledMaintenance(
            schedule_id=request.schedule_id,
            request_id=request.id,
            duration=request.duration,
            asset_id=schedule_plan.asset_id,
            uplink_contact_id=schedule_plan.uplink_contact_id,
            downlink_contact_id=schedule_plan.downlink_contact_id,
            start_time=schedule_plan.time_range.lower,
        )
        session.add(event)

    # set groundstations in outage for transmission contact
    if schedule_plan.uplink_contact_id is not None:
        uplink_contact = session.query(ContactEvent).filter_by(id=schedule_plan.uplink_contact_id).one()
        uplink_groundstation = session.query(GroundStation).filter_by(id=uplink_contact.groundstation_id).one()
        uplink_outage = GroundStationOutage(
            schedule_id=request.schedule_id,
            asset_id=uplink_groundstation.id,
            outage_reason="transmitting",
            start_time=uplink_contact.start_time - uplink_groundstation.reconfig_duration,
            duration=uplink_contact.duration + 2*uplink_groundstation.reconfig_duration
        )
        session.add(uplink_outage)
    
    if schedule_plan.downlink_contact_id is not None:
        downlink_contact = session.query(ContactEvent).filter_by(id=schedule_plan.downlink_contact_id).one()
        downlink_groundstation = session.query(GroundStation).filter_by(id=downlink_contact.groundstation_id).one()
        downlink_outage = GroundStationOutage(
            schedule_id=request.schedule_id,
            asset_id=downlink_groundstation.id,
            outage_reason="transmitting",
            start_time=downlink_contact.start_time - downlink_groundstation.reconfig_duration,
            duration=downlink_contact.duration + 2*downlink_groundstation.reconfig_duration
        )
        session.add(downlink_outage)
    
    session.query(ScheduleRequest).filter_by(id=event.request_id).update({
        "status": "scheduled",
        "status_message": ""
    })
    session.commit()


    # publish event notifying scheduled
    TopicPublisher(rabbit(), f"request.{event.event_type}.scheduled").publish(event.request_id)

    for event in displaced_events:
        # publish event notifying displaced
        TopicPublisher(rabbit(), f"request.{event.event_type}.displaced").publish(event.request_id)


def schedule_outage_request(request_id):
    """
    unschedule all scheduled events that overlap, as well as all events that are associated with overlapping contacts (if this is a groundstation outage)
    """
    session = get_db_session()

    request = session.query(ScheduleRequest).filter_by(id=request_id).one()
    if request.order_type != "gs_outage" and request.order_type != "sat_outage":
        raise Exception("This function only processes outages.")

    if request.asset_type != "satellite":
        raise ValueError("This function is only for scheduling satellite outages")

    # events scheduled to be performed during the outage
    overlapping_events = session.query(TransmittedEvent).filter_by(
        schedule_id=request.schedule_id,
        asset_id=request.asset_id,
        asset_type=request.asset_type
    ).filter(TransmittedEvent.utc_time_range.overlaps(request.utc_window_time_range)).all()

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

    untransmittable_events = session.query(TransmittedEvent).filter(
        or_(
            TransmittedEvent.uplink_contact_id.in_(overlapping_contacts_subquery),
            TransmittedEvent.downlink_contact_id.in_(overlapping_contacts_subquery)
        )
    ).all()

    displaced_events = overlapping_events+untransmittable_events
    for event in displaced_events:
        displace_event(event, message=f"Event was displaced due to an outage at {outage.asset_type} id={outage.asset_id}.")
    
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

    session.query(ScheduleRequest).filter_by(id=outage.request_id).update({
        "status": "scheduled",
        "status_message": ""
    })
    session.commit()


    # publish event notifying scheduled
    TopicPublisher(rabbit(), f"request.{outage.event_type}.scheduled").publish(outage.request_id)

    for event in displaced_events:
        # publish event notifying displaced
        TopicPublisher(rabbit(), f"request.{event.event_type}.displaced").publish(event.request_id)
    
def decline_request(request_id):
    session = get_db_session()
    request = session.query(ScheduleRequest).filter_by(id=request_id).one()

    event = session.query(TransmittedEvent).filter_by(request_id=request_id).one_or_none()
    displace_event(event, "")
    request.status = "declined"
    request.status_message = "The request was declined by an opertor."
    session.commit()

    # publish event notifying declined
    TopicPublisher(rabbit(), f"request.{request.order_type}.declined").publish(request.id)

def displace_event(event, message):
    session = get_db_session()
    if event.uplink_contact_id is not None:
        uplink_transmission_outage = session.query(GroundStationOutage).join(
            ContactEvent,
            and_(
                ContactEvent.id==event.uplink_contact_id,
                ContactEvent.total_uplink_size-event.uplink_size <= 0 # This is the only event left scheduled to be transmitted during this contact (and since we are unscheduling it, there will be no more events scheduled to be transmitted during this contact)
            )
        ).filter(
            GroundStationOutage.schedule_id==event.schedule_id,
            GroundStationOutage.asset_id==ContactEvent.groundstation_id,
            GroundStationOutage.outage_reason=="transmitting",
            GroundStationOutage.utc_time_range.overlaps(ContactEvent.utc_time_range)
        ).one_or_none()
        session.delete(uplink_transmission_outage)
    if event.downlink_contact_id is not None:
        downlink_transmission_outage = session.query(GroundStationOutage).join(
            ContactEvent,
            and_(
                ContactEvent.id==event.downlink_contact_id,
                ContactEvent.total_downlink_size-event.downlink_size <= 0 # This is the only event left scheduled to be transmitted during this contact (and since we are unscheduling it, there will be no more events scheduled to be transmitted during this contact)
            )
        ).filter(
            GroundStationOutage.schedule_id==event.schedule_id,
            GroundStationOutage.asset_id==ContactEvent.groundstation_id,
            GroundStationOutage.outage_reason=="transmitting",
            GroundStationOutage.utc_time_range.overlaps(ContactEvent.utc_time_range)
        ).one_or_none()
        session.delete(downlink_transmission_outage)


    session.delete(event)
    session.query(ScheduleRequest).filter_by(id=event.request_id).update({
        "status": "displaced",
        "status_message": message
    })
    session.commit()