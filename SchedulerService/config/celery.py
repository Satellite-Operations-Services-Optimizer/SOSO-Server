from celery import Celery
from config import rabbit
import os

celery_app = Celery(
    'tasks',
    broker=os.environ.get("CELERY_BROKER_URL", rabbit().as_uri()),
    backend=os.environ.get("CELERY_RESULT_BACKEND", None)
)
