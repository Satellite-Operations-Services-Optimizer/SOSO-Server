from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from typing import Optional

class image_activity(BaseModel):
    image_id: int
    image_type: str
    priority: int
    start_time: datetime
    
class maintenance_activity(BaseModel):
    activity_id: int
    description: str
    priority: int
    start_time: datetime
    payload_flag: bool
    duration: timedelta

# Intended for the satellite to send
class downlink_activity(BaseModel):
    image_id: list[int]
    start_time: datetime
    downlink_stop: datetime

class satellite_schedule(BaseModel):
    satellite_name: str
    schedule_id: int
    activity_window: tuple[datetime,datetime]
    image_activities: list[image_activity] = None
    maintenance_activities: list[maintenance_activity] = None
    downlink_activities: list[downlink_activity] = None

# Intended for the ground station to recieve
class downlink_image(BaseModel):
    image_id: int
    duration_of_downlink: timedelta
    size_of_image: float
    
class ground_station_request(BaseModel):
    station_name: str
    satellite: str
    acquisition_of_signal: datetime
    loss_of_signal: datetime
    satellite_schedule_id: int
    downlink_images: list[downlink_image] = None
            
class outbound_schedule(BaseModel):
    contact_id: int
    satellite_name: str
    activity_window: tuple[datetime,datetime]
    image_activities: list[image_activity] = None
    maintenance_activities: list[maintenance_activity] = None
    downlink_activities: list[downlink_activity] = None
    schedule_status: str
