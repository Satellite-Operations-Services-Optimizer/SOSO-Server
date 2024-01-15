from performance_metrics import *
from app_config import get_db_session
from app_config.database.mapping import Schedule

session = get_db_session()    
    
schedule_name = "test_single_sat_single_gs_valid_schedule"
schedule = session.query(Schedule).filter_by(name=schedule_name).first()

resource_util = ResourceUtilizationMetric(1.0)
resource_util_measure = resource_util.measure(schedule.id)
resource_util_score = resource_util.score(schedule.id)

print(f"Schedule {schedule.name} has resource-util measure: {resource_util_measure} and score: {resource_util_score}")