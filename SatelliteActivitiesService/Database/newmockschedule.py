from datetime import datetime, timedelta
from config.database import scheduled_images, scheduled_outages, scheduled_maintenance, schedule
# Create 2 sample schedules
schedules = [
    schedule(id=1, satellite_id=1, ground_station_id = 1, start_time=datetime(2023, 11, 5, 8, 0),asset_type = "satellite", end_time=datetime(2023, 11, 5, 15, 0), status = "not sent"),
    schedule(id=2, satellite_id=2, ground_station_id = 1, start_time=datetime(2023, 11, 5, 8, 0),asset_type = "satellite", end_time=datetime(2023, 11, 5, 15, 0),status = "not sent")
]

# Create 3 sample image_activity and 3 sample satellite_activity
scheduled_images = [
    scheduled_images(image_id=1, request_id = 1, downlink_start=datetime(2023, 11, 5, 8, 0), downlink_end=datetime(2023, 11, 5, 9, 0),data_size = 100.0, schedule_type = 1, status="scheduled", schedule_id=1),
    scheduled_images(image_id=2, request_id = 1, downlink_start=datetime(2023, 11, 5, 10, 0), downlink_end=datetime(2023, 11, 5, 11, 0),data_size = 100.0, schedule_type = 1, status="scheduled", schedule_id=1),
    scheduled_images(image_id=3, request_id = 1, downlink_start=datetime(2023, 11, 6, 8, 0), downlink_end=datetime(2023, 11, 6, 10, 0),data_size = 100.0, schedule_type = 1, status="scheduled", schedule_id=2)
]

scheduled_maintenances = [
    scheduled_maintenance(maintenance_id=1, maintenance_start=datetime(2023, 11, 5, 8, 0), maintenance_end=datetime(2023, 11, 5, 12, 0), status="scheduled", description="oribit",schedule_id=1,priority=1, repetition_number = 1),
    scheduled_maintenance(naimtenance_id=2, maintenance_start=datetime(2023, 11, 5, 10, 0), maintenance_end=datetime(2023, 11, 5, 14, 0), status="scheduled", description="oribit",schedule_id=2,priority=1, repetition_number = 2),
    scheduled_maintenance(maintenance_id=3, maintenance_start=datetime(2023, 11, 6, 8, 0), maintenance_end=datetime(2023, 11, 6, 12, 0), status="scheduled", description="battery",schedule_id=1,priority=1, repitition_number = 1)
]

scheduled_outages = [
    
    scheduled_outages(outage_id=1, outage_start=datetime(2023, 11, 5, 12, 0), outage_end=datetime(2023, 11, 5, 14, 0), status="scheduled",schedule_id=1),
    scheduled_outages(outage_id=2, outage_start=datetime(2023, 11, 5, 14, 0), outage_end=datetime(2023, 11, 5, 16, 0), status="scheduled",schedule_id=2)
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
    for i in range(len(scheduled_maintenances)):       
        if(scheduled_maintenances[i].schedule_id == sched_id ):
           options.append(schedules[i])
        return options 
    
def get_scheduled_outage(sched_id: int):
    options = []
    for i in range(len(scheduled_outages)):       
        if(scheduled_outages[i].schedule_id == sched_id ):
           options.append(scheduled_outages[i])
        return options 
    
def get_scheduled_image(sched_id: int):
    options = []
    for i in range(len(scheduled_images)):       
        if(scheduled_images[i].schedule_id == sched_id ):
           options.append(scheduled_images[i])
        return options 

if __name__ == "__main__":
    for i in range(len(scheduled_images)):
        print('\n',scheduled_images[i])
    for i in range(len(scheduled_maintenances)):
        print('\n',scheduled_maintenances[1])
    for i in range(len(scheduled_outages)):
        print('\n',scheduled_outages[i])
    for i in range(len(schedules)):
        print('\n',schedules[i])