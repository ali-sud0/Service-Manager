from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from ..core.database import get_db
from ..core.dependencies import get_current_active_user, get_current_user_optional
from ..models.user import User
from ..models.schedule import Schedule
from ..models.service import Service
from ..models.booking import Booking, BookingStatus
from ..schemas.schedule import ScheduleCreate, ScheduleResponse

router = APIRouter(prefix="/schedules", tags=["schedules"])

@router.post("/")
async def create_schedule(
    schedule_data: ScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Check if user owns the service
    service = db.query(Service).filter(Service.id == schedule_data.service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    if service.provider_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Check for overlapping schedules
    overlapping = db.query(Schedule).filter(
        Schedule.service_id == schedule_data.service_id,
        Schedule.start_time < schedule_data.end_time,
        Schedule.end_time > schedule_data.start_time
    ).first()
    
    if overlapping:
        raise HTTPException(status_code=400, detail="Schedule overlaps with existing schedule")
    
    # Check duration matches service duration
    duration = (schedule_data.end_time - schedule_data.start_time).total_seconds() / 60
    if abs(duration - service.duration_minutes) > 5:  # Allow 5 minutes tolerance
        raise HTTPException(
            status_code=400, 
            detail=f"Schedule duration must match service duration ({service.duration_minutes} minutes)"
        )
    
    schedule = Schedule(**schedule_data.dict())
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    
    return schedule

@router.get("/service/{service_id}")
async def get_service_schedules(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get schedules for a service - accessible by everyone"""
    service = db.query(Service).filter(Service.id == service_id).first()
    
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    now = datetime.now()
    
    is_admin = current_user and current_user.role == "admin"
    is_owner = current_user and service.provider_id == current_user.id
    
    if is_admin or is_owner:
        schedules = db.query(Schedule).filter(
            Schedule.service_id == service_id
        ).order_by(Schedule.start_time).all()
        
        result = []
        for schedule in schedules:
            booking = db.query(Booking).filter(
                Booking.schedule_id == schedule.id,
                Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED])
            ).first()
            
            result.append({
                "id": schedule.id,
                "service_id": schedule.service_id,
                "start_time": schedule.start_time,
                "end_time": schedule.end_time,
                "is_available": schedule.is_available and not booking,
                "has_booking": booking is not None,
                "is_passed": schedule.end_time < now,
                "booking_status": booking.status.value if booking else None
            })
    else:
        schedules = db.query(Schedule).filter(
            Schedule.service_id == service_id,
            Schedule.is_available == True,
            Schedule.start_time > now
        ).order_by(Schedule.start_time).all()
        
        result = []
        for schedule in schedules:
            booking = db.query(Booking).filter(
                Booking.schedule_id == schedule.id,
                Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED])
            ).first()
            
            if not booking:
                result.append({
                    "id": schedule.id,
                    "service_id": schedule.service_id,
                    "start_time": schedule.start_time,
                    "end_time": schedule.end_time,
                    "is_available": True,
                    "is_passed": False
                })
    
    return result

@router.delete("/{schedule_id}")
async def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    service = db.query(Service).filter(Service.id == schedule.service_id).first()
    if service.provider_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Check if schedule has any bookings
    booking = db.query(Booking).filter(Booking.schedule_id == schedule_id).first()
    if booking:
        raise HTTPException(status_code=400, detail="Cannot delete schedule with existing bookings")
    
    db.delete(schedule)
    db.commit()
    
    return {"message": "Schedule deleted successfully"}



@router.patch("/{schedule_id}/toggle-status")
async def toggle_schedule_status(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Toggle schedule availability - provider or admin only"""
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    # Check if user owns the service or is admin
    service = db.query(Service).filter(Service.id == schedule.service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    if current_user.role != "admin" and service.provider_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Toggle the status
    schedule.is_available = not schedule.is_available
    db.commit()
    
    return {
        "message": f"Schedule {'activated' if schedule.is_available else 'deactivated'} successfully",
        "is_available": schedule.is_available
    }