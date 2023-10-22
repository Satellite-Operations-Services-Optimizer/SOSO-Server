from typing import Optional
from Models.QueueModel import QueueRequest, QueueDetails
from pydantic import BaseModel


class ServerDataConsumerEvenData(BaseModel):
    message: QueueRequest = None
    details: Optional[QueueDetails] = None
