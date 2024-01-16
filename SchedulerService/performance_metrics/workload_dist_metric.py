from sqlalchemy.sql.expression import func

from app_config import get_db_session
from app_config.database.mapping import Schedule
from .base import PerformanceMetric
from .utils import min_max_norm, z_score
from .resource_util_metric import ResourceUtilizationMetric


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
    Then we combine across asset class
    """
    resource_util_measure: ResourceUtilizationMetric
    def __init__(self, weight: float = 1.0, spread_factor: float = 0.5, stability_factor: float = 0.5):
        super().__init__(weight)
        self.resource_util = ResourceUtilizationMetric(1.0);

    def measures_query(self, schedule_id):
        session = get_db_session()
        asset_resource_util_timelines = self.resource_util_measure.asset_resource_util_timelines_query(
            filters=[Schedule.id==schedule_id]
        ).subquery()

        # calculate the average and standard deviation of resource utilization for each satellite in the schedule
        asset_util = session.query(
            asset_resource_util_timelines.c.schedule_id,
            asset_resource_util_timelines.c.asset_id,
            asset_resource_util_timelines.c.asset_type,
            func.avg(asset_resource_util_timelines.c.resource_util).label('asset_util_avg'),
            func.stddev(asset_resource_util_timelines.c.resource_util).label('asset_util_std')
        ).group_by(
            asset_resource_util_timelines.c.schedule_id,
            asset_resource_util_timelines.c.asset_id,
            asset_resource_util_timelines.c.asset_type
        ).subquery()

        # calculate the asset_util_grade (i.e. z-score of asset_util_avg) and asset_util_flux (i.e. z-score of asset_util_std)
        asset_util_grade = session.query(
            asset_util.c.schedule_id,
            asset_util.c.asset_id,
            asset_util.c.asset_type,
            z_score(asset_util.c.asset_util_avg).label('asset_util_grade'),
            z_score(asset_util.c.asset_util_std).label('asset_util_flux')
        ).subquery()


    def grades_query(self, schedule_id):
        pass