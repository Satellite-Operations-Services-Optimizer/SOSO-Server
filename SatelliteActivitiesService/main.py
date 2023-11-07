from rabbit_wrapper import Consumer
from config.rabbit import rabbit, ServiceQueues
from services.handler import handle_message
import logging

logger = logging.getLogger(__name__)
def startup_event():
    consumer = Consumer(rabbit, ServiceQueues.SAT_ACTIVITIES)
    consumer.consume_messages(callback=handle_message)


if __name__ == "__main__":
    startup_event()
