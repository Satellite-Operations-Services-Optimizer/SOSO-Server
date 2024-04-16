from pydantic import BaseModel


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
    PayloadOutage: str
    
class OutageOrderCreationRequest(BaseModel):
    Target: str
    Activity: str
    Window: Window

