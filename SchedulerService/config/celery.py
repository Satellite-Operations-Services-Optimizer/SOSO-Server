from celery import Celery
from config import rabbit

celery_app = Celery(
    'tasks',
    broker=rabbit().as_uri(),
)
