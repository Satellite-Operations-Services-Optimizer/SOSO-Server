import uuid
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class RequestDetails(BaseModel):
    requestTime: Optional[datetime] = datetime.utcnow()

class ImageRequest(BaseModel):
    Latitude: float
    Longitude: float
    Priority: int
    ImageType: str
    ImageStartTime: str
    ImageEndTime: str
    DeliveryTime: str
    RevisitTime: str
    




class BasicAuth(BaseModel):
    username: str = Field(...)
    password: str = Field(...)
