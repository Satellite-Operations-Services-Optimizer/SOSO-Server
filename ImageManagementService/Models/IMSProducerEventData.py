from Models.QueueModel import ImageRequest, RequestDetails
from pydantic import BaseModel


class IMSProducerEvenData(BaseModel):
    message: ImageRequest = None
    details: RequestDetails = None
