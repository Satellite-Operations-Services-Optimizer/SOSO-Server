from typing import Optional
from Models.QueueModel import QueueRequest, QueueDetails
from pydantic import BaseModel, Field


class EventRelayRequestModel(BaseModel):
    message: QueueRequest = None
    details: Optional[QueueDetails] = None
    destinationServiceQueue: str = Field(...)

