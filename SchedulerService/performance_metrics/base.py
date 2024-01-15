from dataclasses import dataclass
from datetime import datetime
from abc import ABC, abstractmethod
from typing import Optional

from sqlalchemy import Column
from sqlalchemy.sql import BinaryExpression, ClauseElement, Window
from sqlalchemy.sql.expression import func, BinaryExpression
from app_config import get_db_session
from app_config.database.mapping import Schedule

@dataclass
class TimeHorizon:
    start: Optional[datetime]
    end: Optional[datetime]
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




class PerformanceMetric(ABC):
    time_horizon: TimeHorizon
    def __init__(self, weight: float):
        self.weight = weight
        self.time_horizon = TimeHorizon()
    
    def set_time_horizon(self, time_horizon: TimeHorizon):
        self.time_horizon = time_horizon

    def measure(self, schedule_id: int):
        """
        Calculate the schedule performance measure for this metric.
        """
        measure = self.measures_subquery(
            filters=[Schedule.id==schedule_id]
        ).scalar()
        return measure
    
    def score(self, schedule_id: int) -> float:
        """
        Calculate satisfaction grades for each schedule in a group.
        """
        session = get_db_session()
        schedule_group = Schedule.find(schedule_id).group_name

        scores_query = self.scores_subquery(schedule_group)
        score = session.query(scores_query.c.score).filter(Schedule.id==schedule_id).scalar()
        return score

    @abstractmethod
    def scores_subquery(self, schedule_group: str):
        pass

    @abstractmethod
    def measures_subquery(self, filters: list[BinaryExpression]=[], group_by: list[Column]=[]):
        pass