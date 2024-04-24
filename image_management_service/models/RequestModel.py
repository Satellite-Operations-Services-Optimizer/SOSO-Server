from pydantic import BaseModel, Field
from datetime import datetime, timedelta
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
    image_type: str
    window_start: datetime
    window_end: datetime
    delivery_deadline: datetime
    number_of_visits: int
    revisit_frequency: timedelta
    