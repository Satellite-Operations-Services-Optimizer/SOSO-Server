from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class RequestDetails(BaseModel):
    requestTime: Optional[datetime] = None
    requestType: str
    
class Recurrence(BaseModel):
    Revisit: str
    NumberOfRevisits: Optional[int] = None
    RevisitFrequency: Optional[int] = None
    RevisitFrequencyUnits: Optional[str] = None

class ImageRequest(BaseModel):
    Latitude: float
    Longitude: float
    Priority: int
    ImageType: str
    ImageStartTime: str
    ImageEndTime: str
    DeliveryTime: str
    Recurrence: Recurrence
    
class ImageOrder(BaseModel):
    id: int
    latitude: float
    longitude: float
    priority: int
    image_res: int
    image_height: int
    image_width: int
    start_time: datetime
    end_time: datetime
    delivery_deadline: datetime
    retake_count: int
    retake_freq_min: int
    retake_freq_max:int
    