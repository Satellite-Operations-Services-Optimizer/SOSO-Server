from pydantic import BaseModel

class GroundStation(BaseModel):
    name: str
    latitude: float
    longitude: float
    elevation: float
    station_mask: float
    uplink_rate: float
    downlink_rate: float

