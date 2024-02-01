from app_config import logging
from ground_station_out_bound_service.Helpers.data import get_schedule, get_satellite, get_schedule_request, get_scheduled_maintenance, get_scheduled_image, get_maintenance_order, get_image_order, get_scheduled_contact, get_all_scheduled_images_from_contact, get_outbound_schedule, update_outbound_schedule
from ground_station_out_bound_service.Helpers.util import get_active_activities, add_maintenance_activity, add_image_activity, add_downlink_activity, add_downlink_image
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
                              payload_flag = maintenance_order.operations_flag, duration = maintenance_request.duration)
    
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



def handle_cancelled(body):    
    print("cancelled function called!")
    
    request_body    = body["body"]
    request_details = body["details"]
    request_id = request_body["request_id"]
    
    logging.info(f"Recieved {request_body}")
    
    # activity cancelled
    # schedule cancelled
    pass


# def handle_contact(body): 
#     print("contact function called!")
    
#     request_body    = body["body"]
#     request_details = body["details"]
#     request_id = request_body["request_id"] # should be the scheduled_contact id
    
#     logging.info(f"Recieved {request_body}")
    
#     # add downlink to sat schedule 
    
#     scheduled_contact = get_scheduled_contact(request_id)
#     scheduled_images = get_all_scheduled_images_from_contact(request_id)
#     image_ids = []
    
#     for image in scheduled_images:
#         image_ids.append(image.id)
        
#     downlink = downlink_activity(image_id = image_ids,
#                                  start_time = scheduled_contact.start_time,
#                                  downlink_stop = scheduled_contact.start_time + scheduled_contact.duration)
    
#     # add to the gs request with the correct uplink contact in scheduled_contact
    
#     pass


# def handle_message(body):
#     print("Handler function called!")
    
#     request_body    = body["body"]
#     request_details = body["details"]

#     logging.info(f"Recieved {request_body}")
    
#     # created event
#     schedule_id = request_body["created"]["schedule_id"]
#     order_id = request_body["created"]["order_id"]
#     activities_created = request_body["created"]["activities_created"]
    
#     schedule = get_schedule(request_body["schedule_id"])
#     logging.info(f"Retrieved schedule")
    
#     satellite_activities = get_active_activities(schedule)    
#     logging.info(f"compiled all activities in schedule")
    
#     edge_activities = [satellite_activities.image_activities[0], satellite_activities.image_activities[]]
    
#     satellite_schedule_to_send = satellite_schedule(satellite_name = get_satellite(schedule.satellite_id).name, schedule_id = schedule.id, activity_window = ,
#                                                     image_activities = satellite_activities.image_activities,
#                                                     maintenance_activities = satellite_activities.maintenance_activities,
#                                                     downlink_activities = satellite_activities.downlink_activities)
    
#     send_satellite_schedule(satellite_schedule_to_send)


# def send_schedules(outboundschedule: outbound_schedule = None, gs_request: ground_station_request = None):
#     if (outboundschedule != None):
#         schedule = satellite_schedule(satellite_name = outbound_schedule.satellite_name,
#                                     schedule_id = outbound_schedule.id,
#                                     activity_window = outbound_schedule.activity_window,
#                                     image_activities = outbound_schedule.image_activities,
#                                     maintenance_activities = outbound_schedule.maintenance_activities,
#                                     downlink_activities = outbound_schedule.downlink_activities)
#         response = send_satellite_schedule(schedule)
#         if response.status_code == 200:
#             #change status to sent
#             print("satellite schedule sent successfully!")
#             outboundschedule.schedule_status = "sent_to_gs"
#             update_outbound_schedule(outboundschedule)           
            
#         else:
#             return response
#     if(gs_request != None):
#         response = send_ground_station_request(gs_request)
#         if response.status_code == 200:
#             #change status to sent
#             print("ground station request sent successfully!")
#         else:
#             return response
#     pass
 