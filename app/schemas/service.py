from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ServiceCreate(BaseModel):
    name: str
    description: str
    category: str
    price: float
    duration_minutes: int
    image_url: Optional[str] = None

class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    duration_minutes: Optional[int] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None

class ServiceResponse(BaseModel):
    id: int
    name: str
    description: str
    category: str
    price: float
    duration_minutes: int
    image_url: str
    is_active: bool
    provider_id: int
    created_at: datetime
    average_rating: Optional[float] = None
    
    class Config:
        from_attributes = True