from rabbit_wrapper import Consumer
from app_config import rabbit, ServiceQueues
from satellite_state.stream import setup_state_streaming_event_listeners
import logging
from fixed_event_processing.background_jobs import scheduler


logger = logging.getLogger(__name__)
def startup_event():
    setup_state_streaming_event_listeners()
    consumer = Consumer(rabbit(), ServiceQueues.SCHEDULER)
    consumer.register_callback(lambda message: logger.info(f"Received message: {message}"))

    rabbit().start_consuming()

scheduler.start()

if __name__ == "__main__":
    startup_event()
