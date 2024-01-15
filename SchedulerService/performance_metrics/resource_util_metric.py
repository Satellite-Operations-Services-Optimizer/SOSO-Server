from sqlalchemy import Column
from sqlalchemy.orm import Query
from sqlalchemy.sql import BinaryExpression, ClauseElement
from sqlalchemy.sql.expression import func, BinaryExpression

from app_config import get_db_session
from app_config.database.mapping import SatelliteStateChange, Schedule
from base import PerformanceMetric
from utils import min_max_norm_column

class ResourceUtilizationMetric(PerformanceMetric):
    """
    Goal: Minimize the amount of resources used.
    ResourceUtilizationMetric measures the amount of resources used by a schedule.
    resources include just storage for the time being
    """

    def scores_subquery(self, schedule_group: str):
        """
        """
        session = get_db_session()
        schedule_resource_utils = self.measures_subquery(
            filters=[Schedule.group_name==schedule_group]
        )

        # min/max normalize the "resource_util" column of all schedules in this group
        grades_query = session.query(
            schedule_resource_utils.c.schedule_id,
            min_max_norm_column(schedule_resource_utils.c.resource_util).label('score')
        ).group_by(schedule_resource_utils.c.schedule_id).subquery()

        return grades_query
    

    def measures_subquery(self, filters: list[BinaryExpression]=[], group_by: list[Column]=[]):
        """
        Calculates the resource utilization of a schedule.
         For a given schedule, resource utilization is calculated as follows:

        satellite_resource_util = avg(satellite_storage_utilization across time horizon)
        schedule_resource_util = avg(satellite_resource_util)
        """
        session = get_db_session()
        asset_resource_usage_timelines = self.asset_resource_usage_timelines_subquery(*filters)
        
        aggregated_resource_util = session.query(
            Schedule.id,
            func.avg(asset_resource_usage_timelines.c.storage_util).label('resource_util')
        ).group_by(Schedule.id, *group_by).subquery()

        return aggregated_resource_util

    def asset_resource_util_timelines_subquery(self, filters: list[BinaryExpression]):
        session = get_db_session()
        time_filters = self.time_horizon.apply_filters(SatelliteStateChange.snapshot_time)

        schedule_resource_usage_timeline = session.query(
            SatelliteStateChange.schedule_id,
            Schedule.group_name,
            SatelliteStateChange.satellite_id,
            SatelliteStateChange.snapshot_time,
            *self.satellite_resource_usage_columns()
        ).filter(
            SatelliteStateChange.schedule_id == Schedule.id,
            *filters,
            *time_filters
        ).group_by(
            Schedule.group_name, SatelliteStateChange.schedule_id, SatelliteStateChange.satellite_id, SatelliteStateChange.snapshot_time
        ).subquery()
        return schedule_resource_usage_timeline

    def satellite_resource_util_columns(self) -> list[ClauseElement]:
        """
        for now we are only considering storage utilization
        """
        return [
            func.sum(SatelliteStateChange.storage_util_delta).over(
                partition_by=(SatelliteStateChange.schedule_id, SatelliteStateChange.satellite_id),
                order_by=SatelliteStateChange.snapshot_time,
                rows=(None, 0) # all rows up to and including current row
            ).label('storage_util')
        ]