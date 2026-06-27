from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class PaymentCreate(BaseModel):
    payment_method: str = "credit_card"

class PaymentResponse(BaseModel):
    id: int
    booking_id: int
    amount: float
    transaction_id: str
    payment_method: str
    paid_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True