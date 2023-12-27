from datetime import datetime, timedelta
from config.database import db_session
from Models.RequestModel import ActivityRequest
from Models.ResponseModel import scheduling_options
from Helpers.db_curd import maintenance_order, get_all_schedules_in_window, get_all_scheduled_images_from_schedule, get_all_scheduled_maintenence_from_schedule, get_all_scheduled_outage_from_schedule 

class scheduled_activity:
    def __init__(self, schedule_id: int, start_time: datetime, end_time: datetime):
        self.schedule_id = schedule_id
        self.start_time = start_time
        self.end_time = end_time 
 
def get_activities(schedules: list): 
    list_of_activities = []
    
    # **********to be tested with realdata*********   
    
    
    for j in range(len(schedules)):
        
        # **************************************
        
        image_activities = get_all_scheduled_images_from_schedule(db_session, schedules[j].id)
        list_of_activities.extend(image_activities)
        
        maintenence_activities = get_all_scheduled_maintenence_from_schedule(db_session, schedules[j].id)
        list_of_activities.extend(maintenence_activities)
        
        outage_activities = get_all_scheduled_outage_from_schedule(db_session, schedules[j].id)
        list_of_activities.extend(outage_activities)
        
        
        # **************************************
        
        
            
    sorted_schedules = sorted(list_of_activities, key=lambda x: x.start_time)
    print(f"sorted activities are {sorted_schedules}")
    print("\n Activities in the Target schedules are:\n")
    
    for activity in sorted_schedules:
        print(activity.__dict__)
    return sorted_schedules 