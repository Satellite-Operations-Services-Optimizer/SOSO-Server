from app_config import logging
from Helpers.data import get_schedule, get_satellite, get_schedule_request, get_scheduled_maintenance, get_scheduled_image, get_maintenance_order, get_image_order, get_scheduled_contact, get_all_scheduled_images_from_contact
from Helpers.util import get_active_activities
from Models.ScheduleModel import satellite_schedule, maintenance_activity, image_activity, downlink_activity
from services.contact_ground_station import send_ground_station_request, send_satellite_schedule


def handle_message(body):
    print("Handler function called!")
    
    request_body    = body["body"]
    request_details = body["details"]

    logging.info(f"Recieved {request_body}")
    
    # created event
    schedule_id = request_body["created"]["schedule_id"]
    order_id = request_body["created"]["order_id"]
    activities_created = request_body["created"]["activities_created"]
    
    schedule = get_schedule(request_body["schedule_id"])
    logging.info(f"Retrieved schedule")
    
    satellite_activities = get_active_activities(schedule)    
    logging.info(f"compiled all activities in schedule")
    
    edge_activities = [satellite_activities.image_activities[0], satellite_activities.image_activities[]]
    
    satellite_schedule_to_send = satellite_schedule(satellite_name = get_satellite(schedule.satellite_id).name, schedule_id = schedule.id, activity_window = ,
                                                    image_activities = satellite_activities.image_activities,
                                                    maintenance_activities = satellite_activities.maintenance_activities,
                                                    downlink_activities = satellite_activities.downlink_activities)
    
    send_satellite_schedule(satellite_schedule_to_send)
    
def handle_maintenance(body):
    
    print("Handler function called!")
    
    request_body    = body["body"]
    request_details = body["details"]
    request_id = request_body["request_id"]
    
    logging.info(f"Recieved {request_body}")
    
    maintenance_request = get_schedule_request(request_id, "scheduled")
    maintenance_order = get_maintenance_order(maintenance_request.order_id)  
    scheduled_maintenance = get_scheduled_maintenance(request_id)
    
    maintenance = maintenance_activity(activity_id = scheduled_maintenance.id, description = maintenance_order.description,
                              priority = maintenance_request.priority, start_time = scheduled_maintenance.start_time,
                              payload_flag = maintenance_order.operations_flag, duration = maintenance_request.duration)
     
    # add to the gs request with the correct uplink contact in scheduled_contact
    #     
    
    return maintenance

def handle_imaging(body):
    
    print("imaging function called!")
    
    request_body    = body["body"]
    request_details = body["details"]
    request_id = request_body["request_id"]
    
    logging.info(f"Recieved {request_body}")
    
    image_request = get_schedule_request(request_id, "scheduled")    
    scheduled_imaging = get_scheduled_image(request_id)
    image_order = get_image_order(image_request.order_id)
   
    imaging = image_activity(image_id = scheduled_imaging.id, type = image_order.image_res,
                              priority = image_request.priority, start_time = scheduled_imaging.start_time)
             
    return imaging

def handle_contact(body): 
    print("contact function called!")
    
    request_body    = body["body"]
    request_details = body["details"]
    request_id = request_body["request_id"] # should be the scheduled_contact id
    
    logging.info(f"Recieved {request_body}")
    
    # add downlink to sat schedule 
    
    scheduled_contact = get_scheduled_contact(request_id)
    scheduled_images = get_all_scheduled_images_from_contact(request_id)
    image_ids = []
    
    for image in scheduled_images:
        image_ids.append(image.id)
        
    downlink = downlink_activity(image_id = image_ids,
                                 start_time = scheduled_contact.start_time,
                                 downlink_stop = scheduled_contact.start_time + scheduled_contact.duration)
    
    # add to the gs request with the correct uplink contact in scheduled_contact
    
    pass

def handle_cancelled(body):    
    print("cancelled function called!")
    
    request_body    = body["body"]
    request_details = body["details"]
    request_id = request_body["request_id"]
    
    logging.info(f"Recieved {request_body}")
    pass
    