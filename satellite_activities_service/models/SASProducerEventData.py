from satellite_activities_service.models.RequestModel import RequestDetails, ActivityRequest
from satellite_activities_service.models.ResponseModel import ResponseDetails, scheduling_options
from pydantic import BaseModel


class SASProducerOrderData(BaseModel):
    message: ActivityRequest = None
    details: RequestDetails = None

class SASProducerScheduleOptionsData(BaseModel):
    body: scheduling_options = None
    details: RequestDetails = None    