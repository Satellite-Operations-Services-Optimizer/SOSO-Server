from dataclasses import dataclass
from datetime import datetime
from sqlalchemy.sql.expression import func
from sqlalchemy.sql import ClauseElement, Window
from sqlalchemy.orm import aliased
from app_config import get_db_session
from abc import ABC, abstractmethod
from typing import Optional
from sqlalchemy import Column
from app_config.db_classes import SatelliteStateChange, ScheduleBlueprint

@dataclass
class TimeHorizon:
    start: Optional[datetime]
    end: Optional[datetime]
    include_overlap: bool = False

    def apply_filters(self, start_time_column: Column, end_time_column: Optional[Column] = None):
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
    def __init__(self, weight: int):
        self.weight = weight
        self.time_horizon = TimeHorizon()
    
    def set_time_horizon(self, time_horizon: TimeHorizon):
        self.time_horizon = time_horizon

    @abstractmethod
    def calc_schedule_score(self, schedule_id: int):
        """
        Calculate the schedule score for this metric.
        """
        pass

    @abstractmethod
    def calc_satisfaction_grades(self, schedule_group: str):
        """
        Calculate satisfaction grades for each schedule in a group.
        """
        pass

class ThroughputMetric(PerformanceMetric):
    """
    Goal: Fulfil as many orders as possible.
    ThroughputMetric measures the amount of workload fulfilled by a schedule.
    """
    def __init__(self, weight: int):
        super().__init__(weight)

    def calc_schedule_score(self, schedule_id: int):
        session = get_db_session()
        time_filters = self.time_horizon.apply_filters(SatelliteStateChange.snapshot_time)
        throughput = session.query(func.sum(SatelliteStateChange.workload_delta).label('throughput')) \
            .filter(SatelliteStateChange.schedule_id == schedule_id) \
            .filter(SatelliteStateChange.throughput_delta > 0) \
            .filter(*time_filters).scalar()
        return throughput

    def query_satisfaction_grades(self, schedule_group: str):
        """
        Calculates the satisfaction grades of all schedules within the specified group, where the satisfaction grade is the min/max normalized throughput of all the schedules within the group
        """
        session = get_db_session()
        time_filters = self.time_horizon.apply_filters(SatelliteStateChange.snapshot_time)
        throughputs_subquery = session.query(ScheduleBlueprint.schedule_group, ScheduleBlueprint.schedule_id, func.sum(SatelliteStateChange.throughput_delta).label('throughput')) \
            .filter(SatelliteStateChange.schedule_id==ScheduleBlueprint.id) \
            .filter(ScheduleBlueprint.schedule_group == schedule_group) \
            .filter(SatelliteStateChange.throughput_delta > 0) \
            .filter(*time_filters) \
            .group_by(ScheduleBlueprint.schedule_group, ScheduleBlueprint.schedule_id).subquery()

        # min/max normalize the "throughput" column of the workloads_query across all schedules with the same schedule_group
        sat_grades_query = session.query(
            throughputs_subquery.c.schedule_id,
            self._min_max_norm(throughputs_subquery.c.throughput, partition_by=[throughputs_subquery.c.schedule_group]).label('sat_grade')
        ).group_by(throughputs_subquery.c.schedule_id)
        return sat_grades_query

    def _min_max_norm(self, query_value: ClauseElement, partition_by: list[ClauseElement] = None) -> ClauseElement:
        window = Window() if partition_by is None else Window().partition_by(*partition_by)
        
        return (query_value - func.min(query_value).over(window)) / (
            func.max(query_value).over(window) - func.min(query_value).over(window)
        )


class ResourceUtilizationMetric(PerformanceMetric):
    """
    Goal: Minimize the amount of resources used.
    ResourceUtilizationMetric measures the amount of resources used by a schedule.
    resources include just storage for the time being
    """
    def __init__(self, weight: int):
        super().__init__(weight)

    def calc_schedule_score(self, schedule_id: int):
        session = get_db_session()
        time_filters = self.time_horizon.apply_filters(SatelliteStateChange.snapshot_time)
        resources_used = session.query(func.sum(SatelliteStateChange.storage_delta).label('resource_util')) \
            .filter(SatelliteStateChange.schedule_id == schedule_id) \
            .filter(*time_filters).scalar()
        return resources_used

    def query_satisfaction_grades(self, schedule_group: str):
        session = get_db_session()
        time_filters = self.time_horizon.apply_filters(SatelliteStateChange.snapshot_time)
        resources_used_query = session.query(ScheduleBlueprint.schedule_id, func.sum(SatelliteStateChange.storage_delta).label('resource_util')) \
            .filter(ScheduleBlueprint.id == SatelliteStateChange.schedule_id) \
            .filter(ScheduleBlueprint.schedule_group == schedule_group) \
            .filter(*time_filters) \
            .group_by(SatelliteStateChange.schedule_id)
        return resources_used_query

class AssetUtilization(PerformanceMetric):


if __name__ == '__main__':
    print("hi")