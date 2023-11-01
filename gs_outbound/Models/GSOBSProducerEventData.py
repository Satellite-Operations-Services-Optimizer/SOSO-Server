from Models.QueueModel import QueueRequest, QueueDetails
from pydantic import BaseModel


class GSOBSProducerEvenData(BaseModel):
    message: QueueRequest = None
    details: QueueDetails = None
