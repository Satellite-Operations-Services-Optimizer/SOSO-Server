from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import uuid


class QueueDetails(BaseModel):
    requestTime: Optional[datetime] = None
    requestOwner: str = Field(...)


class QueueRequest(BaseModel):
    event: dict = Field(...)
    correlationId: str = str(uuid.uuid4())
