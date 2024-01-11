from dataclasses import dataclass
from datetime import datetime
from sqlalchemy.sql.expression import func
from app_config import get_db_session
from app_config.db_tables import ScheduledEvent
from abc import ABC, abstractmethod

@dataclass
class ScheduleHorizon:
    startHorizon: datetime
    endHorizon: datetime

class PerformanceMetric(ABC):
    def __init__(self, weight: int):
        self.weight = weight
    
    
    def set_horizon(self, schedule_horizon: ScheduleHorizon):
        self.schedule_horizon = schedule_horizon

    @abstractmethod
    def score(self, schedule_id: int):
        pass

    @abstractmethod
    def satisfaction_grade(self, group_id: int):
        pass

    def on_event_scheduled(self, ):
        pass


class Throughput(PerformanceMetric):
    """
    We Calculate the throughput of a schedule by summing up the priorities of all events in the schedule horizon.
    The more events scheduled, the higher the throughput. Also, the higher the priority of the events, the higher the throughput.
    only imaging and maintenance events are considered.
    """
    def score(self, schedule_id: int):
        session = get_db_session()
        score = session.query(func.sum(ScheduledEvent.priority)).filter(
            ScheduledEvent.event_type._in(['imaging', 'maintenance']),
            ScheduledEvent.schedule_id == schedule_id,
            self.schedule_horizon.filter
        ).scalar()
        return score

    def satisfaction_grade(self, schedule_horizon):
        pass

class Makespan(PerformanceMetric):
    def calc_metric(self, schedule_horizon: ScheduleHorizon):
        session = get_db_session()
        session.query(func.max())
        pass

    def calc_satisfaction_grade(self, schedule_horizon):
        pass

class Tardiness(PerformanceMetric):
    def calc_metric(self, schedule_horizon: ScheduleHorizon):
        pass

    def calc_satisfaction_grade(self, schedule_horizon):
        pass



if __name__ == '__main__':
    print("hi")