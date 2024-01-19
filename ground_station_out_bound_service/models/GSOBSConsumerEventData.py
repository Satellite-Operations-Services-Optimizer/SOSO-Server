from models.QueueModel import QueueRequest, QueueDetails
from pydantic import BaseModel
from typing import Optional


class GSOBSConsumerEvenData(BaseModel):
    message: QueueRequest = None
    details: Optional[QueueDetails] = None
