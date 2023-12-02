from datetime import datetime
from pydantic import BaseModel

class ScheduleModel(BaseModel):
    id: int
    satellite_id: int
    ground_station_id: int
    asset_type: int
    start_time: datetime
    end_time: datetime
    status: str
