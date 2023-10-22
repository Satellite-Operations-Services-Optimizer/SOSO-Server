from Models.QueueModel import QueueRequest, QueueDetails
from pydantic import BaseModel


class IMSProducerEvenData(BaseModel):
    message: QueueRequest = None
    details: QueueDetails = None
