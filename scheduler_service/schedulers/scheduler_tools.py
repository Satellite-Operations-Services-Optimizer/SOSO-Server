from datetime import datetime, timedelta
import uuid
from app_config import get_db_session
from app_config.database.mapping import Schedule, ScheduleRequest, SatelliteOutage, TransmittedEvent, ContactEvent, GroundStationOutage, StateCheckpoint, CaptureOpportunity, ImageOrder, Satellite, GroundStation, SatelliteEclipse, SatelliteStateChange, AssetState
from sqlalchemy import or_, exists
from scheduler_service.schedulers.utils import query_gaps, query_islands
from sqlalchemy import func, column, or_, and_, false, case, literal, true, union_all, union
from sqlalchemy.orm import aliased
from typing import Union, Optional
import random

# def create_schedule_population(start_time: datetime, end_time: datetime, schedule_id: int, max_population_size: int, branching_factor: int = 5):
#     """
#     Explodes the schedule `schedule_id` into a population of schedules that are feasible within the time range `start_time` to `end_time`.
#     Assumes that all static events have been populated within the provided time range `start_time` to `end_time`.

#     Returns the schedule group id of the generated population
#     """
#     population_id = f"generated_population_{uuid.uuid4().hex}"

#     # Handle all outage requests
#     session = get_db_session()
#     outage_requests = session.query(ScheduleRequest).filter(
#         ScheduleRequest.schedule_id==schedule_id,
#         or_(
#             ScheduleRequest.order_type=="sat_outage",
#             ScheduleRequest.order_type=="gs_outage"
#         ),
#         ScheduleRequest.status=="processing",
#         ScheduleRequest.window_start >= start_time,
#         ScheduleRequest.window_end <= end_time
#     ).all()

#     for outage_request in outage_requests:
#         schedule_outage(outage_request, unscheduled_requests_state="processing")

#     requests_to_schedule = session.query(ScheduleRequest).filter(
#         ScheduleRequest.schedule_id==schedule_id,
#         ScheduleRequest.status=="processing",
#         or_(
#             ScheduleRequest.order_type=="imaging",
#             ScheduleRequest.order_type=="maintenance"
#         )
#     ).order_by(ScheduleRequest.priority).all()

#     population = []
#     for request in requests_to_schedule:
#         for schedule in population:
#             # for each current schedule we have in our population, 
#             # enrich population with `branching_factor` possible new 
#             # schedules where this request is scheduled
#             request_schedules = generate_schedule_possibilities(
#                 request.id,
#                 schedule_id,
#                 lookback_cutoff_date=datetime.now+timedelta(minutes=10),
#                 branching_factor=branching_factor
#             )
#             for new_schedule in request_schedules:
#                 new_schedule.group_name = population_id


#         if len(request_schedules)==0:
#             pass
#             # change status to rejected, citing no available slots to place it
#         # available_locations = 


#     # get all requests in order of scheduling priority
#     schedule_ids = []
#     return population_id

# def generate_schedule_possibilities(request_id: int, schedule_id: int, lookback_cutoff_date: datetime, branching_factor: int):
#     """
#     Generates `branching_factor` possible schedules where `request` is scheduled.
#     """
#     session = get_db_session()
#     # verify that request exists in the schedule, and is not already scheduled
#     request_valid = session.query(exists().where(
#         ScheduleRequest.id==request_id,
#         ScheduleRequest.schedule_id==schedule_id,
#         ScheduleRequest.status!="scheduled",
#         ScheduleRequest.status!="sent_to_gs"
#     )).scalar()
#     if not request_valid:
#         raise ValueError(f"Request {request_id} is not valid for scheduling in schedule {schedule_id}. Request must exist in the schedule and not be already scheduled/sent to groundstation.")
    
#     top_plans = calculate_top_scheduling_plans(
#         request_id,
#         schedule_id,
#         lookback_cutoff_date,
#         top_n=branching_factor,
#         workload_distribution_factor=0.3
#     )

#     # get top `branching_factor` available spots in the schedule to place the request
#     for plan in top_plans:
#         schedule = copy_schedule(schedule_id)

#         # schedule the request in the spot

#         # find the corresponding request in the new schedule and update its state

