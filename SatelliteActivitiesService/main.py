from rabbit_wrapper import Consumer
from config.rabbit import rabbit, ServiceQueues
from services.handler import handle_activity_request
import logging

logger = logging.getLogger(__name__)
def startup_event():
    consumer = Consumer(rabbit(), ServiceQueues.SAT_ACTIVITIES)
    consumer.register_callback(callback=handle_activity_request) # replace handle_message with whatever function you want to call whenever a message is received.

    # producer = Producer(rabbit, ServiceQueues.SCHEDULER)
    # producer.produce_messages(callback=prepare_message)

    rabbit().start_consuming()

if __name__ == "__main__":
    startup_event()
