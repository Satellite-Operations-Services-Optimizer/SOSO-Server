from sqlalchemy import Column
from sqlalchemy.orm import aliased, Query
from sqlalchemy.sql import BinaryExpression, ClauseElement, Window
from sqlalchemy.sql.expression import func, BinaryExpression

from app_config import get_db_session
from app_config.database.mapping import SatelliteStateChange, Schedule
from base import PerformanceMetric
from utils import min_max_norm_column
from resource_util_metric import ResourceUtilizationMetric


class WorkloadDistributionMetric(PerformanceMetric):
    resource_util: ResourceUtilizationMetric
    def __init__(self, weight: float):
        super().__init__(weight)
        self.resource_util = ResourceUtilizationMetric(1.0);

    def measures_subquery(self, schedule_id):
        asset_resource_util_timelines = self.resource_util.asset_resource_util_timelines_subquery(
            filters=[Schedule.id==schedule_id]
        )

    def scores_subquery(self, schedule_id):
        pass