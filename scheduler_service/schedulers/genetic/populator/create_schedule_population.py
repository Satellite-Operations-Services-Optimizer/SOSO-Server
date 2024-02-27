from datetime import datetime, timedelta
import uuid
from app_config import get_db_session
from app_config.database.mapping import Schedule, ScheduleRequest, SatelliteOutage, TransmittedEvent, ContactEvent, GroundStationOutage, StateCheckpoint, CaptureOpportunity, ImageOrder, Satellite
from sqlalchemy import or_, exists
from scheduler_service.schedulers.outage_scheduler import schedule_outage
from scheduler_service.schedulers.utils import query_gaps, query_islands, union
from sqlalchemy import func, column, or_, and_, false
from sqlalchemy.orm import aliased
from sqlalchemy import select

def create_schedule_population(start_time: datetime, end_time: datetime, schedule_id: int, max_population_size: int, branching_factor: int = 5):
    """
    Explodes the schedule `schedule_id` into a population of schedules that are feasible within the time range `start_time` to `end_time`.
    Assumes that all static events have been populated within the provided time range `start_time` to `end_time`.

    Returns the schedule group id of the generated population
    """
    population_id = f"generated_population_{uuid.uuid4().hex}"

    # Handle all outage requests
    session = get_db_session()
    outage_requests = session.query(ScheduleRequest).filter(
        ScheduleRequest.schedule_id==schedule_id,
        ScheduleRequest.order_type=="outage",
        ScheduleRequest.status=="processing",
        ScheduleRequest.window_start >= start_time,
        ScheduleRequest.window_end <= end_time
    ).all()

    for outage_request in outage_requests:
        schedule_outage(outage_request, unscheduled_items_state="processing")

    requests_to_schedule = session.query(ScheduleRequest).filter(
        ScheduleRequest.schedule_id==schedule_id,
        ScheduleRequest.status=="processing",
        or_(
            ScheduleRequest.order_type=="imaging",
            ScheduleRequest.order_type=="maintenance"
        )
    ).order_by(ScheduleRequest.priority).all()

    population = []
    for request in requests_to_schedule:
        for schedule in population:
            # for each current schedule we have in our population, 
            # enrich population with `branching_factor` possible new 
            # schedules where this request is scheduled
            request_schedules = generate_schedule_possibilities(
                request.id,
                schedule_id,
                contact_history_start=datetime.now+timedelta(minutes=10),
                branching_factor=branching_factor
            )
            for new_schedule in request_schedules:
                new_schedule.group_name = population_id


        if len(request_schedules)==0:
            pass
            # change status to rejected, citing no available slots to place it
        # available_locations = 


    # get all requests in order of scheduling priority
    schedule_ids = []
    return population_id

def generate_schedule_possibilities(request_id: int, schedule_id: int, contact_history_start: datetime, branching_factor: int):
    """
    Generates `branching_factor` possible schedules where `request` is scheduled.
    """
    session = get_db_session()
    # verify that request exists in the schedule, and is not already scheduled
    request_valid = session.query(exists().where(
        ScheduleRequest.id==request_id,
        ScheduleRequest.schedule_id==schedule_id,
        ScheduleRequest.status!="scheduled",
        ScheduleRequest.status!="sent_to_gs"
    )).scalar()
    if not request_valid:
        raise ValueError(f"Request {request_id} is not valid for scheduling in schedule {schedule_id}. Request must exist in the schedule and not be already scheduled/sent to groundstation.")
    
    ranked_slots = calculate_best_schedule_slots(request_id, schedule_id, contact_history_start)

    # get top `branching_factor` available spots in the schedule to place the request
    for spot in available_spots:
        schedule = copy_schedule(schedule_id)

        # schedule the request in the spot

        # find the corresponding request in the new schedule and update its state

def calculate_best_schedule_slots(request_id: int, schedule_id: int, contact_history_start: datetime):
    """
    Calculates the best schedule slots to place the request in.
    """
    valid_slots = query_valid_slots_to_schedule_request(request_id, schedule_id, contact_history_start)

