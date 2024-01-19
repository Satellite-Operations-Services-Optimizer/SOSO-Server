from .RequestModel import ImageRequest, RequestDetails
from pydantic import BaseModel



class IMSProducerEventData(BaseModel):
    message: ImageRequest = None
    details: RequestDetails = None
