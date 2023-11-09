from Models.RequestModel import RequestDetails, ActivityRequest
from Models.ResponseModel import ResponseDetails, satellite_maintenance_request

from pydantic import BaseModel


class SASProducerEventData(BaseModel):
    message: ActivityRequest = None
    details: RequestDetails = None
    
class SASProducerEventData2(BaseModel):
    message: satellite_maintenance_request = None
    details: ResponseDetails = None
