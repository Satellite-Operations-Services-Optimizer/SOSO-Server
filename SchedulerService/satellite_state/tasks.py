from celery import shared_task
from app_config import get_session, rabbit
from .state_generator import Satellite, SatelliteStateGenerator
from celery.contrib.abortable import AbortableTask
from rabbit_wrapper import TopicPublisher
from app_config import logging

logger = logging.getLogger(__name__)

@shared_task(name='state_stream_task', bind=True, base=AbortableTask)
def state_stream_task(self, satellite_id: str):
    logger.info(f"Started state streaming for satellite id={satellite_id}.")
    session = get_session()
    satellite = session.query(Satellite).first()

    state_publisher = TopicPublisher(rabbit(), f"satellite.state.{satellite_id}")
    state_generator = SatelliteStateGenerator(satellite)
    for state in state_generator.stream():
        state_publisher.publish_message(state)
        if self.is_aborted():
            logger.info(f"Successfully aborted state streaming for satellite id={satellite_id}.")
            return