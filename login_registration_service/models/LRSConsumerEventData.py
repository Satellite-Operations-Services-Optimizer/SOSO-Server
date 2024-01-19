from Models.QueueModel import QueueRequest, QueueDetails
from pydantic import BaseModel
from typing import Optional


class LRSConsumerEvenData(BaseModel):
    message: QueueRequest = None
    details: Optional[QueueDetails] = None
