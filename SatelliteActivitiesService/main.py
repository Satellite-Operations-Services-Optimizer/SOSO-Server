from rabbit_wrapper import Consumer
from config.rabbit import rabbit, ServiceQueues
from Services.handler import handle_message
import logging

logger = logging.getLogger(__name__)
def startup_event():
    consumer = Consumer(rabbit(), ServiceQueues.SAT_ACTIVITIES)
    consumer.consume_messages(callback=handle_message)

    # producer = Producer(rabbit, ServiceQueues.SCHEDULER)
    # producer.produce_messages(callback=prepare_message)

if __name__ == "__main__":
    startup_event()