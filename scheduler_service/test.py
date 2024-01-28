from app_config.database.mapping import ScheduleRequest, ScheduledEvent, Schedule
from sqlalchemy import literal
from sqlalchemy.sql.expression import func
from sqlalchemy.sql.expression import insert
from app_config import get_db_session

class SchedulerManager:
    def __init__(self, request_limit: int = 1000):
        self.request_limit = request_limit

    def query_ordered_candidate_requests(self, schedule: Schedule) -> list[ScheduleRequest]:
        session = get_db_session()

        requests_filter = [ScheduleRequest.status=='received']
        # if self.max_schedule_interval:
        #     requests_filter.append((ScheduleRequest.window_start - func.min(ScheduleRequest.window_start)) < self.max_schedule_interval)

        return session.query(ScheduleRequest).filter(
            ScheduleRequest.schedule_id == schedule.id,
            *requests_filter
        ).order_by(ScheduleRequest.window_start).limit(self.request_limit)

    def copy_schedule_within_candidate_requests_span(self, schedule: Schedule) -> Schedule:
        session = get_db_session()
        new_schedule = Schedule(name=schedule.name+" Copy")
        session.flush() #so we get the generated schedule id

        candidate_request_span_start = session.query(func.min(ScheduleRequest.window_start)).filter(
            ScheduleRequest.schedule_id == schedule.id, *self.candidate_requests_filters()
        ).scalar()
        candidate_request_span_end = session.query(func.max(ScheduleRequest.window_end)).filter(
            ScheduleRequest.schedule_id == schedule.id, *self.candidate_requests_filters()
        ).scalar()

        # Copy ScheduleRequest instances that overlap with our span
        schedule_requests_in_span = session.query(
            literal(new_schedule.id).label('schedule_id'), # set schedule_id to the new schedule's id to prime for copying them over to new scheudle
            *(getattr(ScheduleRequest, column.name) for column in ScheduleRequest.__table__.columns if column.name != 'schedule_id')
        ).filter(
            ScheduleRequest.schedule_id == schedule.id,
            func.tsrange(ScheduleRequest.window_start, ScheduleRequest.window_end).op('&&')(func.tsrange(candidate_request_span_start, candidate_request_span_end)) # Check if request overlaps with our span
        )
        requests_insert_stmt = insert(ScheduleRequest).from_select(schedule_requests_in_span)
        session.execute(requests_insert_stmt)

        # Copy ScheduledEvent instances that overlap with our span
        schedule_events_in_span = session.query(
            literal(new_schedule.id).label('schedule_id'), # set schedule_id to the new schedule's id to prime for copying them over to new scheudle
            *(getattr(ScheduledEvent, column.name) for column in ScheduledEvent.__table__.columns if column.name != 'schedule_id')
        ).filter(
            ScheduledEvent.schedule_id == schedule.id,
            func.tsrange(ScheduledEvent.start_time, ScheduledEvent.end_time).op('&&')(func.tsrange(candidate_request_span_start, candidate_request_span_end)) # Check if request overlaps with our span
        )

        events_insert_stmt = insert(ScheduledEvent).from_select(schedule_events_in_span)

        # Copy FixedEvent instances that are outside our span (specifically after our span, but before the maximum deliver_by date of any event within our span). This is so that we can consider all possible times to downlink data from the satellite. We of course limit, so we don't have too many events to consider for scheduling for ram/performance purposes

        candidate_requests = self.query_ordered_candidate_requests(schedule).all()
        if len(candidate_requests) == 0:
            return new_schedule
        
        request_span_start = candidate_requests[0].window_start
        request_span_end = candidate_requests[-1].window_end

        schedule_requests_in_span = session.query(
            literal(new_schedule.id).label('schedule_id'), # set schedule_id to the new schedule's id to prime for copying them over to new scheudle
            *(getattr(ScheduleRequest, column.name) for column in ScheduleRequest.__table__.columns if column.name != 'schedule_id')
        ).filter(
            ScheduleRequest.schedule_id == schedule.id,
            func.tsrange(ScheduleRequest.window_start, ScheduleRequest.window_end).op('&&')(func.tsrange(request_span_start, request_span_end)) # Check if request overlaps with our span
        )

        requests_insert_stmt = insert(ScheduleRequest).from_select(schedule_requests_in_span)
        session.execute(requests_insert_stmt)
        session.flush()
    
    def candidate_requests_filters():
        return [ScheduleRequest.status=='received']