from typing import Union
from satellite_activities_service.models.RequestModel import ActivityRequest, RequestDetails, OutageRequest
from pydantic import BaseModel
from typing import Optional


class SASConsumerEventData(BaseModel):
    message: Union[ActivityRequest, OutageRequest] = None
    details: Optional[RequestDetails] = None
