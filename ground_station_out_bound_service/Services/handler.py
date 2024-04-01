#######################################################
#  All handler methods below have been depricated. 
#  the current implemenation creates and sends schedules 
#  when contact time approaches instead of iteratively 
#  bulding the schedule wasting resources on database  
#  calls and risking data inconsistency.
#########################################################

from app_config import logging
from ground_station_out_bound_service.Helpers.data import get_schedule, get_satellite, get_schedule_request, get_scheduled_maintenance, get_scheduled_image, get_maintenance_order, get_image_order, get_scheduled_contact, get_all_scheduled_images_from_contact, get_outbound_schedule, update_outbound_schedule
from ground_station_out_bound_service.Helpers.util import  add_maintenance_activity, add_image_activity, add_downlink_activity, add_downlink_image
from ground_station_out_bound_service.models.ScheduleModel import satellite_schedule, maintenance_activity, image_activity, downlink_activity, outbound_schedule, ground_station_request
  
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
                              payload_flag = maintenance_order.payload_outage, duration = maintenance_request.duration)
    
    #add maintenance to uplink contact
    outbound_schedule = add_maintenance_activity(maintenance, scheduled_maintenance.uplink_contact_id, maintenance_order)
    
    return outbound_schedule

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
    
    #add image to uplink contact    
    outbound_schedule_with_image = add_image_activity(imaging, image_order, scheduled_imaging)
    
    
    # add when satellite will downlink to downlink contact 
    outbound_schedule_with_downlink = add_downlink_activity(scheduled_imaging)
    
    #add donwlink to downlink contact
    ground_station_schedule_with_downlink = add_downlink_image(scheduled_imaging)
    
    
    return outbound_schedule_with_downlink, ground_station_schedule_with_downlink



def handle_message(body):    
    print("handler function called!")
    
    request_body    = body["body"]
    request_details = body["details"]
    request_id = request_body["request_id"]
    
    logging.info(f"Recieved {request_body}")
    
    pass


 