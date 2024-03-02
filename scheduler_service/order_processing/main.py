from datetime import datetime
from app_config import get_db_session
from app_config.database.mapping import SystemOrder, ScheduleRequest, ImageOrder, MaintenanceOrder, OutageOrder
from scheduler_service.schedulers.utils import TimeHorizon
from typing import Optional
from sqlalchemy import exists

def ensure_orders_requested(start_time: Optional[datetime] = None, end_time: Optional[datetime] = None):
    """
    Ensure that all orders that are requested within the time range are in the database.
    """
    session = get_db_session()

    start_time = start_time or datetime.min
    end_time = end_time or datetime.max
    time_range = TimeHorizon(start_time, end_time, include_overlap=True)
    orders = session.query(SystemOrder).filter(
        *time_range.apply_filters(SystemOrder.start_time, SystemOrder.end_time)
    ).all()

    requests = []
    orders_all_requested = False
    while not orders_all_requested:
        orders_all_requested = True
        for order in orders:
            if order.visits_remaining==0: continue
            order_already_requested = session.query(exists(ScheduleRequest).where(
                ScheduleRequest.schedule_id==order.schedule_id,
                ScheduleRequest.order_id==order.id,
                ScheduleRequest.order_type==order.order_type,
                ScheduleRequest.window_start==order.start_time
            )).scalar()

            if not order_already_requested:
                requests.append(create_request(order))
            order.start_time += order.revisit_frequency
            order.end_time += order.revisit_frequency
            order.delivery_deadline += order.revisit_frequency
            order.visits_remaining -= 1

            end_time_tz = end_time.replace(tzinfo=order.end_time.tzinfo)  # Add timezone information to be able to compare
            orders_all_requested = orders_all_requested and order.start_time > end_time_tz
    session.add_all(requests)
    session.commit()

def create_request(order):
    if order.order_type=="imaging":
        order_class = ImageOrder
    elif order.order_type=="maintenance":
        order_class = MaintenanceOrder
    else:
        order_class = OutageOrder

    session = get_db_session()
    # ensure that the order is in its concrete type, not as a polymorphic type
    order = session.query(order_class).filter_by(id=order.id).first()
    if order.order_type=="imaging" or order.order_type=="maintenance":
        return ScheduleRequest(
            schedule_id=order.schedule_id,
            order_id=order.id,
            order_type=order.order_type,
            window_start=order.start_time,
            window_end=order.end_time,
            duration=order.duration,
            uplink_size=order.uplink_size,
            downlink_size=order.downlink_size,
            power_usage=order.power_usage,
            delivery_deadline=order.delivery_deadline,
            priority=order.priority
        )
    elif order.order_type=="outage":
        return ScheduleRequest(
            schedule_id=order.schedule_id,
            order_id=order.id,
            order_type=order.order_type,
            window_start=order.start_time,
            window_end=order.end_time,
            duration=order.duration,
            uplink_size=0,
            downlink_size=0,
            delivery_deadline=order.delivery_deadline,
            priority=order.priority
        )
    else:
        raise Exception(f"Order with id `{order.id}` has an invalid system order type `{order.order_type}`.")
