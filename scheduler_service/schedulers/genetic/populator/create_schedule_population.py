from datetime import datetime
import uuid
from app_config import get_db_session
from app_config.database.mapping import Schedule, ScheduleRequest, SatelliteOutage, TransmittedEvent, ContactEvent, GroundStationOutage
from sqlalchemy import or_, exists
from scheduler_service.schedulers.outage_scheduler import schedule_outage

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
            request_schedules = generate_schedule_possibilities(request, schedule_id, branching_factor)
            for new_schedule in request_schedules:
                new_schedule.group_name = population_id


        if len(request_schedules)==0:
            # change status to rejected, citing no available slots to place it
        available_locations = 


    # get all requests in order of scheduling priority
    schedule_ids = []
    return population_group

def generate_schedule_possibilities(request: ScheduleRequest, schedule_id: int, branching_factor: int):
    """
    Generates `branching_factor` possible schedules where `request` is scheduled.
    """
    session = get_db_session()
    # verify that request exists in the schedule, and is not already scheduled
    request_valid = session.query(exists().where(
        ScheduleRequest.id==request.id, 
        ScheduleRequest.schedule_id==schedule_id,
        ScheduleRequest.status!="scheduled",
        ScheduleRequest.status!="sent_to_gs"
    )).scalar()
    if not request_valid:
        raise ValueError(f"Request {request.id} is not valid for scheduling in schedule {schedule_id}. Request must exist in the schedule and not be already scheduled/sent to groundstation.")
    
    # get top `branching_factor` available spots in the schedule to place the request
    available_spots = query_available_schedule_slots(request, schedule_id).limit(branching_factor).all()

    for spot in available_spots:
        schedule = copy_schedule(schedule_id)

        # schedule the request in the spot

        # find the corresponding request in the new schedule

def query_available_schedule_slots(request: ScheduleRequest, schedule_id: int):
    """
    Queries the schedule for available spots to place the request.
    """
    session = get_db_session()
    # Get all the invalid spots in the schedule

    event_blocked_regions_query = session.query(TransmittedEvent).filter(
        TransmittedEvent.schedule_id==schedule_id,
        TransmittedEvent.utc_time_range.overlaps(request.utc_window_time_range),
    )
    
    if request.asset_id is not None:
        event_blocked_regions_query = event_blocked_regions_query.filter(TransmittedEvent.asset_id == request.asset_id)
    
    invalid_state_regions_query = session.query
