from performance_metrics import *
from app_config.database.mapping import Schedule

    
    
resource_util = ResourceUtilizationMetric(1.0)

schedule = Schedule.filter_by(name="")
resource_util.measure()