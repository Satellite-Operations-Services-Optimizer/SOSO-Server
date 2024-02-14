from .base import Mutation
from app_config.database.mapping import Schedule, ScheduledEvent, ScheduleRequest
from app_config import get_db_session

class MissedOpportunities(Mutation):
    def mutate(self, schedule: Schedule) -> Schedule:
        session = get_db_session()
        events = session.query(ScheduledEvent).filter(ScheduledEvent.schedule_id == schedule.id).all()
        