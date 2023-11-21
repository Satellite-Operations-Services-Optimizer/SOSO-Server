from pydantic import BaseModel, Json
from typing import Optional

class Satellite(BaseModel):
    name: str
    tle: Json
    storage_capacity: float
    power_capacity: float
    fov_max: float
    fov_min: float
    is_illuminated: bool
    under_outage: bool = False


   