from datetime import datetime
import uuid
from app_config import get_db_session
from app_config.database.mapping import Schedule, ScheduleRequest, SatelliteOutage, TransmittedEvent, ContactEvent, GroundStationOutage, StateCheckpoint
from sqlalchemy import or_, exists
from scheduler_service.schedulers.outage_scheduler import schedule_outage
from scheduler_service.schedulers.utils import query_gaps, query_islands, union
from sqlalchemy import func, column

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
            request_schedules = generate_schedule_possibilities(request.id, schedule_id, branching_factor)
            for new_schedule in request_schedules:
                new_schedule.group_name = population_id


        if len(request_schedules)==0:
            pass
            # change status to rejected, citing no available slots to place it
        # available_locations = 


    # get all requests in order of scheduling priority
    schedule_ids = []
    return population_id

def generate_schedule_possibilities(request_id: ScheduleRequest, schedule_id: int, branching_factor: int):
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
    
    # get top `branching_factor` available spots in the schedule to place the request
    available_spots = query_available_satellite_schedule_slots(request_id, schedule_id).limit(branching_factor).all()

    for spot in available_spots:
        schedule = copy_schedule(schedule_id)

        # schedule the request in the spot

        # find the corresponding request in the new schedule and update its state

def query_available_satellite_schedule_slots(request_id: int, schedule_id: int):
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
    blocking_events_subquery = union(transmitted_event_query, satellite_outage_query).subquery()

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
            invalid_regions_subquery.c.schedule_id,
            invalid_regions_subquery.c.asset_id,
            invalid_regions_subquery.c.asset_type
        ],
        start_time=request.start_time,
        end_time=request.end_time
    ).filter(
        slot_duration >= request.duration
    )

    return available_slots_query


    
