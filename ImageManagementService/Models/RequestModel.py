from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class RequestDetails(BaseModel):
    requestTime: Optional[datetime] = None
    requestType: str
    
class ImageRequest(BaseModel):
    Latitude: float
    Longitude: float
    Priority: int
    ImageType: str
    ImageStartTime: str
    ImageEndTime: str
    DeliveryTime: str
    RevisitTime: str
    
