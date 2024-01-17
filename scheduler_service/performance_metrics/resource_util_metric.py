from sqlalchemy import Column
from sqlalchemy.sql import ClauseElement
from sqlalchemy.sql.expression import func, BinaryExpression, literal_column
from sqlalchemy import text

from app_config import get_db_session
from app_config.database.mapping import SatelliteStateChange, Schedule
from .base import PerformanceMetric
from .utils import min_max_norm

class ResourceUtilizationMetric(PerformanceMetric):
    """
    Goal: Minimize the amount of resources used.
    ResourceUtilizationMetric measures the amount of resources used by a schedule.
    resources include just storage for the time being
    """

    def grades_query(self, schedule_group: str, filters: list[BinaryExpression]=[]):
        """
        """
        session = get_db_session()
        schedule_resource_utils = self.measures_query(
            filters=[Schedule.group_name==schedule_group]
        ).subquery()

        # min/max normalize the "resource_util" column of all schedules in this group
        grades_query = session.query(
            schedule_resource_utils.c.schedule_id,
            min_max_norm(schedule_resource_utils.c.measure).label('grade')
        ).group_by(schedule_resource_utils.c.schedule_id, schedule_resource_utils.c.measure)

        return grades_query
    

    def measures_query(self, filters: list[BinaryExpression]=[], group_by: list[Column]=[]):
        """
        Calculates the resource utilization of a schedule.
         For a given schedule, resource utilization is calculated as follows:

        satellite_resource_util = avg(satellite_storage_utilization across time horizon)
        schedule_resource_util = avg(satellite_resource_util)
        """
        session = get_db_session()
        asset_resource_timelines = self.asset_resource_util_timelines_query(filters).subquery()
        
        aggregated_resource_util = session.query(
            asset_resource_timelines.c.schedule_id,
            func.avg(asset_resource_timelines.c.resource_util).label('measure')
        ).group_by(asset_resource_timelines.c.schedule_id, *group_by)

        return aggregated_resource_util

    def asset_resource_util_timelines_query(self, filters: list[BinaryExpression]=[]):
        session = get_db_session()

        # we are only handling satellites for now, and only considering their storage utilization
        schedule_resource_usage_timeline = session.query(
            SatelliteStateChange.schedule_id,
            SatelliteStateChange.asset_id,
            SatelliteStateChange.asset_type,
            SatelliteStateChange.snapshot_time,
            func.sum(SatelliteStateChange.storage_util_delta).over(
                partition_by=(SatelliteStateChange.schedule_id, SatelliteStateChange.asset_id),
                order_by=SatelliteStateChange.snapshot_time,
                rows=(None, 0) # sum up all rows up to and including current row. Culmulative sum: accumulate the storage_util_delta over time, to form the actual storage of the satellite over time
            ).label('resource_util') # for now, we are only considering storage utilization
        ).join(
            Schedule, SatelliteStateChange.schedule_id==Schedule.id # join with Schedule so we can filter by schedule_group through the 'filters' argument
        ).filter(
            SatelliteStateChange.schedule_id == Schedule.id,
            SatelliteStateChange.storage_util_delta != 0,
            *filters,
            *self.time_horizon.apply_filters(SatelliteStateChange.snapshot_time)
        ).group_by(
            SatelliteStateChange.schedule_id,
            SatelliteStateChange.asset_id,
            SatelliteStateChange.asset_type,
            SatelliteStateChange.snapshot_time,
            SatelliteStateChange.storage_util_delta
        )
        return schedule_resource_usage_timeline
