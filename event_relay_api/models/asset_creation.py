from pydantic import BaseModel

class GroundStationCreationRequest(BaseModel):
    name: str
    latitude: float
    longitude: float
    elevation: float
    send_mask: float
    receive_mask: float
    uplink_rate_mbps: float
    downlink_rate_mbps: float


class SatelliteCreationRequest(BaseModel): 
    storage_capacity: float
    power_capacity: float
    fov_max: float
    fov_min: float