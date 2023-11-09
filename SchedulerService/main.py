from rabbit_wrapper import Consumer, Producer
from configimport rabbit, ServiceQueues
from services.handler import handle_message
import logging


logger = logging.getLogger(__name__)
def startup_event():
    logger.debug("hello")
    consumer = Consumer(rabbit, ServiceQueues.SCHEDULER)
    consumer.consume_messages(callback=handle_message) # replace handle_message with whatever function you want to call whenever a message is received.

    producer = Producer(rabbit, ServiceQueues.RELAY_API)
    producer.publish_message()


if __name__ == "__main__":
    startup_event()