def query_valid_slots_to_schedule_request(request_id: int, schedule_id: int, contact_history_start: datetime):
    session = get_db_session()
    request = session.query(ScheduleRequest).filter_by(id=request_id).one()

    # Get the available slots for the satellite event to occur
    available_time_slots_subquery = query_satellite_available_time_slots(request_id, schedule_id).subquery()

    # Get the candidate uplink and downlink contacts for the request
    candidate_uplink_contact, candidate_downlink_contact = get_candidate_contact_queries(
        request_id, schedule_id, uplink_start_time=contact_history_start,
    )
    candidate_uplink_subquery = candidate_uplink_contact.subquery()
    candidate_downlink_subquery = candidate_downlink_contact.subquery()

    uplink_required = request.uplink_size > 0
    downlink_required = request.downlink_size > 0

    uplink_time_range = func.tstzrange(candidate_uplink_contact.c.start_time, candidate_uplink_contact.c.start_time+candidate_uplink_contact.c.duration)
    downlink_time_range = func.tstzrange(candidate_downlink_contact.c.start_time, candidate_downlink_contact.c.start_time+candidate_downlink_contact.c.duration)
    valid_slots = session.query(
        available_time_slots_subquery.c.schedule_id,
        available_time_slots_subquery.c.asset_id.label('satellite_id'),
        func.tstzrange(
            func.greatest(func.upper(uplink_time_range), func.lower(available_time_slots_subquery.c.time_range)),
            func.least(func.lower(downlink_time_range), func.upper(available_time_slots_subquery.c.time_range)-request.duration)
        ).label('time_range'),
        candidate_uplink_subquery.id.label('uplink_contact_id'),
        candidate_downlink_subquery.id.label('downlink_contact_id'),
    ).join(
        candidate_uplink_subquery,
        and_(
            available_time_slots_subquery.c.asset_id==candidate_uplink_subquery.c.asset_id,
            uplink_time_range.op('<<')(request.window_end-request.duration), # uplink must finish before our last possible chance to perform the event
        ),
        isouter=not uplink_required
    ).join(
        candidate_downlink_subquery,
        and_(
            available_time_slots_subquery.c.asset_id==candidate_downlink_subquery.c.asset_id,
            downlink_time_range.op('<<')(request.delivery_deadline), # downlink must finish before our delivery deadline
        ),
        isouter=not downlink_required
    )
    return valid_slots

