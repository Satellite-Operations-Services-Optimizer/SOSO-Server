from Models.RequestModel import RequestDetails, ActivityRequest
from Models.ResponseModel import ResponseDetails, scheduling_options
from Helpers.db_curd import maintenance_order

from pydantic import BaseModel


class SASProducerOrderData(BaseModel):
    message: ActivityRequest = None
    details: RequestDetails = None

class SASProducerScheduleOptionsData(BaseModel):
    body: scheduling_options = None
    details: RequestDetails = None    