from Models.QueueModel import QueueRequest, QueueDetails
from pydantic import BaseModel


class LRSProducerEvenData(BaseModel):
    message: QueueRequest = None
    details: QueueDetails = None