def get_candidate_contact_queries(request_id: int, schedule_id: int, uplink_start_time: datetime):
    """
    Queries the schedule for available contacts to place the request.
    Looks for all contacts that are not in outage, last long enough to
    transmit what is needed, and are not already scheduled to transmit
    something else with its groundstation at that time.
    """
    session = get_db_session()
    request = session.query(ScheduleRequest).filter_by(id=request_id).one()

    if uplink_start_time is None: uplink_start_time = datetime.min
    uplink_end_time = request.window_end - request.duration
    downlink_start_time = request.window_end
    downlink_end_time = request.delivery_deadline

    # get all contacts that we can uplink with, where the contact's groundstation is not in outage during the contact period
    gs_in_outage_for_contact_check = exists().where(
        GroundStationOutage.schedule_id==schedule_id,
        GroundStationOutage.asset_id==ContactEvent.groundstation_id,
        GroundStationOutage.utc_time_range.op('&&')(ContactEvent.utc_time_range),
        or_(
            GroundStationOutage.outage_reason!="transmitting to satellite",
            # if the groundstation is in outage because it is transmitting to
            # the satellite during *this contact* period, then it is not in outage
            # for this satellite, because you can just keep on transmitting,
            # without needing to reconfigure the groundstation to transmit to another satellite
            and_( 
                GroundStationOutage.outage_reason=="transmitting to satellite",
                or_(
                    # if something is scheduled to be transmitted during this contact.
                    # (given we will make sure to place a groundstation outage whenever
                    # something is scheduled to be transmitted during a contact, we can
                    # safely assume that this contact is the only contact that is scheduled
                    # to transmit from this groundstation, thus the groundstation is not in outage
                    # for this contact - in fact, this is the only contact that the groundstation is available for)
                    ContactEvent.total_uplink_size > 0,
                    ContactEvent.total_downlink_size > 0
                )
            ),
        )
    )
    candidate_uplink_contact = session.query(ContactEvent)
    candidate_downlink_contact = session.query(ContactEvent)

    # Get candidate uplink and downlink contacts if the request has to be either uplinked or downlinked. otherwise, no need to get the contacts (filter by false for empty result set)
    contact_time_range = func.tstzrange(ContactEvent.start_time, ContactEvent.start_time+ContactEvent.duration)
    uplink_window = func.tstzrange(uplink_start_time, uplink_end_time)
    if request.uplink_size > 0:
        candidate_uplink_contact = candidate_uplink_contact.filter(
            ContactEvent.schedule_id==schedule_id,
            (ContactEvent.duration.seconds - ContactEvent.total_transmition_time) >= (request.uplink_size*ContactEvent.uplink_rate_mbps),
            ~gs_in_outage_for_contact_check,
            uplink_window.op('@>')(func.lower(contact_time_range))
        )
    else:
        candidate_uplink_contact = candidate_uplink_contact.filter(false())

    downlink_window = func.tstzrange(downlink_start_time, downlink_end_time)
    if request.downlink_size > 0:
        candidate_downlink_contact = candidate_downlink_contact.filter(
            ContactEvent.schedule_id==schedule_id,
            (ContactEvent.duration.seconds - ContactEvent.total_transmition_time) >= (request.downlink_size*ContactEvent.downlink_rate_mbps),
            ~gs_in_outage_for_contact_check,
            downlink_window.op('@>')(func.lower(contact_time_range))
        )
    else:
        candidate_downlink_contact = candidate_downlink_contact.filter(false())

    candidate_uplink_contact = candidate_uplink_contact.label('candidate_uplink_contact')
    candidate_downlink_contact = candidate_downlink_contact.label('candidate_downlink_contact')

    return (candidate_uplink_contact, candidate_downlink_contact)

