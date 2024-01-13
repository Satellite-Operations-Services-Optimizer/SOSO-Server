from dataclasses import dataclass
from datetime import datetime
from abc import ABC, abstractmethod
from typing import Optional

from sqlalchemy import Column
from sqlalchemy.orm import aliased, Query
from sqlalchemy.sql import BinaryExpression, ClauseElement, Window
from sqlalchemy.sql.expression import func, BinaryExpression

from app_config import get_db_session
from app_config.db_classes import SatelliteStateChange, ScheduleBlueprint

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



def min_max_norm_column(self, column: ClauseElement, partition_by: list[ClauseElement] = None) -> ClauseElement:
    window = Window() if partition_by is None else Window().partition_by(*partition_by)
    return (column - func.min(column).over(window)) / (func.max(column).over(window) - func.min(column).over(window))


class PerformanceMetric(ABC):
    time_horizon: TimeHorizon
    def __init__(self, weight: int):
        self.weight = weight
        self.time_horizon = TimeHorizon()
    
    def set_time_horizon(self, time_horizon: TimeHorizon):
        self.time_horizon = time_horizon

    @abstractmethod
    def calc_measure(self, schedule_id: int):
        """
        Calculate the schedule score for this metric.
        """
        pass

    @abstractmethod
    def query_grades(self, schedule_group: str):
        """
        Calculate satisfaction grades for each schedule in a group.
        """
        pass

class ThroughputMetric(PerformanceMetric):
    """
    Goal: Fulfil as many orders as possible.
    ThroughputMetric measures the amount of workload fulfilled by a schedule.

    throughput signifies how many events have been scheduled to take place for a schedule, weighted by how important the event is.
    """
    def __init__(self, weight: int):
        super().__init__(weight)

    def calc_measure(self, schedule_id: int):
        """
        Calculates the throughput of a schedule.
        Throughput for a schedule is the count of all the scheduled satellite events in the schedule, weighted by how important the schedule item type is 
        (e.g. scheduled_maintenance counts for more than scheduled_imaging)

        For a given schedule, throughput is calculated with the following formula:
        schedule_throughput = Σ_{satellite_event in schedule} satellite_event.event_weight

        
        """
        session = get_db_session()
        time_filters = self.time_horizon.apply_filters(SatelliteStateChange.snapshot_time)
        throughput = session.query(func.sum(SatelliteStateChange.throughput_delta).label('throughput')) \
            .filter(SatelliteStateChange.schedule_id == schedule_id) \
            .filter(SatelliteStateChange.throughput_delta > 0) \
            .filter(*time_filters).scalar()
        
        return throughput

    def query_grades(self, schedule_group: str):
        """
        Creates a query that calculates the throughput satisfaction grade for each schedule in the provided schedule_group.
        throughput_satisfaction_grade is calculated as the min/max normalized schedule_throughput, normalized across all schedules in the same group
        
        For a given schedule, throughpu_grade is calculated with the following formula:
        schedule_throughput_grade = (schedule_throughput-min(schedule_throughput))/(max(schedule_throughput)-min(schedule_throughput))
        where min and max are defined over all schedules in the provided schedule_group
        """
        session = get_db_session()
        time_filters = self.time_horizon.apply_filters(SatelliteStateChange.snapshot_time)
        throughputs_subquery = session.query(ScheduleBlueprint.schedule_group, ScheduleBlueprint.schedule_id, func.sum(SatelliteStateChange.throughput_delta).label('throughput')) \
            .filter(SatelliteStateChange.schedule_id==ScheduleBlueprint.id) \
            .filter(ScheduleBlueprint.group_name == schedule_group) \
            .filter(SatelliteStateChange.throughput_delta > 0) \
            .filter(*time_filters) \
            .group_by(ScheduleBlueprint.group_name, ScheduleBlueprint.schedule_id).subquery()

        # min/max normalize the "throughput" column of the throughputs_query across all schedules with the same schedule_group
        grades_query = session.query(
            throughputs_subquery.c.schedule_id,
            min_max_norm_column(throughputs_subquery.c.throughput, partition_by=[throughputs_subquery.c.schedule_group]).label('grade')
        ).group_by(throughputs_subquery.c.schedule_id)
        return grades_query


