import uuid
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class QueueDetails(BaseModel):
    requestTime: Optional[datetime] = datetime.utcnow()
    requestOwner: str = Field(...)


class QueueRequest(BaseModel):
    event: dict = Field(...)
    correlationId: str = str(uuid.uuid4())


class QueueResponse(BaseModel):
    data: str = Field(...)
    status: str = Field(...)


class BasicAuth(BaseModel):
    username: str = Field(...)
    password: str = Field(...)