def query_satellite_available_time_slots(request_id: int, schedule_id: int):
    """
    Queries the schedule for available spots to place the request.
    """
    session = get_db_session()

    request = session.query(ScheduleRequest).filter_by(id=request_id).one()

    # Get all the invalid spots in the schedule
    transmitted_event_query = session.query(
        TransmittedEvent.schedule_id.label('schedule_id'),
        TransmittedEvent.asset_id.label('asset_id'),
        TransmittedEvent.asset_type.label('asset_type'),
        func.tstzrange(TransmittedEvent.start_time, TransmittedEvent.start_time+TransmittedEvent.duration).label('time_range')
    )
    satellite_outage_query = session.query(
        SatelliteOutage.schedule_id.label('schedule_id'),
        SatelliteOutage.asset_id.label('asset_id'),
        SatelliteOutage.asset_type.label('asset_type'),
        func.tstzrange(SatelliteOutage.start_time, SatelliteOutage.start_time+SatelliteOutage.duration).label('time_range')
    )
    if request.asset_id is not None:
        transmitted_event_query = transmitted_event_query.filter(TransmittedEvent.asset_id==request.asset_id)
        satellite_outage_query = satellite_outage_query.filter(SatelliteOutage.asset_id==request.asset_id)
    

    blocking_events_query = union(transmitted_event_query, satellite_outage_query)

    # Handle imaging opportunities if the request is for imaging - get all areas that are not available for imaging
    if request.order_type == "imaging":
        candidate_capture_opportunities = query_candidate_capture_opportunities(request_id, schedule_id).subquery()
        unimageable_time_ranges_query = query_gaps(
            source_subquery=candidate_capture_opportunities,
            range_column=candidate_capture_opportunities.c.time_range,
            partition_columns=[
                CaptureOpportunity.schedule_id.label('schedule_id'),
                CaptureOpportunity.asset_id.label('asset_id'),
                CaptureOpportunity.asset_type.label('asset_type')
            ],
            start_time=request.window_start,
            end_time=request.window_end
        )
        blocking_events_query = blocking_events_query.union(unimageable_time_ranges_query)
    
    blocking_events_subquery = blocking_events_query.subquery()

    event_blocked_regions_query = session.query(
        blocking_events_subquery
    ).filter(
        blocking_events_subquery.c.schedule_id==schedule_id,
        blocking_events_subquery.c.time_range.op('&&')(func.tstzrange(request.window_start, request.window_end))
    )
    
    if request.asset_id is not None:
        event_blocked_regions_query = event_blocked_regions_query.filter(blocking_events_subquery.asset_id == request.asset_id)
    
    # TODO: Query the StateCheckpoint row with the maximum checkpoint_time that is before the request's start time
    # Power constraint and storage constraint are currently affected by this not being completed
    # checkpoint_time = session.query(func.max(StateCheckpoint.checkpoint_time)).filter(StateCheckpoint.checkpoint_time < request.start_time).scalar()
    # checkpoint = session.query(StateCheckpoint).filter(StateCheckpoint.checkpoint_time == max_checkpoint_time)

    # invalid_state_regions_query = session.query(StateCheckpoint).filter(False) # TODO implement
    # invalid_regions = union(event_blocked_regions_query, invalid_state_regions_query).subquery()

    invalid_regions_subquery = event_blocked_regions_query.subquery() # TODO: this is just a stub until we actually implement what is in the comments above

    islands_subquery = query_islands(
        source_subquery=invalid_regions_subquery,
        range_column=invalid_regions_subquery.c.time_range,
        partition_columns=[
            invalid_regions_subquery.c.schedule_id,
            invalid_regions_subquery.c.asset_id,
            invalid_regions_subquery.c.asset_type
        ],
        range_constructor=func.tstzrange,
    ).subquery()

    slot_duration = func.upper(column('time_range')) - func.lower(column('time_range'))
    available_slots_query = query_gaps(
        source_subquery=islands_subquery,
        range_column=islands_subquery.c.time_range,
        partition_columns=[
            islands_subquery.c.schedule_id,
            islands_subquery.c.asset_id,
            islands_subquery.c.asset_type
        ],
        start_time=request.window_start,
        end_time=request.window_end
    ).filter(
        slot_duration >= request.duration
    )

    # TODO: Handle missing slots - where there are no invalid regions, no gaps are detected, so we need to account for that
    all_assumed_available_slots = session.query(

        Satellite.id.label('asset_id'),
        Satellite.asset_type.label('asset_type'),
        func.tstzrange(request.window_start, request.window_end).label('time_range')
    ).filter(Schedule.id==schedule_id)
    )

    return available_slots_query

def query_candidate_capture_opportunities(request_id: int, schedule_id: int):
    """
    Queries the schedule for available capture opportunities when the imaging can take place
    """
    session = get_db_session()
    request = session.query(ScheduleRequest).filter_by(id=request_id).one()

    capture_time_range = func.tstzrange(CaptureOpportunity.start_time, CaptureOpportunity.start_time+CaptureOpportunity.duration).label('time_range')
    capture_window = capture_time_range.op('*')(func.tstzrange(request.window_start, request.window_end))
    candidate_capture_opportunities = session.query(
        CaptureOpportunity.scheudle_id.label('schedule_id'),
        CaptureOpportunity.asset_id.label('asset_id'),
        CaptureOpportunity.asset_type.label('asset_type'),
        capture_window.label('time_range')
    ).filter(
        CaptureOpportunity.schedule_id==schedule_id,
        (func.upper(capture_window)-func.lower(capture_window)) >= request.duration
    )
    if request.asset_id is not None:
        candidate_capture_opportunities = candidate_capture_opportunities.filter(CaptureOpportunity.asset_id==request.asset_id)
    return candidate_capture_opportunities



    
