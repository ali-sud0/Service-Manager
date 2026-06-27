from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import secrets
from ..core.database import get_db
from ..core.dependencies import get_current_active_user
from ..models.user import User
from ..models.booking import Booking, PaymentStatus
from ..models.payment import Payment
from ..schemas.payment import PaymentCreate, PaymentResponse
from ..services.notification_service import NotificationService

router = APIRouter(prefix="/payments", tags=["payments"])

@router.post("/process/{booking_id}")
async def process_payment(
    booking_id: int,
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Process payment for a booking"""
    
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if booking.status != "confirmed":
        raise HTTPException(status_code=400, detail="Booking must be confirmed before payment")
    
    if booking.payment_status == PaymentStatus.PAID:
        raise HTTPException(status_code=400, detail="Payment already processed")
    
    transaction_id = f"TXN_{secrets.token_hex(8).upper()}"
    
    payment = Payment(
        booking_id=booking_id,
        amount=booking.total_price,
        transaction_id=transaction_id,
        payment_method=payment_data.payment_method,
        paid_at=datetime.now()
    )
    
    booking.payment_status = PaymentStatus.PAID
    
    db.add(payment)
    db.commit()
    db.refresh(payment)
    
    NotificationService.create_notification(
        db, current_user.id,
        "Payment Successful",
        f"Payment of ${booking.total_price} for {booking.service.name} was successful. Transaction ID: {transaction_id}",
        "payment"
    )
    
    NotificationService.create_notification(
        db, booking.provider_id,
        "Payment Received",
        f"Payment of ${booking.total_price} received for booking #{booking_id}",
        "payment"
    )
    
    return {
        "message": "Payment successful",
        "transaction_id": transaction_id,
        "amount": booking.total_price,
        "booking_id": booking_id
    }


@router.get("/status/{booking_id}")
async def get_payment_status(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get payment status for a booking"""
    
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking.customer_id != current_user.id and booking.provider_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    payment = db.query(Payment).filter(Payment.booking_id == booking_id).first()
    
    return {
        "booking_id": booking_id,
        "payment_status": booking.payment_status,
        "amount": booking.total_price,
        "transaction_id": payment.transaction_id if payment else None,
        "paid_at": payment.paid_at if payment else None
    }