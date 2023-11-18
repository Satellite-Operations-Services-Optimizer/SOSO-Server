from Models.RequestModel import RequestDetails, ActivityRequest
from Models.ResponseModel import ResponseDetails
from Database.db_curd import maintenance_order

from pydantic import BaseModel


class SASProducerEventData(BaseModel):
    message: ActivityRequest = None
    details: RequestDetails = None
    