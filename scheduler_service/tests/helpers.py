from app_config import get_db_session
from sqlalchemy import text, func, column, cast, ARRAY, select, bindparam, false
from sqlalchemy.dialects.postgresql import TSRANGE
from sqlalchemy.sql.expression import literal_column
from typing import List, Tuple
from datetime import datetime, timedelta
from app_config.database.mapping import GroundStation, ScheduleRequest, ContactEvent, ScheduledImaging

def create_timeline_subquery(input_ranges: List[Tuple[datetime, datetime]]):
    session = get_db_session()
    if len(input_ranges)==0:
        time_ranges = session.query(
            literal_column("NULL").label("partition"),
            func.tsrange('infinity', 'infinity').label("time_range")
        ).filter(false()).subquery() # empty result set
    else:
        datetime_range_objects = [session.execute(select(func.tsrange(input_range[0], input_range[1]))).scalar() for input_range in input_ranges]
        time_ranges = session.query(
            literal_column('1').label('partition'),  # TODO:  all the same partition for now. Will test partitioning in the future
            func.unnest(datetime_range_objects).label('time_range') 
        ).subquery()
    return time_ranges


def create_dummy_imaging_event(schedule_id, satellite_id, start_time, duration):
    session = get_db_session()
    groundstation = session.query(GroundStation).first()
    request = ScheduleRequest(
        schedule_id=schedule_id,
        asset_id=satellite_id,
        asset_type="satellite",
        order_type="imaging",
        priority=1,
        window_start=start_time,
        window_end=start_time+duration,
        duration=duration,
        delivery_deadline=start_time+duration,
        status="scheduled"
    )
    contact = ContactEvent(
        schedule_id=schedule_id,
        asset_id=satellite_id,
        groundstation_id=groundstation.id,
        start_time=request.window_start - timedelta(minutes=10),
        duration=timedelta(minutes=5)
    )
    session.add_all([request, contact])
    session.flush()

    imaging = ScheduledImaging(
        schedule_id=schedule_id,
        asset_id=satellite_id,
        request_id=request.id,
        start_time=start_time,
        duration=duration,
        window_start=start_time,
        window_end=start_time+duration,
        uplink_contact_id=contact.id,
        uplink_size=request.uplink_size,
        downlink_size=request.downlink_size,
        priority=request.priority
    )
    session.add(imaging)
    session.flush()
    return imaging