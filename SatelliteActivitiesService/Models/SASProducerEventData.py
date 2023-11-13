from Models.RequestModel import RequestDetails, ActivityRequest
from Models.ResponseModel import ResponseDetails
from config.database import maintenance_order

from pydantic import BaseModel


class SASProducerEventData(BaseModel):
    message: ActivityRequest = None
    details: RequestDetails = None
    
class SASProducerEventData2(BaseModel):
    message: maintenance_order = None
    details: ResponseDetails = None
