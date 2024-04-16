from datetime import datetime
from app_config import get_db_session, rabbit, logging
from app_config.database.mapping import SystemOrder, ScheduleRequest, ImageOrder, MaintenanceOrder, SatelliteOutageOrder, GroundStationOutageOrder
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
        SystemOrder.visits_remaining > 0
    ).order_by(SystemOrder.start_time).first()
    if order is None: return False
    
    if order.order_type == "imaging":
        order_table = ImageOrder
    elif order.order_type == "maintenance":
        order_table = MaintenanceOrder
    elif order.order_type == "sat_outage":
        order_table = SatelliteOutageOrder
    elif order.order_type == "gs_outage":
        order_table = GroundStationOutageOrder
    
    order = session.query(order_table).filter_by(id=order.id).with_for_update().first()
    if order.visits_remaining == 0: return True # has been processed by another process

    create_request(order)
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
    elif order.order_type=="gs_outage":
        order_class = GroundStationOutageOrder
    elif order.order_type=="sat_outage":
        order_class = SatelliteOutageOrder
    else:
        raise Exception(f"Order with id `{order.id}` has an invalid system order type `{order.order_type}`.")
    
    if order.visits_remaining == 0:
        return None

    session = get_db_session()
    # ensure that the order is in its concrete type, not as a polymorphic type
    order = session.query(order_class).filter_by(id=order.id).first()
    request = ScheduleRequest(
        schedule_id=order.schedule_id,
        order_id=order.id,
        order_type=order.order_type,
        asset_id=order.asset_id,
        asset_type=order.asset_type,
        window_start=order.start_time,
        window_end=order.end_time,
        duration=order.duration,
        delivery_deadline=order.delivery_deadline,
        priority=order.priority
    )
    if order.order_type=="imaging" or order.order_type=="maintenance":
        request.uplink_size = order.uplink_size,
        request.downlink_size=order.downlink_size,
        request.power_usage=order.power_usage,

    session.add(request)

    order.start_time += order.revisit_frequency
    order.end_time += order.revisit_frequency
    order.delivery_deadline += order.revisit_frequency
    order.visits_remaining -= 1
    session.commit()

    # publish request created
    TopicPublisher(rabbit(), f"schedule.request.{order.order_type}.created").publish_message(request.id)
    return request