def calculate_top_scheduling_plans(request_id: int, context_cutoff_time: datetime, top_n: int, workload_distribution_factor: float):
    """
    Calculates the best schedule slots to place the request in.
    """

    if workload_distribution_factor > 0: workload_distribution_factor = 1.0
    if workload_distribution_factor < 0: workload_distribution_factor = 0.0

    session = get_db_session()
    request = session.query(ScheduleRequest).filter_by(id=request_id).one()

    # Get the available slots for the satellite event to occur. start without any priority threshold, then incrementally start allowing it to displace other events of lower priority
    candidate_plans = []
    for priority_threshold in range(request.priority+1):
        unfiltered_candidate_plans = query_candidate_scheduling_plans(request_id, context_cutoff_time, priority_threshold).subquery()
        # candidate_plans = filter_out_candidate_plans_causing_invalid_state(unfiltered_candidate_plans).subquery()
        candidate_plans = unfiltered_candidate_plans # TODO: temporary, for testing purposes. we need to filter for invalid state
        if len(priority_threshold)>0: break

    punctuality_ordered_candidates = candidate_plans.limit(top_n).all() # it is already ordered by punctuality, so we can just take the top n
    asset_grouped_candidates = session.query(
        candidate_plans.c.schedule_id,
        candidate_plans.c.asset_id,
        func.array_agg(candidate_plans.c.time_range).limit(top_n).label('time_ranges'),
        func.array_agg(candidate_plans.c.uplink_contact_id).limit(top_n).label('uplink_ids'),
        func.array_agg(candidate_plans.c.downlink_contact_id).limit(top_n).label('downlink_ids')
    ).group_by(candidate_plans.c.schedule_id, candidate_plans.c.asset_id).all()


    number_of_candidates = len(punctuality_ordered_candidates) # we could possibly have less than top_n candidates
    number_of_assets = len(asset_grouped_candidates)

    top_n_candidates = []
    for _ in range(number_of_candidates):
        choose_from_asset_list = random.random() < workload_distribution_factor

        if choose_from_asset_list:
            for _ in range(number_of_assets): # keep trying to get an asset with a candidate
                asset_index = int(random.uniform(0, number_of_assets)) # randomly choose an index using uniform distribution for evenly distribted workload chances
                asset_candidates = asset_grouped_candidates[asset_index]
                if len(asset_candidates.time_ranges) == 0: # no more candidates in this asset
                    asset_grouped_candidates.pop(asset_index)
                    asset_candidates = None
            if asset_candidates == None: # should never happen because we must always have at least number_of_candidates candidates
                break
            candidate_time_range = asset_candidates.time_ranges.pop(0)
            candidate_uplink_id = asset_candidates.uplink_ids.pop(0)
            candidate_downlink_id = asset_candidates.downlink_ids.pop(0)

            chosen_candidate = session.query(
                func.literal(asset_candidates.schedule_id).label('schedule_id'),
                func.literal(asset_candidates.asset_id).label('asset_id'),
                func.literal(candidate_time_range).label('time_range'),
                func.literal(candidate_uplink_id).label('uplink_contact_id'),
                func.literal(candidate_downlink_id).label('downlink_contact_id')
            ).one()
        else:
            chosen_candidate = random.choice(punctuality_ordered_candidates).pop(0)
        
        top_n_candidates.append(chosen_candidate)
    return top_n_candidates


