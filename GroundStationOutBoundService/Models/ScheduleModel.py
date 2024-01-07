from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from typing import Optional

class image_activity(Basemodel):
    image_id: int
    type: str
    priority: str
    image_time: datetime
    
class maintenance_activity(Basemodel):
    activity_id: int
    description: str
    priority: str
    activity_time: datetime
    payload_flag: bool
    duration: timedelta

# Intended for the satellite to send
class downlink_activity(Basemodel):
    image_id: int
    downlink_start: datetime
    downlink_stop: datetime

class satellite_schedule(Basemodel):
    satellite_name: str
    schedule_id: int
    activity_window: list[datetime,datetime]
    image_activities: list[image_activity]
    maintenance_activities: list[maintenance_activity]
    downlink_activities: list[downlink_activity]

# Intended for the ground station to recieve
class downlink_image(Basemodel):
    image_id: int
    duration_of_downlink: timedelta
    size_of_image: str
    
class ground_station_request(Basemodel):
    station_name: str
    satellite: str
    acquisition_of_signal: datetime
    loss_of_signal: datetime
    satellite_schedule_id: int
    images_to_be_downlinked: list[downlink_image]