from typing import Optional, Union
from models.image_request import ImageRequest
from models.activity_request import ActivityRequest
from pydantic import BaseModel
from datetime import datetime

class RequestDetails(BaseModel):
    requestTime: Optional[datetime] = datetime.utcnow()

class EventRelayApiMessage(BaseModel):
    body: Union[ImageRequest, ActivityRequest]
    details: Optional[RequestDetails] = RequestDetails()
