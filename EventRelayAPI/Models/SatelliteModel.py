from pydantic import BaseModel #,Json

""" class Satellite(BaseModel):
    name: str
    tle: Json
    storage_capacity: float
    power_capacity: float
    fov_max: float
    fov_min: float
    is_illuminated: bool
    under_outage: bool """

class SatelliteCreationRequest(BaseModel): 
    storage_capacity: float
    power_capacity: float
    fov_max: float
    fov_min: float