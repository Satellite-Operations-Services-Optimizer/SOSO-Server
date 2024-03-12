import warnings
import logging
# Suppress all warnings, including SQLAlchemy warnings
warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.CRITICAL + 1)

from app_config import get_db_session
from app_config.database.mapping import ScheduleRequest
from scheduler_service.tests.scheduler_report import create_report
from sqlalchemy import or_
import time
from datetime import timedelta
from format_duration import format_duration, DurationLimit


def wait_for_scheduler(max_wait_time: int = 10):
    start_time = time.perf_counter()

    scheduler_started = False
    while not scheduler_started and time.perf_counter() - start_time < max_wait_time:
        scheduler_started = session.query(ScheduleRequest).filter(
            or_(
                ScheduleRequest.status=='received',
                ScheduleRequest.status=='processing',
                ScheduleRequest.status=='displaced' # wait for displaced events to be rescheduled
            )
        ).count() > 0
        if scheduler_started: return True
    return False

if __name__ == '__main__':
    session = get_db_session()

    wait_time = 10
    print(f"Waiting for a while (max {wait_time} secs) to allow scheduler system to notice new orders and kick off...")
    wait_for_scheduler(wait_time)
    print("Starting scheduler timer...")
    start = time.perf_counter()
    scheduler_finished = False
    while not scheduler_finished:
        unprocessed_requests_remain = session.query(ScheduleRequest).filter(
            or_(
                ScheduleRequest.status=='received',
                ScheduleRequest.status=='processing',
                ScheduleRequest.status=='displaced' # wait for displaced events to be rescheduled
            )
        ).count() > 0

        scheduler_finished = not unprocessed_requests_remain

    duration = timedelta(seconds=time.perf_counter() - start)
    limit = DurationLimit.SECOND
    is_abbreviated = False

    duration_str = format_duration(duration, is_abbreviated, limit)
    print(f"Scheduler finished in {duration_str}.")
    print("Creating report...")
    create_report()
    print("\n\n\n\n")
