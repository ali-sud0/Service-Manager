from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from ..models.booking import Booking, BookingStatus
from ..models.schedule import Schedule
from ..models.service import Service
from ..models.user import User

class BookingService:
    
    @staticmethod
    def check_cancellation_possible(booking: Booking) -> bool:
        """Check if booking can be cancelled (at least 2 hours before start)"""
        if booking.status in [BookingStatus.CANCELLED, BookingStatus.COMPLETED]:
            return False
        
        schedule = booking.schedule
        if not schedule:
            return False
        
        cancellation_limit = schedule.start_time - timedelta(hours=2)
        return datetime.now() < cancellation_limit
    
    @staticmethod
    def get_cancellation_time_left(booking: Booking) -> timedelta:
        """Get remaining time for cancellation"""
        schedule = booking.schedule
        if not schedule:
            return timedelta(0)
        
        cancellation_limit = schedule.start_time - timedelta(hours=2)
        remaining = cancellation_limit - datetime.now()
        return remaining if remaining > timedelta(0) else timedelta(0)
    
    @staticmethod
    def can_book_schedule(db: Session, schedule_id: int, service_id: int) -> bool:
        """Check if a schedule can be booked"""
        schedule = db.query(Schedule).filter(
            Schedule.id == schedule_id,
            Schedule.service_id == service_id,
            Schedule.is_available == True
        ).first()
        
        if not schedule:
            return False
        
        # Check if schedule is already booked
        existing_booking = db.query(Booking).filter(
            Booking.schedule_id == schedule_id,
            Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED])
        ).first()
        
        return existing_booking is None