from Models.RequestModel import RequestDetails, ActivityRequest
from pydantic import BaseModel


class SASProducerEventData(BaseModel):
    message: ActivityRequest = None
    details: RequestDetails = None
