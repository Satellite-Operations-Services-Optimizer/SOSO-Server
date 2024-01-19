from sqlalchemy.sql.expression import func

from app_config import get_db_session
from app_config.database.mapping import Schedule
from .base import PerformanceMetric
from .utils import min_max_norm, normalized_avg, z_score
from .resource_util import ResourceUtilizationMetric
from sqlalchemy.sql.expression import BinaryExpression
from sqlalchemy import Column


class WorkloadDistributionMetric(PerformanceMetric):
    """
    Goal: Spread out the workload evenly among satellites.
    WorkloadDistributionMetric measures the spread of workload among satellites in a schedule.

    For a schedule, WorkloadDistributionMetric is calculated as follows:
    we measure the z-score of the average resource utilization of each satellite in the schedule (let's call it asset_util_grade)
    we then measure the z-score of the standard deviation of resource utilization of each satellite in the schedule (let's call it asset_util_flux)
    The two above z-score calculations are sampled based on the class of assets (e.g. satellites, groundstations, etc.) - the population is the set of all assets of the same class

    workload distribution is then calculated as follows:
    # we weight these two factors using two weight parameters: stability_factor and spread_factor
    workload_distribution = 1 - (spread_factor * avg(asset_util_grade across all assets) + stability_factor * avg(asset_util_flux across all assets))

    Above, I mention only satellites, but we apply the same formula to each class of assets, including groundstations.
    Then we combine across all asset class
    """
    resource_util: ResourceUtilizationMetric
    def __init__(self, weight: float = 1.0, spread_factor: float = 0.5, stability_factor: float = 0.5):
        super().__init__(weight)
        self.resource_util = ResourceUtilizationMetric(1.0);
        self.spread_factor = spread_factor
        self.stability_factor = stability_factor

    def measures_query(self, filters: list[BinaryExpression]=[], group_by: list[Column]=[]):
        session = get_db_session()
        asset_resource_util_timelines = self.resource_util.asset_resource_util_timelines_query(filters).subquery()

        # calculate the average and standard deviation of resource utilization for each satellite in the schedule
        asset_util_stats = session.query(
            asset_resource_util_timelines.c.schedule_id,
            asset_resource_util_timelines.c.asset_id,
            asset_resource_util_timelines.c.asset_type,
            func.avg(asset_resource_util_timelines.c.resource_util).label('util_avg'),
            func.stddev(asset_resource_util_timelines.c.resource_util).label('util_std')
        ).group_by(
            asset_resource_util_timelines.c.schedule_id,
            asset_resource_util_timelines.c.asset_id,
            asset_resource_util_timelines.c.asset_type
        ).subquery()

        # calculate the asset_util_grade (i.e. z-score of asset_util_avg) and asset_util_flux (i.e. z-score of asset_util_std)
        asset_util = session.query(
            asset_util_stats.c.schedule_id,
            asset_util_stats.c.asset_id,
            asset_util_stats.c.asset_type,
            z_score(asset_util_stats.c.util_avg).label('asset_util_grade'),
            z_score(asset_util_stats.c.util_std).label('asset_util_flux')
        ).subquery()

        schedule_util = session.query(
            asset_util.c.schedule_id,
            asset_util.c.asset_type,
            normalized_avg(asset_util.c.asset_util_grade).label('schedule_util_grade'),
            normalized_avg(asset_util.c.asset_util_flux).label('schedule_util_flux')
        ).group_by(
            asset_util.c.schedule_id,
            asset_util.c.asset_type, # calculate normalized utilization for each asset class (normalize within the asset class)
            asset_util.c.asset_util_grade,
            asset_util.c.asset_util_flux
        ).subquery()

        # calculate the workload distribution for each schedule
        workload_distribution = session.query(
            schedule_util.c.schedule_id,
            (1 - (self.spread_factor * func.avg(schedule_util.c.schedule_util_grade) + self.stability_factor * func.avg(schedule_util.c.schedule_util_flux))).label('measure') # The averaging is to combine the workload distribution across all asset classes
        ).group_by(schedule_util.c.schedule_id, *group_by) # combined workload distribution across all asset classes (unless the 'group_by' argument is specified, in which case we calculate workload distribution for each group specified)

        return workload_distribution


    def grades_query(self, schedule_group: str, filters: list[BinaryExpression]=[]):
        session = get_db_session()
        workload_distribution = self.measures_query(
            filters=[Schedule.group_name==schedule_group] + filters
        ).subquery()

        # min/max normalize the "workload_dist" column of all schedules in this group
        grades_query = session.query(
            workload_distribution.c.schedule_id,
            min_max_norm(workload_distribution.c.measure).label('grade')
        ).group_by(workload_distribution.c.schedule_id, workload_distribution.c.measure)

        return grades_query