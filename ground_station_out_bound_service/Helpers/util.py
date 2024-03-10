from typing import Optional
from app_config.logs import logging
from app_config.database.mapping import ScheduledImaging, ScheduledMaintenance
from ground_station_out_bound_service.Helpers.data import get_outbound_schedule, update_outbound_schedule, create_outbound_schedule_with_image, create_outbound_schedule_with_maintenance, get_scheduled_contact,  get_satellite,  get_ground_station,  get_maintenance_order, get_schedule_request, get_image_order
from ground_station_out_bound_service.models.ScheduleModel import  image_activity, maintenance_activity, downlink_activity,  downlink_image
from fastapi.encoders import jsonable_encoder
import json


def add_maintenance_activity(scheduled_maintenance: ScheduledMaintenance):
    
    maintenance_request = get_schedule_request(scheduled_maintenance.request_id, "scheduled")
    if(maintenance_request != None):
        maintenance_order = get_maintenance_order(maintenance_request.order_id)  
    
        maint_activity = maintenance_activity(activity_id = scheduled_maintenance.id, description = maintenance_order.description,
                                priority = maintenance_request.priority, start_time = scheduled_maintenance.start_time,
                                payload_flag = maintenance_order.operations_flag, duration = maintenance_request.duration)
        
        contact_id = scheduled_maintenance.uplink_contact_id
        outbound_schedule = get_outbound_schedule(contact_id)
        
        if(outbound_schedule == None):
            window = [maint_activity.start_time, maint_activity.start_time + maint_activity.duration]
            satellite = get_satellite(maintenance_order.asset_id)
            outbound_schedule = create_outbound_schedule_with_maintenance(contact_id = contact_id, 
                                                        satellite_name = satellite.name , 
                                                        active_window =  window, 
                                                        maintenance = [maint_activity] )
        else:
            
            if(outbound_schedule.maintenance_activities == None):
                outbound_schedule.maintenance_activities = [jsonable_encoder(maint_activity)]
            else:
                outbound_schedule.maintenance_activities.append(maint_activity)
            if(outbound_schedule.activity_window[0] > maint_activity.start_time):
                outbound_schedule.activity_window[0] = maint_activity.start_time
            if(outbound_schedule.activity_window[0] < maint_activity.start_time + maint_activity.duration):
                outbound_schedule.activity_window[0] = maint_activity.start_time + maint_activity.duration
        
        updated_outbound_schedule = update_outbound_schedule(outbound_schedule);
        
        return updated_outbound_schedule
    return None

# the returned outbound schedule will have the image activity/cature, uplink and downlink information
def add_image_activity(scheduled_image: ScheduledImaging):
    
    image_request = get_schedule_request(scheduled_image.request_id, "scheduled")
    if(image_request != None):    
        image_order = get_image_order(image_request.order_id)            
                   
        imaging_activity = image_activity(image_id = scheduled_image.id, 
                                          image_type = image_order.image_type,
                                          priority = image_request.priority,
                                          start_time = scheduled_image.start_time)
        
        
        outbound_schedule = get_outbound_schedule(scheduled_image.uplink_contact_id)
        window = [imaging_activity.start_time, imaging_activity.start_time + image_order.duration]
        
        if(outbound_schedule == None):    
            satellite = get_satellite(scheduled_image.asset_id)
            outbound_schedule = create_outbound_schedule_with_image(contact_id = scheduled_image.uplink_contact_id, 
                                                        satellite_name = satellite.name, 
                                                        active_window =  window, 
                                                        image = imaging_activity )
        else:
            if(outbound_schedule.image_activities == None):
                outbound_schedule.image_activities = [jsonable_encoder(imaging_activity)]
            else:
                outbound_schedule.image_activities.append(imaging_activity)
            if(outbound_schedule.activity_window[0] > window[0]):
                outbound_schedule.activity_window[0] = window[0]
            if(outbound_schedule.activity_window[0] < window[1]):
                outbound_schedule.activity_window[0] = window[1]
        
        outbound_schedule= update_outbound_schedule(outbound_schedule);
    
        return outbound_schedule
    return None

def add_downlink_activity(scheduled_image: ScheduledImaging):
    
    uplinked_outbound_schedule = get_outbound_schedule(scheduled_image.uplink_contact_id)  
    
    scheduled_contact = get_scheduled_contact(uplinked_outbound_schedule.contact_id)
    
    if(uplinked_outbound_schedule.downlink_activities == None):        
        image_ids = [scheduled_image.id]
        downlink = downlink_activity(image_id = image_ids ,
                                    start_time = scheduled_contact.start_time,
                                    downlink_stop = scheduled_contact.start_time + scheduled_contact.duration)
    else:
        image_ids = uplinked_outbound_schedule.downlink_activities[0]["image_id"]
        image_ids.append(scheduled_image.id)
        
        downlink = downlink_activity(image_id = image_ids ,
                                    start_time = scheduled_contact.start_time,
                                    downlink_stop = scheduled_contact.start_time + scheduled_contact.duration)
        
    
        
    window = [downlink.start_time, downlink.downlink_stop]
    
    if(uplinked_outbound_schedule.downlink_activities == None):
        uplinked_outbound_schedule.downlink_activities = [jsonable_encoder(downlink)]
    else:
        uplinked_outbound_schedule.downlink_activities.append(downlink)
    if(uplinked_outbound_schedule.activity_window[0] > window[0]):
        uplinked_outbound_schedule.activity_window[0] = window[0]
    if(uplinked_outbound_schedule.activity_window[0] < window[1]):
        uplinked_outbound_schedule.activity_window[0] = window[1]
    
         
    # for the satellite to send  
            
    uplinked_outbound_schedule= update_outbound_schedule(uplinked_outbound_schedule)
     
    return uplinked_outbound_schedule

# add downlink images to groundstation schedule(scheduled_contact)
def add_downlink_image(scheduled_image: ScheduledImaging):
    
    #for contact when the downlink occurs 
    downlink_contact = get_scheduled_contact(scheduled_image.downlink_contact_id)
        
    downlink_rate = get_ground_station(downlink_contact.groundstation_id).downlink_rate_mbps
     
    downlink = downlink_image(image_id = scheduled_image.id ,
                                    duration_of_downlink= scheduled_image.downlink_size/downlink_rate,
                                    size_of_image = scheduled_image.downlink_size)
    
    # if(downlink_contact.downlink_images == None):        
    #     downlink_contact.downlink_images = [downlink]
    # else:
    #     downlink_contact.downlink_images.append(scheduled_image.id)
    
    # downlink_contact = update_contact_with_downlink(downlink_contact)
    
    return downlink


    

