from performance_metrics import *
from app_config import get_db_session
from app_config.database.mapping import Schedule

session = get_db_session()    
    
schedule_name = "test_single_sat_single_gs_valid_schedule"
schedule = session.query(Schedule).filter_by(name=schedule_name).first()

throughput = ThroughputMetric()
throughput_measure = throughput.measure(schedule.id)
throughput_grade = throughput.grade(schedule.id)

resource_util = ResourceUtilizationMetric()
resource_util_measure = resource_util.measure(schedule.id)
resource_util_grade = resource_util.grade(schedule.id)

workload_dist = WorkloadDistributionMetric()
workload_dist_measure = workload_dist.measure(schedule.id)
workload_dist_grade = workload_dist.grade(schedule.id)

print(f"""
Schedule name: {schedule.name}

Pefrormance Metric: Throughput
measure: {throughput_measure}
grade: {throughput_grade}

Performance Metric: Resource Utilization
measure: {resource_util_measure}
grade: {resource_util_grade}

Performance Metric: Workload Distribution
measure: {workload_dist_measure}
grade: {workload_dist_grade}
""")