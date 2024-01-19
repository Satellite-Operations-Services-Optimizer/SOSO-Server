from sqlalchemy import Column
from sqlalchemy.sql.expression import func, BinaryExpression

from app_config import get_db_session
from app_config.database.mapping import SatelliteStateChange, Schedule
from .base import PerformanceMetric
from .utils import min_max_norm

class ThroughputMetric(PerformanceMetric):
    """
    Goal: Fulfil as many orders as possible.
    ThroughputMetric measures the amount of workload fulfilled by a schedule.

    throughput signifies how many events have been scheduled to take place for a schedule, weighted by how important the event is.
    """

    def grades_query(self, schedule_group: str, filters: list[BinaryExpression]=[]):
        """
        Creates a query that calculates the throughput satisfaction grade for each schedule in the provided schedule_group.
        throughput_satisfaction_grade is calculated as the min/max normalized schedule_throughput, normalized across all schedules in the same group
        
        For a given schedule, throughpu_grade is calculated with the following formula:
        schedule_throughput_grade = (schedule_throughput-min(schedule_throughput))/(max(schedule_throughput)-min(schedule_throughput))
        where min and max are defined over all schedules in the provided schedule_group
        """
        session = get_db_session()
        throughputs_subquery = self.measures_query(
            filters=[Schedule.group_name==schedule_group] + filters
        ).subquery()

        # min/max normalize the throughput value across all schedules with the same schedule_group
        grades_query = session.query(
            throughputs_subquery.c.schedule_id,
            min_max_norm(throughputs_subquery.c.measure).label('grade')
        ).group_by(throughputs_subquery.c.schedule_id, throughputs_subquery.c.measure)
        return grades_query
    
    def measures_query(self, filters: list[BinaryExpression]=[], group_by: list[Column]=[]):
        """
        Calculates the throughput of a schedule.
        Throughput for a schedule is the count of all the scheduled satellite events in the schedule, weighted by how important the schedule item type is 
        (e.g. scheduled_maintenance counts for more than scheduled_imaging)

        For a given schedule, throughput is calculated with the following formula:
        schedule_throughput = Σ_{satellite_event in schedule} satellite_event.event_weight

        
        """
        session = get_db_session()
        time_filters = self.time_horizon.apply_filters(SatelliteStateChange.snapshot_time)

        throughputs_query = session.query(
            SatelliteStateChange.schedule_id,
            func.sum(SatelliteStateChange.throughput_delta).label('measure')
        ).join(
            Schedule, SatelliteStateChange.schedule_id==Schedule.id # join with Schedule so we can filter by schedule_group through the 'filters' argument
        ).filter(
            SatelliteStateChange.schedule_id==Schedule.id,
            SatelliteStateChange.throughput_delta != 0,
            *filters,
            *time_filters
        ).group_by(SatelliteStateChange.schedule_id, *group_by)

        return throughputs_query
