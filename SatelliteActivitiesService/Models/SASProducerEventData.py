from Models.QueueModel import QueueRequest, QueueDetails
from pydantic import BaseModel


class SASProducerEvenData(BaseModel):
    message: QueueRequest = None
    details: QueueDetails = None
