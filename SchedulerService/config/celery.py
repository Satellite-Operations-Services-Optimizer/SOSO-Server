from celery import Celery
from config import rabbit
from config.database import db_url
import os

celery_app = Celery(
    'scheduler-celery-worker',
    broker=os.environ.get("CELERY_BROKER_URL", rabbit().as_uri()),
    backend=os.environ.get("CELERY_RESULT_BACKEND", f"db+{db_url}"), # We need a proper database backend (not rpc://) to use AbortableTask (to be able to abort tasks)
    imports=['satellite_state.tasks']
)