from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class BookingCreate(BaseModel):
    service_id: int
    schedule_id: int

class BookingUpdate(BaseModel):
    status: Optional[str] = None

class BookingResponse(BaseModel):
    id: int
    customer_id: int
    provider_id: int
    service_id: int
    schedule_id: int
    status: str
    payment_status: str
    total_price: float
    cancellation_deadline: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True