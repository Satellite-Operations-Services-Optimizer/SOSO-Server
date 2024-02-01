from models.RequestModel import RequestDetails, ActivityRequest
from models.ResponseModel import ResponseDetails, scheduling_options
from helpers.db_curd import maintenance_order

from pydantic import BaseModel


class SASProducerOrderData(BaseModel):
    message: ActivityRequest = None
    details: RequestDetails = None

class SASProducerScheduleOptionsData(BaseModel):
    body: scheduling_options = None
    details: RequestDetails = None    