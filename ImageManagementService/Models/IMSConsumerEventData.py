from RequestModel import ImageRequest, RequestDetails
from pydantic import BaseModel
from typing import Optional


class IMSConsumerEventData(BaseModel):
    body: ImageRequest = None
    details: Optional[RequestDetails] = None
