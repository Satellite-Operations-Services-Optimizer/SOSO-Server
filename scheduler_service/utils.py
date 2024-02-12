from datetime import datetime
from typing import Optional
from sqlalchemy import Column
from sqlalchemy.sql.expression import BinaryExpression
from dataclasses import dataclass
from app_config.database.mapping import Schedule
from typing import Optional, TypedDict, List
from utils import TimeHorizon
from datetime import timedelta
from app_config.database.mapping import ScheduledEvent
from app_config import get_db_session

@dataclass
class TimeHorizon:
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    include_overlap: bool = False

    def apply_filters(self, start_time_column: Column, end_time_column: Optional[Column] = None) -> list[BinaryExpression]:
        filters = []

        if self.start is not None:
            start_filter = (start_time_column >= self.start)
            if end_time_column and self.include_overlap:
                start_filter |= (end_time_column >= self.start)
            filters.append(start_filter)
        
        if self.end is not None:
            end_column = end_time_column if end_time_column else start_time_column
            end_filter = (end_column <= self.end)
            if start_time_column and self.include_overlap:
                end_filter |= (start_time_column <= self.end)
            filters.append(end_filter)

        return filters

class CopyOptions(TypedDict, total=False):
    copied_schedule_request_types: List[str]
    lookback_duration: Optional[timedelta]

def copy_schedule(self, schedule: Schedule, time_range: TimeHorizon = TimeHorizon(None, None),  **options: Optional[dict]):
    """

    """
    session = get_db_session()
    new_schedule = Schedule(name=f"{schedule.name} - Copy_{datetime.now()}")
    session.add(new_schedule)

    copy_options = {
        'copied_schedule_request_types': ['received'],
        'context_duration': None,
        'context_event_types': ['sat_outage', 'gs_outage', 'contact', 'eclipse'],
        'backpopulate_contact_events': True
    }
    copy_options.update(options)
    if time_range.start is None:
        copy_options['lookback_duration'] = None
    
    if copy_options['lookback_duration'] is not None:
        fixed_event_lookback_time_range = TimeHorizon(time_range.start - copy_options['lookback_duration'])
        fixed_event_lookback_constraint = (ScheduledEvent.event_type=='fixed')



    # Copy ScheduleRequest instances that overlap with our span
    schedule_requests_in_span = session.query()
