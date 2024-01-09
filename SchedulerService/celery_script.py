from config import celery_app
import subprocess
import os

if __name__ == '__main__':
    # get log level env var lowercase or None if not set
    log_level = os.environ.get("LOG_LEVEL", None)
    if log_level is not None:
        log_level = log_level.lower()

    # cancel all celery tasks
    celery_app.control.purge()

    worker = celery_app.Worker(
        include=['satellite_state.tasks'],
        loglevel=log_level,
        pool='solo',
    )
    worker.start()