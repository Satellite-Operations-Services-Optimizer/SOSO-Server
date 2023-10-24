from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import uuid


class RequestDetails(BaseModel):
    requestTime: Optional[datetime] = None


class QueueRequest(BaseModel):
    event: dict = Field(...)
    correlationId: str = str(uuid.uuid4())

class ImageRequest(BaseModel):
    Latitude: float
    Longitude: float
    Priority: int
    ImageType: str
    ImageStartTime: str
    ImageEndTime: str
    DeliveryTime: str
    RevisitTime: str
    
