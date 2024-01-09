from dataclasses import dataclass
from datetime import datetime
from sqlalchemy.sql.expression import func
from app_config import get_session
from abc import ABC, abstractmethod

@dataclass
class ScheduleHorizon:
    startHorizon: datetime
    endHorizon: datetime

    def calc_makespan(self):
        session = get_session()
        session.query(func.max())
    
    def calc_tardiness(self):
        session = get_session()
        session.query()

class PerformanceMetric(ABC):
    def __init__(self, weight: int):
        self.weight = weight

    @abstractmethod
    def calc_metric(self, schedule_horizon: ScheduleHorizon):
        pass

    @abstractmethod
    def calc_satisfaction_grade(self, schedule_horizon):
        pass

class Makespan(PerformanceMetric):
    def calc_metric(self, schedule_horizon: ScheduleHorizon):
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