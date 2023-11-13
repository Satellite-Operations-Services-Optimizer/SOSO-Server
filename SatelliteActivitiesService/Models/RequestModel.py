from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class RequestDetails(BaseModel):
    requestTime: Optional[datetime] = None

class Window(BaseModel):
    Start: str
    End: str

class Frequency(BaseModel):
    MinimumGap: str
    MaximumGap: str

class RepeatCycle(BaseModel):
    Frequency: Frequency
    Repetition: str

class ActivityRequest(BaseModel):
    Target: str
    Activity: str
    Window: Window
    Duration: str
    RepeatCycle: RepeatCycle
    PayloadOutage: bool
    
class OutageRequest(BaseModel):
    Target: str
    Activity: str
    Window: Window
