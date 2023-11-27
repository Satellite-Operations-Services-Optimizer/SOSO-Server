from celery import Celery
from config import rabbit

celery_app = Celery(
    'tasks',
    broker='amqp://guest:guest@rabbit:5672/'#rabbit().as_uri(),
)
