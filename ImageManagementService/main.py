from rabbit_wrapper import Consumer
from config import rabbit, ServiceQueues
from services.handler import handle_message
import logging

logger = logging.getLogger(__name__)
def startup_event():
    
    consumer = Consumer(rabbit(), ServiceQueues.IMAGE_MANAGEMENT)
    consumer.consume_messages(callback=handle_message) # replace handle_message with whatever function you want to call whenever a message is received.


if __name__ == "__main__":
    startup_event()

