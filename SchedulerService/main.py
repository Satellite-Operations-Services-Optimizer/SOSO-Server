from rabbit_wrapper import Consumer
from config import rabbit, ServiceQueues
from tasks.satellite_state.stream import setup_state_streaming_event_listeners
import logging

logger = logging.getLogger(__name__)
def startup_event():
    setup_state_streaming_event_listeners()
    consumer = Consumer(rabbit(), ServiceQueues.SCHEDULER)
    consumer.register_callback(lambda message: logger.info(f"Received message: {message}"))

    rabbit().start_consuming()


if __name__ == "__main__":
    startup_event()
