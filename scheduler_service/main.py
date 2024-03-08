from rabbit_wrapper import Consumer, TopicConsumer
from app_config import rabbit, ServiceQueues
from satellite_state.stream import register_state_streaming_event_listeners
from scheduler_service.event_processing.order_processing import register_order_processor_listener
from scheduler_service.schedulers.basic_scheduler import register_request_scheduler_listener
import logging


logger = logging.getLogger(__name__)
def startup_event():
    register_state_streaming_event_listeners()
    register_order_processor_listener()
    register_request_scheduler_listener()
    rabbit().start_consuming()

if __name__ == "__main__":
    startup_event()
