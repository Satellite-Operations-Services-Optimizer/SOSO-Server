from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime

app = FastAPI()

class ImageRequest(BaseModel):
    latitude: float
    longitude: float
    priority: Literal["low", "medium", "high"] = "low"
    resolution: Literal["low", "medium", "high"]
    imaging_time: TimeRange = Depends()
    deliver_by: datetime
    revisit: Repeat



@app.get("/")
def index():
    return {"message": "Hello, I am the image management server!"}

@app.get("/request_image")
def index(region: ImageRequest = Depends()):
    return {"message": "Hello, I am the image management server!"}
