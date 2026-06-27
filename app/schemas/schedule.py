from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ScheduleCreate(BaseModel):
    service_id: int
    start_time: datetime
    end_time: datetime

class ScheduleResponse(BaseModel):
    id: int
    service_id: int
    start_time: datetime
    end_time: datetime
    is_available: bool
    
    class Config:
        from_attributes = True