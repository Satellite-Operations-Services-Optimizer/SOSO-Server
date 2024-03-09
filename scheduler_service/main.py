from app_config import rabbit, logging
from scheduler_service.satellite_state.stream import register_state_streaming_listeners
from scheduler_service.event_processing.order_processing import register_order_processing_listener
from scheduler_service.schedulers.basic_scheduler import register_request_scheduler_listener


logger = logging.getLogger(__name__)
def startup_event():
    register_state_streaming_listeners()
    register_order_processing_listener()
    register_request_scheduler_listener()
    rabbit().start_consuming()

if __name__ == "__main__":
    startup_event()
