from typing import Optional, Union
from models.ImageRequestModel import ImageRequest
from models.ActivityRequestModel import ActivityRequest
from pydantic import BaseModel
from datetime import datetime

class RequestDetails(BaseModel):
    requestTime: Optional[datetime] = datetime.utcnow()

class EventRelayApiMessage(BaseModel):
    body: Union[ImageRequest, ActivityRequest]
    details: Optional[RequestDetails] = RequestDetails()
