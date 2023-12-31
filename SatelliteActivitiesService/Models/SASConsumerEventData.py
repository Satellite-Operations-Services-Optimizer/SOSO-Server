from typing import Union
from Models.RequestModel import ActivityRequest, RequestDetails, OutageRequest
from pydantic import BaseModel
from typing import Optional


class SASConsumerEventData(BaseModel):
    message: Union[ActivityRequest, OutageRequest] = None
    details: Optional[RequestDetails] = None
