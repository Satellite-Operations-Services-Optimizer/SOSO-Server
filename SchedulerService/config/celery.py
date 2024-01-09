from celery import Celery
from config import rabbit
import os

celery_app = Celery(
    'scheduler-celery-worker',
    broker=os.environ.get("CELERY_BROKER_URL", rabbit().as_uri()),
    backend=os.environ.get("CELERY_RESULT_BACKEND", "rpc://"),
    imports=['satellite_state.tasks']
)