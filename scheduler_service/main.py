from multiprocessing import Process
from app_config import rabbit, logging
from scheduler_service.satellite_state.stream import register_state_streaming_listeners
from scheduler_service.event_processing.order_processing import register_order_processing_listener
from scheduler_service.schedulers.basic_scheduler import register_request_scheduler_listener
from scheduler_service.event_processing.order_processing import process_earliest_order
import time

logger = logging.getLogger(__name__)

def process_orders():
    while True:
        process_earliest_order()
        time.sleep(0) #yield to other processes

def startup_event():
    register_state_streaming_listeners()
    register_order_processing_listener()
    register_request_scheduler_listener()

    # # Run the process_earliest_order task in a separate process, in a while true loop
    # process = Process(target=process_orders)
    # process.start()

    rabbit().start_consuming()

if __name__ == "__main__":
    startup_event()