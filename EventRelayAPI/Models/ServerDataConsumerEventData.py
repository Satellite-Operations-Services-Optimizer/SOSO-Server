from typing import Optional
from Models.QueueModel import ImageRequest, RequestDetails, ImageRequest
from pydantic import BaseModel


class Message(BaseModel):
    body: ImageRequest = None
    details: Optional[RequestDetails] = None
