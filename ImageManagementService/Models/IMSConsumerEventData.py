from Models.QueueModel import QueueRequest, QueueDetails
from pydantic import BaseModel
from typing import Optional


class IMSConsumerEvenData(BaseModel):
    message: QueueRequest = None
    details: Optional[QueueDetails] = None
