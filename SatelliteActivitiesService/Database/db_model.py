from pydantic import BaseModel
from datetime import datetime, timedelta


class satellite_maintenance_request(BaseModel):
    id: int
    activity_description: str
    start_time: datetime
    end_time: datetime
    duration: timedelta
    repetition: timedelta
    frequency_min_gap: timedelta
    frequency_max_gap: timedelta
    payload_flag: bool
    
    class Config:
        from_attributes = True


# CREATE INDEX idx_time: ON satellite_maintenance_request(BaseModel):
# 	image_start_time,
# 	image_end_time


class satellite_maintenance_request_bridge(BaseModel):
    satellite_id: int
    maintenance_id: int
    
    class Config:
        from_attributes = True
	# PRIMARY KEY (satellite_id, maintenance_id)
	# CONSTRAint fk_satellite_id: FOREIGN KEY (satellite_id) REFERENCES satellite(BaseModel):id) ON UPDATE CASCADE ON DELETE CASCADE,
	# CONSTRAint fk_maintenance_id: FOREIGN KEY (maintenance_id) REFERENCES satellite_maintenance_request(BaseModel):id) ON UPDATE CASCADE ON DELETE CASCADE


class satellite_outage_request(BaseModel):
    id: int
    satellite_id: int
    start_time: datetime
    end_time: datetime
    status: int
    
    class Config:
        from_attributes = True


# CREATE INDEX idx_time: ON satellite_outage_request(BaseModel):
# 	image_start_time,
# 	image_end_time


class satellite_outage_request_bridge(BaseModel):
    satellite_id: int
    outage_request_id: int
    
    class Config:
        from_attributes = True
	# PRIMARY KEY (satellite_id, outage_request_id)
	# CONSTRAint fk_satellite_id: FOREIGN KEY (satellite_id) REFERENCES satellite(BaseModel):id) ON UPDATE CASCADE ON DELETE CASCADE,
	# CONSTRAint fk_outage_request_id: FOREIGN KEY (outage_request_id) REFERENCES satellite_outage_request(BaseModel):id) ON UPDATE CASCADE ON DELETE CASCADE

class outage_activity(BaseModel):
    id: int
    satellite_id: int
    start_time: datetime
    end_time: datetime
    status: int
    satellite_activity_schedule_id: int
    
    class Config:
        from_attributes = True

class ground_station_outage_request(BaseModel):
    id: int
    ground_station_id: int
    start_time: datetime
    end_time: datetime
    status: int
    
    class Config:
        from_attributes = True
	# CONSTRAint fk_ground_station_id: FOREIGN KEY (ground_station_id) REFERENCES ground_station(BaseModel):id) ON UPDATE CASCADE ON DELETE CASCADE


# CREATE INDEX idx_time: ON ground_station_outage_request(BaseModel):
# 	image_start_time,
# 	image_end_time



class satellite_activity_schedule(BaseModel):
    id: int
    satellite_id: int
    start_time: datetime
    end_time: datetime
    status: int
    
    class Config:
        from_attributes = True
	# CONSTRAint fk_satellite_id: FOREIGN KEY (satellite_id) REFERENCES satellite(BaseModel):id) ON UPDATE CASCADE ON DELETE CASCADE


class image_activity(BaseModel):
    id: int
    image_resolution: int
    priority: int
    image_time: datetime
    satellite_activity_schedule_id: int
    
    class Config:
        from_attributes = True
    # CONSTRAint fk_satellite_activity_schedule_id: FOREIGN KEY (satellite_activity_schedul_id) REFERENCES satellite_actvity_schedule(BaseModel):id) ON UPDATE CASCADE ON DELETE CASCADE


class maintenance_activity(BaseModel):
    id: int
    description: str
    priority: int
    start_time: datetime
    duration: timedelta
    payload_flag: bool
    satellite_activity_schedule_id: int
    
    class Config:
        from_attributes = True
	# CONSTRAint fk_satellite_activity_schedule_id: FOREIGN KEY (satellite_activity_schedul_id) REFERENCES satellite_actvity_schedule(BaseModel):id) ON UPDATE CASCADE ON DELETE CASCADE
