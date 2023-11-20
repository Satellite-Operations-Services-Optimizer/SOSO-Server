from pydantic import BaseModel, Field
from typing import Optional

class Recurrence(BaseModel):
    Revisit: str
    NumberOfRevisits: Optional[int] = None
    RevisitFrequency: Optional[int] = None
    RevisitFrequencyUnits: Optional[str] = None

class ImageRequest(BaseModel):
    Latitude: float
    Longitude: float
    Priority: int
    ImageType: str
    ImageStartTime: str
    ImageEndTime: str
    DeliveryTime: str
    Recurrence: Recurrence
