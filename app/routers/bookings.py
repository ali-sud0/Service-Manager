from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timedelta
from ..core.database import get_db
from ..core.dependencies import get_current_active_user, require_role
from ..core.templates import templates
from ..models.user import User
from ..models.booking import Booking, BookingStatus, PaymentStatus
from ..models.schedule import Schedule
from ..models.service import Service
from ..schemas.booking import BookingCreate, BookingUpdate, BookingResponse
from ..services.booking_service import BookingService
from ..services.notification_service import NotificationService

router = APIRouter(prefix="/bookings", tags=["bookings"])

@router.get("/all")
async def get_all_bookings(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Get all bookings - admin only"""
    
    from sqlalchemy.orm import aliased
    
    Customer = aliased(User)
    Provider = aliased(User)
    
    results = db.query(
        Booking.id,
        Booking.status,
        Booking.payment_status,
        Booking.total_price,
        Booking.created_at,
        Service.name.label("service_name"),
        Customer.full_name.label("customer_name"),
        Customer.email.label("customer_email"),
        Provider.full_name.label("provider_name"),
        Schedule.start_time,
        Schedule.end_time
    ).join(
        Service, Booking.service_id == Service.id
    ).join(
        Customer, Booking.customer_id == Customer.id
    ).join(
        Provider, Booking.provider_id == Provider.id
    ).join(
        Schedule, Booking.schedule_id == Schedule.id
    ).order_by(Booking.created_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for booking in results:
        result.append({
            "id": booking.id,
            "customer_name": booking.customer_name,
            "customer_email": booking.customer_email,
            "provider_name": booking.provider_name,
            "service_name": booking.service_name,
            "start_time": booking.start_time.isoformat() if booking.start_time else None,
            "end_time": booking.end_time.isoformat() if booking.end_time else None,
            "status": booking.status.value if hasattr(booking.status, 'value') else booking.status,
            "payment_status": booking.payment_status.value if hasattr(booking.payment_status, 'value') else booking.payment_status,
            "total_price": float(booking.total_price),
            "created_at": booking.created_at.isoformat() if booking.created_at else None
        })
    
    return result


@router.post("/")
async def create_booking(
    booking_data: BookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # ONLY CUSTOMERS CAN BOOK SERVICES
    if current_user.role != "customer":
        raise HTTPException(status_code=403, detail="Only customers can book services.")
    
    # Check if schedule exists and is available
    schedule = db.query(Schedule).filter(
        Schedule.id == booking_data.schedule_id,
        Schedule.is_available == True
    ).first()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found or not available")
    
    # Check if schedule time has passed
    if schedule.end_time < datetime.now():
        raise HTTPException(status_code=400, detail="Cannot book a time slot that has already passed")
    
    # Check if schedule is already booked
    existing = db.query(Booking).filter(
        Booking.schedule_id == booking_data.schedule_id,
        Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED])
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="This time slot is already booked")
    
    # Get service
    service = db.query(Service).filter(Service.id == booking_data.service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # Check if provider is active
    if not service.provider.is_active:
        raise HTTPException(status_code=400, detail="Service provider is currently inactive")
    
    # Calculate cancellation deadline (2 hours before service start)
    cancellation_deadline = schedule.start_time - timedelta(hours=2)
    
    # Create booking
    booking = Booking(
        customer_id=current_user.id,
        provider_id=service.provider_id,
        service_id=booking_data.service_id,
        schedule_id=booking_data.schedule_id,
        total_price=service.price,
        cancellation_deadline=cancellation_deadline,
        status=BookingStatus.PENDING,
        payment_status=PaymentStatus.UNPAID
    )
    
    db.add(booking)
    
    # Mark schedule as booked
    schedule.is_available = False
    
    db.commit()
    db.refresh(booking)
    
    # Reload booking with relationships to get customer and service names
    booking_with_details = db.query(Booking).options(
        joinedload(Booking.customer),
        joinedload(Booking.provider),
        joinedload(Booking.service),
        joinedload(Booking.schedule)
    ).filter(Booking.id == booking.id).first()
    
    # Create notification for provider
    NotificationService.create_notification(
        db, service.provider_id,
        "New Booking Request",
        f"{current_user.full_name} has requested to book your service: {service.name} on {schedule.start_time.strftime('%Y-%m-%d %H:%M')}",
        "booking"
    )
    
    # Return full booking details
    return {
        "id": booking_with_details.id,
        "customer_id": booking_with_details.customer_id,
        "customer_name": booking_with_details.customer.full_name if booking_with_details.customer else None,
        "provider_id": booking_with_details.provider_id,
        "provider_name": booking_with_details.provider.full_name if booking_with_details.provider else None,
        "service_id": booking_with_details.service_id,
        "service_name": booking_with_details.service.name if booking_with_details.service else None,
        "schedule_id": booking_with_details.schedule_id,
        "schedule_start_time": booking_with_details.schedule.start_time if booking_with_details.schedule else None,
        "schedule_end_time": booking_with_details.schedule.end_time if booking_with_details.schedule else None,
        "status": booking_with_details.status.value if hasattr(booking_with_details.status, 'value') else booking_with_details.status,
        "payment_status": booking_with_details.payment_status.value if hasattr(booking_with_details.payment_status, 'value') else booking_with_details.payment_status,
        "total_price": booking_with_details.total_price,
        "cancellation_deadline": booking_with_details.cancellation_deadline,
        "created_at": booking_with_details.created_at
    }


@router.get("/my-bookings")
async def get_my_bookings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    bookings = db.query(Booking).options(
        joinedload(Booking.customer),
        joinedload(Booking.provider),
        joinedload(Booking.service),
        joinedload(Booking.schedule)
    ).filter(Booking.customer_id == current_user.id).all()
    
    result = []
    for booking in bookings:
        can_cancel = BookingService.check_cancellation_possible(booking)
        time_left = BookingService.get_cancellation_time_left(booking)
        
        formatted_time_left = None
        
        if (time_left and time_left.total_seconds() > 0 and 
            booking.status == BookingStatus.CONFIRMED and 
            booking.payment_status != PaymentStatus.PAID):
            
            total_seconds = int(time_left.total_seconds())
            days = total_seconds // 86400
            hours = (total_seconds % 86400) // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            if days > 0:
                formatted_time_left = f"{days}d {hours}h {minutes}m"
            elif hours > 0:
                formatted_time_left = f"{hours}h {minutes}m"
            elif minutes > 0:
                formatted_time_left = f"{minutes}m"
            else:
                formatted_time_left = f"{seconds}s"
        
        result.append({
            "id": booking.id,
            "service_name": booking.service.name if booking.service else None,
            "provider_name": booking.provider.full_name if booking.provider else None,
            "start_time": booking.schedule.start_time if booking.schedule else None,
            "status": booking.status.value if hasattr(booking.status, 'value') else booking.status,
            "payment_status": booking.payment_status.value if hasattr(booking.payment_status, 'value') else booking.payment_status,
            "total_price": booking.total_price,
            "can_cancel": can_cancel,
            "cancellation_time_left": formatted_time_left
        })
    
    return result


@router.get("/provider-bookings")
async def get_provider_bookings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role not in ["provider", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    results = db.query(
        Booking.id,
        Booking.status,
        Booking.payment_status,
        Booking.total_price,
        Booking.created_at,
        Service.name.label("service_name"),
        User.full_name.label("customer_name"),
        User.email.label("customer_email"),
        Schedule.start_time,
        Schedule.end_time
    ).join(
        Service, Booking.service_id == Service.id
    ).join(
        User, Booking.customer_id == User.id
    ).join(
        Schedule, Booking.schedule_id == Schedule.id
    ).filter(
        Booking.provider_id == current_user.id
    ).all()
    
    result = []
    for booking in results:
        result.append({
            "id": booking.id,
            "customer_name": booking.customer_name,
            "customer_email": booking.customer_email,
            "service_name": booking.service_name,
            "start_time": booking.start_time,
            "end_time": booking.end_time,
            "status": booking.status.value if hasattr(booking.status, 'value') else booking.status,
            "payment_status": booking.payment_status.value if hasattr(booking.payment_status, 'value') else booking.payment_status,
            "total_price": booking.total_price,
            "created_at": booking.created_at
        })
    
    return result


@router.put("/{booking_id}/status")
async def update_booking_status(
    booking_id: int,
    status_update: BookingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Check permission
    if current_user.role == "provider" and booking.provider_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    elif current_user.role == "customer" and booking.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    old_status = booking.status
    booking.status = BookingStatus(status_update.status)
    
    # Get service name for notification
    service = db.query(Service).filter(Service.id == booking.service_id).first()
    service_name = service.name if service else "Service"
    
    # Create notification for customer
    if status_update.status == "confirmed":
        NotificationService.create_notification(
            db, booking.customer_id,
            "Booking Confirmed",
            f"Your booking for {service_name} has been confirmed!",
            "booking"
        )
    elif status_update.status == "rejected":
        NotificationService.create_notification(
            db, booking.customer_id,
            "Booking Rejected",
            f"Sorry, your booking for {service_name} was rejected.",
            "booking"
        )
    elif status_update.status == "cancelled":
        # Make schedule available again if cancelled
        if booking.schedule:
            booking.schedule.is_available = True
        customer = db.query(User).filter(User.id == booking.customer_id).first()
        customer_name = customer.full_name if customer else "Customer"
        NotificationService.create_notification(
            db, booking.provider_id,
            "Booking Cancelled",
            f"{customer_name} cancelled booking for {service_name}",
            "booking"
        )
    
    db.commit()
    
    return {"message": f"Booking {status_update.status} successfully"}


@router.post("/{booking_id}/cancel")
async def cancel_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    booking = db.query(Booking).options(
        joinedload(Booking.customer),
        joinedload(Booking.provider),
        joinedload(Booking.service),
        joinedload(Booking.schedule)
    ).filter(Booking.id == booking_id).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if not BookingService.check_cancellation_possible(booking):
        raise HTTPException(status_code=400, detail="Cancellation deadline has passed")
    
    booking.status = BookingStatus.CANCELLED
    if booking.schedule:
        booking.schedule.is_available = True
    
    db.commit()
    
    # Notify provider
    NotificationService.create_notification(
        db, booking.provider_id,
        "Booking Cancelled",
        f"{current_user.full_name} cancelled booking for {booking.service.name if booking.service else 'Service'}",
        "booking"
    )
    
    return {"message": "Booking cancelled successfully"}



