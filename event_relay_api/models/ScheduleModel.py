from datetime import datetime
from pydantic import BaseModel

class ScheduleModel(BaseModel):
    id: int
    name: str
    group_name: str