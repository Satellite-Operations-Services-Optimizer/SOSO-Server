from rabbit_wrapper import Consumer, TopicConsumer
from config import rabbit, ServiceQueues
from config.celery import celery_app
from tasks.satellite_state.stream import SatelliteStateStreamManager
import logging

def startup_state_streaming_events():
    consumer = TopicConsumer(rabbit(blocking=False), "satellite.state.listener.create")
    consumer.consume_messages(lambda message: SatelliteStateStreamManager().create_listener(message["id"], message["satellite_id"]))

    consumer = TopicConsumer(rabbit(blocking=False), "satellite.state.listener.destroy")
    consumer.consume_messages(lambda message: SatelliteStateStreamManager().destroy_listener(message["id"]))

logger = logging.getLogger(__name__)
def startup_event():
    celery_app.start(["worker"])
    startup_state_streaming_events()
    consumer = Consumer(rabbit(), ServiceQueues.SCHEDULER)
    consumer.consume_messages(lambda message: logger.info(f"Received message: {message}"))

    rabbit().channel.start_consuming()


if __name__ == "__main__":
    startup_event()
