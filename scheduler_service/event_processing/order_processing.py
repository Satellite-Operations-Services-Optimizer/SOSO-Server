from datetime import datetime
from app_config import get_db_session, rabbit, logging
from app_config.database.mapping import SystemOrder, ScheduleRequest, ImageOrder, MaintenanceOrder, OutageOrder
from scheduler_service.schedulers.utils import TimeHorizon
from typing import Optional
from sqlalchemy import exists
from multiprocessing import Process
from rabbit_wrapper import TopicConsumer, TopicPublisher


logger = logging.getLogger(__name__)
def register_order_processing_listener():
    consumer = TopicConsumer(rabbit(), "order.*.created")
    consumer.register_callback(lambda _: ensure_order_processor_running())

order_processor = None
def ensure_order_processor_running():
    global order_processor
    if order_processor is None or not order_processor.is_alive():
        order_processor = Process(target=order_processing_task)
        order_processor.start()
        logger.info("Order processor started.")

def order_processing_task():
    while process_earliest_order():
        pass
    logger.info("No more orders to process. Exiting order processor.")
def process_earliest_order():
    session = get_db_session()
    order = session.query(SystemOrder).filter(
        SystemOrder.visit_counter < SystemOrder.number_of_visits
    ).order_by(SystemOrder.window_start).first()
    if order is None: return False
    
    if order.order_type == "imaging":
        order_table = ImageOrder
    elif order.order_type == "maintenance":
        order_table = MaintenanceOrder
    elif order.order_type == "outage":
        order_table = OutageOrder
    
    order = session.query(order_table).filter_by(id=order.id).with_for_update().first()
    if order.visit_counter == order.number_of_visits: return True # has been processed by another process

    create_request(order)
    order.visit_counter += 1
    session.commit()
    return True

def ensure_orders_requested(start_time: Optional[datetime] = None, end_time: Optional[datetime] = None):
    """
    Ensure that all orders that are requested within the time range are in the database.
    """
    session = get_db_session()

    start_time = start_time or datetime.min
    end_time = end_time or datetime.max
    time_range = TimeHorizon(start_time, end_time, include_overlap=True)
    orders = session.query(SystemOrder).filter(
        *time_range.apply_filters(SystemOrder.window_start, SystemOrder.window_end)
    ).all()

    requests = []
    while order.visit_counter < order.number_of_visits:
        for order in orders:
            if order.visit_counter==order.number_of_visits: continue
            order_already_requested = session.query(exists(ScheduleRequest).where(
                ScheduleRequest.schedule_id==order.schedule_id,
                ScheduleRequest.order_id==order.id,
                ScheduleRequest.order_type==order.order_type,
                ScheduleRequest.window_start==order.start_time
            )).scalar()

            if not order_already_requested:
                requests.append(create_request(order))
            order.visit_counter += 1

    session.add_all(requests)
    session.commit()

def create_request(order):
    if order.order_type=="imaging":
        order_table = ImageOrder
    elif order.order_type=="maintenance":
        order_table = MaintenanceOrder
    elif order.order_type=="outage":
        order_table = OutageOrder
    else:
        raise Exception(f"Order with id `{order.id}` has an invalid system order type `{order.order_type}`.")
    
    if order.visit_counter == order.number_of_visits:
        return None

    session = get_db_session()
    # ensure that the order is in its concrete type, not as a polymorphic type
    order = session.query(order_table).filter_by(id=order.id).first()
    time_offset = order.revisit_frequency * order.visit_counter
    request = ScheduleRequest(
        schedule_id=order.schedule_id,
        order_id=order.id,
        order_type=order.order_type,
        asset_id=order.asset_id,
        asset_type=order.asset_type,
        window_start=order.window_start + time_offset,
        window_end=order.window_end + time_offset,
        duration=order.duration,
        delivery_deadline=order.delivery_deadline + time_offset,
        priority=order.priority
    )
    if order.order_type=="imaging" or order.order_type=="maintenance":
        request.uplink_size = order.uplink_size,
        request.downlink_size=order.downlink_size,
        request.power_usage=order.power_usage,

    session.add(request)
    session.commit()

    # publish request created
    TopicPublisher(rabbit(), f"schedule.request.{order.order_type}.created").publish_message(request.id)
    return request
