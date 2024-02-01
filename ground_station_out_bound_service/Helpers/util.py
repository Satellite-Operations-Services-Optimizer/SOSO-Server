from typing import Optional
from app_config.logs import logging
from app_config.database import ImageOrder, MaintenanceOrder, OutageSchedule, ScheduledImaging, ScheduledContact
from Helpers.data import schedule
from data import get_outbound_schedule, update_outbound_schedule, create_outbound_schedule, get_scheduled_contact, get_image_request, get_scheduled_image, get_maintenance_request, get_scheduled_maintenance, get_schedule, get_satellite, get_ground_station_request, get_ground_station, update_contact_with_downlink
from data import scheduled_images, scheduled_maintenance, scheduled_outages, maintenance_order
from ground_station_out_bound_service.models.ScheduleModel import satellite_schedule, image_activity, maintenance_activity, downlink_activity, ground_station_request, downlink_image
import json

def add_maintenance_activity(maint_activity: maintenance_activity, contact_id: int, maint_order: MaintenanceOrder):
    
    outbound_schedule = get_outbound_schedule(contact_id)
    
    if(outbound_schedule == None):
        window = [maint_activity.start_time, maint_activity.start_time + maint_activity.duration]
        satellite = get_satellite(maint_order.asset_id).name
        outbound_schedule = create_outbound_schedule(contact_id = contact_id, 
                                                    satellite_name = get_satellite(maint_order.asset_id).name , 
                                                    actiivity_window =  window, 
                                                    maintenance_activity = maint_activity )
    else:
        outbound_schedule.maintenance_activities.append(maint_activity)
        if(outbound_schedule.window[0] > maint_activity.start_time):
            outbound_schedule.window[0] = maint_activity.start_time
        if(outbound_schedule.window[0] < maint_activity.start_time + maint_activity.duration):
            outbound_schedule.window[0] = maint_activity.start_time + maint_activity.duration
    
    updated_outbound_schedule = update_outbound_schedule(outbound_schedule);
    
    return updated_outbound_schedule

# the returned outbound schedule will have the image activity/cature, uplink and downlink information
def add_image_activity(imaging_activity: image_activity, image_order: ImageOrder, scheduled_image: ScheduledImaging):
    
    outbound_schedule = get_outbound_schedule(scheduled_image.uplink_contact_id)
    window = [imaging_activity.start_time, imaging_activity.start_time + image_order.duration]
       
    if(outbound_schedule == None):    
        satellite = get_satellite(scheduled_image.asset_id).name
        outbound_schedule = create_outbound_schedule(contact_id = scheduled_image.uplink_contact_id, 
                                                    satellite_name = satellite, 
                                                    actiivity_window =  window, 
                                                    maintenance_activity = imaging_activity )
    else:
        outbound_schedule.image_activities.append(imaging_activity)
        if(outbound_schedule.window[0] > window[0]):
            outbound_schedule.window[0] = window[0]
        if(outbound_schedule.window[0] < window[1]):
            outbound_schedule.window[0] = window[1]
    
    outbound_schedule= update_outbound_schedule(outbound_schedule);
    
    return outbound_schedule

def add_downlink_activity(scheduled_image: ScheduledImaging):
    
    uplinked_outbound_schedule = get_outbound_schedule(scheduled_image.uplink_contact_id)  
    
    scheduled_contact = get_scheduled_contact(uplinked_outbound_schedule.contact_id)
    
    if(uplinked_outbound_schedule.downlink_activity == None):        
        image_ids = [scheduled_image.id]
    else:
        image_ids.append(scheduled_image.id)
        
    downlink = downlink_activity(image_id = image_ids ,
                                    start_time = scheduled_contact.start_time,
                                    downlink_stop = scheduled_contact.start_time + scheduled_contact.duration)
    
    ###################################################################
    
    # should the downlink time be conted towards the activity window??
    
    ###################################################################
    
    window = [downlink.start_time, downlink.downlink_stop]
       
    uplinked_outbound_schedule.downlink_activities.append(downlink)
    if(uplinked_outbound_schedule.window[0] > window[0]):
        uplinked_outbound_schedule.window[0] = window[0]
    if(uplinked_outbound_schedule.window[0] < window[1]):
        uplinked_outbound_schedule.window[0] = window[1]
    
         
    # for the satellite to send  
            
    uplinked_outbound_schedule= update_outbound_schedule(uplinked_outbound_schedule)
     
    return uplinked_outbound_schedule

# add downlink images to groundstation schedule(scheduled_contact)
def add_downlink_image(scheduled_image: ScheduledImaging):
    
    #for contact when the downlink occurs 
    downlink_contact = get_scheduled_contact(scheduled_image.downlink_contact_id)
    
    ##################################################################   
    # time to downlink images should be corrected after confirmation #
    ##################################################################
    
    downlink_rate = get_ground_station(downlink_contact.groundstation_id).downlink_rate_mbps
     
    downlink = downlink_image(image_id = scheduled_image.id ,
                                    duration_of_downlink= scheduled_image.downlink_size/downlink_rate, ##### wrong #######
                                    size_of_image = scheduled_image.downlink_size)  ## need to confirm
    
    if(downlink_contact.downlink_images == None):        
        downlink_contact.downlink_images = [downlink]
    else:
        downlink_contact.downlink_images.append(scheduled_image.id)
    
    downlink_contact = update_contact_with_downlink(downlink_contact)
    
    return downlink_contact


# def make_image_activity(image_id: int, state: str):
#     image_order = get_image_request(image_id)
#     scheduled_image = get_scheduled_image(image_id, state)
    
#     activity = image_activity(image_id = image_id, type = image_order.image_res,
#                               priority = image_order.priority, start_time = scheduled_image.downlink_start)
#     return activity

# def make_maintenance_activity(maintenance_id, state: str):
#     maintenance_order = get_maintenance_request(maintenance_id)
#     scheduled_maintenance = get_scheduled_maintenance(maintenance_id, state)
    
#     activity = image_activity(activity_id = maintenance_id, description = maintenance_order.description,
#                               priority = maintenance_order.priority, start_time = scheduled_maintenance.maintenance_start,
#                               payload_flag = maintenance_order.operations_flag, duration = maintenance_order.duration)
#     return activity


# # create downlink activities, add them to the schedule

# def make_satellite_schedule(schedule_id: int, activities_image: list[image_activity], activities_maintenance: list[maintenance_activity]):
#     active_window = [min(activities_image + activities_maintenance, key=lambda x: x.start_time).start_time,
#                      max(activities_image + activities_maintenance, key=lambda x: x.start_time).start_time ]
#     schedule = get_schedule(schedule_id)
#     satellite = get_satellite(schedule.satellite_id)
    
#     satellite_schedule_to_send = satellite_schedule(satellite_name = satellite.name, schedule_id = schedule.id, activity_window = active_window,
#                                                     image_activities = activities_image, maintenance_activities = activities_maintenance)
    
#     return satellite_schedule_to_send

# def make_ground_station_request(request_id: int, activities: list[downlink_image]):
#     gs_request = get_ground_station_request(request_id)
#     ground_station = get_ground_station(gs_request.station_id)
#     schedule = get_schedule(gs_request.schedule_id)
#     satellite = get_satellite(schedule.satellite_id)
#     ground_station_request_to_send = ground_station_request(station_name = ground_station.name, satellite = satellite.name, acquisition_of_signal = gs_request.signal_aquisition,
#                                                             loss_of_signal = gs_request.signal_loss, satellite_schedule_id = gs_request.schedule_id, images_to_be_downlinked = activities)
#     return ground_station_request_to_send

# def parse_created_event(request_body: json):
    
    