def query_candidate_scheduling_plans(request_id: int, context_cutoff_time: datetime, priority_threshold: int):
    session = get_db_session()
    request = session.query(ScheduleRequest).filter_by(id=request_id).one()

    # Get the available slots for the satellite event to occur
    available_time_slots_subquery = query_satellite_available_time_slots(request_id, priority_threshold).subquery()

    # Get the candidate uplink and downlink contacts for the request
    candidate_uplink_contact, candidate_downlink_contact = get_candidate_contact_queries(
        request_id, uplink_cutoff_time=context_cutoff_time,
    )
    candidate_uplink_subquery = candidate_uplink_contact.subquery()
    candidate_downlink_subquery = candidate_downlink_contact.subquery()

    uplink_required = True # request.uplink_size > 0 TODO: we should never have a case where we have to model something in our system that doesn't need uplink. we need to uplink for sat to know what to do. verify with csa
    downlink_required = request.downlink_size > 0

    uplink_time_range = func.tstzrange(candidate_uplink_subquery.c.start_time, candidate_uplink_subquery.c.start_time+candidate_uplink_subquery.c.duration)
    downlink_time_range = func.tstzrange(candidate_downlink_subquery.c.start_time, candidate_downlink_subquery.c.start_time+candidate_downlink_subquery.c.duration)
    uplink_downlink_gap = func.tstzrange(
        case(
            (candidate_uplink_subquery!=None, func.upper(uplink_time_range)),
            else_=func.lower(available_time_slots_subquery.c.time_range)
        ),
        case(
            (candidate_downlink_subquery!=None, func.lower(downlink_time_range)),
            else_=func.upper(available_time_slots_subquery.c.time_range)
        )
    )

    latest_event_start_time = func.upper(available_time_slots_subquery.c.time_range)-ScheduleRequest.duration # the latest possible time we can start the event and still be able to complete it within the available time slot
    earliest_event_end_time = func.lower(available_time_slots_subquery.c.time_range)+ScheduleRequest.duration
    event_time_range = uplink_downlink_gap*available_time_slots_subquery.c.time_range
    event_duration = func.upper(event_time_range)-func.lower(event_time_range)
    candidate_schedule_plans = session.query(
        ScheduleRequest.id.label('request_id'),
        available_time_slots_subquery.c.schedule_id,
        available_time_slots_subquery.c.asset_id.label('asset_id'),
        event_time_range.label('time_range'),
        candidate_uplink_subquery.c.id.label('uplink_contact_id'),
        candidate_downlink_subquery.c.id.label('downlink_contact_id'),
    ).select_from(
        available_time_slots_subquery
    ).join(
        ScheduleRequest,
        ScheduleRequest.id==request.id
    ).join(
        candidate_uplink_subquery,
        and_(
            available_time_slots_subquery.c.asset_id==candidate_uplink_subquery.c.asset_id,
            func.upper(uplink_time_range) < latest_event_start_time, # uplink must finish before the last possible chance to perform the event within the available time slot
        ),
        isouter=not uplink_required
    ).join(
        candidate_downlink_subquery,
        and_(
            available_time_slots_subquery.c.asset_id==candidate_downlink_subquery.c.asset_id,
            func.upper(uplink_time_range) < candidate_downlink_subquery.c.start_time,
            case(
                (candidate_uplink_subquery==None, func.lower(downlink_time_range) > earliest_event_end_time), # downlink must start after we have had a chance to perform the event
                else_= event_duration >= ScheduleRequest.duration # enough time between uplink finish and downlink start to actually perform the event
            )
        ),
        isouter=not downlink_required
    ).order_by(candidate_downlink_subquery.c.start_time, column('time_range')) #earlier to downlink, better. next in priority is earlier for event to take place, the better
    return candidate_schedule_plans

