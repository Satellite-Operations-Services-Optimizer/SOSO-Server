from pydantic import BaseModel

class GroundStationCreationRequest(BaseModel):
    name: str
    latitude: float
    longitude: float
    elevation: float
    station_mask: float
    uplink_rate: float
    downlink_rate: float


class SatelliteCreationRequest(BaseModel): 
    storage_capacity: float
    power_capacity: float
    fov_max: float
    fov_min: float