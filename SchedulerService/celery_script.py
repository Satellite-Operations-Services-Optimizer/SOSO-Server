from config import celery_app
import subprocess
import os

if __name__ == '__main__':
    # get log level env var lowercase or None if not set
    log_level = os.environ.get("LOG_LEVEL", None)
    if log_level is not None:
        log_level = log_level.lower()

    worker = celery_app.Worker(
        include=['satellite_state.tasks'],
        loglevel=log_level,
        pool='solo',
    )

    worker.start()
    
    # # navigate to this script's path
    # os.chdir(os.path.dirname(os.path.realpath(__file__)))

    # # command to start celery worker
    # start_command = ['celery', 'worker', '-A', 'config.celery_app']

    # # add log level if specified
    # log_level = os.environ.get("LOG_LEVEL", None)
    # start_command = start_command + ['--loglevel=' + log_level.lower()] if log_level else start_command

    # # run start command, setting the shell value correctly for all systems
    # shell=True if os.name == 'nt' else False # shell=True for windows otherwise windows will not be able to find the celery command
    # subprocess.run(start_command, shell=shell)