def get_candidate_contact_queries(request_id: int, uplink_cutoff_time: datetime):
    """
    Queries the schedule for available contacts to place the request.
    Looks for all contacts that are not in outage, last long enough to
    transmit what is needed, and are not already scheduled to transmit
    something else with its groundstation at that time.
    """
    session = get_db_session()
    request = session.query(ScheduleRequest).filter_by(id=request_id).one()

    if uplink_cutoff_time is None: uplink_cutoff_time = datetime.min
    uplink_end_time = request.window_end - request.duration # the uplink must finish in time for the event to be able to start and finish within the window period
    downlink_start_time = request.window_start + request.duration # the event must have finished before the downlink starts
    downlink_end_time = request.delivery_deadline

    contact_is_scheduled_to_transmit = or_(
        ContactEvent.total_uplink_size > 0,
        ContactEvent.total_downlink_size > 0
    )

    # get all contacts that we can uplink with, where the contact's groundstation is not in outage during the contact period
    gs_in_outage_for_contact_check = exists(GroundStationOutage).where(
        GroundStationOutage.schedule_id==request.schedule_id,
        GroundStationOutage.asset_id==ContactEvent.groundstation_id,
        GroundStationOutage.utc_time_range.op('&&')(ContactEvent.utc_time_range),
        or_(
            GroundStationOutage.outage_reason!="transmitting",
            # if the groundstation is in outage because it is transmitting to
            # the satellite during *this contact* period, then it is not in outage
            # for this satellite, because you can just keep on transmitting,
            # without needing to reconfigure the groundstation to transmit to another satellite
            and_( 
                # if something is scheduled to be transmitted during this contact.
                # (given we will make sure to place a groundstation outage whenever
                # something is scheduled to be transmitted during a contact, we can
                # safely assume that this contact is the only contact that is scheduled
                # to transmit from this groundstation, thus the groundstation is not in outage
                # for this contact - in fact, this is the only contact that the groundstation is available for)
                GroundStationOutage.outage_reason=="transmitting",
                ~contact_is_scheduled_to_transmit,
            ),
        )
    )
    candidate_uplink_contact = session.query(ContactEvent)
    candidate_downlink_contact = session.query(ContactEvent)

    if request.asset_id is not None:
        candidate_uplink_contact = candidate_uplink_contact.filter(ContactEvent.asset_id==request.asset_id)
        candidate_downlink_contact = candidate_downlink_contact.filter(ContactEvent.asset_id==request.asset_id)

    # Get candidate uplink and downlink contacts if the request has to be either uplinked or downlinked. otherwise, no need to get the contacts (filter by false for empty result set)
    transmission_duration = func.make_interval(0, 0, 0, 0, 0, 0, ContactEvent.total_transmission_time)
    contact_time_range = func.tstzrange(ContactEvent.start_time + transmission_duration, ContactEvent.start_time + ContactEvent.duration)
    uplink_window = func.tstzrange(uplink_cutoff_time, uplink_end_time)
    contact_uplink_overlap = contact_time_range * uplink_window
    contact_uplink_overlap_duration = func.upper(contact_uplink_overlap)-func.lower(contact_uplink_overlap)
    if request.uplink_size > 0:
        request_uplink_duration = request.uplink_size/ContactEvent.uplink_rate_mbps
        request_uplink_duration = func.make_interval(0, 0, 0, 0, 0, 0, request_uplink_duration)
        candidate_uplink_contact = candidate_uplink_contact.filter(
            ContactEvent.schedule_id==request.schedule_id,
            contact_uplink_overlap_duration >= request_uplink_duration,
            ~gs_in_outage_for_contact_check
        )
    else:
        candidate_uplink_contact = candidate_uplink_contact.filter(false()) # We don't need to uplink anything, so we don't need to consider any uplink contacts

    downlink_window = func.tstzrange(downlink_start_time, downlink_end_time)
    contact_downlink_overlap = contact_time_range * downlink_window
    contact_downlink_overlap_duration = func.upper(contact_downlink_overlap)-func.lower(contact_downlink_overlap)
    if request.downlink_size > 0:
        request_downlink_duration = request.downlink_size/ContactEvent.downlink_rate_mbps
        request_downlink_duration = func.make_interval(0, 0, 0, 0, 0, 0, request_downlink_duration)
        candidate_downlink_contact = candidate_downlink_contact.filter(
            ContactEvent.schedule_id==request.schedule_id,
            contact_downlink_overlap_duration >= request_downlink_duration,
            ~gs_in_outage_for_contact_check,
        )
    else:
        candidate_downlink_contact = candidate_downlink_contact.filter(false())

    candidate_uplink_contact = candidate_uplink_contact
    candidate_downlink_contact = candidate_downlink_contact

    return (candidate_uplink_contact, candidate_downlink_contact)

def query_satellite_available_time_slots(request_id: int, priority_threshold: Optional[int] = None):
    """
    Queries the schedule for available spots to place the request.
    """
    session = get_db_session()

    request = session.query(ScheduleRequest).filter_by(id=request_id).one()

    # Get all the invalid spots in the schedule
    blocking_transmitted_event_query = session.query(
        TransmittedEvent.schedule_id.label('schedule_id'),
        TransmittedEvent.asset_id.label('asset_id'),
        TransmittedEvent.asset_type.label('asset_type'),
        func.tstzrange(TransmittedEvent.start_time, TransmittedEvent.start_time+TransmittedEvent.duration).label('time_range')
    )
    if priority_threshold:
        blocking_transmitted_event_query = blocking_transmitted_event_query.filter(
            or_(
                TransmittedEvent.event_type=="maintenance" & request.order_type=="imaging", # imaging events are never allowed to displace maintenance events
                TransmittedEvent.priority >= priority_threshold
            )
        )
    satellite_outage_query = session.query(
        SatelliteOutage.schedule_id.label('schedule_id'),
        SatelliteOutage.asset_id.label('asset_id'),
        SatelliteOutage.asset_type.label('asset_type'),
        func.tstzrange(SatelliteOutage.start_time, SatelliteOutage.start_time+SatelliteOutage.duration).label('time_range')
    )
    if request.asset_id is not None:
        blocking_transmitted_event_query = blocking_transmitted_event_query.filter(TransmittedEvent.asset_id==request.asset_id)
        satellite_outage_query = satellite_outage_query.filter(SatelliteOutage.asset_id==request.asset_id)
    

    blocking_events_queries = [blocking_transmitted_event_query, satellite_outage_query]

    valid_partition_values_subquery = session.query(
        literal(request.schedule_id).label('schedule_id'),
        Satellite.id.label('asset_id'),
        Satellite.asset_type.label('asset_type')
    ).filter(
        Satellite.id==request.asset_id if request.asset_id is not None else true()
    ).subquery()

    # Handle imaging opportunities if the request is for imaging - get all areas that are not available for imaging
    if request.order_type == "imaging":
        candidate_capture_opportunities = query_candidate_capture_opportunities(request_id).subquery()
        unimageable_time_ranges_query = query_gaps(
            source_subquery=candidate_capture_opportunities,
            range_column=candidate_capture_opportunities.c.time_range,
            partition_columns=[
                candidate_capture_opportunities.c.schedule_id.label('schedule_id'),
                candidate_capture_opportunities.c.asset_id.label('asset_id'),
                candidate_capture_opportunities.c.asset_type.label('asset_type')
            ],
            start_time=request.window_start,
            end_time=request.window_end,
            valid_partition_values_subquery=valid_partition_values_subquery
        )
        blocking_events_queries.append(unimageable_time_ranges_query)
    
    blocking_events_subquery = union(*blocking_events_queries).subquery()

    event_blocked_regions_query = session.query(
        blocking_events_subquery
    ).filter(
        blocking_events_subquery.c.schedule_id==request.schedule_id,
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
        end_time=request.window_end,
        valid_partition_values_subquery=valid_partition_values_subquery
    ).filter(
        slot_duration >= request.duration
    )

    return available_slots_query

