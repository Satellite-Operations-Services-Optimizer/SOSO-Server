from typing import Optional
from Models.QueueModel import RequestDetails, ImageRequest
from pydantic import BaseModel, Field




class EventRelayRequestModel(BaseModel):
    body: ImageRequest