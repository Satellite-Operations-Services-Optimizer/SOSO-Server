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
import os

logger = logging.getLogger(__name__)

def startup_event():
    register_state_streaming_listeners()
    register_order_processing_listener()
    # Order processor runs whenever an order is created. make sure we process all orders that came in before we started listening for the order created event
    ensure_order_processor_running() 
    register_request_scheduler_listener()

    # os.system(f"sleep 10; python {os.path.dirname(__file__)}/restart_interrupted_requests.py")
    rabbit().start_consuming()




if __name__ == "__main__":
    startup_event()