def filter_out_candidate_plans_causing_invalid_state(request_id, schedule_id, candidates_subquery):
    """
    Take all possible schedule plan candidates and filter out the ones that cause an invalid state when they are actually performed.
    """
    session = get_db_session()
    # check that from event start to downlink end, the storage usage is low enough to fit the downlink size
    # check that if there is an eclipse that overlaps with uplink/downlink/event, energy usage from max(eclipse_start, event/contact start) to eclipse end remains low enough to be able to fit the power usage required by the overlapping event/contact
    uplink_event = aliased(ContactEvent)
    downlink_event = aliased(ContactEvent)

    # We pre-compute the state timeline by making it a subquery, so it can be reused, since it is not a corollated subquery - it is not dependent on the candidate schedule plan query
    # NOTE: There is a significant trade-off here though. We do not know exactly what time range we want states for,
    # so we use (request.start_time, request.delivery_deadline) as an estimated time range.
    # This is a trade-off because we could use the actual time range from the candidate schedule plan, 
    # to know exactly what time ranges we need the state for, but if we do that, the query would then be dependent
    # on the candidate schedule plan query, meaning that the satellite state timeline (an expensive query) will be 
    # re-computed for every candidate schedule plan (and it is possible to have a lot of candidate plans)

    # Why is our estimate of the time range (request.start_time, request.delivery_deadline) a reasonable estimate?
    # well, because for now, we are only interested in storage and power capacity, and we need to make sure storage is valid from
    # the time the event occurs that increases storage, until the downlink is complete and storage for event payload is released.
    # The earliest possible time the event can occur is at request.start_time, and the latest possible time the downlink can end is at request.delivery_deadline.
    # For the power constraint, we only care about the power usage from the time the event occurs that increases energy usage, and the earliest possible time that
    # can happen is at request.start_time. For the end time, delivery_deadline is a less reliable, but still reasonable estimate, as if an eclipse spans the period from when
    # the request is being performed to past when the delivery deadline is, then we need to make sure we have enough power to sustain the event until the eclipse ends, but we don't.
    # We only consider till the delivery deadline. This is a good enough estimate for now though.
    request = session.query(ScheduleRequest).filter_by(id=request_id).one()

    state_window_start = request.start_time
    state_window_end = request.delivery_deadline
    overflowing_eclipse_end = session.query(
        func.max(SatelliteEclipse.start_time+SatelliteEclipse.duration)
    ).filter(
        SatelliteEclipse.asset_id==candidates_subquery.c.asset_id,
        SatelliteEclipse.asset_type==candidates_subquery.c.asset_type,
        func.tstzrange(SatelliteEclipse.start_time, SatelliteEclipse.start_time+SatelliteEclipse.duration).op('&&')(state_window_end),
        SatelliteEclipse.start_time + SatelliteEclipse.duration > state_window_end
    ).first()
    state_window_end = state_window_end if overflowing_eclipse_end is None else overflowing_eclipse_end

    state_timeline_subquery = query_state_timeline(
        request_id,
        schedule_id,
        start_time=state_window_start,
        end_time=state_window_end
    )

    eclipse_time_range = func.tstzrange(SatelliteEclipse.start_time, SatelliteEclipse.start_time+SatelliteEclipse.duration)
    event_eclipse_overlap = eclipse_time_range * candidates_subquery.c.time_range
    overlap_duration = func.upper(event_eclipse_overlap)-func.lower(event_eclipse_overlap)
    energy_used_for_request = ScheduleRequest.power_usage*overlap_duration
    valid_candidate_plans = session.query(
        candidates_subquery
    ).join(
        ScheduleRequest,
        ScheduleRequest.id==candidates_subquery.request_id
    # ).join(
    #     uplink_event,
    #     candidates_subquery.uplink_contact_id == uplink_event.id
    ).join(
        downlink_event,
        candidates_subquery.downlink_contact_id == downlink_event.id
    ).join(
        Satellite,
        Satellite.id==candidates_subquery.asset_id
    ).filter(
        ~exists(state_timeline_subquery).where( # storage constraint
            state_timeline_subquery.schedule_id==candidates_subquery.schedule_id,
            state_timeline_subquery.asset_id==candidates_subquery.asset_id,
            state_timeline_subquery.asset_type==candidates_subquery.asset_type,
            and_( # condition in which storage is exceeded
                state_timeline_subquery.c.snapshot_time >= func.lower(candidates_subquery.c.time_range), # From the time the event occurs that increases storage
                state_timeline_subquery.c.snapshot_time <= func.upper(downlink_event.start_time+downlink_event.duration), # until the downlink is complete and storage for event payload is released
                state_timeline_subquery.c.state.storage + ScheduleRequest.downlink_size > Satellite.storage_capacity
            )
        ),
        ~exists(SatelliteEclipse).where( # power constraint - make sure that for all eclipses that overlap with this event, from the overlap start to the eclipse end, there is enough power to sustain the event
            SatelliteEclipse.asset_id==candidates_subquery.asset_id,
            SatelliteEclipse.asset_type==candidates_subquery.asset_type,
            eclipse_time_range.op('&&')(candidates_subquery.c.time_range), # TODO: we are currently considering the event, and not data transmission during contacts, as the only thing that take power
            exists(state_timeline_subquery).where( # condition in which battery capacity is exceeded
                state_timeline_subquery.schedule_id==candidates_subquery.schedule_id,
                state_timeline_subquery.asset_id==candidates_subquery.asset_id,
                state_timeline_subquery.asset_type==candidates_subquery.asset_type,
                state_timeline_subquery.c.snapshot_time >= func.greatest(func.lower(eclipse_time_range), func.lower(candidates_subquery.c.time_range)), # From the time the event occurs that increases energy usage (or from the start of the eclipse if the event starts before the eclipse)
                state_timeline_subquery.c.snapshot_time <= func.upper(eclipse_time_range), # until the eclipse ends (sunlight is available again)
                state_timeline_subquery.c.state.energy_usage + energy_used_for_request > Satellite.battery_capacity_wh*3600, # convert to watt-seconds. Explanation: energy usage must never increase beyond what is needed to perform this event until the sunlight is available again
                state_timeline_subquery.c.power_draw + ScheduleRequest.power_usage > Satellite.power_capacity
            )
        )
    )
    return valid_candidate_plans



