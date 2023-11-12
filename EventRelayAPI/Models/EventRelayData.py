from typing import Optional, Union
from Models.ImageRequestModel import ImageRequest
from Models.ActivityRequestModel import ActivityRequest
from pydantic import BaseModel
from datetime import datetime

class RequestDetails(BaseModel):
    requestTime: Optional[datetime] = datetime.utcnow()
    requestType: str
    
class EventRelayApiMessage(BaseModel):
    body: Union[ImageRequest, ActivityRequest]
    details: Optional[RequestDetails]