class ResourceUtilizationMetric(PerformanceMetric):
    """
    Goal: Minimize the amount of resources used.
    ResourceUtilizationMetric measures the amount of resources used by a schedule.
    resources include just storage for the time being
    """
    def __init__(self, weight: int):
        super().__init__(weight)

    def calc_measure(self, schedule_id: int):
        """
        Calculates the resource utilization of a schedule.
         For a given schedule, resource utilization is calculated as follows:

        satellite_resource_util = avg(satellite_storage_utilization across time horizon)
        schedule_resource_util = avg(satellite_resource_util)
        """
        session = get_db_session()
        time_filters = self.time_horizon.apply_filters(SatelliteStateChange.snapshot_time)

        schedule_resource_usage_timeline = session.query(
            SatelliteStateChange.schedule_id,
            ScheduleBlueprint.group_name,
            SatelliteStateChange.satellite_id,
            SatelliteStateChange.snapshot_time,
            *self.satellite_resource_usage_columns()
        ).filter(
            SatelliteStateChange.schedule_id == ScheduleBlueprint.id,
            SatelliteStateChange.schedule_id == schedule_id,
            *time_filters
        ).group_by(
            ScheduleBlueprint.group_name, SatelliteStateChange.schedule_id, SatelliteStateChange.satellite_id, SatelliteStateChange.snapshot_time
        ).subquery()
        
        resource_utilization = session.query(
            func.avg(schedule_resource_usage_timeline.c.storage_util)
        ).group_by(schedule_resource_usage_timeline.group_name).scalar()

        return resource_utilization

    def query_grades(self, schedule_group: str) -> Query:
        """
        Create a 
        """
        session = get_db_session()
        time_filters = self.time_horizon.apply_filters(SatelliteStateChange.snapshot_time)

        schedule_resource_usage_timeline = session.query(
            SatelliteStateChange.schedule_id,
            ScheduleBlueprint.group_name,
            SatelliteStateChange.satellite_id,
            SatelliteStateChange.snapshot_time,
            *self.satellite_resource_usage_columns()
        ).filter(
            SatelliteStateChange.schedule_id == ScheduleBlueprint.schedule_id,
            ScheduleBlueprint.group_name == schedule_group
            *time_filters
        ).group_by(
            ScheduleBlueprint.group_name, SatelliteStateChange.schedule_id, SatelliteStateChange.satellite_id, SatelliteStateChange.snapshot_time
        ).subquery()
        
        schedule_resource_utilizations = session.query(
            func.avg(schedule_resource_usage_timeline.c.storage_usage).label('resource_utilization')
        ).group_by(schedule_resource_usage_timeline.group_name).subquery()

        # min/max normalize the "resource utilization" column of the throughputs_query across all schedules with the same schedule_group
        grades_query = session.query(
            schedule_resource_utilizations.c.schedule_id,
            self._min_max_norm(schedule_resource_utilizations.c.resource_utilization, partition_by=[schedule_resource_utilizations.c.schedule_group]).label('grade')
        ).group_by(schedule_resource_utilizations.c.schedule_id)

        return grades_query
    
    def satellite_resource_usage_timeline_subquery(self, schedule_filters, satellite_filters) -> Query:


    def satellite_resource_usage_columns(self) -> list[ClauseElement]:
        """
        for now we are only considering storage utilization
        """
        return [
            func.sum(SatelliteStateChange.storage_delta).over(
                partition_by=(SatelliteStateChange.schedule_id, SatelliteStateChange.satellite_id),
                order_by=SatelliteStateChange.snapshot_time,
                rows=(None, 0) # all rows up to and including current row
            ).label('storage_usage')
        ]

    
    

class WorkloadDistributionMetric(PerformanceMetric):
    pass


genetic_algo(Throughput(weight=0.3), ResourceUtilization(weight=0.7), 


if __name__ == '__main__':
    print("hi")