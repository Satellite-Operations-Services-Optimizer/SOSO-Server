from models.RequestModel import ActivityRequest, RequestDetails
from pydantic import BaseModel
from typing import Optional


class SASConsumerEventData(BaseModel):
    message: ActivityRequest = None
    details: Optional[RequestDetails] = None
