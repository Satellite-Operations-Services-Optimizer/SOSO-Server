from pydantic import BaseModel


class Window(BaseModel):
    start: str
    end: str

class Frequency(BaseModel):
    minimum_gap: str
    maximum_gap: str

class RepeatCycle(BaseModel):
    frequency: Frequency
    repetition: str
    
class ActivityRequest(BaseModel):
    target: str
    activity: str
    window: Window
    duration: str
    repeat_cycle: RepeatCycle
    payload_outage: str
    



