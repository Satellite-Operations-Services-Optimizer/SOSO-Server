from pydantic import BaseModel, Field

class ImageRequest(BaseModel):
    latitude: float
    longitude: float
    priority: int
    image_type: str
    start_time: str
    end_time: str
    delivery_time: str
    revisit_time: str
