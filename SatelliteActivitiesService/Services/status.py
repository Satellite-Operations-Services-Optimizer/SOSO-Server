from typing import Optional, Union
from config.database import db_session
from Database.db_curd import *

status_data = {
    "scheduled_request": {
        Requestobject
    },
    "repeat": {
        "single_activity[0]": {
            
        },
        "single_activity[1]": {
            
        }
    }
}
class single_activity:
    repeat_number: Optional[int] = None
    status: str

class Request_status:
    scheduled_request: Union[maintenance_order, image_order, outage_order]
    repeat: list[single_activity]

def get_image_status(image_id: int):
    activities = get_all_repeats_from_image_request(db_session, image_id)
    list_of_repeats = get_repeated_activities(activities)     
    
    request = get_image_request(db_session, image_id)
    request_status = Request_status(scheduled_request = request, repeat = list_of_repeats) 
    return request_status
    
def get_maintenance_status(maintenance_id: int):
    activities = get_all_repeats_from_maintenance_request(db_session, maintenance_id)
    list_of_repeats = get_repeated_activities(activities)     
    
    request = get_maintenence_request(db_session, maintenance_id)
    request_status = Request_status(scheduled_request = request, repeat = list_of_repeats) 
    return request_status

def get_outage_status(outage_id: int):
    
    outage_activity = get_scheduled_outage(db_session, outage_id)
      
    request = get_outage_request(db_session, outage_id)
    request_status = Request_status(scheduled_request = request, repeat = [outage_activity]) 
    return request_status


def get_repeated_activities(activities: list):
    
    list_of_repeats = []
    for i in range(len(activities)):
        repeat_activity = single_activity(repeat_number = i+1, status = activities[i].status)
        list_of_repeats.append(repeat_activity)
     
    return list_of_repeats