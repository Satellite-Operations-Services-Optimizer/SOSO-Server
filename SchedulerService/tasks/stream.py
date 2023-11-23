from celery import shared_task
from config import db_session
from utils.satellite import Satellite, SatelliteStateGenerator
from celery.contrib.abortable import AbortableTask
from config import rabbit
from rabbit_wrapper import TopicPublisher
from config import logging

logger = logging.getLogger(__name__)
@shared_task(bind=True, base=AbortableTask)
def stream_satellite_state(self, satellite_id: str):
    satellite = db_session.query(Satellite).first()

    state_publisher = TopicPublisher(rabbit(), f"satellite.state.{satellite_id}")
    state_generator = SatelliteStateGenerator(satellite)
    for state in state_generator.stream():
        state_publisher.publish_message(state)
        if self.is_aborted():
            return

class SatelliteStateStreamManager:
    satellite_listeners: dict[str, set[str]] = dict() # map satellite_id -> set of listeners
    listener_info: dict[str, str] = dict() # map from listener id -> satellite it is listening to

    def create_listener(self, listener_id: str, satellite_id: str):
        logger.debug(f"Creating listener {listener_id} for satellite {satellite_id}")
        # in case this listener was listening to a different satellite previously, delete the listener before creating it again
        self.destroy_listener(listener_id) 

        # attach listener to satellite
        if satellite_id not in self.satellite_listeners:
            self.satellite_listeners[satellite_id] = set()
        self.satellite_listeners[satellite_id].add(listener_id)
        self.listener_info[satellite_id].add(listener_id)

        # providing task id ensures that the task is only run once per satellite
        stream_satellite_state.apply_async(args=[satellite_id], task_id=satellite_id)

    def destroy_listener(self, listener_id: str):
        logger.debug(f"Destroying listener {listener_id}")
        if listener_id not in self.listener_info: return
        satellite_id = self.listener_info.pop(listener_id)
        self.satellite_listeners[satellite_id].remove(listener_id)
        if len(self.satellite_listeners[satellite_id])==0:
            del self.satellite_listeners[satellite_id]
            self._abort_task(satellite_id)

    def _abort_task(task_id: str):
        task = stream_satellite_state.AsyncResult(task_id)
        task.abort()