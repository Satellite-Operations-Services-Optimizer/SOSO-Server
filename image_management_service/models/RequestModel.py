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
    start_time: datetime
    end_time: datetime
    delivery_deadline: datetime
    visits_remaining: int
    revisit_frequency: timedelta
    