from app_config import get_db_session
from sqlalchemy import text, func, column, cast, ARRAY, select, bindparam, false, literal
from typing import List, Tuple
from datetime import datetime, timedelta
from app_config.database.mapping import GroundStation, ScheduleRequest, ContactEvent, ScheduledImaging, ImageOrder
import random

def create_timeline_subquery(input_ranges: List[Tuple[datetime, datetime]]):
    session = get_db_session()
    if len(input_ranges)==0:
        time_ranges = session.query(
            literal(None).label("partition"),
            func.tsrange('infinity', 'infinity').label("time_range")
        ).filter(false()).subquery() # empty result set
    else:
        datetime_range_objects = [session.execute(select(func.tsrange(input_range[0], input_range[1]))).scalar() for input_range in input_ranges]
        time_ranges = session.query(
            literal(1).label('partition'),  # TODO:  all the same partition for now. Will test partitioning in the future
            func.unnest(datetime_range_objects).label('time_range') 
        ).subquery()
    return time_ranges


def create_dummy_imaging_event(schedule_id, satellite_id, start_time, contact_start=None):
    session = get_db_session()
    groundstation = session.query(GroundStation).first()
    # Define the range of latitude and longitude
    min_latitude = -90
    max_latitude = 90
    min_longitude = -180
    max_longitude = 180

    # Generate random latitude and longitude
    latitude = random.uniform(min_latitude, max_latitude)
    longitude = random.uniform(min_longitude, max_longitude)

    window_start = start_time - timedelta(minutes=10)
    window_end = start_time + timedelta(minutes=30)
    # Use the generated latitude and longitude in your code
    order = ImageOrder(
        schedule_id=schedule_id,
        latitude=latitude,
        longitude=longitude,
        image_type="medium",
        window_start=window_start,
        window_end=window_end,
        delivery_deadline=window_end+timedelta(minutes=10)
    )
    session.add(order)
    session.flush()

    order = session.query(ImageOrder).filter_by(id=order.id).one()
    request = ScheduleRequest(
        schedule_id=schedule_id,
        asset_id=satellite_id,
        asset_type="satellite",
        order_type="imaging",
        order_id=order.id,
        priority=1,
        window_start=order.window_start,
        window_end=order.window_end,
        duration=order.duration,
        delivery_deadline=order.delivery_deadline,
        status="scheduled"
    )
    contact = ContactEvent(
        schedule_id=schedule_id,
        asset_id=satellite_id,
        groundstation_id=groundstation.id,
        uplink_rate_mbps=groundstation.uplink_rate_mbps,
        downlink_rate_mbps=groundstation.downlink_rate_mbps,
        start_time=contact_start or (request.window_start - timedelta(minutes=10)),
        duration=timedelta(minutes=5)
    )
    session.add_all([request, contact])
    session.flush()

    imaging = ScheduledImaging(
        schedule_id=schedule_id,
        asset_id=satellite_id,
        request_id=request.id,
        start_time=start_time,
        duration=request.duration,
        window_start=start_time,
        window_end=start_time+request.duration,
        uplink_contact_id=contact.id,
        uplink_size=request.uplink_size,
        downlink_size=request.downlink_size,
        power_usage=request.power_usage,
        priority=request.priority
    )
    session.add(imaging)
    session.flush()
    return imaging