def query_state_timeline(request_id: int, schedule_id: int, start_time: Union[datetime, column], end_time: Union[datetime, column]):
    """
    query the state timeline
    """
    session = get_db_session()
    request = session.query(ScheduleRequest).filter_by(id=request_id).one()

    checkpoint_state = session.query(
        StateCheckpoint.schedule_id,
        StateCheckpoint.asset_id,
        StateCheckpoint.asset_type,
        func.max(StateCheckpoint.checkpoint_time).over(
            partition_by=[
                StateCheckpoint.schedule_id,
                StateCheckpoint.asset_id,
                StateCheckpoint.asset_type
            ],
            order_by=StateCheckpoint.checkpoint_time
        )
    ).filter(
        StateCheckpoint.schedule_id==schedule_id,
        StateCheckpoint.checkpoint_time <= start_time
    ).subquery()

    state_changes = session.query(SatelliteStateChange).subquery()
    state_timeline = session.query(
        state_changes.c.schedule_id,
        state_changes.c.asset_id,
        state_changes.c.asset_type,
        state_changes.c.snapshot_time,
        checkpoint_state.c.state + func.sum(
            SatelliteStateChange.delta
        ).over(
            partition_by=[
                state_changes.c.schedule_id,
                state_changes.c.asset_id,
                state_changes.c.asset_type
            ],
            order_by=state_changes.c.snapshot_time,
            rows=(None, 0)
        ).label('state')
    ).join(
        checkpoint_state,
        and_(
            checkpoint_state.c.schedule_id==state_changes.c.schedule_id,
            checkpoint_state.c.asset_id==state_changes.c.asset_id,
            checkpoint_state.c.asset_type==state_changes.c.asset_type
        )
    ).filter(
        state_changes.c.schedule_id==schedule_id,
        state_changes.c.asset_id==request.asset_id if request.asset_id is not None else true(),
        state_changes.c.snapshot_time > checkpoint_state.c.checkpoint_time,
        state_changes.c.snapshot_time <= end_time
    )
    return state_timeline



