from Models.QueueModel import QueueRequest, QueueDetails
from pydantic import BaseModel


class SSProducerEvenData(BaseModel):
    message: QueueRequest = None
    details: QueueDetails = None
