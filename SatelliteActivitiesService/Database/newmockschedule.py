from datetime import datetime, timedelta
from Database.db_model import image_activity, satellite_activity_schedule, maintenance_activity, satellite_outage_request, outage_activity

# Create 2 sample schedules
schedules = [
    satellite_activity_schedule(id=1, satellite_id=1, start_time=datetime(2023, 11, 5, 8, 0),end_time=datetime(2023, 11, 5, 15, 0),status=1),
    satellite_activity_schedule(id=2, satellite_id=2, start_time=datetime(2023, 11, 5, 8, 0),end_time=datetime(2023, 11, 5, 15, 0),status=1)
]

# Create 3 sample image_activity and 3 sample satellite_activity
image_activities = [
    image_activity(id=1, image_resolution=10, priority=1, image_time=datetime(2023, 11, 5, 8, 0), satellite_activity_schedule_id=1),
    image_activity(id=2, image_resolution=8, priority=2, image_time=datetime(2023, 11, 5, 10, 0), satellite_activity_schedule_id=1),
    image_activity(id=3, image_resolution=12, priority=3, image_time=datetime(2023, 11, 6, 8, 0), satellite_activity_schedule_id=2)
]

satellite_activities = [
    maintenance_activity(id=1, satellite_id=1, start_time=datetime(2023, 11, 5, 8, 0), end_time=datetime(2023, 11, 5, 12, 0), status=1, description="oribit",payload_flag=True,satellite_activity_schedule_id=1,priority=1,duration=timedelta(seconds=180)),
    maintenance_activity(id=2, satellite_id=2, start_time=datetime(2023, 11, 5, 10, 0), end_time=datetime(2023, 11, 5, 14, 0), status=2, description="oribit",payload_flag=True,satellite_activity_schedule_id=2,priority=1,duration=timedelta(seconds=110)),
    maintenance_activity(id=3, satellite_id=1, start_time=datetime(2023, 11, 6, 8, 0), end_time=datetime(2023, 11, 6, 12, 0), status=3, description="battery",payload_flag=False,satellite_activity_schedule_id=1,priority=1,duration=timedelta(seconds=300))
]

outage_activities = [
    
    outage_activity(id=1, satellite_id=1, start_time=datetime(2023, 11, 5, 12, 0), end_time=datetime(2023, 11, 5, 14, 0), status=1,satellite_activity_schedule_id=1),
    outage_activity(id=2, satellite_id=2, start_time=datetime(2023, 11, 5, 14, 0), end_time=datetime(2023, 11, 5, 16, 0), status=2,satellite_activity_schedule_id=2)
]
options = []
def get_schedule(sat_id: int, start: datetime, end: datetime):
    options = []
    for i in range(len(schedules)):       
        if(schedules[i].satellite_id == sat_id and schedules[i].start_time < start, schedules[i].end_time > end): #maybe the schedule doesn't need to end after the window  closes if every activity can be scheduled
           options.append(schedules[i])
        return options 

def get_scheduled_maintenence(sched_id: int):
    options = []
    for i in range(len(satellite_activities)):       
        if(satellite_activities[i].satellite_activity_schedule_id == sched_id ): #maybe the schedule doesn't need to end after the window  closes if every activity can be scheduled
           options.append(schedules[i])
        return options 
    
def get_scheduled_outage(sched_id: int):
    options = []
    for i in range(len(outage_activities)):       
        if(outage_activities[i].satellite_activity_schedule_id == sched_id ): #maybe the schedule doesn't need to end after the window  closes if every activity can be scheduled
           options.append(outage_activities[i])
        return options 
    
def get_scheduled_image(sched_id: int):
    options = []
    for i in range(len(image_activities)):       
        if(image_activities[i].satellite_activity_schedule_id == sched_id ): #maybe the schedule doesn't need to end after the window  closes if every activity can be scheduled
           options.append(image_activities[i])
        return options 

if __name__ == "__main__":
    for i in range(len(image_activities)):
        print('\n',image_activities[i])
    for i in range(len(satellite_activities)):
        print('\n',satellite_activities[1])
    for i in range(len(outage_activities)):
        print('\n',outage_activities[i])
    for i in range(len(schedules)):
        print('\n',schedules[i])