def query_candidate_capture_opportunities(request_id: int):
    """
    Queries the schedule for available capture opportunities when the imaging can take place
    """
    session = get_db_session()
    request = session.query(ScheduleRequest).filter_by(id=request_id).one()

    capture_time_range = func.tstzrange(CaptureOpportunity.start_time, CaptureOpportunity.start_time+CaptureOpportunity.duration).label('time_range')
    capture_window = capture_time_range.op('*')(func.tstzrange(request.window_start, request.window_end))
    candidate_capture_opportunities = session.query(
        literal(request.schedule_id).label('schedule_id'),
        CaptureOpportunity.asset_id.label('asset_id'),
        CaptureOpportunity.asset_type.label('asset_type'),
        capture_window.label('time_range')
    ).join(
        ImageOrder,
        and_(
            ImageOrder.id==request.order_id,
            request.order_type=="imaging"
        )
    ).filter(
        CaptureOpportunity.schedule_id==request.schedule_id, # TODO: should we remove this from consideration? will CaptureOpportunities be copied over when we copy schedules? I think yes, but not 100% sure yet
        CaptureOpportunity.latitude==ImageOrder.latitude,
        CaptureOpportunity.longitude==ImageOrder.longitude,
        CaptureOpportunity.image_type==ImageOrder.image_type,
        (func.upper(capture_window)-func.lower(capture_window)) >= request.duration # make sure the capture opportunity is long enough to capture the image
    )
    if request.asset_id is not None:
        candidate_capture_opportunities = candidate_capture_opportunities.filter(CaptureOpportunity.asset_id==request.asset_id)
    return candidate_capture_opportunities


