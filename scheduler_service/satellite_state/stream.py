from app_config import rabbit
from rabbit_wrapper import TopicConsumer
from app_config import logging
from .tasks import state_stream_task
# from celery.app.control import revoke

logger = logging.getLogger(__name__)

manager = None
def register_state_streaming_listeners():
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
        state_stream_task.apply_async(args=[satellite_id], task_id=f"satellite_id")

    def destroy_listener(self, satellite_id: str):
        if satellite_id not in self.listener_counts: return
        self.listener_counts[satellite_id] -= 1
        logger.info(f"Destroyed state listener for satellite id={satellite_id}. Total listener count: {self.listener_counts[satellite_id]}")

        if self.listener_counts[satellite_id]==0:
            del self.listener_counts[satellite_id]
            self._abort_task(satellite_id)

    def _abort_task(self, task_id: str):
        task = state_stream_task.AsyncResult(task_id)
        task.abort()
        # revoke(task_id, terminate=True)
        logger.info(f"Requested abortion of state streaming task with id={task_id}")