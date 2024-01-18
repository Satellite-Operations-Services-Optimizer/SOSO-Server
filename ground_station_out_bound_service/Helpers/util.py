from typing import Optional
from app_config.logs import logging
from Helpers.data import schedule
from data import get_image_request, get_scheduled_image, get_maintenance_request, get_scheduled_maintenance, get_schedule, get_satellite, get_ground_station_request, get_ground_station
from data import scheduled_images, scheduled_maintenance, scheduled_outages
from Models.ScheduleModel import satellite_schedule, image_activity, maintenance_activity, downlink_activity, ground_station_request, downlink_image
import json

def make_image_activity(image_id: int, state: str):
    image_order = get_image_request(image_id)
    scheduled_image = get_scheduled_image(image_id, state)
    
    activity = image_activity(image_id = image_id, type = image_order.image_res,
                              priority = image_order.priority, start_time = scheduled_image.downlink_start)
    return activity

def make_maintenance_activity(maintenance_id, state: str):
    maintenance_order = get_maintenance_request(maintenance_id)
    scheduled_maintenance = get_scheduled_maintenance(maintenance_id, state)
    
    activity = image_activity(activity_id = maintenance_id, description = maintenance_order.description,
                              priority = maintenance_order.priority, start_time = scheduled_maintenance.maintenance_start,
                              payload_flag = maintenance_order.operations_flag, duration = maintenance_order.duration)
    return activity


# create downlink activities, add them to the schedule

def make_satellite_schedule(schedule_id: int, activities_image: list[image_activity], activities_maintenance: list[maintenance_activity]):
    active_window = [min(activities_image + activities_maintenance, key=lambda x: x.start_time).start_time,
                     max(activities_image + activities_maintenance, key=lambda x: x.start_time).start_time ]
    schedule = get_schedule(schedule_id)
    satellite = get_satellite(schedule.satellite_id)
    
    satellite_schedule_to_send = satellite_schedule(satellite_name = satellite.name, schedule_id = schedule.id, activity_window = active_window,
                                                    image_activities = activities_image, maintenance_activities = activities_maintenance)
    
    return satellite_schedule_to_send

def make_ground_station_request(request_id: int, activities: list[downlink_image]):
    gs_request = get_ground_station_request(request_id)
    ground_station = get_ground_station(gs_request.station_id)
    schedule = get_schedule(gs_request.schedule_id)
    satellite = get_satellite(schedule.satellite_id)
    ground_station_request_to_send = ground_station_request(station_name = ground_station.name, satellite = satellite.name, acquisition_of_signal = gs_request.signal_aquisition,
                                                            loss_of_signal = gs_request.signal_loss, satellite_schedule_id = gs_request.schedule_id, images_to_be_downlinked = activities)
    return ground_station_request_to_send

def parse_created_event(request_body: json):
    
    