def asset_state_changes_query(events_subquery=None):
    session = get_db_session()
    if events_subquery is None:
        events_subquery = session.query(TransmittedEvent).subquery()
    
    uplink_start = session.query(
        events_subquery.c.schedule_id,
        events_subquery.c.asset_id,
        events_subquery.c.asset_type,
        ContactEvent.start_time.label('snapshot_time'),
        AssetState(
            storage=events_subquery.uplink_size,
            storage_util=0.0,
            throughput=0.0,
            energy_usage=0.0,
            power_draw=0.0
        ).label('delta'),
    ).join(
        ContactEvent,
        events_subquery.c.uplink_contact_id == ContactEvent.id
    )

    event_start = session.query(
        events_subquery.c.schedule_id,
        events_subquery.c.asset_id,
        events_subquery.c.asset_type,
        events_subquery.c.start_time.label('snapshot_time'),
        AssetState(
            storage=events_subquery.c.downlink_size - events_subquery.c.uplink_size, # the command data that was uplinked can now be deleted as the command has been executed. The result of executing the command may now takes up space
            storage_util=0.0,
            throughput=events_subquery.c.priority,
            energy_usage=0.0,
            power_draw=0.0
        ).label('delta'),
    )

    downlink_start = session.query(
        events_subquery.c.schedule_id,
        events_subquery.c.asset_id,
        events_subquery.c.asset_type,
        ContactEvent.start_time.label('snapshot_time'),
        AssetState(
            storage=-1*events_subquery.c.downlink_size,
            storage_util=0.0,
            throughput=0.0,
            energy_usage=0.0,
            power_draw=0.0
        ).label('delta'),
    ).join(
        ContactEvent,
        events_subquery.c.downlink_contact_id == ContactEvent.id
    )

    event_eclipse_overlap = events_subquery.c.utc_time_range * func.max(SatelliteEclipse.utc_time_range) # we group eclipses that start at same time (should never happen unless eclipses are copied into new schedule. they never overlap in time in reality)
    event_eclipse_overlap_duration = func.upper(event_eclipse_overlap)-func.lower(event_eclipse_overlap)
    energy_usage = events_subquery.c.power_usage * func.extract('epoch', event_eclipse_overlap_duration)
    event_start_in_eclipse = session.query(
        events_subquery.c.schedule_id,
        events_subquery.c.asset_id,
        events_subquery.c.asset_type,
        func.greatest(SatelliteEclipse.start_time, events_subquery.c.start_time).label('snapshot_time'),
        AssetState(
            storage=0.0,
            storage_util=0.0,
            throughput=0.0,
            energy_usage=energy_usage,
            power_draw=events_subquery.c.power_usage
        ).label('delta'),
    ).join(
        SatelliteEclipse,
        and_(
            SatelliteEclipse.asset_id == events_subquery.c.asset_id,
            SatelliteEclipse.asset_type == events_subquery.c.asset_type,
            SatelliteEclipse.utc_time_range.op('&&')(events_subquery.c.utc_time_range)
        )
    ).group_by(
        events_subquery.c.schedule_id,
        events_subquery.c.asset_id,
        events_subquery.c.asset_type,
        SatelliteEclipse.start_time,
        SatelliteEclipse.duration
    )

    event_end_in_eclipse = session.query(
        events_subquery.c.schedule_id,
        events_subquery.c.asset_id,
        events_subquery.c.asset_type,
        func.least(SatelliteEclipse.start_time+SatelliteEclipse.duration, events_subquery.c.start_time+events_subquery.c.duration).label('snapshot_time'),
        AssetState(
            storage=0.0,
            storage_util=0.0,
            throughput=0.0,
            energy_usage=0.0,
            power_draw=-1*events_subquery.c.power_usage
        ).label('delta'),
    ).join(
        SatelliteEclipse,
        and_(
            SatelliteEclipse.asset_id == events_subquery.c.asset_id,
            SatelliteEclipse.asset_type == events_subquery.c.asset_type,
            SatelliteEclipse.utc_time_range.op('&&')(events_subquery.c.utc_time_range)
        )
    ).group_by(
        events_subquery.c.schedule_id,
        events_subquery.c.asset_id,
        events_subquery.c.asset_type,
        SatelliteEclipse.start_time,
        SatelliteEclipse.duration
    )

    eclipse_end = session.query(
        events_subquery.c.schedule_id,
        events_subquery.c.asset_id,
        events_subquery.c.asset_type,
        func.max(SatelliteEclipse.start_time+SatelliteEclipse.duration).label('snapshot_time'),
        AssetState(
            storage=0.0,
            storage_util=0.0,
            throughput=0.0,
            energy_usage=-1*func.sum(energy_usage),
            power_draw=0.0
        ).label('delta'),
    ).join(
        SatelliteEclipse,
        and_(
            SatelliteEclipse.asset_id == events_subquery.c.asset_id,
            SatelliteEclipse.asset_type == events_subquery.c.asset_type,
            SatelliteEclipse.utc_time_range.op('&&')(events_subquery.c.utc_time_range)
        )
    ).group_by(
        events_subquery.c.schedule_id,
        events_subquery.c.asset_id,
        events_subquery.c.asset_type,
        SatelliteEclipse.start_time,
        SatelliteEclipse.duration
    )

    eventwise_state_changes = union_all(
        uplink_start,
        event_start,
        downlink_start,
        event_start_in_eclipse,
        event_end_in_eclipse,
        eclipse_end
    ).subquery()

    state_changes = session.query(
        eventwise_state_changes.c.schedule_id,
        eventwise_state_changes.c.asset_id,
        eventwise_state_changes.c.asset_type,
        eventwise_state_changes.c.snapshot_time,
        AssetState(
            func.sum(eventwise_state_changes.c.delta.storage),
            func.sum(eventwise_state_changes.c.delta.storage) / Satellite.storage_capacity,
            func.sum(eventwise_state_changes.c.delta.throughput),
            func.sum(eventwise_state_changes.c.delta.energy_usage),
            func.sum(eventwise_state_changes.c.delta.power_draw)
        ).label('delta')
    ).group_by(
        eventwise_state_changes.c.schedule_id,
        eventwise_state_changes.c.asset_id,
        eventwise_state_changes.c.asset_type,
        eventwise_state_changes.c.snapshot_time
    )

    return state_changes
    
