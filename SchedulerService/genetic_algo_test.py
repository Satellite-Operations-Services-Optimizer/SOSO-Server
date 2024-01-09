from dataclasses import dataclass
from datetime import datetime
from sqlalchemy.sql.expression import func
from config import db_session
from abc import ABC, abstractmethod

@dataclass
class ScheduleHorizon:
    startHorizon: datetime
    endHorizon: datetime

    def calc_makespan(self):
        db_session.query(func.max())
    
    def calc_tardiness(self):
        db_session.query()

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

# create table in the database called activity_stream


if __name__ == '__main__':
    