from celery import shared_task
from config import db_session
from .state_generator import Satellite, SatelliteStateGenerator
from celery.contrib.abortable import AbortableTask
from config import rabbit
from rabbit_wrapper import TopicPublisher, TopicConsumer
from config import logging

logger = logging.getLogger(__name__)
@shared_task(bind=True, base=AbortableTask)
def stream_satellite_state(self, satellite_id: str):
    logger.info(f"Started state streaming for satellite id={satellite_id}.")
    satellite = db_session.query(Satellite).first()

    state_publisher = TopicPublisher(rabbit(), f"satellite.state.{satellite_id}")
    state_generator = SatelliteStateGenerator(satellite)
    for state in state_generator.stream():
        state_publisher.publish_message(state)
        if self.is_aborted():
            logger.info(f"Successfully aborted state streaming for satellite id={satellite_id}.")
            return

manager = None
def setup_state_streaming_event_listeners():
    global manager
    if manager is None:
        manager = SatelliteStateStreamManager()

    create_listener_consumer = TopicConsumer(rabbit(), "satellite.state.listener.create")
    create_listener_consumer.register_callback(lambda message: manager.create_listener(message["satellite_id"]))

    destroy_listener_consumer = TopicConsumer(rabbit(), "satellite.state.listener.destroy")
    destroy_listener_consumer.register_callback(lambda message: manager.destroy_listener(message["satellite_id"]))


class SatelliteStateStreamManager:
    listener_counts: dict[str, int] = dict() # map from satellite id -> number of listeners

    def create_listener(self, satellite_id: str):

        if satellite_id not in self.listener_counts:
            self.listener_counts[satellite_id] = 0
        self.listener_counts[satellite_id] += 1

        logger.info(f"Created state listener for satellite id={satellite_id}. Total listener count: {self.listener_counts[satellite_id]}")

        # providing task id ensures that the task is only run once per satellite
        stream_satellite_state.apply_async(args=[satellite_id], task_id=f"satellite_id")

    def destroy_listener(self, satellite_id: str):
        if satellite_id not in self.listener_counts: return
        logger.info(f"Destroyed state listener for satellite id={satellite_id}. Total listener count: {self.listener_counts[satellite_id]}")
        self.listener_counts[satellite_id] -= 1

        if self.listener_counts[satellite_id]==0:
            del self.listener_counts[satellite_id]
            self._abort_task(satellite_id)

    def _abort_task(self, task_id: str):
        task = stream_satellite_state.AsyncResult(task_id)
        task.abort()
        logger.info(f"Requested abortion of state streaming task with id={task_id}")