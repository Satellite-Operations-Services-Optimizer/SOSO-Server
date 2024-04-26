from multiprocessing import Process
from app_config import rabbit, logging, get_db_session, create_rabbit
from scheduler_service.satellite_state.stream import register_state_streaming_listeners
from scheduler_service.event_processing.order_processing import register_order_processing_listener
from scheduler_service.schedulers.basic_scheduler import register_request_scheduler_listener
from scheduler_service.event_processing.order_processing import ensure_order_processor_running
import time
import threading
from app_config.database.mapping import ScheduleRequest
from rabbit_wrapper import TopicPublisher
from sqlalchemy import or_
import threading

def restart_interrupted_requests():
    session = get_db_session()
    # if there were orders we never finished processing, reset them
    interrupted_requests = session.query(ScheduleRequest).filter(
        or_(
            ScheduleRequest.status=="processing",
            ScheduleRequest.status=="received"
        )
    ).all()
    for request in interrupted_requests:
        request.status = "received"
        TopicPublisher(create_rabbit(), f"schedule.request.{request.order_type}.created").publish_message(request.id)
        session.commit()

if __name__ == "__main__":
    restart_interrupted_requests()