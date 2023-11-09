from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from typing import Optional


class ResponseDetails(BaseModel):
    requestTime: Optional[datetime] = None


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