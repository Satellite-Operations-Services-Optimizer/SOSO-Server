from Models.QueueModel import ImageRequest, RequestDetails
from pydantic import BaseModel
from typing import Optional


class IMSConsumerEvenData(BaseModel):
    body: ImageRequest = None
    details: Optional[RequestDetails] = None
